from decimal import Decimal

def process_waterfall_payment(cursor, tenant_id, payment_amount, rent_pct=None, elec_pct=None, water_pct=None, idempotency_key=None):
    cursor.execute("""
        SELECT first_name, last_name, email, property_id, rent_outstanding, electricity_outstanding, water_outstanding 
        FROM tenants WHERE id = %s FOR UPDATE
    """, (tenant_id,))
    tenant_data = cursor.fetchone()
    
    if not tenant_data:
        raise Exception("Tenant not found")
        
    first_name, last_name, email, property_id, rent_owed, elec_owed, water_owed = tenant_data
    
    cursor.execute("SELECT id, balance, credit_limit, credit_balance, credit_debt FROM wallets WHERE tenant_id = %s FOR UPDATE", (tenant_id,))
    wallet_row = cursor.fetchone()
    if not wallet_row:
        raise Exception("Wallet not found")
    wallet_id, current_balance, credit_limit, credit_balance, credit_debt = wallet_row
    
    payment_amount = Decimal(str(payment_amount))
    
    if not rent_pct and not elec_pct and not water_pct:
        rent_pct = Decimal('100')
        elec_pct = Decimal('0')
        water_pct = Decimal('0')
    else:
        rent_pct = Decimal(str(rent_pct or 0))
        elec_pct = Decimal(str(elec_pct or 0))
        water_pct = Decimal(str(water_pct or 0))

    rent_target = payment_amount * (rent_pct / Decimal('100'))
    elec_target = payment_amount * (elec_pct / Decimal('100'))
    water_target = payment_amount * (water_pct / Decimal('100'))
    
    spillover = Decimal('0.0')
    
    def insert_txn(amount, t_type, ref, before_bal, after_bal, suffix):
        key = f"{idempotency_key}-{suffix}" if idempotency_key else None
        cursor.execute("""
            INSERT INTO transactions (wallet_id, amount, transaction_type, reference, property_id, before_balance, after_balance, idempotency_key) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (wallet_id, amount, t_type, ref, property_id, before_bal, after_bal, key))

    # STEP 1: Allocate Rent
    if rent_target > 0:
        if rent_owed > 0:
            allocation = min(rent_target, rent_owed)
            new_rent_owed = rent_owed - allocation
            rent_owed = new_rent_owed
            spillover += (rent_target - allocation) 
            cursor.execute("UPDATE tenants SET rent_outstanding = %s WHERE id = %s", (new_rent_owed, tenant_id))
            insert_txn(allocation, 'RENT_PAYMENT', 'Percentage Waterfall', current_balance, current_balance, "RENT")
        else:
            spillover += rent_target

    # STEP 2: Allocate Electricity
    if elec_target > 0:
        if elec_owed > 0:
            allocation = min(elec_target, elec_owed)
            new_elec_owed = elec_owed - allocation
            elec_owed = new_elec_owed
            spillover += (elec_target - allocation)
            cursor.execute("UPDATE tenants SET electricity_outstanding = %s WHERE id = %s", (new_elec_owed, tenant_id))
            insert_txn(allocation, 'ELECTRICITY_PAYMENT', 'Percentage Waterfall', current_balance, current_balance, "ELEC")
        else:
            spillover += elec_target

    # STEP 3: Allocate Water
    if water_target > 0:
        if water_owed > 0:
            allocation = min(water_target, water_owed)
            new_water_owed = water_owed - allocation
            water_owed = new_water_owed
            spillover += (water_target - allocation)
            cursor.execute("UPDATE tenants SET water_outstanding = %s WHERE id = %s", (new_water_owed, tenant_id))
            insert_txn(allocation, 'WATER_PAYMENT', 'Percentage Waterfall', current_balance, current_balance, "WATER")
        else:
            spillover += water_target

    # STEP 4: Handle Spillover (If a specific utility had no arrears, its % goes to the remaining arrears)
    if spillover > 0:
        if rent_owed > 0:
            allocation = min(spillover, rent_owed)
            new_rent_owed = rent_owed - allocation
            spillover -= allocation
            cursor.execute("UPDATE tenants SET rent_outstanding = %s WHERE id = %s", (new_rent_owed, tenant_id))
            insert_txn(allocation, 'RENT_PAYMENT', 'Waterfall Spillover', current_balance, current_balance, "SPILL_RENT")
        
        if spillover > 0 and elec_owed > 0:
            allocation = min(spillover, elec_owed)
            new_elec_owed = elec_owed - allocation
            spillover -= allocation
            cursor.execute("UPDATE tenants SET electricity_outstanding = %s WHERE id = %s", (new_elec_owed, tenant_id))
            insert_txn(allocation, 'ELECTRICITY_PAYMENT', 'Waterfall Spillover', current_balance, current_balance, "SPILL_ELEC")
            
        if spillover > 0 and water_owed > 0:
            allocation = min(spillover, water_owed)
            new_water_owed = water_owed - allocation
            spillover -= allocation
            cursor.execute("UPDATE tenants SET water_outstanding = %s WHERE id = %s", (new_water_owed, tenant_id))
            insert_txn(allocation, 'WATER_PAYMENT', 'Waterfall Spillover', current_balance, current_balance, "SPILL_WATER")

    # STEP 5: Repay Emergency Fund Debt (The Loan)
    # Pay off the debt WITHOUT restoring the credit_balance.
    if spillover > 0 and credit_debt and credit_debt > 0:
        repayment_amount = min(spillover, credit_debt)
        new_credit_debt = credit_debt - repayment_amount
        spillover -= repayment_amount
        cursor.execute("UPDATE wallets SET credit_debt = %s WHERE id = %s", (new_credit_debt, wallet_id))
        insert_txn(repayment_amount, 'EMERGENCY_FUND_REPAYMENT', 'Loan Repayment', current_balance, current_balance, "CRED_REPAY")

    # STEP 6: Top up main wallet with anything left over
    if spillover > 0:
        new_wallet_balance = current_balance + spillover
        cursor.execute("UPDATE wallets SET balance = %s WHERE id = %s", (new_wallet_balance, wallet_id))
        insert_txn(spillover, 'WALLET_TOPUP', 'Waterfall Spillover', current_balance, new_wallet_balance, "WALLET")

    return {"status": "success", "message": "Payment allocated successfully via percentage waterfall"}