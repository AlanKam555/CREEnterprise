"""
CRE Enterprise Suite - FastAPI Backend
Complete financial modeling, authentication, ML predictions, and multi-user support
"""
import os
import sqlite3
import uuid
import json
import hashlib
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from typing import Optional
import io
import bcrypt
from documents import PDFGenerator, ExcelProcessor
from pydantic import BaseModel, Field, EmailStr
import jwt
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd

# ============ CONFIG ============
DB_PATH = Path(__file__).parent / "cre.db"
SECRET_KEY = "cre-enterprise-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

security = HTTPBearer(auto_error=False)

# ============ DATABASE SETUP ============
def get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT DEFAULT 'analyst',
            created_at TEXT,
            is_active BOOLEAN DEFAULT 1
        );
        
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            asset_type TEXT,
            address TEXT,
            purchase_price REAL,
            purchase_date TEXT,
            data JSON,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        
        CREATE TABLE IF NOT EXISTS rent_rolls (
            id TEXT PRIMARY KEY,
            property_id TEXT NOT NULL,
            unit_number TEXT,
            tenant_name TEXT,
            lease_start TEXT,
            lease_end TEXT,
            monthly_rent REAL,
            status TEXT,
            data JSON,
            created_at TEXT,
            FOREIGN KEY(property_id) REFERENCES properties(id)
        );
        
        CREATE TABLE IF NOT EXISTS valuations (
            id TEXT PRIMARY KEY,
            property_id TEXT NOT NULL,
            valuation_type TEXT,
            irr REAL,
            coc REAL,
            dscr REAL,
            noi REAL,
            cap_rate REAL,
            valuation_data JSON,
            created_at TEXT,
            FOREIGN KEY(property_id) REFERENCES properties(id)
        );
        
        CREATE TABLE IF NOT EXISTS market_comps (
            id TEXT PRIMARY KEY,
            asset_type TEXT,
            location TEXT,
            price_per_unit REAL,
            cap_rate REAL,
            data JSON,
            created_at TEXT
        );
        
        CREATE TABLE IF NOT EXISTS memos (
            id TEXT PRIMARY KEY,
            property_id TEXT NOT NULL,
            title TEXT,
            content TEXT,
            memo_type TEXT,
            created_at TEXT,
            FOREIGN KEY(property_id) REFERENCES properties(id)
        );
        
        CREATE TABLE IF NOT EXISTS ml_predictions (
            id TEXT PRIMARY KEY,
            property_id TEXT NOT NULL,
            prediction_type TEXT,
            predicted_value REAL,
            confidence REAL,
            model_version TEXT,
            created_at TEXT,
            FOREIGN KEY(property_id) REFERENCES properties(id)
        );
    """)
    db.commit()
    db.close()

init_db()

# ============ PYDANTIC MODELS ============
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "analyst"

class UserLogin(BaseModel):
    email: str
    password: str

class PropertyCreate(BaseModel):
    name: str
    asset_type: str
    address: str
    purchase_price: float
    purchase_date: str

class RentRollEntry(BaseModel):
    unit_number: str
    tenant_name: str
    lease_start: str
    lease_end: str
    monthly_rent: float
    status: str = "occupied"

class ValuationRequest(BaseModel):
    property_id: str
    valuation_type: str
    noi: float
    cap_rate: float
    debt_service: float
    equity_invested: float

class MemoRequest(BaseModel):
    property_id: str
    title: str
    memo_type: str

# ============ AUTHENTICATION ============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def verify_token(authorization: Optional[str] = Header(None)):
    try:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token")
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ FINANCIAL CALCULATIONS ============
class FinancialCalculator:
    @staticmethod
    def calculate_irr(cash_flows: List[float], guess: float = 0.1) -> float:
        """Calculate Internal Rate of Return"""
        try:
            # Newton-Raphson method for IRR
            rate = guess
            for _ in range(100):
                npv = sum(cf / (1 + rate) ** i for i, cf in enumerate(cash_flows))
                npv_derivative = sum(-i * cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cash_flows))
                if abs(npv_derivative) < 1e-6:
                    break
                rate = rate - npv / npv_derivative
            return rate
        except:
            return 0.0

    @staticmethod
    def calculate_coc(equity_invested: float, cash_flows: List[float]) -> float:
        """Calculate Cash-on-Cash Return"""
        if equity_invested == 0:
            return 0.0
        annual_cash_flow = sum(cash_flows) / len(cash_flows) if cash_flows else 0
        return (annual_cash_flow / equity_invested) * 100

    @staticmethod
    def calculate_dscr(noi: float, debt_service: float) -> float:
        """Calculate Debt Service Coverage Ratio"""
        if debt_service == 0:
            return 0.0
        return noi / debt_service

    @staticmethod
    def calculate_cap_rate(noi: float, property_value: float) -> float:
        """Calculate Capitalization Rate"""
        if property_value == 0:
            return 0.0
        return (noi / property_value) * 100

    @staticmethod
    def pro_forma_model(noi: float, growth_rate: float, years: int) -> Dict[str, Any]:
        """Generate pro forma financial model"""
        model = {
            "year_0_noi": noi,
            "growth_rate": growth_rate,
            "projections": []
        }
        for year in range(1, years + 1):
            projected_noi = noi * ((1 + growth_rate) ** year)
            model["projections"].append({
                "year": year,
                "noi": round(projected_noi, 2),
                "growth": round(projected_noi - noi, 2)
            })
        return model

# ============ ML MODELS ============
class MLPredictor:
    @staticmethod
    def predict_property_value(historical_data: List[Dict]) -> Dict[str, Any]:
        """Predict property value using ML"""
        if len(historical_data) < 3:
            return {"error": "Insufficient data"}
        
        # Extract features and targets
        X = np.array([[d.get("cap_rate", 5), d.get("noi", 100000)] for d in historical_data]).reshape(-1, 2)
        y = np.array([d.get("value", 1000000) for d in historical_data])
        
        # Train model
        model = LinearRegression()
        model.fit(X, y)
        
        # Make prediction
        latest = historical_data[-1]
        prediction = model.predict([[latest.get("cap_rate", 5), latest.get("noi", 100000)]])[0]
        
        return {
            "predicted_value": round(prediction, 2),
            "confidence": round(model.score(X, y) * 100, 2),
            "model_version": "v1.0"
        }

    @staticmethod
    def predict_vacancy_risk(historical_occupancy: List[float]) -> Dict[str, Any]:
        """Predict vacancy risk"""
        if not historical_occupancy:
            return {"risk_score": 50}
        
        avg_occupancy = np.mean(historical_occupancy)
        volatility = np.std(historical_occupancy)
        risk_score = max(0, min(100, 100 - avg_occupancy + volatility * 10))
        
        return {
            "risk_score": round(risk_score, 2),
            "avg_occupancy": round(avg_occupancy, 2),
            "volatility": round(volatility, 2),
            "recommendation": "High risk" if risk_score > 60 else "Moderate risk" if risk_score > 30 else "Low risk"
        }

    @staticmethod
    def predict_market_trends(historical_prices: List[float]) -> Dict[str, Any]:
        """Predict market trends"""
        if len(historical_prices) < 2:
            return {"trend": "insufficient_data"}
        
        X = np.arange(len(historical_prices)).reshape(-1, 1)
        y = np.array(historical_prices)
        
        model = LinearRegression()
        model.fit(X, y)
        
        slope = model.coef_[0]
        trend = "upward" if slope > 0 else "downward"
        
        return {
            "trend": trend,
            "slope": round(slope, 2),
            "predicted_next_price": round(model.predict([[len(historical_prices)]])[0], 2)
        }

# ============ FASTAPI APP ============
app = FastAPI(title="CRE Enterprise Suite", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ AUTH ENDPOINTS ============
@app.post("/api/auth/register")
async def register(user: UserCreate):
    db = get_db()
    
    # Check if user exists
    existing = db.execute("SELECT * FROM users WHERE email=? OR username=?", (user.email, user.username)).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_id = str(uuid.uuid4())[:8]
    hashed_pwd = hash_password(user.password)
    now = datetime.utcnow().isoformat()
    
    db.execute("""
        INSERT INTO users (id, email, username, hashed_password, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, user.email, user.username, hashed_pwd, user.role, now))
    
    db.commit()
    db.close()
    
    access_token = create_access_token({"sub": user_id})
    return {"access_token": access_token, "token_type": "bearer", "user_id": user_id}

