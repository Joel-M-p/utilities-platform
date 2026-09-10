import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Import your modular routers (INCLUDING AUDIT, METER EVENTS, AND FRAUD)
from api.routers import (
    auth, tenants, billing, transactions, tariffs, recon, invoices, 
    company, aging, stats, reports, bulk, bi, advanced_reports, export, 
    properties, erp, users, audit, meter_events, fraud
)

app = FastAPI(title="Utilities Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth.router)
app.include_router(tenants.router)
app.include_router(billing.router)
app.include_router(transactions.router)
app.include_router(tariffs.router)
app.include_router(recon.router)
app.include_router(invoices.router)
app.include_router(company.router)
app.include_router(aging.router)
app.include_router(stats.router)
app.include_router(reports.router)
app.include_router(bulk.router)
app.include_router(bi.router)
app.include_router(advanced_reports.router)
app.include_router(export.router)
app.include_router(properties.router)
app.include_router(erp.router)
app.include_router(users.router)
app.include_router(audit.router)
app.include_router(meter_events.router)
app.include_router(fraud.router) # NEW: For Fraud Intelligence

if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Modular Utilities Platform API! The server is running."}

@app.get("/setup")
def setup_database():
    try:
        from api.models import init_db
        init_db()
        return {"status": "success", "message": "Database tables created successfully in the cloud!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Serve the Web Pages ---
@app.get("/dashboard", response_class=HTMLResponse)
def serve_dashboard():
    with open("dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/m", response_class=HTMLResponse)
def serve_mobile_pm():
    with open("mobile_pm.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/tenant", response_class=HTMLResponse)
def serve_tenant():
    with open("tenant_portal.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/bi", response_class=HTMLResponse)
def serve_bi():
    with open("bi_dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/reports", response_class=HTMLResponse)
def serve_reports():
    with open("reports_dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())