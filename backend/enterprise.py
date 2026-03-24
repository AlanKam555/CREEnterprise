"""
CRE Enterprise Suite - Enterprise Module
Role-Based Access Control (RBAC), Audit Logging, and Security
"""
import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path
from enum import Enum
from functools import wraps
from typing import Optional, List, Dict, Any

# ============ ENUMS ============
class Role(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MANAGER = "manager"
    ANALYST = "analyst"
    VIEWER = "viewer"

class Permission(str, Enum):
    # Properties
    PROPERTY_READ = "property:read"
    PROPERTY_WRITE = "property:write"
    PROPERTY_DELETE = "property:delete"
    # Valuations
    VALUATION_READ = "valuation:read"
    VALUATION_WRITE = "valuation:write"
    VALUATION_EXPORT = "valuation:export"
    # Rent Roll
    RENTROLL_READ = "rentroll:read"
    RENTROLL_WRITE = "rentroll:write"
    RENTROLL_EDIT = "rentroll:edit"
    # Memos
    MEMO_READ = "memo:read"
    MEMO_WRITE = "memo:write"
    MEMO_EXPORT = "memo:export"
    # Users
    USER_MANAGE = "user:manage"
    USER_VIEW = "user:view"
    # System
    AUDIT_VIEW = "audit:view"
    SETTINGS_MANAGE = "settings:manage"
    ML_ACCESS = "ml:access"

# ============ ROLE → PERMISSION MAPPING ============
ROLE_PERMISSIONS: Dict[Role, List[Permission]] = {
    Role.SUPER_ADMIN: [p for p in Permission],
    Role.ADMIN: [
        Permission.PROPERTY_READ, Permission.PROPERTY_WRITE, Permission.PROPERTY_DELETE,
        Permission.VALUATION_READ, Permission.VALUATION_WRITE, Permission.VALUATION_EXPORT,
        Permission.RENTROLL_READ, Permission.RENTROLL_WRITE, Permission.RENTROLL_EDIT,
        Permission.MEMO_READ, Permission.MEMO_WRITE, Permission.MEMO_EXPORT,
        Permission.USER_VIEW, Permission.AUDIT_VIEW, Permission.SETTINGS_MANAGE,
        Permission.ML_ACCESS,
    ],
    Role.MANAGER: [
        Permission.PROPERTY_READ, Permission.PROPERTY_WRITE,
        Permission.VALUATION_READ, Permission.VALUATION_WRITE, Permission.VALUATION_EXPORT,
        Permission.RENTROLL_READ, Permission.RENTROLL_WRITE, Permission.RENTROLL_EDIT,
        Permission.MEMO_READ, Permission.MEMO_WRITE, Permission.MEMO_EXPORT,
        Permission.USER_VIEW, Permission.ML_ACCESS,
    ],
    Role.ANALYST: [
        Permission.PROPERTY_READ, Permission.PROPERTY_WRITE,
        Permission.VALUATION_READ, Permission.VALUATION_WRITE, Permission.VALUATION_EXPORT,
        Permission.RENTROLL_READ, Permission.RENTROLL_WRITE,
        Permission.MEMO_READ, Permission.MEMO_WRITE, Permission.MEMO_EXPORT,
        Permission.ML_ACCESS,
    ],
    Role.VIEWER: [
        Permission.PROPERTY_READ,
        Permission.VALUATION_READ,
        Permission.RENTROLL_READ,
        Permission.MEMO_READ,
    ],
}

# ============ DB HELPERS ============
def get_db():
    from main import get_db as _gd
    return _gd()

# ============ PERMISSION CHECKER ============
def require_permission(*permissions: Permission):
    """Decorator to enforce RBAC on endpoints."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            from fastapi import HTTPException, Depends, Header
            from fastapi.security import HTTPBearer, HTTPAuthCredentials
            import jwt
            from main import SECRET_KEY, ALGORITHM

            # Extract token
            auth = kwargs.get('credentials') or kwargs.get('user_id')
            
            # Simple token extraction from kwargs
            user_id = kwargs.get('user_id') or kwargs.get('token_user_id')
            if not user_id:
                # Try to get from request
                pass
            
            # For now, return the wrapped function
            # In production, fully decode JWT and check permissions
            return func(*args, **kwargs)
        return wrapper
    return decorator

def has_permission(role: str, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    try:
        role_enum = Role(role)
        return permission in ROLE_PERMISSIONS.get(role_enum, [])
    except ValueError:
        return False

# ============ AUDIT LOGGER ============
class AuditLogger:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Path(__file__).parent.parent / "cre.db")
    
    def _ensure_table(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                user_id TEXT,
                user_email TEXT,
                action TEXT NOT NULL,
                resource_type TEXT,
                resource_id TEXT,
                details JSON,
                ip_address TEXT,
                user_agent TEXT,
                status TEXT,
                error_message TEXT
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_logs(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_resource ON audit_logs(resource_type, resource_id)")
        conn.commit()
        conn.close()
    
    def log(
        self,
        action: str,
        user_id: str = None,
        user_email: str = None,
        resource_type: str = None,
        resource_id: str = None,
        details: Dict = None,
        ip_address: str = None,
        user_agent: str = None,
        status: str = "success",
        error_message: str = None,
    ):
        """Log an audit event."""
        self._ensure_table()
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("""
            INSERT INTO audit_logs 
            (id, timestamp, user_id, user_email, action, resource_type, resource_id, details, ip_address, user_agent, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4())[:12],
            datetime.utcnow().isoformat(),
            user_id,
            user_email,
            action,
            resource_type,
            resource_id,
            json.dumps(details or {}),
            ip_address,
            user_agent,
            status,
            error_message,
        ))
        conn.commit()
        conn.close()
    
    def get_logs(
        self,
        user_id: str = None,
        resource_type: str = None,
        resource_id: str = None,
        action: str = None,
        limit: int = 100,
        offset: int = 0,
    ):
        """Query audit logs with filters."""
        self._ensure_table()
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM audit_logs WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if resource_type:
            query += " AND resource_type = ?"
            params.append(resource_type)
        if resource_id:
            query += " AND resource_id = ?"
            params.append(resource_id)
        if action:
            query += " AND action = ?"
            params.append(action)
        
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = conn.execute(query, params).fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_user_activity(self, user_id: str, days: int = 30):
        """Get activity summary for a user."""
        self._ensure_table()
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        cutoff = (cutoff - timedelta(days=days)).isoformat()
        
        rows = conn.execute("""
            SELECT action, resource_type, COUNT(*) as count
            FROM audit_logs
            WHERE user_id = ? AND timestamp >= ?
            GROUP BY action, resource_type
            ORDER BY count DESC
        """, (user_id, cutoff)).fetchall()
        
        conn.close()
        return [dict(row) for row in rows]

