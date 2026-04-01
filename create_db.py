import sqlite3

conn = sqlite3.connect("ewaste.db")
cur = conn.cursor()

# USERS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    email TEXT,
    phone TEXT,
    password TEXT
)
""")

# REQUESTS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fullname TEXT,
    device_type TEXT,
    quantity TEXT,
    address TEXT,
    pickup_date TEXT,
    status TEXT DEFAULT 'Pending',
    employee_name TEXT
)
""")

# EMPLOYEES TABLE (IMPORTANT)
cur.execute("""
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT
)
""")

conn.commit()
conn.close()

print("Database created successfully ✅")