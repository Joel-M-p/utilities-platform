import os
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Header
from jose import jwt, JWTError

# Pull the secret key from environment variables. Fallback is for local dev only.
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-dev-key-change-in-production")
ALGORITHM = "HS256"

# Backward compatibility for old hardcoded tokens (if you still need them)
SECRET_TOKEN = "super-secret-pm-wristband"
TENANT_TOKEN = "tenant-secret-wristband"

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
    
    # Backward compatibility for old hardcoded tokens
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