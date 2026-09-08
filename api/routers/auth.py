from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import create_token, verify_token
import hashlib

router = APIRouter()

@router.post("/login/")
def api_login(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        username = payload.get("username")
        password = payload.get("password")
        hashed_pass = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("SELECT id, username, password, role, property_id FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        
        if not user or user[2] != hashed_pass:
            raise HTTPException(status_code=401, detail="Invalid username or password")
            
        # Create the secure JWT token
        token = create_token(user[0], user[3], user[4])
        return {
            "status": "success", 
            "token": token, 
            "role": user[3], 
            "property_id": user[4],
            "message": "Login successful!"
        }
    finally:
        cursor.close()
        conn.close()

@router.post("/tenant-login/")
def api_tenant_login(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        property_id = payload.get("property_id")
        unit_number = payload.get("unit_number")
        email = payload.get("email")
        
        cursor.execute("SELECT id, email, property_id FROM tenants WHERE unit_number = %s AND property_id = %s", (unit_number, property_id))
        tenant_data = cursor.fetchone()
        
        if not tenant_data:
            raise HTTPException(status_code=404, detail="Tenant not found for this Unit Number at this Property")
        if tenant_data[1] != email:
            raise HTTPException(status_code=401, detail="Invalid email for this Unit Number")
            
        # Issue a real JWT for the tenant, embedding their tenant_id and property_id
        token = create_token(user_id=tenant_data[0], role="TENANT", property_id=tenant_data[2], tenant_id=tenant_data[0])
        
        return {
            "status": "success", 
            "token": token, 
            "tenant_id": tenant_data[0], 
            "property_id": tenant_data[2],
            "message": "Tenant login successful!"
        }
    finally:
        cursor.close()
        conn.close()

# --- USER MANAGEMENT ENDPOINTS ---

@router.get("/users/", dependencies=[Depends(verify_token)])
def api_get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT u.id, u.username, u.role, u.property_id, p.name 
            FROM users u 
            LEFT JOIN properties p ON u.property_id = p.id
            ORDER BY u.id ASC
        """)
        users = cursor.fetchall()
        users_list = []
        for u in users:
            users_list.append({
                "id": u[0],
                "username": u[1],
                "role": u[2],
                "property_id": u[3],
                "property_name": u[4] if u[4] else "All Properties (Admin)"
            })
        return {"users": users_list}
    finally:
        cursor.close()
        conn.close()

@router.post("/users/", dependencies=[Depends(verify_token)])
def api_create_user(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        username = payload.get("username")
        password = payload.get("password")
        role = payload.get("role")
        property_id = payload.get("property_id")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
            
        if not property_id:
            property_id = None # Ensure it's NULL for Admins, not an empty string

        hashed_pass = hashlib.sha256(password.encode()).hexdigest()

        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Username already exists")

        cursor.execute("""
            INSERT INTO users (username, password, role, property_id) 
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (username, hashed_pass, role, property_id))
        user_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "message": "User created successfully", "user_id": user_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()