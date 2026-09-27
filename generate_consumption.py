from api.database import get_db_connection
from datetime import datetime, timedelta
import random
import uuid

def generate_consumption():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT t.id, t.property_id, w.id as wallet_id, w.balance, m.meter_type, m.id as meter_id
            FROM tenants t
            JOIN wallets w ON t.id = w.tenant_id
            LEFT JOIN meters m ON m.tenant_id = t.id AND m.is_active = TRUE
            WHERE t.status = 'ACTIVE'
        """)
        tenants = cursor.fetchall()
        
        if not tenants:
            print("No active tenants with wallets found.")
            return
        
        print(f"Found {len(tenants)} active tenant-meter combinations.")
        print("Generating 30 days of consumption data...\n")
        
        total_transactions = 0
        now = datetime.now()
        
        for t in tenants:
            tenant_id, property_id, wallet_id, wallet_balance, meter_type, meter_id = t
            
            # Convert to float to avoid Decimal/float mismatch
            current_balance = float(wallet_balance) if wallet_balance else 0.0
            
            for days_ago in range(30, 0, -1):
                date = now - timedelta(days=days_ago)
                
                if random.random() < 0.15:
                    continue
                
                num_txns = random.choice([1, 1, 1, 2, 2, 3])
                
                for _ in range(num_txns):
                    hour = random.randint(6, 22)
                    minute = random.randint(0, 59)
                    tx_date = date.replace(hour=hour, minute=minute, second=0)
                    
                    if meter_type == 'ELECTRICITY':
                        amount = round(random.uniform(5, 50), 2)
                        tx_type = 'USAGE_ELECTRICITY'
                        reference = f'Electricity usage: {random.uniform(2, 15):.1f} kWh'
                    elif meter_type == 'WATER_COLD':
                        amount = round(random.uniform(2, 20), 2)
                        tx_type = 'USAGE_WATER_COLD'
                        reference = f'Cold water usage: {random.uniform(50, 500):.0f} L'
                    elif meter_type == 'WATER_HOT':
                        amount = round(random.uniform(3, 30), 2)
                        tx_type = 'USAGE_WATER_HOT'
                        reference = f'Hot water usage: {random.uniform(20, 200):.0f} L'
                    else:
                        amount = round(random.uniform(2, 25), 2)
                        tx_type = 'USAGE'
                        reference = f'Utility usage: {random.uniform(10, 100):.0f} units'
                    
                    new_balance = current_balance - amount
                    if new_balance < 0:
                        new_balance = 0.0
                    
                    cursor.execute("""
                        INSERT INTO transactions 
                        (wallet_id, amount, transaction_type, reference, created_at, 
                         property_id, meter_id, status, idempotency_key, before_balance, after_balance)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'COMPLETED', %s, %s, %s)
                    """, (wallet_id, -abs(amount), tx_type, reference, tx_date,
                          property_id, meter_id, str(uuid.uuid4()),
                          current_balance, new_balance))
                    
                    current_balance = new_balance
                    total_transactions += 1
            
            cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (current_balance, wallet_id))
        
        conn.commit()
        print(f"\nSUCCESS! Generated {total_transactions} usage transactions.")
        print(f"Wallet balances updated.")
        
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    generate_consumption()