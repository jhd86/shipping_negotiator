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
                print(f"Found potential quote email from {msg.from_}")

                sender_email = msg.from_
                carrier_name = next((name for name, info in carriers_config.items() if info.get('contact') == sender_email), None)

                if not carrier_name:
                    print(f"   - Could not find a matching carrier for email: {sender_email}. Skipping.")
                    continue

                # Use AI to parse the price from the full email text
                price = parse_quote_with_ai(msg.text)

                # Extract shipment ID from the subject
                shipment_id_match = re.search(r'#(\d+)', msg.subject)
                if not shipment_id_match:
                    print(f"   - Could not find shipment ID in subject: '{msg.subject}'. Skipping.")
                    continue
                shipment_id = int(shipment_id_match.group(1))

                # Logic to handle initial vs. final quotes
                if 'Quote Request' in msg.subject:
                    quote_type = 'initial'
                    if price is None:
                        print(f"   - ❌ AI could not find a quote in INITIAL reply from {carrier_name}. Marking as failed.")
                        cursor.execute("UPDATE quotes SET status = 'failed' WHERE shipment_id = ? AND carrier_name = ? AND quote_type = ?", (shipment_id, carrier_name, quote_type))
                    else:
                        print(f"   - ✅ AI found INITIAL quote of ${price:.2f} from {carrier_name}")
                        cursor.execute("UPDATE quotes SET price = ?, received_at = ?, status = 'received' WHERE shipment_id = ? AND carrier_name = ? AND quote_type = ?", (price, datetime.now().isoformat(), shipment_id, carrier_name, quote_type))

                elif 'Final Offer Request' in msg.subject:
                    quote_type = 'final'
                    if price is None:
                        print(f"   - ❌ AI could not find a quote in FINAL reply from {carrier_name}. Marking as failed.")
                        cursor.execute("INSERT INTO quotes (shipment_id, carrier_name, quote_type, status) VALUES (?, ?, ?, ?)", (shipment_id, carrier_name, quote_type, 'failed'))
                    else:
                        print(f"   - ✅ AI found FINAL quote of ${price:.2f} from {carrier_name}")
                        cursor.execute("INSERT INTO quotes (shipment_id, carrier_name, quote_type, price, received_at, status) VALUES (?, ?, ?, ?, ?, ?)", (shipment_id, carrier_name, quote_type, price, datetime.now().isoformat(), 'received'))

                conn.commit()
                mailbox.flag(msg.uid, '\\Seen', True)

    except Exception as e:
        print(f"EMAIL PARSER ERROR: Could not connect or process emails. Error: {e}")
