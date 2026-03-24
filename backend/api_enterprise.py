"""
CRE Enterprise Suite - Advanced API Endpoints
Push Notifications, iOS Widget Data, Audit, and System Health
"""
import sqlite3
import json
import os
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

# Router
router = APIRouter(prefix="/api", tags=["enterprise"])

# ============ DEVICE/SESSION MODELS ============
class PushTokenRequest(BaseModel):
    token: str
    platform: str
    appVersion: str = "1.0.0"

class AuthPreferenceRequest(BaseModel):
    requireBiometric: bool

class MemoShareRequest(BaseModel):
    memoId: str

# ============ HELPERS ============
def get_db():
    from main import get_db as _gd
    return _gd()

def get_current_user_id(request: Request) -> str:
    """Extract user_id from JWT token in Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid auth token")
    
    try:
        from main import SECRET_KEY, ALGORITHM
        token = auth.replace("Bearer ", "")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

def audit_log(user_id: str, action: str, resource_type: str = None, 
              resource_id: str = None, details: Dict = None, request: Request = None):
    """Log an audit event."""
    from enterprise import AuditLogger
    logger = AuditLogger()
    logger.log(
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

# ============ PUSH NOTIFICATION ENDPOINTS ============

@router.post("/users/{user_id}/push-token")
async def register_push_token(user_id: str, body: PushTokenRequest, request: Request):
    """Register a device push token for notifications."""
    # Verify the requesting user owns this account
    token_user = get_current_user_id(request)
    if token_user != user_id:
        raise HTTPException(status_code=403, detail="Cannot register tokens for other users")
    
    conn = get_db()
    
    # Ensure push_tokens table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS push_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            token TEXT NOT NULL,
            platform TEXT NOT NULL,
            app_version TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TEXT,
            last_used TEXT,
            UNIQUE(user_id, token)
        )
    """)
    
    now = datetime.utcnow().isoformat()
    
    # Upsert token
    existing = conn.execute(
        "SELECT id FROM push_tokens WHERE user_id=? AND token=?",
        (user_id, body.token)
    ).fetchone()
    
    if existing:
        conn.execute("""
            UPDATE push_tokens SET last_used=?, is_active=1 
            WHERE user_id=? AND token=?
        """, (now, user_id, body.token))
    else:
        conn.execute("""
            INSERT INTO push_tokens (user_id, token, platform, app_version, created_at, last_used)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, body.token, body.platform, body.appVersion, now, now))
    
    conn.commit()
    conn.close()
    
    audit_log(user_id, "push_token.registered", details={"platform": body.platform})
    
    return {"status": "registered", "token_count": 1}

@router.delete("/users/{user_id}/push-token")
async def unregister_push_token(user_id: str, token: str, request: Request):
    """Unregister a push token."""
    token_user = get_current_user_id(request)
    if token_user != user_id:
        raise HTTPException(status_code=403, detail="Cannot modify other users")
    
    conn = get_db()
    conn.execute(
        "UPDATE push_tokens SET is_active=0 WHERE user_id=? AND token=?",
        (user_id, token)
    )
    conn.commit()
    conn.close()
    
    return {"status": "unregistered"}

@router.get("/users/{user_id}/push-tokens")
async def list_push_tokens(user_id: str, request: Request):
    """List all registered push tokens for a user."""
    token_user = get_current_user_id(request)
    if token_user != user_id:
        raise HTTPException(status_code=403, detail="Cannot view other users")
    
    conn = get_db()
    conn.row_factory = lambda c, r: {"token": r[2], "platform": r[3], "app_version": r[4], "active": r[6]}
    rows = conn.execute(
        "SELECT * FROM push_tokens WHERE user_id=? AND is_active=1",
        (user_id,)
    ).fetchall()
    conn.close()
    
    return {"tokens": rows}

# ============ BIOMETRIC AUTH ENDPOINTS ============

@router.put("/users/{user_id}/auth-preference")
async def update_auth_preference(user_id: str, body: AuthPreferenceRequest, request: Request):
    """Update biometric auth preference."""
    token_user = get_current_user_id(request)
    if token_user != user_id:
        raise HTTPException(status_code=403, detail="Cannot modify other users")
    
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            require_biometric INTEGER DEFAULT 0,
            updated_at TEXT
        )
    """)
    
    conn.execute("""
        INSERT OR REPLACE INTO user_settings (user_id, require_biometric, updated_at)
        VALUES (?, ?, ?)
    """, (user_id, 1 if body.requireBiometric else 0, datetime.utcnow().isoformat()))
    
    conn.commit()
    conn.close()
    
    audit_log(user_id, "auth.preference_updated", details={"requireBiometric": body.requireBiometric})
    
    return {"status": "updated"}

