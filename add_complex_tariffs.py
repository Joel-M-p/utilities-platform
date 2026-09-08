import psycopg2

conn = psycopg2.connect(
    dbname="utilities_platform",
    user="postgres",
    password="5432",
    host="localhost",
    port="5432"
)
conn.autocommit = True
cursor = conn.cursor()

# Add complex tariff columns
cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS structure_type VARCHAR(20) DEFAULT 'FLAT'")
cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS rate_flat DECIMAL(10, 3) DEFAULT 0")
cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tier_1_limit INT DEFAULT 0")
cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tier_1_rate DECIMAL(10, 3) DEFAULT 0")
cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tier_2_rate DECIMAL(10, 3) DEFAULT 0")
cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tou_peak_rate DECIMAL(10, 3) DEFAULT 0")
cursor.execute("ALTER TABLE tariffs ADD COLUMN IF NOT EXISTS tou_offpeak_rate DECIMAL(10, 3) DEFAULT 0")

# Migrate old 'rate' data into 'rate_flat' if it exists
cursor.execute("UPDATE tariffs SET rate_flat = rate WHERE rate IS NOT NULL AND rate_flat = 0")

print("SUCCESS: Complex tariff structure columns added.")
cursor.close()
conn.close()