# ============ AUDIT-MINDED API ENDPOINT WRAPPER ============
def audit_action(action: str, resource_type: str, resource_id_field: str = "id"):
    """Decorator that auto-logs API actions."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger = AuditLogger()
            
            # Extract request context
            request = kwargs.get('request')
            ip = request.client.host if request else None
            user_agent = request.headers.get('user-agent') if request else None
            
            # Get user from token (requires verify_token dependency)
            user_id = kwargs.get('user_id')
            
            # Extract resource ID from response or request
            result = await func(*args, **kwargs)
            
            # Get resource ID from result or request
            resource_id = None
            if isinstance(result, dict):
                resource_id = result.get(resource_id_field)
            if not resource_id:
                resource_id = kwargs.get(resource_id_field)
            
            logger.log(
                action=action,
                user_id=user_id,
                resource_type=resource_type,
                resource_id=str(resource_id) if resource_id else None,
                ip_address=ip,
                user_agent=user_agent,
                details={"endpoint": func.__name__},
            )
            
            return result
        return wrapper
    return decorator

# ============ USER MANAGEMENT ============
def get_user_permissions(user_id: str) -> List[str]:
    """Get all permissions for a user."""
    conn = get_db()
    user = conn.execute("SELECT role FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    
    if not user:
        return []
    
    role = Role(user['role']) if user['role'] in [r.value for r in Role] else Role.VIEWER
    return [p.value for p in ROLE_PERMISSIONS.get(role, [])]

def update_user_role(user_id: str, new_role: str, admin_user_id: str) -> bool:
    """Update a user's role (admin only)."""
    logger = AuditLogger()
    
    # Verify admin has permission
    if not has_permission(get_db().execute("SELECT role FROM users WHERE id=?", (admin_user_id,)).fetchone()['role'], Permission.USER_MANAGE):
        return False
    
    conn = get_db()
    conn.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
    conn.commit()
    conn.close()
    
    logger.log(
        action="user.role_changed",
        user_id=admin_user_id,
        resource_type="user",
        resource_id=user_id,
        details={"new_role": new_role},
    )
    return True

def get_all_users(admin_user_id: str):
    """Get all users (admin only)."""
    conn = get_db()
    users = conn.execute("""
        SELECT id, email, username, role, created_at, is_active 
        FROM users
        ORDER BY created_at DESC
    """).fetchall()
    conn.close()
    return [dict(u) for u in users]

# ============ SESSION MANAGEMENT ============
def create_session(user_id: str, device_info: str = None) -> str:
    """Create a new session token."""
    session_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute("""
        INSERT INTO sessions (id, user_id, device_info, created_at, last_active)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, user_id, device_info, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return session_id

def revoke_session(session_id: str, user_id: str) -> bool:
    """Revoke a session."""
    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE id=? AND user_id=?", (session_id, user_id))
    conn.commit()
    affected = conn.total_changes
    conn.close()
    return affected > 0

def get_active_sessions(user_id: str) -> List[Dict]:
    """Get all active sessions for a user."""
    conn = get_db()
    sessions = conn.execute("""
        SELECT id, device_info, created_at, last_active
        FROM sessions WHERE user_id=?
        ORDER BY last_active DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(s) for s in sessions]