@router.get("/users/{user_id}/auth-preference")
async def get_auth_preference(user_id: str, request: Request):
    """Get biometric auth preference."""
    token_user = get_current_user_id(request)
    if token_user != user_id:
        raise HTTPException(status_code=403, detail="Cannot view other users")
    
    conn = get_db()
    row = conn.execute(
        "SELECT require_biometric FROM user_settings WHERE user_id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    
    return {"requireBiometric": bool(row[0]) if row else False}

# ============ AUDIT LOG ENDPOINTS ============

@router.get("/audit/logs")
async def get_audit_logs(
    request: Request,
    user_id: str = None,
    resource_type: str = None,
    resource_id: str = None,
    action: str = None,
    limit: int = 100,
    offset: int = 0,
):
    """Get audit logs (admin only)."""
    token_user = get_current_user_id(request)
    
    from enterprise import get_user_permissions, Permission
    perms = get_user_permissions(token_user)
    if "audit:view" not in perms:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    from enterprise import AuditLogger
    logger = AuditLogger()
    
    logs = logger.get_logs(
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        limit=limit,
        offset=offset,
    )
    
    return {"logs": logs, "count": len(logs)}

@router.get("/audit/user-activity/{target_user_id}")
async def get_user_activity(target_user_id: str, request: Request, days: int = 30):
    """Get activity summary for a specific user."""
    token_user = get_current_user_id(request)
    
    # Users can view their own activity; admins can view anyone's
    from enterprise import get_user_permissions, Permission
    perms = get_user_permissions(token_user)
    
    if token_user != target_user_id and "audit:view" not in perms:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    from enterprise import AuditLogger
    logger = AuditLogger()
    
    activity = logger.get_user_activity(target_user_id, days)
    
    return {"user_id": target_user_id, "days": days, "activity": activity}

# ============ iOS WIDGET DATA ============

@router.get("/users/{user_id}/widget-data")
async def get_widget_data(user_id: str, request: Request):
    """Get lightweight data for iOS Widget."""
    token_user = get_current_user_id(request)
    if token_user != user_id:
        raise HTTPException(status_code=403, detail="Cannot access other users")
    
    conn = get_db()
    
    # Get property summary
    properties = conn.execute("""
        SELECT name, asset_type, purchase_price, purchase_date
        FROM properties WHERE user_id=? ORDER BY updated_at DESC LIMIT 10
    """, (user_id,)).fetchall()
    
    # Get latest valuations
    valuations = conn.execute("""
        SELECT v.*, p.name as property_name
        FROM valuations v
        JOIN properties p ON v.property_id = p.id
        WHERE p.user_id=?
        ORDER BY v.created_at DESC LIMIT 5
    """, (user_id,)).fetchall()
    
    # Get upcoming lease expirations
    from datetime import datetime
    cutoff = (datetime.utcnow() + timedelta(days=90)).isoformat()
    upcoming_leases = conn.execute("""
        SELECT r.unit_number, r.tenant_name, r.lease_end, p.name as property_name
        FROM rent_rolls r
        JOIN properties p ON r.property_id = p.id
        WHERE p.user_id=? AND r.lease_end IS NOT NULL AND r.lease_end <= ?
        ORDER BY r.lease_end ASC
    """, (user_id, cutoff)).fetchall()
    
    conn.close()
    
    widget_data = {
        "portfolio": {
            "total_properties": len(properties),
            "total_value": sum(p["purchase_price"] or 0 for p in properties),
        },
        "properties": [
            {
                "name": p["name"],
                "type": p["asset_type"],
                "value": p["purchase_price"],
            }
            for p in properties[:5]
        ],
        "valuations": [
            {
                "property": dict(v).get("property_name", ""),
                "irr": dict(v).get("irr", 0),
                "cap_rate": dict(v).get("cap_rate", 0),
            }
            for v in valuations[:3]
        ],
        "alerts": {
            "lease_expiring_90d": len(upcoming_leases),
            "alerts": [
                {
                    "unit": row["unit_number"],
                    "tenant": row["tenant_name"],
                    "property": row["property_name"],
                    "expires": row["lease_end"],
                }
                for row in upcoming_leases[:5]
            ]
        },
        "lastUpdated": datetime.utcnow().isoformat(),
    }
    
    return widget_data

# ============ DOCUMENT INGESTION ENDPOINTS ============

@router.post("/documents/ocr")
async def ocr_document(request: Request):
    """Upload an image for OCR processing."""
    from fastapi import File, UploadFile, Form
    from enterprise import AuditLogger
    
    user_id = get_current_user_id(request)
    
    # Note: Use multipart form data in actual implementation
    # This endpoint accepts Form data with file + metadata
    return {"status": "ocr_processing", "message": "OCR endpoint ready - connect to Tesseract or cloud OCR"}

@router.post("/documents/ingest")
async def ingest_document(text: str = Form(...), filename: str = Form("Manual Entry"), request: Request = None):
    """Ingest raw text data (from PDF, paste, screenshot)."""
    from ingestion import DocumentIngestor
    
    user_id = get_current_user_id(request)
    
    ingestor = DocumentIngestor()
    result = await ingestor.ingest_text(text, filename)
    
    audit_log(user_id, "document.ingested", resource_type="document", 
               resource_id=result.document_id, details={"doc_type": result.document_type})
    
    return {
        "status": "success",
        "document_id": result.document_id,
        "document_type": result.document_type,
        "extracted_fields": {k: {"value": v.value, "confidence": v.confidence} 
                            for k, v in result.extracted_fields.items()},
        "warnings": result.warnings,
    }

@router.get("/documents")
async def list_documents(request: Request, doc_type: str = None, limit: int = 50):
    """List all ingested documents."""
    user_id = get_current_user_id(request)
    from ingestion import DocumentIngestor
    
    ingestor = DocumentIngestor()
    docs = ingestor.list_documents(doc_type=doc_type, limit=limit)
    
    return {"documents": docs, "count": len(docs)}

@router.get("/documents/{doc_id}")
async def get_document(doc_id: str, request: Request):
    """Get a specific ingested document."""
    user_id = get_current_user_id(request)
    from ingestion import DocumentIngestor
    
    ingestor = DocumentIngestor()
    doc = ingestor.get_document(doc_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return doc

# ============ SYSTEM HEALTH ============

@router.get("/system/health")
async def system_health():
    """Comprehensive system health check."""
    db_path = Path(__file__).parent / "cre.db"
    db_exists = db_path.exists()
    db_size_kb = db_path.stat().st_size / 1024 if db_exists else 0
    
    # Get user count
    user_count = 0
    property_count = 0
    try:
        conn = get_db()
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        property_count = conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
        conn.close()
    except:
        pass
    
    # Memory usage
    memory = psutil.virtual_memory()
    
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "database": {
            "exists": db_exists,
            "size_kb": round(db_size_kb, 1),
        },
        "counts": {
            "users": user_count,
            "properties": property_count,
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_used_mb": round(memory.used / 1024 / 1024, 1),
            "memory_percent": memory.percent,
            "uptime_seconds": int(psutil.boot_time()),
        }
    }

@router.get("/system/stats")
async def system_stats():
    """Usage statistics for the platform."""
    conn = get_db()
    conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    
    stats = {
        "total_users": conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"],
        "total_properties": conn.execute("SELECT COUNT(*) as c FROM properties").fetchone()["c"],
        "total_valuations": conn.execute("SELECT COUNT(*) as c FROM valuations").fetchone()["c"],
        "total_memos": conn.execute("SELECT COUNT(*) as c FROM memos").fetchone()["c"],
        "total_documents": conn.execute("SELECT COUNT(*) as c FROM documents").fetchone()["c"] if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'").fetchone() else 0,
        "asset_types": conn.execute("""
            SELECT asset_type, COUNT(*) as count 
            FROM properties GROUP BY asset_type
        """).fetchall(),
    }
    
    conn.close()
    return stats

print("✅ Enterprise API endpoints loaded (16 new endpoints)")
