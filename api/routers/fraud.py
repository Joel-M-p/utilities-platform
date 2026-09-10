from fastapi import APIRouter, HTTPException, Depends
from api.database import get_db_connection
from api.security import verify_token
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/fraud-analysis/")
def get_fraud_analysis(property_id: int = None, current_user: dict = Depends(verify_token)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        user_role = current_user.get("role")
        user_prop_id = current_user.get("property_id")

        target_property_id = None
        if user_role == "ADMIN":
            if property_id is not None and property_id > 0:
                target_property_id = property_id
        else:
            target_property_id = user_prop_id

        # 1. Get active tenants with active PREPAID electricity meters
        query = """
            SELECT t.id, t.unit_number, t.first_name, t.last_name, w.id as wallet_id, w.balance, w.credit_limit
            FROM tenants t
            JOIN meters m ON m.tenant_id = t.id AND m.meter_type = 'ELECTRICITY' AND m.billing_type = 'PREPAID' AND m.is_active = TRUE
            JOIN wallets w ON w.tenant_id = t.id
            WHERE t.status = 'ACTIVE'
        """
        params = []
        if target_property_id:
            query += " AND t.property_id = %s"
            params.append(target_property_id)
        
        cursor.execute(query, params)
        tenants = cursor.fetchall()
        
        if not tenants:
            return {"status": "success", "flags": []}

        # 2. Fetch all electricity purchases for these tenants in the last 90 days
        txn_query = """
            SELECT wallet_id, amount, created_at 
            FROM transactions 
            WHERE transaction_type = 'ELECTRICITY_PURCHASE' 
            AND created_at >= NOW() - INTERVAL '90 days'
        """
        if target_property_id:
            txn_query += " AND property_id = %s"
            cursor.execute(txn_query, (target_property_id,))
        else:
            cursor.execute(txn_query)

        txns = cursor.fetchall()

        # 3. Organize transactions by wallet_id
        wallet_txns = {}
        for t in txns:
            w_id = t[0]
            if w_id not in wallet_txns:
                wallet_txns[w_id] = []
            wallet_txns[w_id].append({"amount": float(t[1]), "date": t[2]})

        # 4. Analyze patterns
        flags = []
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        ninety_days_ago = now - timedelta(days=90)

        for t in tenants:
            t_id, unit, first, last, w_id, wallet_bal, credit_lim = t
            tenant_name = f"{first} {last}"
            tenant_txns = wallet_txns.get(w_id, [])
            
            # Calculate usage totals
            last_30_days_total = sum(t['amount'] for t in tenant_txns if t['date'] >= thirty_days_ago)
            prev_60_days_total = sum(t['amount'] for t in tenant_txns if t['date'] >= ninety_days_ago and t['date'] < thirty_days_ago)

            # Rule 1: Zero Purchases in 30 days (Possible Bypass)
            if last_30_days_total == 0:
                flags.append({
                    "tenant_id": t_id,
                    "unit_number": unit,
                    "tenant_name": tenant_name,
                    "flag_type": "ZERO PURCHASES (30 DAYS)",
                    "details": "Tenant has an active prepaid meter but has not purchased electricity in the last 30 days. Possible meter bypass or illegal connection.",
                    "severity": "HIGH"
                })
            
            # Rule 2: Sudden Drop (>50% drop compared to previous 60 days)
            elif prev_60_days_total > 0:
                # Project the 30-day total to a 60-day equivalent to compare fairly
                projected_60_day_rate = last_30_days_total * 2
                if projected_60_day_rate < (prev_60_days_total * 0.50): 
                    flags.append({
                        "tenant_id": t_id,
                        "unit_number": unit,
                        "tenant_name": tenant_name,
                        "flag_type": "SUDDEN DROP IN USAGE",
                        "details": f"Usage dropped from R{prev_60_days_total:.2f} (prev 2 months) to R{last_30_days_total:.2f} (last month). Possible meter tampering.",
                        "severity": "MEDIUM"
                    })

            # Rule 3: High Reliance on Credit (Financial Distress)
            # If wallet balance is 0 or negative, but they have a credit limit and are still buying power
            if float(wallet_bal) <= 0 and float(credit_lim or 0) > 0:
                flags.append({
                    "tenant_id": t_id,
                    "unit_number": unit,
                    "tenant_name": tenant_name,
                    "flag_type": "HIGH RELIANCE ON CREDIT",
                    "details": f"Wallet balance is R{float(wallet_bal):.2f}. Tenant is surviving entirely on their R{float(credit_lim):.2f} overdraft. High risk of defaulting on next rent cycle.",
                    "severity": "LOW"
                })

        # Sort flags by severity (HIGH first)
        severity_order = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
        flags.sort(key=lambda x: severity_order.get(x["severity"], 4))

        return {"status": "success", "flags": flags}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()