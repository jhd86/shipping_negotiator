# src/database_setup.py
import sqlite3
import os

DB_PATH = os.path.join("data", "shipping_quotes.db")

def create_database():
    """Creates the database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Table to store main shipment info
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shipments (
        shipment_id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_date TEXT NOT NULL,
        spots INTEGER NOT NULL,
        weight REAL NOT NULL,
        destination_zip TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        final_winner TEXT,
        final_price REAL
    );
    """)

    # Table to store every quote received
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            quote_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id INTEGER NOT NULL,
            carrier_name TEXT NOT NULL,
            quote_type TEXT NOT NULL, -- 'initial' or 'final'
            price REAL,
            received_at TEXT,
            status TEXT NOT NULL DEFAULT 'pending', -- ADDED THIS LINE
            FOREIGN KEY (shipment_id) REFERENCES shipments (shipment_id)
        );
        """)

    conn.commit()
    conn.close()
    print("Database and tables created successfully.")

if __name__ == '__main__':
    create_database()
