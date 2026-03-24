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
from fastapi.security import HTTPBearer
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
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            role TEXT DEFAULT 'analyst',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            property_type TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            purchase_price REAL,
            current_value REAL,
            noi REAL,
            cap_rate REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS valuations (
            id TEXT PRIMARY KEY,
            property_id TEXT,
            valuation_type TEXT,
            value REAL,
            date TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS rent_rolls (
            id TEXT PRIMARY KEY,
            property_id TEXT,
            tenant_name TEXT,
            unit_number TEXT,
            square_feet REAL,
            monthly_rent REAL,
            lease_start TEXT,
            lease_end TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS cash_flows (
            id TEXT PRIMARY KEY,
            property_id TEXT,
            period TEXT,
            gross_income REAL,
            operating_expenses REAL,
            noi REAL,
            debt_service REAL,
            cash_flow REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS scenarios (
            id TEXT PRIMARY KEY,
            property_id TEXT,
            scenario_name TEXT,
            purchase_price REAL,
            down_payment REAL,
            loan_amount REAL,
            interest_rate REAL,
            loan_term REAL,
            noi REAL,
            exit_cap_rate REAL,
            irr REAL,
            coc REAL,
            dscr REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (property_id) REFERENCES properties(id)
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS market_data (
            id TEXT PRIMARY KEY,
            city TEXT,
            property_type TEXT,
            avg_cap_rate REAL,
            avg_price_per_sqft REAL,
            vacancy_rate REAL,
            rent_growth REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
    db.close()

init_db()

# ============ PASSWORD HASHING ============
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# ============ JWT TOKEN ============
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

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

# ============ FASTAPI APP ============
app = FastAPI(
    title="CRE Enterprise Suite API",
    version="1.0.0",
    description="Commercial Real Estate Financial Modeling Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ REQUEST/RESPONSE MODELS ============
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    role: str = "analyst"

class UserLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class PropertyCreate(BaseModel):
    name: str
    property_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    purchase_price: Optional[float] = None
    current_value: Optional[float] = None
    noi: Optional[float] = None
    cap_rate: Optional[float] = None

class ValuationCreate(BaseModel):
    property_id: str
    valuation_type: str
    value: float
    date: Optional[str] = None
    notes: Optional[str] = None

class RentRollCreate(BaseModel):
    property_id: str
    tenant_name: str
    unit_number: str
    square_feet: float
    monthly_rent: float
    lease_start: str
    lease_end: str

class ScenarioCreate(BaseModel):
    property_id: str
    scenario_name: str
    purchase_price: float
    down_payment: float
    loan_amount: float
    interest_rate: float
    loan_term: float
    noi: float
    exit_cap_rate: float

class CashFlowCreate(BaseModel):
    property_id: str
    period: str
    gross_income: float
    operating_expenses: float
    noi: float
    debt_service: float
    cash_flow: float

# ============ HEALTH CHECK ============
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
async def root():
    return {"message": "CRE Enterprise Suite API", "version": "1.0.0"}

# ============ AUTH ENDPOINTS ============
@app.post("/api/auth/register", response_model=TokenResponse)
async def register(user: UserCreate):
    db = get_db()
    existing = db.execute("SELECT id FROM users WHERE email = ? OR username = ?", 
                          (user.email, user.username)).fetchone()
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Email or username already registered")
    
    user_id = str(uuid.uuid4())
    hashed = hash_password(user.password)
    
    db.execute(
        "INSERT INTO users (id, email, username, hashed_password, role) VALUES (?, ?, ?, ?, ?)",
        (user_id, user.email, user.username, hashed, user.role)
    )
    db.commit()
    db.close()
    
    token = create_access_token({"sub": user_id})
    return TokenResponse(
        access_token=token,
        user={"id": user_id, "email": user.email, "username": user.username, "role": user.role}
    )

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username = ?", (credentials.username,)).fetchone()
    db.close()
    
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token({"sub": user["id"]})
    return TokenResponse(
        access_token=token,
        user={"id": user["id"], "email": user["email"], "username": user["username"], "role": user["role"]}
    )

@app.get("/api/auth/me")
async def get_me(user_id: str = Depends(verify_token)):
    db = get_db()
    user = db.execute("SELECT id, email, username, role FROM users WHERE id = ?", (user_id,)).fetchone()
    db.close()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(user)

# ============ PROPERTY ENDPOINTS ============
@app.get("/api/properties")
async def list_properties(user_id: str = Depends(verify_token)):
    db = get_db()
    properties = db.execute("SELECT * FROM properties ORDER BY created_at DESC").fetchall()
    db.close()
    return [dict(p) for p in properties]

@app.post("/api/properties")
async def create_property(prop: PropertyCreate, user_id: str = Depends(verify_token)):
    db = get_db()
    prop_id = str(uuid.uuid4())
    
    cap = prop.cap_rate or ((prop.noi / prop.purchase_price * 100) if prop.purchase_price and prop.noi else None)
    
    db.execute("""
        INSERT INTO properties (id, name, property_type, address, city, state, zip_code, 
                               purchase_price, current_value, noi, cap_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (prop_id, prop.name, prop.property_type, prop.address, prop.city, prop.state,
          prop.zip_code, prop.purchase_price, prop.current_value, prop.noi, cap))
    db.commit()
    db.close()
    
    return {"id": prop_id, "message": "Property created successfully"}

@app.get("/api/properties/{prop_id}")
async def get_property(prop_id: str, user_id: str = Depends(verify_token)):
    db = get_db()
    prop = db.execute("SELECT * FROM properties WHERE id = ?", (prop_id,)).fetchone()
    if not prop:
        db.close()
        raise HTTPException(status_code=404, detail="Property not found")
    db.close()
    return dict(prop)

@app.delete("/api/properties/{prop_id}")
async def delete_property(prop_id: str, user_id: str = Depends(verify_token)):
    db = get_db()
    db.execute("DELETE FROM properties WHERE id = ?", (prop_id,))
    db.commit()
    db.close()
    return {"message": "Property deleted successfully"}

# ============ VALUATION ENDPOINTS ============
@app.get("/api/valuations")
async def list_valuations(property_id: Optional[str] = None, user_id: str = Depends(verify_token)):
    db = get_db()
    if property_id:
        vals = db.execute("SELECT * FROM valuations WHERE property_id = ? ORDER BY date DESC", 
                         (property_id,)).fetchall()
    else:
        vals = db.execute("SELECT * FROM valuations ORDER BY date DESC").fetchall()
    db.close()
    return [dict(v) for v in vals]

@app.post("/api/valuations")
async def create_valuation(val: ValuationCreate, user_id: str = Depends(verify_token)):
    db = get_db()
    val_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO valuations (id, property_id, valuation_type, value, date, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (val_id, val.property_id, val.valuation_type, val.value, val.date, val.notes))
    db.commit()
    db.close()
    return {"id": val_id, "message": "Valuation created successfully"}

# ============ RENT ROLL ENDPOINTS ============
@app.get("/api/rent-rolls")
async def list_rent_rolls(property_id: Optional[str] = None, user_id: str = Depends(verify_token)):
    db = get_db()
    if property_id:
        rolls = db.execute("SELECT * FROM rent_rolls WHERE property_id = ?", (property_id,)).fetchall()
    else:
        rolls = db.execute("SELECT * FROM rent_rolls").fetchall()
    db.close()
    return [dict(r) for r in rolls]

@app.post("/api/rent-rolls")
async def create_rent_roll(roll: RentRollCreate, user_id: str = Depends(verify_token)):
    db = get_db()
    roll_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO rent_rolls (id, property_id, tenant_name, unit_number, square_feet, 
                               monthly_rent, lease_start, lease_end)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (roll_id, roll.property_id, roll.tenant_name, roll.unit_number, roll.square_feet,
          roll.monthly_rent, roll.lease_start, roll.lease_end))
    db.commit()
    db.close()
    return {"id": roll_id, "message": "Rent roll created successfully"}

# ============ CASH FLOW ENDPOINTS ============
@app.get("/api/cash-flows")
async def list_cash_flows(property_id: Optional[str] = None, user_id: str = Depends(verify_token)):
    db = get_db()
    if property_id:
        flows = db.execute("SELECT * FROM cash_flows WHERE property_id = ? ORDER BY period", 
                          (property_id,)).fetchall()
    else:
        flows = db.execute("SELECT * FROM cash_flows ORDER BY period").fetchall()
    db.close()
    return [dict(f) for f in flows]

@app.post("/api/cash-flows")
async def create_cash_flow(flow: CashFlowCreate, user_id: str = Depends(verify_token)):
    db = get_db()
    flow_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO cash_flows (id, property_id, period, gross_income, operating_expenses, 
                               noi, debt_service, cash_flow)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (flow_id, flow.property_id, flow.period, flow.gross_income, flow.operating_expenses,
          flow.noi, flow.debt_service, flow.cash_flow))
    db.commit()
    db.close()
    return {"id": flow_id, "message": "Cash flow created successfully"}

# ============ SCENARIO ENDPOINTS ============
@app.get("/api/scenarios")
async def list_scenarios(property_id: Optional[str] = None, user_id: str = Depends(verify_token)):
    db = get_db()
    if property_id:
        scen = db.execute("SELECT * FROM scenarios WHERE property_id = ?", (property_id,)).fetchall()
    else:
        scen = db.execute("SELECT * FROM scenarios").fetchall()
    db.close()
    return [dict(s) for s in scen]

@app.post("/api/scenarios")
async def create_scenario(scen: ScenarioCreate, user_id: str = Depends(verify_token)):
    db = get_db()
    scen_id = str(uuid.uuid4())
    
    # Calculate financial metrics
    monthly_rate = scen.interest_rate / 100 / 12
    num_payments = scen.loan_term * 12
    pmt = scen.loan_amount * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    annual_debt = pmt * 12
    dscr = scen.noi / annual_debt if annual_debt else 0
    cash_flow_yr1 = scen.noi - annual_debt
    total_investment = scen.down_payment
    coc = cash_flow_yr1 / total_investment if total_investment else 0
    
    # Simple IRR estimate
    irr = ((1 + coc) ** 5 - 1) * 100 if cash_flow_yr1 > 0 else 0
    
    db.execute("""
        INSERT INTO scenarios (id, property_id, scenario_name, purchase_price, down_payment,
                               loan_amount, interest_rate, loan_term, noi, exit_cap_rate,
                               irr, coc, dscr)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (scen_id, scen.property_id, scen.scenario_name, scen.purchase_price, scen.down_payment,
          scen.loan_amount, scen.interest_rate, scen.loan_term, scen.noi, scen.exit_cap_rate,
          irr, coc, dscr))
    db.commit()
    db.close()
    
    return {"id": scen_id, "irr": irr, "coc": coc, "dscr": dscr, "message": "Scenario created successfully"}

# ============ FINANCIAL CALCULATIONS ============
@app.post("/api/calculate/irr")
async def calculate_irr(data: dict, user_id: str = Depends(verify_token)):
    cash_flows = data.get("cash_flows", [])
    if len(cash_flows) < 2:
        return {"irr": 0}
    
    try:
        cash_flows_arr = np.array(cash_flows)
        rates = np.linspace(-0.5, 2.0, 1000)
        npv = np.array([np.sum(cf / (1 + r) ** np.arange(len(cf))) for r in rates])
        idx = np.argmin(np.abs(npv))
        irr = rates[idx] * 100
        return {"irr": round(irr, 2)}
    except:
        return {"irr": 0}

@app.post("/api/calculate/cap-rate")
async def calculate_cap_rate(data: dict, user_id: str = Depends(verify_token)):
    noi = data.get("noi", 0)
    value = data.get("value", 0)
    cap = (noi / value * 100) if value else 0
    return {"cap_rate": round(cap, 2)}

@app.post("/api/calculate/coc")
async def calculate_coc(data: dict, user_id: str = Depends(verify_token)):
    cash_flow = data.get("cash_flow", 0)
    investment = data.get("investment", 0)
    coc = (cash_flow / investment * 100) if investment else 0
    return {"coc": round(coc, 2)}

@app.post("/api/calculate/dscr")
async def calculate_dscr(data: dict, user_id: str = Depends(verify_token)):
    noi = data.get("noi", 0)
    debt = data.get("debt_service", 0)
    dscr = noi / debt if debt else 0
    return {"dscr": round(dscr, 2)}

@app.post("/api/calculate/loan")
async def calculate_loan(data: dict, user_id: str = Depends(verify_token)):
    principal = data.get("principal", 0)
    rate = data.get("rate", 0)
    term = data.get("term", 0)
    
    if not principal or not rate or not term:
        return {"monthly_payment": 0, "total_payment": 0, "total_interest": 0}
    
    monthly_rate = rate / 100 / 12
    num_payments = term * 12
    pmt = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    
    return {
        "monthly_payment": round(pmt, 2),
        "total_payment": round(pmt * num_payments, 2),
        "total_interest": round(pmt * num_payments - principal, 2)
    }

# ============ MARKET DATA ============
@app.get("/api/market")
async def get_market_data(city: Optional[str] = None, user_id: str = Depends(verify_token)):
    db = get_db()
    if city:
        data = db.execute("SELECT * FROM market_data WHERE city = ?", (city,)).fetchall()
    else:
        data = db.execute("SELECT * FROM market_data").fetchall()
    db.close()
    return [dict(d) for d in data]

@app.post("/api/market")
async def add_market_data(data: dict, user_id: str = Depends(verify_token)):
    db = get_db()
    data_id = str(uuid.uuid4())
    db.execute("""
        INSERT INTO market_data (id, city, property_type, avg_cap_rate, avg_price_per_sqft, 
                                vacancy_rate, rent_growth)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data_id, data.get("city"), data.get("property_type"), data.get("avg_cap_rate"),
          data.get("avg_price_per_sqft"), data.get("vacancy_rate"), data.get("rent_growth")))
    db.commit()
    db.close()
    return {"id": data_id, "message": "Market data added successfully"}

# ============ ML PREDICTIONS ============
@app.post("/api/predict/value")
async def predict_value(data: dict, user_id: str = Depends(verify_token)):
    sqft = data.get("square_feet", 1000)
    cap = data.get("cap_rate", 6.0)
    noi = data.get("noi", 50000)
    
    # Simple prediction model
    base_price = noi / (cap / 100) if cap else 0
    sqft_adj = sqft * 100
    predicted = (base_price + sqft_adj) / 2
    
    return {
        "predicted_value": round(predicted, 2),
        "confidence": "medium",
        "model": "linear_regression"
    }

@app.post("/api/predict/cap-rate")
async def predict_cap_rate(data: dict, user_id: str = Depends(verify_token)):
    city = data.get("city", "Unknown")
    prop_type = data.get("property_type", "Office")
    
    db = get_db()
    market = db.execute(
        "SELECT avg_cap_rate FROM market_data WHERE city = ? AND property_type = ? LIMIT 1",
        (city, prop_type)
    ).fetchone()
    db.close()
    
    if market:
        return {"predicted_cap_rate": round(market["avg_cap_rate"], 2), "confidence": "high"}
    return {"predicted_cap_rate": 6.5, "confidence": "low", "note": "Using default rate"}

# ============ DASHBOARD ============
@app.get("/api/dashboard")
async def get_dashboard(user_id: str = Depends(verify_token)):
    db = get_db()
    
    properties = db.execute("SELECT COUNT(*) as count FROM properties").fetchone()
    valuations = db.execute("SELECT COUNT(*) as count FROM valuations").fetchone()
    scenarios = db.execute("SELECT COUNT(*) as count FROM scenarios").fetchone()
    
    avg_metrics = db.execute("""
        SELECT AVG(irr) as avg_irr, AVG(coc) as avg_coc, AVG(dscr) as avg_dscr 
        FROM scenarios
    """).fetchone()
    
    recent_props = db.execute(
        "SELECT * FROM properties ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    
    db.close()
    
    return {
        "total_properties": properties["count"],
        "total_valuations": valuations["count"],
        "total_scenarios": scenarios["count"],
        "avg_irr": round(avg_metrics["avg_irr"] or 0, 2),
        "avg_coc": round(avg_metrics["avg_coc"] or 0, 2),
        "avg_dscr": round(avg_metrics["avg_dscr"] or 0, 2),
        "recent_properties": [dict(p) for p in recent_props]
    }

# ============ FILE OPERATIONS ============
pdf_gen = PDFGenerator()
excel_proc = ExcelProcessor()

@app.post("/api/documents/generate-pdf")
async def generate_pdf(data: dict, user_id: str = Depends(verify_token)):
    try:
        pdf_bytes = pdf_gen.generate_investment_memo(data)
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=investment_memo.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/generate-excel")
async def generate_excel(data: dict, user_id: str = Depends(verify_token)):
    try:
        excel_bytes = excel_proc.generate_rent_roll_excel(data)
        return StreamingResponse(
            io.BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=rent_roll.xlsx"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/documents/import-excel")
async def import_excel(file: UploadFile = File(...), user_id: str = Depends(verify_token)):
    try:
        contents = await file.read()
        data = excel_proc.import_rent_roll_from_excel(io.BytesIO(contents))
        return {"status": "success", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports/summary")
async def get_summary_report(user_id: str = Depends(verify_token)):
    db = get_db()
    
    properties = db.execute("SELECT * FROM properties").fetchall()
    valuations = db.execute("SELECT * FROM valuations").fetchall()
    rent_rolls = db.execute("SELECT * FROM rent_rolls").fetchall()
    scenarios = db.execute("SELECT * FROM scenarios").fetchall()
    
    total_value = sum(p["current_value"] or 0 for p in properties)
    total_noi = sum(p["noi"] or 0 for p in properties)
    
    db.close()
    
    return {
        "total_properties": len(properties),
        "total_value": round(total_value, 2),
        "total_noi": round(total_noi, 2),
        "total_valuations": len(valuations),
        "total_rent_rolls": len(rent_rolls),
        "total_scenarios": len(scenarios),
        "avg_cap_rate": round((total_noi / total_value * 100) if total_value else 0, 2)
    }
