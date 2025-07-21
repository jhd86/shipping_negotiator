import sqlite3
import os
import sys

# Ensure the script can find the database file
DB_PATH = os.path.join("data", "shipping_quotes.db")

def reset_database():
    """
    Deletes all records from the shipments and quotes tables and resets
    the auto-incrementing ID counters.
    """
    # ⚠️ Safety check to prevent accidental deletion
    print("⚠️ WARNING: This will permanently delete ALL shipment and quote data.")
    print("This action is irreversible.")

    confirm = input("Are you sure you want to continue? Type 'yes' to proceed: ")

    if confirm.lower() != 'yes':
        print("Reset cancelled.")
        sys.exit()

    try:
        print("\nConnecting to database...")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Delete all records from the tables
        print("Deleting records from 'quotes' table...")
        cursor.execute("DELETE FROM quotes;")

        print("Deleting records from 'shipments' table...")
        cursor.execute("DELETE FROM shipments;")

        # 2. Reset the auto-increment counters for the tables
        # SQLite stores these counters in a special table called 'sqlite_sequence'
        print("Resetting auto-increment IDs...")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('shipments', 'quotes');")

        # Commit all changes to the database
        conn.commit()

        print("\n✅ Database has been successfully reset. All data is gone.")

    except sqlite3.Error as e:
        print(f"❌ An error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            print("Database connection closed.")


if __name__ == '__main__':
    reset_database()
