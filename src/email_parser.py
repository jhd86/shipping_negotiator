# src/email_parser.py
from imap_tools import MailBox, A
import re
from datetime import datetime

def parse_incoming_quotes(conn, carriers_config):
    """Logs into email, finds quote replies, parses them, and updates the DB."""
    SENDER_EMAIL = "your_email@example.com"
    SENDER_PASSWORD = "your_password"
    IMAP_SERVER = "imap.gmail.com"

    cursor = conn.cursor()

    print("Checking for new quote emails...")
    # UPDATED: Fetch ALL unread emails to catch both types of replies
    with MailBox(IMAP_SERVER).login(SENDER_EMAIL, SENDER_PASSWORD, 'INBOX') as mailbox:
        for msg in mailbox.fetch(A(seen=False)):
            print(f"Found potential quote email from {msg.from_}")

            # --- Common logic for both reply types ---
            email_parts = re.split(r'\nOn .* wrote:', msg.text, maxsplit=1)
            reply_content = email_parts[0]

            sender_email = msg.from_
            carrier_name = next((name for name, info in carriers_config.items() if info.get('contact') == sender_email), None)

            if not carrier_name:
                print(f"   - Could not find a matching carrier for email: {sender_email}. Skipping.")
                continue

            shipment_id_match = re.search(r'#(\d+)', msg.subject)
            if not shipment_id_match:
                continue
            shipment_id = int(shipment_id_match.group(1))

            price_match = re.search(r'Quote: \$?([\d,]+\.?\d*)', reply_content)

            # --- NEW: Logic to handle initial vs. final quotes ---
            if 'Quote Request' in msg.subject:
                quote_type = 'initial'
                if not price_match:
                    print(f"   - ❌ No valid format in INITIAL reply from {carrier_name}. Marking as failed.")
                    cursor.execute("UPDATE quotes SET status = 'failed' WHERE shipment_id = ? AND carrier_name = ? AND quote_type = ?", (shipment_id, carrier_name, quote_type))
                else:
                    price = float(price_match.group(1).replace(',', ''))
                    print(f"   - ✅ Found INITIAL quote of ${price:.2f} from {carrier_name}")
                    cursor.execute("UPDATE quotes SET price = ?, received_at = ?, status = 'received' WHERE shipment_id = ? AND carrier_name = ? AND quote_type = ?", (price, datetime.now().isoformat(), shipment_id, carrier_name, quote_type))

            elif 'Final Offer Request' in msg.subject:
                quote_type = 'final'
                # For final offers, we INSERT a new row
                if not price_match:
                    print(f"   - ❌ No valid format in FINAL reply from {carrier_name}. Marking as failed.")
                    cursor.execute("INSERT INTO quotes (shipment_id, carrier_name, quote_type, status) VALUES (?, ?, ?, ?)", (shipment_id, carrier_name, quote_type, 'failed'))
                else:
                    price = float(price_match.group(1).replace(',', ''))
                    print(f"   - ✅ Found FINAL quote of ${price:.2f} from {carrier_name}")
                    cursor.execute("INSERT INTO quotes (shipment_id, carrier_name, quote_type, price, received_at, status) VALUES (?, ?, ?, ?, ?, ?)", (shipment_id, carrier_name, quote_type, price, datetime.now().isoformat(), 'received'))

            conn.commit()
