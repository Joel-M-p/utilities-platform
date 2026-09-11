import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Header, Depends
from jose import jwt, JWTError

# Pull the secret key from environment variables. Fallback is for local dev only.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-dev-key-change-in-production")
ALGORITHM = "HS256"

# Backward compatibility for old hardcoded tokens.
# These are permanent, unrevocable, DB-independent bearer credentials (ADMIN / TENANT
# full access) baked into source. They must be OFF by default in any deployed
# environment. Only flip ENABLE_LEGACY_TOKENS=true for local dev if you still need them,
# and never set it on Render/production.
SECRET_TOKEN = "super-secret-pm-wristband"
TENANT_TOKEN = "tenant-secret-wristband"
LEGACY_TOKENS_ENABLED = os.getenv("ENABLE_LEGACY_TOKENS", "false").lower() == "true"

def create_token(user_id: int, role: str, property_id: int = None, tenant_id: int = None):
    # Token expires in 12 hours
    expire = datetime.now(timezone.utc) + timedelta(hours=12)
    payload = {
        "user_id": user_id, 
        "role": role, 
        "property_id": property_id,
        "tenant_id": tenant_id,
        "exp": expire
    }
    # Encode and sign the token
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    token = authorization.split(" ")[1]
    
    # Backward compatibility for old hardcoded tokens (disabled unless explicitly enabled)
    if LEGACY_TOKENS_ENABLED:
        if token == SECRET_TOKEN:
            return {"user_id": 0, "role": "ADMIN", "property_id": None, "tenant_id": None}
        if token == TENANT_TOKEN:
            return {"user_id": -1, "role": "TENANT", "property_id": None, "tenant_id": None}
        
    try:
        # Decode and verify the signature. If it was tampered with, this throws an error.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token. Please log in again.")

def enforce_property_access(current_user: dict, target_property_id: int):
    """
    Ensures a Manager can only interact with tenants/meters belonging to their property.
    Admins and Tenants bypass this specific check.
    """
    role = current_user.get("role")
    if role in ["ADMIN", "TENANT"]:
        return
    
    user_property_id = current_user.get("property_id")
    if user_property_id is None or user_property_id != target_property_id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this property's data.")

def require_staff(current_user: dict = Depends(verify_token)):
    """
    FastAPI dependency that blocks TENANT-role tokens from staff/admin-only endpoints
    (manual billing, wallet adjustments, credit limit changes, restrict/unrestrict,
    admin wallet resets). enforce_property_access() intentionally waves TENANT role
    through its property check (since tenants aren't scoped by property staff
    assignment), which means any endpoint that relies on enforce_property_access alone
    is reachable by a TENANT token unless it's gated here as well. Property-level
    scoping for staff is still enforced separately at the call site.
    """
    if current_user.get("role") == "TENANT":
        raise HTTPException(status_code=403, detail="Forbidden: this action requires property staff access.")
    return current_user