@app.post("/api/auth/login")
async def login(user: UserLogin):
    db = get_db()
    db_user = db.execute("SELECT * FROM users WHERE email=?", (user.email,)).fetchone()
    db.close()
    
    if not db_user or not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token({"sub": db_user["id"]})
    return {"access_token": access_token, "token_type": "bearer", "user_id": db_user["id"]}

# ============ PROPERTY ENDPOINTS ============
@app.post("/api/properties")
async def create_property(prop: PropertyCreate, user_id: str = Depends(verify_token)):
    db = get_db()
    prop_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    db.execute("""
        INSERT INTO properties (id, user_id, name, asset_type, address, purchase_price, purchase_date, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (prop_id, user_id, prop.name, prop.asset_type, prop.address, prop.purchase_price, prop.purchase_date, now, now))
    
    db.commit()
    db.close()
    
    return {"id": prop_id, "status": "created"}

@app.get("/api/properties")
async def list_properties(user_id: str = Depends(verify_token)):
    db = get_db()
    rows = db.execute("SELECT * FROM properties WHERE user_id=? ORDER BY created_at DESC", (user_id,)).fetchall()
    db.close()
    
    return {"properties": [dict(row) for row in rows]}

@app.get("/api/properties/{property_id}")
async def get_property(property_id: str, user_id: str = Depends(verify_token)):
    db = get_db()
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    db.close()
    
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    
    return dict(prop)

# ============ RENT ROLL ENDPOINTS ============
@app.post("/api/properties/{property_id}/rent-roll")
async def add_rent_roll(property_id: str, entry: RentRollEntry, user_id: str = Depends(verify_token)):
    db = get_db()
    
    # Verify property ownership
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    
    entry_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    db.execute("""
        INSERT INTO rent_rolls (id, property_id, unit_number, tenant_name, lease_start, lease_end, monthly_rent, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (entry_id, property_id, entry.unit_number, entry.tenant_name, entry.lease_start, entry.lease_end, entry.monthly_rent, entry.status, now))
    
    db.commit()
    db.close()
    
    return {"id": entry_id, "status": "created"}

@app.get("/api/properties/{property_id}/rent-roll")
async def get_rent_roll(property_id: str, user_id: str = Depends(verify_token)):
    db = get_db()
    
    # Verify property ownership
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    
    rows = db.execute("SELECT * FROM rent_rolls WHERE property_id=?", (property_id,)).fetchall()
    db.close()
    
    entries = [dict(row) for row in rows]
    total_rent = sum(e["monthly_rent"] for e in entries)
    occupied = len([e for e in entries if e["status"] == "occupied"])
    
    return {
        "entries": entries,
        "total_monthly_rent": total_rent,
        "occupied_units": occupied,
        "total_units": len(entries),
        "occupancy_rate": round((occupied / len(entries) * 100) if entries else 0, 2)
    }

# ============ VALUATION ENDPOINTS ============
@app.post("/api/valuations")
async def create_valuation(val: ValuationRequest, user_id: str = Depends(verify_token)):
    db = get_db()
    
    # Verify property ownership
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (val.property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Calculate metrics
    irr = FinancialCalculator.calculate_irr([val.noi * 0.9, val.noi, val.noi * 1.1])
    coc = FinancialCalculator.calculate_coc(val.equity_invested, [val.noi] * 5)
    dscr = FinancialCalculator.calculate_dscr(val.noi, val.debt_service)
    
    val_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    valuation_data = {
        "irr": round(irr * 100, 2),
        "coc": round(coc, 2),
        "dscr": round(dscr, 2),
        "cap_rate": round(val.cap_rate, 2),
        "noi": val.noi,
        "debt_service": val.debt_service,
        "equity_invested": val.equity_invested
    }
    
    db.execute("""
        INSERT INTO valuations (id, property_id, valuation_type, irr, coc, dscr, noi, cap_rate, valuation_data, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (val_id, val.property_id, val.valuation_type, irr, coc, dscr, val.noi, val.cap_rate, json.dumps(valuation_data), now))
    
    db.commit()
    db.close()
    
    return {"id": val_id, "valuation": valuation_data}

@app.get("/api/properties/{property_id}/valuations")
async def get_valuations(property_id: str, user_id: str = Depends(verify_token)):
    db = get_db()
    
    # Verify property ownership
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    
    rows = db.execute("SELECT * FROM valuations WHERE property_id=? ORDER BY created_at DESC", (property_id,)).fetchall()
    db.close()
    
    valuations = []
    for row in rows:
        v = dict(row)
        v["valuation_data"] = json.loads(v["valuation_data"] or "{}")
        valuations.append(v)
    
    return {"valuations": valuations}

# ============ PRO FORMA ENDPOINTS ============
@app.post("/api/properties/{property_id}/pro-forma")
async def generate_pro_forma(property_id: str, noi: float, growth_rate: float = 0.03, years: int = 5, user_id: str = Depends(verify_token)):
    db = get_db()
    
    # Verify property ownership
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    
    db.close()
    
    model = FinancialCalculator.pro_forma_model(noi, growth_rate, years)
    return model

# ============ ML PREDICTION ENDPOINTS ============
@app.post("/api/properties/{property_id}/predict-value")
async def predict_value(property_id: str, user_id: str = Depends(verify_token)):
    db = get_db()
    
    # Get property valuations
    rows = db.execute("SELECT valuation_data FROM valuations WHERE property_id=? ORDER BY created_at DESC LIMIT 10", (property_id,)).fetchall()
    db.close()
    
    if not rows:
        return {"error": "Insufficient valuation data"}
    
    historical_data = [json.loads(row["valuation_data"]) for row in rows]
    prediction = MLPredictor.predict_property_value(historical_data)
    
    return prediction

@app.post("/api/properties/{property_id}/predict-vacancy")
async def predict_vacancy(property_id: str, user_id: str = Depends(verify_token)):
    db = get_db()
    
    # Get rent roll occupancy history
    rows = db.execute("SELECT status FROM rent_rolls WHERE property_id=?", (property_id,)).fetchall()
    db.close()
    
    if not rows:
        return {"error": "No rent roll data"}
    
    occupancy_rates = [len([r for r in rows if r["status"] == "occupied"]) / len(rows) * 100]
    prediction = MLPredictor.predict_vacancy_risk(occupancy_rates)
    
    return prediction

# ============ MEMO ENDPOINTS ============
@app.post("/api/properties/{property_id}/memo")
async def generate_memo(property_id: str, memo: MemoRequest, user_id: str = Depends(verify_token)):
    db = get_db()
    
    # Verify property ownership
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Get property data
    rent_roll = db.execute("SELECT * FROM rent_rolls WHERE property_id=?", (property_id,)).fetchall()
    valuations = db.execute("SELECT * FROM valuations WHERE property_id=? ORDER BY created_at DESC LIMIT 1", (property_id,)).fetchone()
    
    # Generate memo content
    content = f"""
    INVESTMENT MEMORANDUM
    
    Property: {prop['name']}
    Address: {prop['address']}
    Asset Type: {prop['asset_type']}
    Purchase Price: ${prop['purchase_price']:,.2f}
    Purchase Date: {prop['purchase_date']}
    
    RENT ROLL SUMMARY
    Total Units: {len(rent_roll)}
    Occupied Units: {len([r for r in rent_roll if r['status'] == 'occupied'])}
    Total Monthly Rent: ${sum(r['monthly_rent'] for r in rent_roll):,.2f}
    
    VALUATION METRICS
    """
    
    if valuations:
        val_data = json.loads(valuations["valuation_data"])
        content += f"""
    IRR: {val_data.get('irr', 'N/A')}%
    CoC: {val_data.get('coc', 'N/A')}%
    DSCR: {val_data.get('dscr', 'N/A')}
    Cap Rate: {val_data.get('cap_rate', 'N/A')}%
    """
    
    memo_id = str(uuid.uuid4())[:8]
    now = datetime.utcnow().isoformat()
    
    db.execute("""
        INSERT INTO memos (id, property_id, title, content, memo_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (memo_id, property_id, memo.title, content, memo.memo_type, now))
    
    db.commit()
    db.close()
    
    return {"id": memo_id, "memo": content}

# ============ MARKET COMPS ENDPOINTS ============
@app.get("/api/market-comps")
async def get_market_comps(asset_type: str = None):
    db = get_db()
    
    query = "SELECT * FROM market_comps"
    params = []
    if asset_type:
        query += " WHERE asset_type = ?"
        params.append(asset_type)
    
    rows = db.execute(query, params).fetchall()
    db.close()
    
    comps = [dict(row) for row in rows]
    return {"comps": comps, "total": len(comps)}

# ============ DASHBOARD ENDPOINTS ============
@app.get("/api/dashboard")
async def get_dashboard(user_id: str = Depends(verify_token)):
    db = get_db()
    
    # Get user properties
    properties = db.execute("SELECT COUNT(*) as count FROM properties WHERE user_id=?", (user_id,)).fetchone()
    
    # Get total valuations
    valuations = db.execute("""
        SELECT COUNT(*) as count FROM valuations 
        WHERE property_id IN (SELECT id FROM properties WHERE user_id=?)
    """, (user_id,)).fetchone()
    
    # Get average metrics
    avg_metrics = db.execute("""
        SELECT AVG(irr) as avg_irr, AVG(coc) as avg_coc, AVG(dscr) as avg_dscr
        FROM valuations 
        WHERE property_id IN (SELECT id FROM properties WHERE user_id=?)
    """, (user_id,)).fetchone()
    
    db.close()
    
    return {
        "total_properties": properties["count"],
        "total_valuations": valuations["count"],
        "avg_irr": round(avg_metrics["avg_irr"] * 100, 2) if avg_metrics["avg_irr"] else 0,
        "avg_coc": round(avg_metrics["avg_coc"], 2) if avg_metrics["avg_coc"] else 0,
        "avg_dscr": round(avg_metrics["avg_dscr"], 2) if avg_metrics["avg_dscr"] else 0
    }

# ============ PDF EXPORT ENDPOINTS ============
@app.get("/api/properties/{property_id}/export/memo")
async def export_memo_pdf(property_id: str, user_id: str = Depends(verify_token)):
    """Export investment memorandum as PDF"""
    db = get_db()
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    
    rent_roll = db.execute("SELECT * FROM rent_rolls WHERE property_id=?", (property_id,)).fetchall()
    valuation = db.execute("SELECT * FROM valuations WHERE property_id=? ORDER BY created_at DESC LIMIT 1", (property_id,)).fetchone()
    
    prop_dict = dict(prop)
    rent_dict = {
        "entries": [dict(r) for r in rent_roll],
        "total_units": len(rent_roll),
        "occupied_units": len([r for r in rent_roll if r["status"] == "occupied"]),
        "total_monthly_rent": sum(r["monthly_rent"] for r in rent_roll),
        "occupancy_rate": round(len([r for r in rent_roll if r["status"] == "occupied"]) / len(rent_roll) * 100) if rent_roll else 0
    }
    val_dict = json.loads(valuation["valuation_data"]) if valuation else {}
    db.close()
    
    pdf_content = PDFGenerator.generate_investment_memo(prop_dict, rent_dict, val_dict)
    return StreamingResponse(io.BytesIO(pdf_content), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=memo_{property_id}.pdf"})

@app.get("/api/properties/{property_id}/export/rent-roll")
async def export_rent_roll_pdf(property_id: str, user_id: str = Depends(verify_token)):
    """Export rent roll as PDF"""
    db = get_db()
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    rent_roll = db.execute("SELECT * FROM rent_rolls WHERE property_id=?", (property_id,)).fetchall()
    rent_dict = {
        "entries": [dict(r) for r in rent_roll],
        "total_units": len(rent_roll),
        "occupied_units": len([r for r in rent_roll if r["status"] == "occupied"]),
        "total_monthly_rent": sum(r["monthly_rent"] for r in rent_roll),
        "occupancy_rate": round(len([r for r in rent_roll if r["status"] == "occupied"]) / len(rent_roll) * 100) if rent_roll else 0
    }
    db.close()
    pdf_content = PDFGenerator.generate_rent_roll_pdf(prop["name"], rent_dict)
    return StreamingResponse(io.BytesIO(pdf_content), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=rent_roll_{property_id}.pdf"})

@app.get("/api/properties/{property_id}/export/valuation")
async def export_valuation_pdf(property_id: str, user_id: str = Depends(verify_token)):
    """Export valuation report as PDF"""
    db = get_db()
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    valuation = db.execute("SELECT * FROM valuations WHERE property_id=? ORDER BY created_at DESC LIMIT 1", (property_id,)).fetchone()
    val_dict = json.loads(valuation["valuation_data"]) if valuation else {}
    db.close()
    pdf_content = PDFGenerator.generate_valuation_report(dict(prop), val_dict)
    return StreamingResponse(io.BytesIO(pdf_content), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=valuation_{property_id}.pdf"})

# ============ EXCEL IMPORT/EXPORT ENDPOINTS ============
@app.post("/api/rent-roll/import")
async def import_rent_roll(file: UploadFile = File(...), property_id: str = None, user_id: str = Depends(verify_token)):
    """Import rent roll from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files supported")
    content = await file.read()
    result = ExcelProcessor.parse_rent_roll(content)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    if property_id:
        db = get_db()
        for entry in result.get("entries", []):
            entry_id = str(uuid.uuid4())[:8]
            db.execute("INSERT INTO rent_rolls (id, property_id, unit_number, tenant_name, lease_start, lease_end, monthly_rent, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (entry_id, property_id, entry["unit_number"], entry["tenant_name"], entry["lease_start"], entry["lease_end"], entry["monthly_rent"], entry["status"], datetime.utcnow().isoformat()))
        db.commit()
        db.close()
    return {"status": "success", "imported": len(result.get("entries", [])), "data": result}

@app.post("/api/properties/import")
async def import_properties(file: UploadFile = File(...), user_id: str = Depends(verify_token)):
    """Import properties from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files supported")
    content = await file.read()
    result = ExcelProcessor.parse_property_data(content)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result.get("error"))
    db = get_db()
    created = []
    for prop in result.get("properties", []):
        prop_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow().isoformat()
        db.execute("INSERT INTO properties (id, user_id, name, asset_type, address, purchase_price, purchase_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (prop_id, user_id, prop["name"], prop["asset_type"], prop["address"], prop["purchase_price"], prop["purchase_date"], now, now))
        created.append(prop_id)
    db.commit()
    db.close()
    return {"status": "success", "created": len(created), "ids": created}

@app.get("/api/properties/{property_id}/export/rent-roll/excel")
async def export_rent_roll_excel(property_id: str, user_id: str = Depends(verify_token)):
    """Export rent roll as Excel"""
    db = get_db()
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    rent_roll = db.execute("SELECT * FROM rent_rolls WHERE property_id=?", (property_id,)).fetchall()
    rent_dict = {
        "entries": [dict(r) for r in rent_roll],
        "total_units": len(rent_roll),
        "occupied_units": len([r for r in rent_roll if r["status"] == "occupied"]),
        "total_monthly_rent": sum(r["monthly_rent"] for r in rent_roll),
        "occupancy_rate": round(len([r for r in rent_roll if r["status"] == "occupied"]) / len(rent_roll) * 100) if rent_roll else 0
    }
    db.close()
    excel_content = ExcelProcessor.export_rent_roll(prop["name"], rent_dict)
    return StreamingResponse(io.BytesIO(excel_content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=rent_roll_{property_id}.xlsx"})

@app.get("/api/properties/{property_id}/export/valuation/excel")
async def export_valuation_excel(property_id: str, user_id: str = Depends(verify_token)):
    """Export valuation as Excel"""
    db = get_db()
    prop = db.execute("SELECT * FROM properties WHERE id=? AND user_id=?", (property_id, user_id)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    valuation = db.execute("SELECT * FROM valuations WHERE property_id=? ORDER BY created_at DESC LIMIT 1", (property_id,)).fetchone()
    val_dict = json.loads(valuation["valuation_data"]) if valuation else {}
    db.close()
    excel_content = ExcelProcessor.export_valuation_report(prop["name"], val_dict)
    return StreamingResponse(io.BytesIO(excel_content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f"attachment; filename=valuation_{property_id}.xlsx"})

# ============ HEALTH CHECK ============
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "CRE Enterprise Suite API", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
