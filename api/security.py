import os
import hmac
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

def resolve_property_scope(current_user: dict, requested_property_id: int = None):
    """Returns the property_id a request is allowed to operate on, or None for 'all properties'.

    This is the single source of truth for property-level data isolation on any endpoint
    that reads or writes across tenants. The rule:

      - ADMIN may pass an explicit property_id to filter by, or omit it to see everything.
      - Every other role (PM_SUPER, PM_USER, ...) is ALWAYS forced to their own assigned
        property, regardless of what property_id the client sent. A non-admin with no
        assigned property gets 403 rather than silently falling through to global data.

    Endpoints must apply the returned value as a WHERE filter. Trusting a client-supplied
    property_id without passing it through here is what allowed a Manager on Property A to
    read and mutate Property B's data.
    """
    role = current_user.get("role")
    if role == "ADMIN":
        if requested_property_id is not None and requested_property_id > 0:
            return requested_property_id
        return None

    user_property_id = current_user.get("property_id")
    if not user_property_id:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: your user account is not assigned to a property."
        )
    return user_property_id


def verify_webhook_secret(x_webhook_secret: str = Header(None)):
    """Authenticates server-to-server webhook calls from the external ERP system.

    The ERP webhook mutates tenant arrears and sweeps real wallet balances, so it cannot be
    left open. It is machine-to-machine, so it uses a shared secret header rather than a JWT.
    Set ERP_WEBHOOK_SECRET in the environment (Render dashboard) and have the ERP send the
    same value in the X-Webhook-Secret header. If the variable is unset the endpoint refuses
    all calls: failing closed is correct here, since failing open is the vulnerability.
    """
    expected = os.getenv("ERP_WEBHOOK_SECRET")
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="ERP webhook is not configured on this server (ERP_WEBHOOK_SECRET is not set)."
        )
    if not x_webhook_secret or not hmac.compare_digest(x_webhook_secret, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing webhook secret.")
    return True


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