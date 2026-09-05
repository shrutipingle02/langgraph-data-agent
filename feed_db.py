import os
import csv
import psycopg2
from dotenv import load_dotenv
load_dotenv()

if 'port' not in os.environ:
    os.environ['port'] = '5432'

# ============================================================
# CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": os.environ['host'],
    "port": int(os.environ['port']),
    "database": os.environ['database'],
    "user": os.environ['user'],
    "password": os.environ['password'],
}

CSV_DIR = "data"


# ============================================================
# DATABASE CONNECTION
# ============================================================

conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = False

cursor = conn.cursor()

print("Connected to PostgreSQL")


# ============================================================
# CREATE TABLES
# ============================================================

create_tables_sql = """

CREATE SCHEMA IF NOT EXISTS public;

-- =========================================================
-- USERS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.users (
    user_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(50),
    city VARCHAR(100),
    province VARCHAR(50),
    user_type VARCHAR(20) NOT NULL,
    signup_date DATE,
    is_active BOOLEAN
);

-- =========================================================
-- VEHICLES
-- =========================================================

CREATE TABLE IF NOT EXISTS public.vehicles (
    vehicle_id INTEGER PRIMARY KEY,
    driver_id INTEGER REFERENCES public.users(user_id),
    make VARCHAR(50),
    model VARCHAR(50),
    year INTEGER,
    license_plate VARCHAR(20),
    color VARCHAR(30),
    is_active BOOLEAN
);

-- =========================================================
-- RIDES
-- =========================================================

CREATE TABLE IF NOT EXISTS public.rides (
    ride_id INTEGER PRIMARY KEY,
    rider_id INTEGER REFERENCES public.users(user_id),
    driver_id INTEGER REFERENCES public.users(user_id),
    requested_at TIMESTAMP,
    pickup_time TIMESTAMP,
    dropoff_time TIMESTAMP,
    pickup_latitude NUMERIC(9,6),
    pickup_longitude NUMERIC(9,6),
    dropoff_latitude NUMERIC(9,6),
    dropoff_longitude NUMERIC(9,6),
    distance_km NUMERIC(10,2),
    fare NUMERIC(10,2),
    surge_multiplier NUMERIC(4,2),
    status VARCHAR(20),
    cancellation_reason VARCHAR(50)
);

-- =========================================================
-- PAYMENTS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.payments (
    payment_id INTEGER PRIMARY KEY,
    ride_id INTEGER REFERENCES public.rides(ride_id),
    user_id INTEGER REFERENCES public.users(user_id),
    amount NUMERIC(10,2),
    payment_method VARCHAR(30),
    payment_status VARCHAR(20),
    transaction_id VARCHAR(50),
    payment_time TIMESTAMP
);

-- =========================================================
-- RATINGS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.ratings (
    rating_id INTEGER PRIMARY KEY,
    ride_id INTEGER REFERENCES public.rides(ride_id),
    rider_id INTEGER REFERENCES public.users(user_id),
    driver_id INTEGER REFERENCES public.users(user_id),
    rating INTEGER,
    comment TEXT,
    rated_at TIMESTAMP
);

"""

cursor.execute(create_tables_sql)
conn.commit()
print("Tables created")


# ============================================================
# LOAD CSVs
# ============================================================

# Order matters, the foreign keys need the parent rows in place first.
LOAD_ORDER = ["users", "vehicles", "rides", "payments", "ratings"]

# Columns that are empty strings in the CSV but need to be NULL in Postgres
NULLABLE = {
    "rides": ["pickup_time", "dropoff_time", "cancellation_reason"],
}


def load_table(table_name):

    file_path = os.path.join(CSV_DIR, f"{table_name}.csv")

    if not os.path.exists(file_path):
        print(f"  {table_name}: {file_path} not found, skipping. Run generate_data.py first.")
        return

    # Start clean so re-running this script does not trip the primary keys
    cursor.execute(f"TRUNCATE TABLE public.{table_name} CASCADE;")

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)

        blank_to_null = NULLABLE.get(table_name, [])
        null_idx = [header.index(c) for c in blank_to_null if c in header]

        rows = []
        for row in reader:
            for i in null_idx:
                if row[i] == "":
                    row[i] = None
            rows.append(row)

    placeholders = ",".join(["%s"] * len(header))
    columns = ",".join(header)
    insert_sql = f"INSERT INTO public.{table_name} ({columns}) VALUES ({placeholders})"

    cursor.executemany(insert_sql, rows)
    conn.commit()

    print(f"  {table_name:12} {len(rows):>7,} rows loaded")


print("Loading CSVs...")
for table in LOAD_ORDER:
    load_table(table)


# ============================================================
# VERIFY
# ============================================================

print("\nRow counts in the database:")
for table in LOAD_ORDER:
    cursor.execute(f"SELECT COUNT(*) FROM public.{table};")
    print(f"  {table:12} {cursor.fetchone()[0]:>7,}")

cursor.close()
conn.close()
print("\nDone.")
