import re
from datetime import datetime
from imap_tools import MailBox, A
from src.ai_parser import parse_quote_with_ai
from src.config import SENDER_EMAIL, SENDER_PASSWORD, IMAP_SERVER

def parse_incoming_quotes(conn, carriers_config):
    """
    Logs into email, fetches replies, uses AI to parse them, and updates the database.
    """
    cursor = conn.cursor()
    print("Checking for new quote emails...")
    try:
        with MailBox(IMAP_SERVER).login(SENDER_EMAIL, SENDER_PASSWORD, 'INBOX') as mailbox:
            for msg in mailbox.fetch(A(seen=False)):
                print(f"Found potential quote email from {msg.from_} with subject '{msg.subject}'")

                sender_email = msg.from_
                carrier_name = next((name for name, info in carriers_config.items() if info.get('contact') == sender_email), None)

                if not carrier_name:
                    print(f"   - Could not find a matching carrier for email: {sender_email}. Skipping.")
                    mailbox.flag(msg.uid, '\\Seen', True) # Mark non-carrier emails as read
                    continue

                shipment_id_match = re.search(r'#(\d+)', msg.subject)
                if not shipment_id_match:
                    print(f"   - Could not find shipment ID in subject. Skipping.")
                    mailbox.flag(msg.uid, '\\Seen', True) # Mark malformed subjects as read
                    continue

                shipment_id = int(shipment_id_match.group(1))
                print(f"   - Matched to Shipment ID: {shipment_id}, Carrier: {carrier_name}")

                # Use AI to parse the price from the full email text
                price = parse_quote_with_ai(msg.text)

                quote_type = 'final' if 'Final Offer Request' in msg.subject else 'initial'

                if price is None:
                    print(f"   - ❌ AI could not find a quote in {quote_type.upper()} reply. Marking as failed.")
                    status_update_sql = "UPDATE quotes SET status = 'failed' WHERE shipment_id = ? AND carrier_name = ? AND quote_type = ?"
                    if quote_type == 'final':
                        status_update_sql = "INSERT INTO quotes (shipment_id, carrier_name, quote_type, status) VALUES (?, ?, ?, 'failed')"
                    cursor.execute(status_update_sql, (shipment_id, carrier_name, quote_type))
                else:
                    print(f"   - ✅ AI found {quote_type.upper()} quote of ${price:.2f}. Updating database...")
                    if quote_type == 'initial':
                        cursor.execute("UPDATE quotes SET price = ?, received_at = ?, status = 'received' WHERE shipment_id = ? AND carrier_name = ? AND quote_type = ?", (price, datetime.now().isoformat(), shipment_id, carrier_name, quote_type))
                    else: # Final
                        cursor.execute("INSERT INTO quotes (shipment_id, carrier_name, quote_type, price, received_at, status) VALUES (?, ?, ?, ?, ?, ?)", (shipment_id, carrier_name, quote_type, price, datetime.now().isoformat(), 'received'))

                # --- BUG FIX: Only commit and mark as read if the DB operation was successful ---
                conn.commit()
                print(f"   - Database updated for Shipment ID: {shipment_id}.")
                mailbox.flag(msg.uid, '\\Seen', True)
                print(f"   - Marked email as read.")

    except Exception as e:
        print(f"EMAIL PARSER ERROR: Could not connect or process emails. Error: {e}")
