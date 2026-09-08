from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import psycopg2
from decimal import Decimal
import random

# Create the API App
app = FastAPI(title="Utilities Platform API")

# Allow web browsers to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security Configuration ---
PM_USERNAME = "admin"
PM_PASSWORD = "password123"
SECRET_TOKEN = "super-secret-pm-wristband"
TENANT_TOKEN = "tenant-secret-wristband"

# --- Data Models ---
class PaymentRequest(BaseModel):
    tenant_id: int
    amount: float

class TenantRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    rent_outstanding: float = 0.0
    utility_outstanding: float = 0.0

class BillRequest(BaseModel):
    tenant_id: int
    utility_amount: float

class TokenRequest(BaseModel):
    tenant_id: int
    amount: float

class LoginRequest(BaseModel):
    username: str
    password: str

class TenantLoginRequest(BaseModel):
    tenant_id: int
    email: str

# --- Database Connection Function ---
def get_db_connection():
    return psycopg2.connect(
        dbname="utilities_platform",
        user="postgres",
        password="5432",
        host="localhost",
        port="5432"
    )

# --- Security Function to check the Token ---
def verify_token(authorization: str = Header(...)):
    if authorization not in [f"Bearer {SECRET_TOKEN}", f"Bearer {TENANT_TOKEN}"]:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing token. Please log in.")
    return True

# --- Notification System ---
def send_notification(tenant_name, contact_info, message):
    print("\n" + "="*50)
    print("📱 NOTIFICATION MODULE")
    print(f"To: {tenant_name} ({contact_info})")
    print(f"Message: {message}")
    print("="*50 + "\n")

# --- The Waterfall of Payments Logic ---
def process_waterfall_payment(tenant_id, payment_amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT first_name, last_name, email, rent_outstanding, utility_outstanding FROM tenants WHERE id = %s", (tenant_id,))
        tenant_data = cursor.fetchone()
        if not tenant_data:
            raise Exception("Tenant not found")
        first_name, last_name, email, rent_owed, utility_owed = tenant_data
        cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant_id,))
        wallet_id = cursor.fetchone()[0]
        remaining_payment = Decimal(str(payment_amount))
        
        if remaining_payment > 0 and rent_owed > 0:
            allocation = min(remaining_payment, rent_owed)
            new_rent_owed = rent_owed - allocation
            remaining_payment -= allocation
            cursor.execute("UPDATE tenants SET rent_outstanding = %s WHERE id = %s", (new_rent_owed, tenant_id))
            cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, 'RENT_PAYMENT', 'API Waterfall')", (wallet_id, allocation))

        if remaining_payment > 0 and utility_owed > 0:
            allocation = min(remaining_payment, utility_owed)
            new_utility_owed = utility_owed - allocation
            remaining_payment -= allocation
            cursor.execute("UPDATE tenants SET utility_outstanding = %s WHERE id = %s", (new_utility_owed, tenant_id))
            cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, 'UTILITY_PAYMENT', 'API Waterfall')", (wallet_id, allocation))

        if remaining_payment > 0:
            cursor.execute("UPDATE wallets SET balance = balance + %s WHERE id = %s", (remaining_payment, wallet_id))
            cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, 'WALLET_TOPUP', 'API Waterfall')", (wallet_id, remaining_payment))

        conn.commit()
        send_notification(f"{first_name} {last_name}", email, f"We have received your payment of R{payment_amount:.2f}. Thank you!")
        return {"status": "success", "message": "Payment allocated successfully"}
    except Exception as e:
        conn.rollback()
        raise Exception(str(e))
    finally:
        cursor.close()
        conn.close()

# --- The API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Utilities Platform API! The server is running."}

@app.post("/login/")
def api_login(login: LoginRequest):
    if login.username == PM_USERNAME and login.password == PM_PASSWORD:
        return {"status": "success", "token": SECRET_TOKEN, "message": "Login successful!"}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

