import sqlite3
import os

def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS farmers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vendors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS charities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS produce (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity REAL NOT NULL,
        price REAL NOT NULL,
        farmer_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (farmer_id) REFERENCES farmers(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        produce_id INTEGER NOT NULL,
        vendor_id INTEGER NOT NULL,
        quantity REAL NOT NULL,
        price_per_unit REAL NOT NULL,
        total_price REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (produce_id) REFERENCES produce(id),
        FOREIGN KEY (vendor_id) REFERENCES vendors(id)
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_name TEXT NOT NULL,
        quantity REAL NOT NULL,
        vendor_address TEXT NOT NULL,
        vendor_phone TEXT NOT NULL,
        vendor_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'available',
        FOREIGN KEY (vendor_id) REFERENCES vendors(id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Database tables created/updated successfully.")

# ---------- FARMERS ----------
def insert_farmer(name, email, password):
    _insert_user("farmers", name, email, password)

def get_farmer_by_email(email):
    return _get_user_by_email("farmers", email)

def get_farmer_purchases(farmer_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 
        purchases.id,
        produce.name as produce_name,
        purchases.quantity,
        purchases.price_per_unit,
        purchases.total_price,
        purchases.created_at,
        vendors.name as vendor_name
    FROM purchases
    JOIN produce ON purchases.produce_id = produce.id
    JOIN vendors ON purchases.vendor_id = vendors.id
    WHERE produce.farmer_id = ?
    ORDER BY purchases.created_at DESC
    ''', (farmer_id,))
    purchases = cursor.fetchall()
    conn.close()
    return purchases

def get_farmer_revenue(farmer_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 
        SUM(purchases.total_price) as total_revenue,
        COUNT(purchases.id) as total_orders,
        SUM(purchases.quantity) as total_quantity_sold
    FROM purchases
    JOIN produce ON purchases.produce_id = produce.id
    WHERE produce.farmer_id = ?
    ''', (farmer_id,))
    revenue_data = cursor.fetchone()
    conn.close()
    return {
        'total_revenue': revenue_data[0] or 0,
        'total_orders': revenue_data[1] or 0,
        'total_quantity_sold': revenue_data[2] or 0
    }

def get_farmer_produce(farmer_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 
        id,
        name,
        quantity,
        price,
        created_at
    FROM produce 
    WHERE farmer_id = ?
    ORDER BY created_at DESC
    ''', (farmer_id,))
    produce = cursor.fetchall()
    conn.close()
    return produce

# ---------- VENDORS ----------
def insert_vendor(name, email, password):
    _insert_user("vendors", name, email, password)

def get_vendor_by_email(email):
    return _get_user_by_email("vendors", email)

def get_vendor_purchases(vendor_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 
        purchases.id,
        produce.name,
        purchases.quantity,
        purchases.price_per_unit,
        purchases.total_price,
        purchases.created_at,
        farmers.name as farmer_name
    FROM purchases
    JOIN produce ON purchases.produce_id = produce.id
    JOIN farmers ON produce.farmer_id = farmers.id
    WHERE purchases.vendor_id = ?
    ORDER BY purchases.created_at DESC
    ''', (vendor_id,))
    purchases = cursor.fetchall()
    conn.close()
    return purchases

def get_vendor_donations(vendor_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 
        id,
        item_name,
        quantity,
        vendor_address,
        vendor_phone,
        created_at,
        status
    FROM donations
    WHERE vendor_id = ?
    ORDER BY created_at DESC
    ''', (vendor_id,))
    donations = cursor.fetchall()
    conn.close()
    return donations

# ---------- CHARITIES ----------
def insert_charity(name, email, password):
    _insert_user("charities", name, email, password)

def get_charity_by_email(email):
    return _get_user_by_email("charities", email)

def get_charity_by_id(charity_id):
    """Get charity details by ID"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM charities WHERE id = ?', (charity_id,))
    charity = cursor.fetchone()
    conn.close()
    return charity

# ---------- COMMON HELPERS ----------
def _insert_user(table, name, email, password):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute(f'''
    INSERT INTO {table} (name, email, password) 
    VALUES (?, ?, ?)
    ''', (name, email, password))
    conn.commit()
    conn.close()

def _get_user_by_email(table, email):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute(f'''
    SELECT * FROM {table} WHERE email = ?
    ''', (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def insert_produce(farmer_id, produce, quantity, price):
    try:
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO produce (name, quantity, price, farmer_id) 
        VALUES (?, ?, ?, ?)
        ''', (produce, quantity, price, farmer_id))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error occurred while inserting produce: {e}")

def get_all_produce():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 
        produce.id,
        produce.name,
        produce.quantity,
        produce.price,
        produce.farmer_id,
        farmers.name as farmer_name
    FROM produce 
    JOIN farmers ON produce.farmer_id = farmers.id
    ''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def insert_purchase(produce_id, vendor_id, quantity, price_per_unit):
    try:
        conn = sqlite3.connect("data.db")
        cursor = conn.cursor()
        
        # Calculate total price
        total_price = quantity * price_per_unit
        
        # Insert the purchase record
        cursor.execute('''
        INSERT INTO purchases (produce_id, vendor_id, quantity, price_per_unit, total_price)
        VALUES (?, ?, ?, ?, ?)
        ''', (produce_id, vendor_id, quantity, price_per_unit, total_price))
        
        # Update the produce quantity
        cursor.execute('''
        UPDATE produce 
        SET quantity = quantity - ?
        WHERE id = ? AND quantity >= ?
        ''', (quantity, produce_id, quantity))
        
        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            return False, "Insufficient quantity available"
        
        conn.commit()
        conn.close()
        return True, "Purchase successful"
    except Exception as e:
        return False, str(e)

def get_produce_by_id(produce_id):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute('''
    SELECT 
        produce.*,
        farmers.name as farmer_name
    FROM produce
    JOIN farmers ON produce.farmer_id = farmers.id
    WHERE produce.id = ?
    ''', (produce_id,))
    produce = cursor.fetchone()
    conn.close()
    return produce

# ---------- DONATIONS ----------
def insert_donation(vendor_id, item_name, quantity, vendor_address, vendor_phone):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    try:
        cursor.execute('''
        INSERT INTO donations (vendor_id, item_name, quantity, vendor_address, vendor_phone)
        VALUES (?, ?, ?, ?, ?)
        ''', (vendor_id, item_name, quantity, vendor_address, vendor_phone))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error inserting donation: {e}")
        return False
    finally:
        conn.close()

def get_available_donations():
    """Get all available donations"""
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            d.id,
            d.item_name,
            d.quantity,
            d.vendor_address,
            d.vendor_phone,
            datetime(d.created_at) as formatted_date,
            v.name as vendor_name
        FROM donations d
        JOIN vendors v ON d.vendor_id = v.id
        WHERE d.status = 'available'
        ORDER BY d.created_at DESC
    ''')
    donations = cursor.fetchall()
    conn.close()
    return donations

def update_donation_status(donation_id, status):
    """Update the status of a donation"""
    try:
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE donations
            SET status = ?
            WHERE id = ?
        ''', (status, donation_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False