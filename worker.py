import sqlite3
import time
from datetime import datetime

# Import all the necessary functions from your utility files
from src.database_setup import DB_PATH
from src.quoting import send_email_quote_request, get_api_quote
from src.email_parser import parse_incoming_quotes
from src.negotiation import send_negotiation_request
from src.config import CARRIERS, TIMEOUT_HOURS
# from src.ml_model import predict_final_offer

# --- Configuration ---
POLLING_INTERVAL_SECONDS = 60 # Check for new work every 60 seconds

def get_db_connection():
    """Establishes a connection to the database."""
    return sqlite3.connect(DB_PATH)

def start_new_shipments(conn):
    """Finds shipments with status 'quoting' and starts the process."""
    cursor = conn.cursor()
    # Find new shipments that haven't been processed yet
    cursor.execute("SELECT shipment_id, spots, weight, destination_zip FROM shipments WHERE status = 'quoting'")
    new_shipments = cursor.fetchall()

    for shipment in new_shipments:
        shipment_id, spots, weight, destination_zip = shipment
        print(f"WORKER: Found new shipment #{shipment_id}. Starting quote process...")

        shipment_details = {
            'shipment_id': shipment_id,
            'spots': spots,
            'weight': weight,
            'destination_zip': destination_zip
        }

        # Send quote requests to all carriers for this shipment
        for name, info in CARRIERS.items():
            cursor.execute("INSERT INTO quotes (shipment_id, carrier_name, quote_type) VALUES (?, ?, ?)", (shipment_id, name, 'initial'))
            if info['type'] == 'api':
                price = get_api_quote(name, shipment_details)
                if price:
                     cursor.execute("UPDATE quotes SET price = ?, received_at = ? WHERE shipment_id = ? AND carrier_name = ? AND quote_type = 'initial'",
                                   (price, datetime.now().isoformat(), shipment_id, name))
                     conn.commit()
            elif info['type'] == 'email':
                send_email_quote_request(info['contact'], shipment_details)

        # Update the shipment status to show it's being processed
        cursor.execute("UPDATE shipments SET status = 'awaiting_initial_quotes' WHERE shipment_id = ?", (shipment_id,))
        conn.commit()
        print(f"WORKER: Initial quote requests sent for shipment #{shipment_id}.")


'''def advance_to_negotiation(conn):
    """
    Finds shipments ready for negotiation, uses the ML model to predict outcomes,
    and sends counter-offer emails to promising candidates.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.shipment_id, s.spots, s.weight, s.destination_zip
        FROM shipments s
        WHERE s.status = 'awaiting_initial_quotes' AND
              (SELECT COUNT(*) FROM quotes q WHERE q.shipment_id = s.shipment_id AND q.quote_type = 'initial' AND q.status IN ('received', 'failed')) = ?
    """, (len(CARRIERS),))

    ready_shipments = cursor.fetchall()

    for shipment in ready_shipments:
        shipment_id, spots, weight, destination_zip = shipment
        shipment_details = {
            'shipment_id': shipment_id,
            'spots': spots,
            'weight': weight,
            'destination_zip': destination_zip,
            # This is the feature for the ML model
            'dest_zip_encoded': int(str(destination_zip)[0])
        }

        print(f"WORKER: Shipment #{shipment_id} is ready for negotiation.")

        # Find the initial leader
        cursor.execute("SELECT carrier_name, price FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' ORDER BY price ASC LIMIT 1", (shipment_id,))
        result = cursor.fetchone()
        if not result:
            print(f"WORKER: No successful initial bids for #{shipment_id}. Marking as complete.")
            cursor.execute("UPDATE shipments SET status = 'complete' WHERE shipment_id = ?", (shipment_id,))
            conn.commit()
            continue

        leader_carrier, lowest_bid = result
        print(f"WORKER: Initial leader for #{shipment_id} is {leader_carrier} at ${lowest_bid:.2f}. Using ML to check for negotiation candidates.")

        # Get all carriers that were not the leader
        cursor.execute("SELECT carrier_name FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' AND carrier_name != ?", (shipment_id, leader_carrier))
        carriers_to_check = cursor.fetchall()

        # Use the ML model to decide who to negotiate with
        for (carrier_name,) in carriers_to_check:
            predicted_price = predict_final_offer(carrier_name, shipment_details, lowest_bid)

            # Only negotiate if the model predicts a better price
            if predicted_price and predicted_price < lowest_bid:
                print(f"   - Model predicts {carrier_name} may beat the price (Predicted: ${predicted_price:.2f}). Sending negotiation request.")
                contact_email = CARRIERS[carrier_name]['contact']
                send_negotiation_request(contact_email, shipment_id, lowest_bid)
            else:
                print(f"   - Model predicts {carrier_name} will not beat the price. Skipping.")

        # Update status to show we're waiting for final offers
        cursor.execute("UPDATE shipments SET status = 'awaiting_final_offers' WHERE shipment_id = ?", (shipment_id,))
        conn.commit()'''

