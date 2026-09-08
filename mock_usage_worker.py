import os
import time
import random
import psycopg2
from decimal import Decimal

def get_db_connection():
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if "?sslmode=" not in db_url:
            db_url += "?sslmode=require"
        return psycopg2.connect(db_url)
    else:
        return psycopg2.connect(
            dbname="utilities_platform",
            user="postgres",
            password="5432",
            host="localhost",
            port="5432"
        )

def process_meter_usage(cursor, meter):
    meter_id, tenant_id, meter_type, billing_type, tariff_id, current_meter_balance, hardware_type = meter
    
    if not tariff_id:
        print(f"  [SKIP] Meter {meter_id} ({meter_type}): No tariff assigned to this meter.")
        return
        
    # Simulate usage between 0.1 and 1.5 units (kWh or kL)
    usage = Decimal(str(round(random.uniform(0.1, 1.5), 2)))
    
    # Fetch full tariff details
    cursor.execute("""
        SELECT structure_type, rate_flat, tier_1_limit, tier_1_rate, tier_2_rate, tou_peak_rate, tou_offpeak_rate 
        FROM tariffs WHERE id = %s
    """, (tariff_id,))
    tariff_data = cursor.fetchone()
    
    if not tariff_data:
        print(f"  [SKIP] Meter {meter_id} ({meter_type}): Tariff not found.")
        return
        
    structure = tariff_data[0]
    rate_flat = tariff_data[1] or Decimal('0')
    tier_1_limit = tariff_data[2] or 0
    tier_1_rate = tariff_data[3] or Decimal('0')
    tier_2_rate = tariff_data[4] or Decimal('0')
    tou_peak_rate = tariff_data[5] or Decimal('0')
    tou_offpeak_rate = tariff_data[6] or Decimal('0')

    bill_amount = Decimal('0.0')
    
    if structure == 'FLAT':
        bill_amount = usage * rate_flat
    elif structure == 'TIERED':
        if usage <= tier_1_limit:
            bill_amount = usage * tier_1_rate
        else:
            bill_amount = (Decimal(tier_1_limit) * tier_1_rate) + ((usage - Decimal(tier_1_limit)) * tier_2_rate)
    elif structure == 'TOU':
        # Mock worker assumes all usage is off-peak for simplicity
        bill_amount = usage * tou_offpeak_rate
    else:
        print(f"  [SKIP] Meter {meter_id} ({meter_type}): Unknown tariff structure {structure}.")
        return

    cost = bill_amount
    
    # Lock the wallet for safe deduction
    cursor.execute("SELECT id, balance FROM wallets WHERE tenant_id = %s FOR UPDATE", (tenant_id,))
    wallet_data = cursor.fetchone()
    if not wallet_data:
        print(f"  [SKIP] Meter {meter_id} ({meter_type}): Tenant has no wallet.")
        return
        
    wallet_id, wallet_balance = wallet_data
    
    if billing_type == 'PREPAID':
        if wallet_balance >= cost:
            # Sufficient funds: deduct from wallet
            new_wallet_balance = wallet_balance - cost
            cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_wallet_balance, wallet_id))
            
            # If it's a Smart IoT meter, increase the meter balance
            if hardware_type == 'SMART_IOT':
                cursor.execute("UPDATE meters SET meter_balance = meter_balance + %s WHERE id = %s", (usage, meter_id))
                
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference) 
                VALUES (%s, %s, %s, %s)
            """, (wallet_id, cost, f"{meter_type}_USAGE", f"Mock usage: {usage} units"))
            print(f"  [OK] Meter {meter_id} ({meter_type}): Deducted R{cost:.2f} for {usage} units.")
        else:
            # Insufficient funds: empty wallet, add shortfall to arrears, restrict meter
            shortfall = cost - wallet_balance
            cursor.execute("UPDATE wallets SET balance = 0.00 WHERE id = %s", (wallet_id,))
            
            if meter_type == 'ELECTRICITY':
                cursor.execute("UPDATE tenants SET electricity_outstanding = electricity_outstanding + %s WHERE id = %s", (shortfall, tenant_id))
                cursor.execute("UPDATE meters SET valve_status = 'DISCONNECTED' WHERE id = %s", (meter_id,))
            elif meter_type.startswith('WATER'):
                cursor.execute("UPDATE tenants SET water_outstanding = water_outstanding + %s WHERE id = %s", (shortfall, tenant_id))
                cursor.execute("UPDATE meters SET valve_status = 'TRICKLE' WHERE id = %s", (meter_id,))
                
            cursor.execute("""
                INSERT INTO transactions (wallet_id, amount, transaction_type, reference) 
                VALUES (%s, %s, %s, %s)
            """, (wallet_id, cost, f"{meter_type}_USAGE", f"Mock usage shortfall: {usage} units"))
            print(f"  [ARREARS] Meter {meter_id} ({meter_type}): Shortfall of R{shortfall:.2f}. Meter restricted!")
            
    elif billing_type == 'POSTPAID':
        # Postpaid: just add to arrears
        if meter_type == 'ELECTRICITY':
            cursor.execute("UPDATE tenants SET electricity_outstanding = electricity_outstanding + %s WHERE id = %s", (cost, tenant_id))
        elif meter_type.startswith('WATER'):
            cursor.execute("UPDATE tenants SET water_outstanding = water_outstanding + %s WHERE id = %s", (cost, tenant_id))
            
        cursor.execute("""
            INSERT INTO transactions (wallet_id, amount, transaction_type, reference) 
            VALUES (%s, %s, %s, %s)
        """, (wallet_id, cost, f"{meter_type}_BILL", f"Mock postpaid bill: {usage} units"))
        print(f"  [OK] Meter {meter_id} ({meter_type}): Postpaid bill of R{cost:.2f} added to arrears.")

def run_worker():
    print("Starting Mock Utility Usage Worker...")
    print("Press Ctrl+C to stop.")
    while True:
        conn = None
        try:
            conn = get_db_connection()
            conn.autocommit = False
            cursor = conn.cursor()
            
            # Get all active meters
            cursor.execute("""
                SELECT id, tenant_id, meter_type, billing_type, tariff_id, meter_balance, hardware_type 
                FROM meters WHERE is_active = TRUE
            """)
            meters = cursor.fetchall()
            
            print(f"\n--- Processing {len(meters)} active meters ---")
            
            for meter in meters:
                try:
                    process_meter_usage(cursor, meter)
                except Exception as e:
                    print(f"  [ERROR] Processing meter {meter[0]} failed: {e}")
                    conn.rollback() # Rollback just this meter's transaction if it fails
                    
            conn.commit()
            print("--- Cycle complete. Sleeping for 15 seconds... ---")
            
        except Exception as e:
            print(f"Worker loop error: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                cursor.close()
                conn.close()
                
        # Sleep for 15 seconds to simulate real-time usage
        time.sleep(15)

if __name__ == "__main__":
    run_worker()