@app.post("/tenant-login/")
def api_tenant_login(login: TenantLoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, email FROM tenants WHERE id = %s", (login.tenant_id,))
        tenant_data = cursor.fetchone()
        if not tenant_data:
            raise HTTPException(status_code=404, detail="Tenant not found")
        if tenant_data[1] != login.email:
            raise HTTPException(status_code=401, detail="Invalid email for this Tenant ID")
        return {"status": "success", "token": TENANT_TOKEN, "message": "Tenant login successful!"}
    finally:
        cursor.close()
        conn.close()

@app.post("/process-payment/", dependencies=[Depends(verify_token)])
def api_process_payment(payment: PaymentRequest):
    try:
        result = process_waterfall_payment(payment.tenant_id, payment.amount)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/tenant-balance/{tenant_id}", dependencies=[Depends(verify_token)])
def api_get_tenant_balance(tenant_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT first_name, last_name, rent_outstanding, utility_outstanding FROM tenants WHERE id = %s", (tenant_id,))
        tenant_data = cursor.fetchone()
        if not tenant_data:
            raise HTTPException(status_code=404, detail="Tenant not found")
        cursor.execute("SELECT balance FROM wallets WHERE tenant_id = %s", (tenant_id,))
        wallet_data = cursor.fetchone()
        return {
            "tenant_name": f"{tenant_data[0]} {tenant_data[1]}",
            "rent_outstanding": float(tenant_data[2]),
            "utility_outstanding": float(tenant_data[3]),
            "wallet_balance": float(wallet_data[0])
        }
    finally:
        cursor.close()
        conn.close()

@app.get("/all-tenants/", dependencies=[Depends(verify_token)])
def api_get_all_tenants():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT t.id, t.first_name, t.last_name, t.email, t.rent_outstanding, t.utility_outstanding, w.balance
            FROM tenants t JOIN wallets w ON t.id = w.tenant_id ORDER BY t.id ASC
        """)
        rows = cursor.fetchall()
        tenants_list = []
        for row in rows:
            tenants_list.append({
                "tenant_id": row[0], "first_name": row[1], "last_name": row[2], "email": row[3],
                "rent_outstanding": float(row[4]), "utility_outstanding": float(row[5]),
                "wallet_balance": float(row[6])
            })
        return {"status": "success", "tenants": tenants_list}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# NEW ENDPOINT: BI Dashboard Stats
@app.get("/bi-stats/", dependencies=[Depends(verify_token)])
def api_get_bi_stats():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Get total tenants, total rent owed, total utility owed
        cursor.execute("SELECT COUNT(*), COALESCE(SUM(rent_outstanding), 0), COALESCE(SUM(utility_outstanding), 0) FROM tenants")
        stats = cursor.fetchone()
        
        # Get total wallet balances across all tenants
        cursor.execute("SELECT COALESCE(SUM(balance), 0) FROM wallets")
        wallet_stats = cursor.fetchone()
        
        return {
            "total_tenants": stats[0],
            "total_rent_outstanding": float(stats[1]),
            "total_utility_outstanding": float(stats[2]),
            "total_wallet_balance": float(wallet_stats[0])
        }
    finally:
        cursor.close()
        conn.close()

@app.post("/create-tenant/", dependencies=[Depends(verify_token)])
def api_create_tenant(tenant: TenantRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO tenants (first_name, last_name, email, rent_outstanding, utility_outstanding) 
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (tenant.first_name, tenant.last_name, tenant.email, tenant.rent_outstanding, tenant.utility_outstanding))
        new_tenant_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO wallets (tenant_id, balance) VALUES (%s, 0.00)", (new_tenant_id,))
        conn.commit()
        send_notification(f"{tenant.first_name} {tenant.last_name}", tenant.email, "Welcome to the Utilities Platform!")
        return {"status": "success", "message": "Tenant created successfully!", "tenant_id": new_tenant_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/generate-bill/", dependencies=[Depends(verify_token)])
def api_generate_bill(bill: BillRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT first_name, last_name, email, utility_outstanding FROM tenants WHERE id = %s", (bill.tenant_id,))
        tenant_data = cursor.fetchone()
        if not tenant_data:
            raise HTTPException(status_code=404, detail="Tenant not found")
        first_name, last_name, email, current_utility_owed = tenant_data
        new_utility_owed = current_utility_owed + Decimal(str(bill.utility_amount))
        cursor.execute("UPDATE tenants SET utility_outstanding = %s WHERE id = %s", (new_utility_owed, bill.tenant_id))
        cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (bill.tenant_id,))
        wallet_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, 'UTILITY_BILL', 'Monthly Meter Reading')", (wallet_id, bill.utility_amount))
        conn.commit()
        send_notification(f"{first_name} {last_name}", email, f"Your monthly utility bill of R{bill.utility_amount:.2f} has been generated.")
        return {"status": "success", "message": "Utility bill generated successfully!", "new_utility_outstanding": float(new_utility_owed)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@app.post("/buy-electricity/", dependencies=[Depends(verify_token)])
def api_buy_electricity(req: TokenRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT first_name, last_name, email FROM tenants WHERE id = %s", (req.tenant_id,))
        tenant_data = cursor.fetchone()
        if not tenant_data:
            raise HTTPException(status_code=404, detail="Tenant not found")
        first_name, last_name, email = tenant_data
        cursor.execute("SELECT id, balance FROM wallets WHERE tenant_id = %s", (req.tenant_id,))
        wallet_data = cursor.fetchone()
        if not wallet_data:
            raise HTTPException(status_code=404, detail="Wallet not found")
        wallet_id, current_balance = wallet_data
        amount_decimal = Decimal(str(req.amount))
        
        if current_balance < amount_decimal:
            send_notification(f"{first_name} {last_name}", email, "Attempt to buy electricity failed. Insufficient funds.")
            raise HTTPException(status_code=400, detail="Insufficient funds in wallet. Please top up first.")
            
        new_balance = current_balance - amount_decimal
        cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_balance, wallet_id))
        token = ''.join([str(random.randint(0, 9)) for _ in range(20)])
        cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, 'ELECTRICITY_PURCHASE', %s)", (wallet_id, amount_decimal, f"Token: {token}"))
        conn.commit()
        send_notification(f"{first_name} {last_name}", email, f"Electricity purchase successful! Your token is: {token}")
        return {"status": "success", "message": "Electricity purchased successfully!", "token": token, "amount_paid": float(amount_decimal), "new_wallet_balance": float(new_balance)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# --- Serve the Web Pages from the API ---
@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/tenant", response_class=HTMLResponse)
def serve_tenant():
    with open("tenant_portal.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# NEW: Serve the BI Dashboard
@app.get("/bi", response_class=HTMLResponse)
def serve_bi():
    with open("bi_dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())