import sqlite3
import time
from datetime import datetime

# Import functions from your other modules
from src.database_setup import DB_PATH
from src.quoting import get_api_quote, send_email_quote_request
from src.email_parser import parse_incoming_quotes
from src.negotiation import send_negotiation_request
from src.config import CARRIERS
from src.ml_model import predict_final_offer

# --- Configuration ---
POLLING_INTERVAL_SECONDS = 60 # Check for new emails every 60 seconds
POLLING_TIMEOUT_MINUTES = 20 # Give up after 20 minutes

def process_new_shipment(shipment_details):
    """Orchestrates the entire quote and negotiation process for a new shipment."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print(f"\n🚀 STARTING PROCESS FOR NEW SHIPMENT: {shipment_details}")

    # === Step 1: Log the new shipment to the database ===
    cursor.execute(
        "INSERT INTO shipments (request_date, spots, weight, destination_zip, status) VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), shipment_details['spots'], shipment_details['weight'], shipment_details['destination_zip'], 'quoting')
    )
    shipment_id = cursor.lastrowid
    shipment_details['shipment_id'] = shipment_id
    conn.commit()
    print(f"Shipment logged with ID: {shipment_id}")

    # === Step 2: Request initial quotes from all carriers ===
    for name, info in CARRIERS.items():
        # Register that we are waiting for a quote
        cursor.execute("INSERT INTO quotes (shipment_id, carrier_name, quote_type) VALUES (?, ?, ?)", (shipment_id, name, 'initial'))
        conn.commit()

        if info['type'] == 'api':
            price = get_api_quote(name, shipment_details)
            if price:
                 cursor.execute("UPDATE quotes SET price = ?, received_at = ? WHERE shipment_id = ? AND carrier_name = ? AND quote_type = 'initial'",
                               (price, datetime.now().isoformat(), shipment_id, name))
                 conn.commit()
        elif info['type'] == 'email':
            send_email_quote_request(info['contact'], shipment_details)

    # === Step 3: Wait for all initial quotes to be processed ===
    print("\n⏳ Waiting for initial quotes from email carriers...")
    start_time = time.time()
    while time.time() - start_time < POLLING_TIMEOUT_MINUTES * 60:
        parse_incoming_quotes(conn, CARRIERS) # Check and process new emails

        # UPDATED: Check for quotes that are either 'received' or 'failed'
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status IN ('received', 'failed')", (shipment_id,))
        processed_count = cursor.fetchone()[0]

        if processed_count == len(CARRIERS):
            print("✅ All initial quotes have been processed (received or failed).")
            break

        print(f"   ({processed_count}/{len(CARRIERS)} processed). Checking again in {POLLING_INTERVAL_SECONDS}s...")
        time.sleep(POLLING_INTERVAL_SECONDS)
    else:
        print("❌ TIMEOUT: Did not process all initial quotes in time. Continuing with what we have.")

    # === Step 4: Analyze initial quotes and find the leader ===
    cursor.execute("SELECT carrier_name, price FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND price IS NOT NULL ORDER BY price ASC", (shipment_id,))
    initial_quotes = cursor.fetchall()

    if not initial_quotes:
        print("❌ No initial quotes received. Aborting process.")
        conn.close()
        return

    leader_carrier, lowest_bid = initial_quotes[0]
    print(f"\n🏆 Initial Leader: {leader_carrier} with a bid of ${lowest_bid:.2f}")

    # === Step 5: Start the intelligent negotiation round ===
    print("\n🤖 Starting intelligent negotiation round...")
    cursor.execute("UPDATE shipments SET status = 'negotiating' WHERE shipment_id = ?", (shipment_id,))
    conn.commit()

    carriers_to_negotiate = []
    for carrier_name, initial_price in initial_quotes[1:]: # Loop through everyone except the leader
        # Predict what this carrier's final offer would be
        '''predicted_price = predict_final_offer(carrier_name, shipment_details, lowest_bid)

        if predicted_price and predicted_price < lowest_bid:
            print(f"   - Model predicts {carrier_name} might beat the price (Predicted: ${predicted_price:.2f}). Negotiating...")
            carriers_to_negotiate.append(carrier_name)
            # Send the negotiation email
            contact_email = CARRIERS[carrier_name]['contact']
            send_negotiation_request(contact_email, shipment_id, lowest_bid)
        else:
            print(f"   - Skipping negotiation with {carrier_name}. Model predicts they won't beat the price.")'''

        print(f"   - Collecting data: Sending negotiation request to {carrier_name}.")
        carriers_to_negotiate.append(carrier_name)
        contact_email = CARRIERS[carrier_name]['contact']
        send_negotiation_request(contact_email, shipment_id, lowest_bid)

    # === Step 6: Wait for final offers ===
    if carriers_to_negotiate:
        print("\n⏳ Waiting for final offers...")
        # For simplicity, we assume the email parser can handle both initial and final replies.
        time.sleep(POLLING_INTERVAL_SECONDS * 5) # Wait some time for final offers
        parse_incoming_quotes(conn, CARRIERS) # Run parser again

    # === Step 7: Determine the final winner ===
    print("\n🏁 Determining final winner...")
    cursor.execute("SELECT carrier_name, price FROM quotes WHERE shipment_id = ? AND price IS NOT NULL ORDER BY price ASC", (shipment_id,))
    all_quotes = cursor.fetchall()

    final_winner, final_price = all_quotes[0]

    # === Step 8: Report the results ===
    print("\n--- PROCESS COMPLETE ---")
    print(f"Initial Winning Bid: ${lowest_bid:.2f} from {leader_carrier}")
    print(f"FINAL WINNING BID:   ${final_price:.2f} from {final_winner}")
    if final_price < lowest_bid:
        print(f"💰 Savings from negotiation: ${lowest_bid - final_price:.2f}")

    cursor.execute("UPDATE shipments SET status = 'complete' WHERE shipment_id = ?", (shipment_id,))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    # This is how you would run the process for a new shipment.
    # The 'dest_zip_encoded' is a placeholder for a feature your ML model needs.
    # You would generate this based on the ZIP code (e.g., mapping ZIPs to regions).
    new_shipment_data = {
        'spots': 4,
        'weight': 3500,
        'destination_zip': '90210',
        'dest_zip_encoded': 7 # Example: 7 represents 'West Coast'
    }

    process_new_shipment(new_shipment_data)
