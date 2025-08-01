import pandas as pd
import sqlite3
from src.database_setup import DB_PATH

def import_csv_to_db(csv_file_path):
    """Imports generated sample data into the SQLite database."""
    df = pd.read_csv(csv_file_path)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"Importing {len(df)} records into the database...")

    for _, row in df.iterrows():
        # Insert into shipments table
        cursor.execute("""
            INSERT INTO shipments (shipment_id, request_date, spots, weight, destination_zip, status, final_winner, final_price)
            VALUES (?, ?, ?, ?, ?, 'complete', ?, ?)
        """, (row['shipment_id'], row['request_date'], row['spots'], row['weight'], row['destination_zip'], row['final_winner'], row['final_price']))

        # Insert initial quotes
        for carrier in ["Budget Freight", "Premium Express", "Regional Pro"]:
            carrier_col = carrier.replace(' ', '_')
            cursor.execute("""
                INSERT INTO quotes (shipment_id, carrier_name, quote_type, price, status)
                VALUES (?, ?, 'initial', ?, 'received')
            """, (row['shipment_id'], carrier, row[f'{carrier_col}_initial']))

            # Insert final quotes if they are different from initial
            if row[f'{carrier_col}_final'] != row[f'{carrier_col}_initial']:
                cursor.execute("""
                    INSERT INTO quotes (shipment_id, carrier_name, quote_type, price, status)
                    VALUES (?, ?, 'final', ?, 'received')
                """, (row['shipment_id'], carrier, row[f'{carrier_col}_final']))

    conn.commit()
    conn.close()
    print("✅ Data import complete.")

if __name__ == '__main__':
    import_csv_to_db('sample_shipment_data.csv')
