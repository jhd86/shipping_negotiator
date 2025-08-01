import sqlite3
import os
import sys

# --- NEW: Reliable path logic for packaged apps ---
def get_base_path():
    """Gets the base path, whether running from source or as a bundled app."""
    if getattr(sys, 'frozen', False):
        # If the application is run as a bundle, the PyInstaller bootloader
        # extends the sys module by a flag frozen=True and sets the sys._MEIPASS
        # attribute to the path of the temporary folder.
        return sys._MEIPASS
    else:
        # If running in a normal Python environment, the base path is the project root.
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Define the absolute path to the database file
BASE_PATH = get_base_path()
DB_PATH = os.path.join(BASE_PATH, "data", "shipping_quotes.db")
DATA_DIR = os.path.join(BASE_PATH, "data")


def create_database():
    """Creates the database and tables if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # (Your CREATE TABLE statements remain unchanged)
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS quotes (
            quote_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shipment_id INTEGER NOT NULL,
            carrier_name TEXT NOT NULL,
            quote_type TEXT NOT NULL,
            price REAL,
            received_at TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (shipment_id) REFERENCES shipments (shipment_id)
        );
        """)

    conn.commit()
    conn.close()
    print(f"Database setup complete. Path: {DB_PATH}")

if __name__ == '__main__':
    create_database()
