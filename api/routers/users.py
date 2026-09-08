from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token
import hashlib

router = APIRouter()

@router.get("/users/", dependencies=[Depends(verify_token)])
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Self-healing schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'PM_USER',
                property_id INTEGER
            );
        """)
        conn.commit()

        cursor.execute("SELECT id, username, role, property_id FROM users ORDER BY id ASC")
        rows = cursor.fetchall()
        users = []
        for r in rows:
            users.append({"id": r[0], "username": r[1], "role": r[2], "property_id": r[3]})
        return {"users": users}
    finally:
        cursor.close()
        conn.close()

@router.post("/users/", dependencies=[Depends(verify_token)])
def create_user(payload: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Self-healing schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'PM_USER',
                property_id INTEGER
            );
        """)
        conn.commit()

        username = payload.get("username")
        password = payload.get("password")
        role = payload.get("role", "PM_USER")
        property_id = payload.get("property_id")
        
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required")
            
        hashed_pass = hashlib.sha256(password.encode()).hexdigest()
        
        cursor.execute("""
            INSERT INTO users (username, password, role, property_id) 
            VALUES (%s, %s, %s, %s) RETURNING id
        """, (username, hashed_pass, role.upper(), property_id))
        user_id = cursor.fetchone()[0]
        conn.commit()
        return {"status": "success", "message": "User created successfully", "user_id": user_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()