def advance_to_negotiation(conn):
    """Finds shipments ready for negotiation and sends the counter-offer emails."""
    cursor = conn.cursor()
    # Find shipments where all initial quotes have been received
    cursor.execute("""
        SELECT s.shipment_id, s.spots, s.weight, s.destination_zip
        FROM shipments s
        WHERE s.status = 'awaiting_initial_quotes' AND
              (SELECT COUNT(*) FROM quotes q WHERE q.shipment_id = s.shipment_id AND q.quote_type = 'initial' AND q.status IN ('received', 'failed')) = ?
    """, (len(CARRIERS),))

    ready_shipments = cursor.fetchall()

    for shipment in ready_shipments:
        shipment_id, spots, weight, destination_zip = shipment
        print(f"WORKER: Shipment #{shipment_id} is ready for negotiation.")

        # Find the initial leader
        cursor.execute("SELECT carrier_name, price FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' ORDER BY price ASC LIMIT 1", (shipment_id,))
        result = cursor.fetchone()
        if not result:
            print(f"WORKER: No successful initial bids for #{shipment_id}. Marking as complete.")
            cursor.execute("UPDATE shipments SET status = 'complete' WHERE shipment_id = ?", (shipment_id,))
            conn.commit()
            continue

        leader_carrier, lowest_bid = result

        # In a real app, you would add your ML logic here to decide who to negotiate with
        print(f"WORKER: Initial leader for #{shipment_id} is {leader_carrier} at ${lowest_bid:.2f}. Starting negotiation round.")

        cursor.execute("SELECT carrier_name FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' AND carrier_name != ?", (shipment_id, leader_carrier))
        carriers_to_negotiate_with = cursor.fetchall()

        for (carrier_name,) in carriers_to_negotiate_with:
            contact_email = CARRIERS[carrier_name]['contact']
            send_negotiation_request(contact_email, shipment_id, lowest_bid)

        # Update status to show we're waiting for final offers
        cursor.execute("UPDATE shipments SET status = 'awaiting_final_offers' WHERE shipment_id = ?", (shipment_id,))
        conn.commit()



def complete_shipments(conn):
    """
    Finds shipments awaiting final offers, determines the true winner,
    and marks them as complete.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT shipment_id FROM shipments WHERE status = 'awaiting_final_offers'")
    shipments_to_check = cursor.fetchall()

    for (shipment_id,) in shipments_to_check:
        # First, find out how many final offers we were expecting.
        cursor.execute("""
            SELECT COUNT(*) FROM quotes
            WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' AND
                  price > (SELECT MIN(price) FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received')
        """, (shipment_id, shipment_id))
        expected_final_offers = cursor.fetchone()[0]

        # Now, count how many we actually received.
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE shipment_id = ? AND quote_type = 'final' AND status IN ('received', 'failed')", (shipment_id,))
        received_final_offers = cursor.fetchone()[0]

        # Only proceed if all expected offers are in.
        if received_final_offers >= expected_final_offers:
            print(f"WORKER: All final offers received for shipment #{shipment_id}. Determining winner...")

            # Get the initial winner
            cursor.execute("SELECT carrier_name, price FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' ORDER BY price ASC LIMIT 1", (shipment_id,))
            initial_winner, initial_price = cursor.fetchone()

            # Find the best *negotiated* final offer
            cursor.execute("SELECT carrier_name, price FROM quotes WHERE shipment_id = ? AND quote_type = 'final' AND status = 'received' ORDER BY price ASC LIMIT 1", (shipment_id,))
            best_final_offer = cursor.fetchone()

            final_winner = initial_winner
            final_price = initial_price

            # If a better final offer exists, it becomes the new winner.
            if best_final_offer and best_final_offer[1] < initial_price:
                final_winner = best_final_offer[0]
                final_price = best_final_offer[1]
                print(f"WORKER: ✅ Negotiation successful! New winner is {final_winner} at ${final_price:.2f}.")
            else:
                print(f"WORKER: Negotiation did not produce a better offer. Initial winner {initial_winner} stands.")

            # Update the shipments table with the definitive result
            cursor.execute(
                "UPDATE shipments SET status = 'complete', final_winner = ?, final_price = ? WHERE shipment_id = ?",
                (final_winner, final_price, shipment_id)
            )
            conn.commit()


def timeout_stale_shipments(conn):
    """Finds shipments that are stuck and marks them as complete."""
    cursor = conn.cursor()
    # Find shipments older than the timeout period that are still awaiting responses
    cursor.execute("""
        SELECT shipment_id FROM shipments
        WHERE status LIKE 'awaiting%' AND
              request_date < datetime('now', '-' || ? || ' hours')
    """, (TIMEOUT_HOURS,))

    stale_shipments = cursor.fetchall()

    for (shipment_id,) in stale_shipments:
        print(f"WORKER: ⚠️ Shipment #{shipment_id} has timed out. Marking as complete.")
        # Mark as complete with no winner
        cursor.execute(
            "UPDATE shipments SET status = 'complete', final_winner = 'Timed Out' WHERE shipment_id = ?",
            (shipment_id,)
        )
        conn.commit()

def worker_loop():
    """The main infinite loop for the background worker."""
    print("🚀 Worker started. Looking for jobs...")
    while True:
        try:
            conn = get_db_connection()

            # Task 1: Always parse incoming emails first
            parse_incoming_quotes(conn, CARRIERS)

            # Task 2: Find and start any brand new shipments
            start_new_shipments(conn)

            # Task 3: Find shipments ready for negotiation
            advance_to_negotiation(conn)

            # Task 4: Find and complete finished negotiations
            complete_shipments(conn)

            # NEW Task 5: Find and time out stale shipments
            timeout_stale_shipments(conn)

            conn.close()
        except Exception as e:
            print(f"WORKER ERROR: An error occurred: {e}")

        # Wait before the next cycle
        print(f"Cycle complete. Waiting for {POLLING_INTERVAL_SECONDS} seconds...")
        time.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == '__main__':
    worker_loop()
