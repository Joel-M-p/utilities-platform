import psycopg2
from decimal import Decimal  # Added this to fix the math error!

# --- Database Connection Function ---
def get_db_connection():
    return psycopg2.connect(
        dbname="utilities_platform",
        user="postgres",
        password="5432",
        host="localhost",
        port="5432"
    )

# --- The Waterfall of Payments Logic ---
def process_waterfall_payment(tenant_id, payment_amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Get the tenant's current arrears
        cursor.execute("SELECT rent_outstanding, utility_outstanding FROM tenants WHERE id = %s", (tenant_id,))
        rent_owed, utility_owed = cursor.fetchone()
        
        # Get the wallet ID
        cursor.execute("SELECT id FROM wallets WHERE tenant_id = %s", (tenant_id,))
        wallet_id = cursor.fetchone()[0]
        
        # Ensure we are using Decimal for our math
        remaining_payment = Decimal(str(payment_amount))
        
        # STEP 1: Pay outstanding rent
        if remaining_payment > 0 and rent_owed > 0:
            allocation = min(remaining_payment, rent_owed)
            new_rent_owed = rent_owed - allocation
            remaining_payment -= allocation
            
            # Update tenant rent arrears
            cursor.execute("UPDATE tenants SET rent_outstanding = %s WHERE id = %s", (new_rent_owed, tenant_id))
            # Record transaction
            cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, 'RENT_PAYMENT', 'Waterfall allocation')", (wallet_id, allocation))
            print(f"Allocated R{allocation:.2f} to Rent. Remaining rent owed: R{new_rent_owed:.2f}")

        # STEP 2: Pay outstanding utility bills
        if remaining_payment > 0 and utility_owed > 0:
            allocation = min(remaining_payment, utility_owed)
            new_utility_owed = utility_owed - allocation
            remaining_payment -= allocation
            
            # Update tenant utility arrears
            cursor.execute("UPDATE tenants SET utility_outstanding = %s WHERE id = %s", (new_utility_owed, tenant_id))
            # Record transaction
            cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, 'UTILITY_PAYMENT', 'Waterfall allocation')", (wallet_id, allocation))
            print(f"Allocated R{allocation:.2f} to Utilities. Remaining utility owed: R{new_utility_owed:.2f}")

        # STEP 3: Top up wallet for future utilities
        if remaining_payment > 0:
            cursor.execute("UPDATE wallets SET balance = balance + %s WHERE id = %s", (remaining_payment, wallet_id))
            cursor.execute("INSERT INTO transactions (wallet_id, amount, transaction_type, reference) VALUES (%s, %s, 'WALLET_TOPUP', 'Waterfall allocation')", (wallet_id, remaining_payment))
            print(f"Allocated R{remaining_payment:.2f} to Wallet Top-up.")

        # Commit the changes to the database
        conn.commit()
        print("\nSUCCESS: Payment fully allocated!")
        
    except Exception as e:
        conn.rollback() # Undo everything if there's an error
        print("ERROR:", e)
    finally:
        cursor.close()
        conn.close()

# --- Setup a Test Tenant ---
def setup_test_tenant():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Clear old test data
    cursor.execute("DELETE FROM transactions")
    cursor.execute("DELETE FROM wallets")
    cursor.execute("DELETE FROM tenants")
    
    # Create a tenant who owes R1000 rent and R500 utilities
    cursor.execute("""
        INSERT INTO tenants (first_name, last_name, rent_outstanding, utility_outstanding) 
        VALUES ('John', 'Doe', 1000.00, 500.00) RETURNING id
    """)
    tenant_id = cursor.fetchone()[0]
    
    # Create their wallet
    cursor.execute("INSERT INTO wallets (tenant_id, balance) VALUES (%s, 0.00)", (tenant_id,))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("--- Test Tenant Created ---")
    print("Name: John Doe")
    print("Rent Owed: R1000.00")
    print("Utility Owed: R500.00")
    print("Wallet Balance: R0.00\n")
    return tenant_id

# --- Run the Test! ---
if __name__ == "__main__":
    # 1. Create our fake tenant
    test_tenant_id = setup_test_tenant()
    
    # 2. Let's pretend John Doe pays R1200.
    print("--- Processing Payment of R1200.00 ---")
    process_waterfall_payment(test_tenant_id, Decimal('1200.00')) # Changed to Decimal!