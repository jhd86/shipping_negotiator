import sqlite3
import time
# from datetime import datetime

# Import all the necessary functions from your utility files
from src.database_setup import DB_PATH
from src.quoting import send_email_quote_request
from src.email_parser import parse_incoming_quotes
from src.negotiation import send_negotiation_request
from src.config import CARRIERS, POLLING_INTERVAL_SECONDS, TIMEOUT_HOURS

def get_db_connection():
    """Establishes a connection to the database."""
    return sqlite3.connect(DB_PATH)

def start_new_shipments(conn):
    """Finds shipments with status 'quoting' and starts the process."""
    cursor = conn.cursor()
    cursor.execute("SELECT shipment_id, spots, weight, destination_zip FROM shipments WHERE status = 'quoting'")
    new_shipments = cursor.fetchall()

    for shipment in new_shipments:
        shipment_id, spots, weight, destination_zip = shipment
        print(f"WORKER: Found new shipment #{shipment_id}. Locking and starting quote process...")

        # --- BUG FIX: Immediately lock the shipment to prevent reprocessing ---
        cursor.execute("UPDATE shipments SET status = 'processing_initial' WHERE shipment_id = ?", (shipment_id,))
        conn.commit()

        shipment_details = {'shipment_id': shipment_id, 'spots': spots, 'weight': weight, 'destination_zip': destination_zip}

        for name, info in CARRIERS.items():
            cursor.execute("INSERT INTO quotes (shipment_id, carrier_name, quote_type) VALUES (?, ?, ?)", (shipment_id, name, 'initial'))
            if info.get('type') == 'email':
                send_email_quote_request(info['contact'], shipment_details)

        cursor.execute("UPDATE shipments SET status = 'awaiting_initial_quotes' WHERE shipment_id = ?", (shipment_id,))
        conn.commit()
        print(f"WORKER: Initial quote requests sent for shipment #{shipment_id}.")


def advance_to_negotiation(conn):
    """
    Finds shipments ready for negotiation and sends counter-offer emails to all non-winners.
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

        cursor.execute("SELECT carrier_name, price FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' ORDER BY price ASC LIMIT 1", (shipment_id,))
        result = cursor.fetchone()

        if not result:
            print(f"WORKER: No successful initial bids for #{shipment_id}. Marking as complete.")
            cursor.execute("UPDATE shipments SET status = 'complete', final_winner = 'No Bids' WHERE shipment_id = ?", (shipment_id,))
            conn.commit()
            continue

        leader_carrier, lowest_bid = result
        print(f"WORKER: Initial leader for #{shipment_id} is {leader_carrier} at ${lowest_bid:.2f}.")

        cursor.execute("SELECT carrier_name FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' AND carrier_name != ?", (shipment_id, leader_carrier))
        carriers_to_negotiate_with = cursor.fetchall()

        if not carriers_to_negotiate_with:
            print(f"WORKER: No negotiation candidates for shipment #{shipment_id}. Finalizing.")
            cursor.execute(
                "UPDATE shipments SET status = 'complete', final_winner = ?, final_price = ? WHERE shipment_id = ?",
                (leader_carrier, lowest_bid, shipment_id)
            )
        else:
            print(f"WORKER: Starting negotiation with {len(carriers_to_negotiate_with)} carrier(s).")
            for (carrier_name,) in carriers_to_negotiate_with:
                contact_email = CARRIERS[carrier_name]['contact']
                send_negotiation_request(contact_email, shipment_id, lowest_bid)

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
        cursor.execute("""
            SELECT COUNT(*) FROM quotes
            WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' AND
                  price > (SELECT MIN(price) FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received')
        """, (shipment_id, shipment_id))
        expected_final_offers = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM quotes WHERE shipment_id = ? AND quote_type = 'final' AND status IN ('received', 'failed')", (shipment_id,))
        received_final_offers = cursor.fetchone()[0]

        if received_final_offers >= expected_final_offers:
            print(f"WORKER: All final offers received for shipment #{shipment_id}. Determining winner...")

            cursor.execute("SELECT carrier_name, price FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received' ORDER BY price ASC LIMIT 1", (shipment_id,))
            initial_winner, initial_price = cursor.fetchone()

            cursor.execute("SELECT carrier_name, price FROM quotes WHERE shipment_id = ? AND quote_type = 'final' AND status = 'received' ORDER BY price ASC LIMIT 1", (shipment_id,))
            best_final_offer = cursor.fetchone()

            final_winner = initial_winner
            final_price = initial_price

            if best_final_offer and best_final_offer[1] < initial_price:
                final_winner = best_final_offer[0]
                final_price = best_final_offer[1]
                print(f"WORKER: ✅ Negotiation successful! New winner is {final_winner} at ${final_price:.2f}.")
            else:
                print(f"WORKER: Negotiation did not produce a better offer. Initial winner {initial_winner} stands.")

            cursor.execute(
                "UPDATE shipments SET status = 'complete', final_winner = ?, final_price = ? WHERE shipment_id = ?",
                (final_winner, final_price, shipment_id)
            )
            conn.commit()


def timeout_stale_shipments(conn):
    """Finds shipments that are stuck and marks them as complete."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT shipment_id FROM shipments
        WHERE status LIKE 'awaiting%' AND
              request_date < datetime('now', '-' || ? || ' hours')
    """, (TIMEOUT_HOURS,))

    stale_shipments = cursor.fetchall()

    for (shipment_id,) in stale_shipments:
        print(f"WORKER: ⚠️ Shipment #{shipment_id} has timed out. Marking as complete.")
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
            parse_incoming_quotes(conn, CARRIERS)
            start_new_shipments(conn)
            advance_to_negotiation(conn)
            complete_shipments(conn)
            timeout_stale_shipments(conn)
            conn.close()
        except Exception as e:
            print(f"WORKER ERROR: An error occurred: {e}")

        print(f"Cycle complete. Waiting for {POLLING_INTERVAL_SECONDS} seconds...")
        time.sleep(POLLING_INTERVAL_SECONDS)

if __name__ == '__main__':
    worker_loop()
