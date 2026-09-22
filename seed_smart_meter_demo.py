from api.database import get_db_connection
from datetime import datetime, timedelta
import random

def seed_demo_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # 1. Update all meters with mock battery voltage and last comms
        cursor.execute("SELECT id FROM meters WHERE is_active = TRUE")
        meters = cursor.fetchall()
        
        for m in meters:
            meter_id = m[0]
            # Mock battery voltage (3.2V-3.6V normal, one at 2.9V for demo)
            if meter_id == meters[0][0]:
                battery = 2.9  # Low battery demo
            else:
                battery = round(random.uniform(3.2, 3.6), 2)
            
            # Mock last communication (1-30 minutes ago)
            minutes_ago = random.randint(1, 30)
            last_comms = datetime.now() - timedelta(minutes=minutes_ago)
            
            cursor.execute("""
                UPDATE meters 
                SET meter_balance = %s,
                    valve_status = %s
                WHERE id = %s
            """, (
                round(random.uniform(50, 500), 2),
                random.choice(['OPEN', 'OPEN', 'OPEN', 'TRICKLE', 'CLOSED']),
                meter_id
            ))
        
        conn.commit()
        print(f"Updated {len(meters)} meters with mock data.")
        
        # 2. Insert mock meter events (alarms)
        alarms = [
            ('METER_101', 'WATER_LEAKAGE', 'Continuous flow detected for 26 hours. Flow: 0.3 m³/h', 'HIGH'),
            ('METER_205', 'LOW_BATTERY', 'Battery voltage at 2.9V. Replacement recommended within 30 days.', 'MEDIUM'),
            ('METER_308', 'TAMPER_DETECT', 'Magnetic interference detected. Valve auto-closed.', 'HIGH'),
            ('METER_412', 'VALVE_FAIL', 'Valve close command failed after 3 retries.', 'HIGH'),
            ('METER_503', 'LOW_BATTERY', 'Battery voltage at 3.1V. First level warning.', 'LOW'),
        ]
        
        for meter_serial, event_type, notes, severity in alarms:
            cursor.execute("""
                INSERT INTO meter_events (meter_id, event_type, event_notes, recorded_by, created_at)
                VALUES (
                    (SELECT id FROM meters WHERE serial_number = %s LIMIT 1),
                    %s, %s, 'SYSTEM', %s
                )
            """, (meter_serial, event_type, notes, datetime.now() - timedelta(hours=random.randint(1, 12))))
        
        conn.commit()
        print(f"Inserted {len(alarms)} mock alarms.")
        
        # 3. Insert mock hourly consumption data for trends
        cursor.execute("SELECT id FROM tenants WHERE status = 'ACTIVE' LIMIT 5")
        tenants = cursor.fetchall()
        
        for t in tenants:
            tenant_id = t[0]
            for hour in range(24):
                # Simulate realistic usage pattern (low at night, high morning/evening)
                if 0 <= hour < 6:
                    usage = round(random.uniform(0.5, 2.0), 2)
                elif 6 <= hour < 9:
                    usage = round(random.uniform(5.0, 15.0), 2)
                elif 9 <= hour < 17:
                    usage = round(random.uniform(2.0, 8.0), 2)
                elif 17 <= hour < 21:
                    usage = round(random.uniform(8.0, 20.0), 2)
                else:
                    usage = round(random.uniform(1.0, 4.0), 2)
                
                cursor.execute("""
                    INSERT INTO transactions (wallet_id, amount, transaction_type, reference, created_at, property_id)
                    VALUES (
                        (SELECT id FROM wallets WHERE tenant_id = %s LIMIT 1),
                        %s, 'USAGE', 
                        %s,
                        %s,
                        (SELECT property_id FROM tenants WHERE id = %s LIMIT 1)
                    )
                """, (
                    tenant_id, -usage, 
                    f'Hourly usage: {hour}:00 - {usage} L',
                    datetime.now().replace(hour=hour, minute=random.randint(0, 59), second=0),
                    tenant_id
                ))
        
        conn.commit()
        print(f"Inserted 24 hours of consumption data for {len(tenants)} tenants.")
        print("\nDemo data seeded successfully!")
        
    except Exception as e:
        print(f"ERROR: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    seed_demo_data()