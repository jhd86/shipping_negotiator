import smtplib
from email.message import EmailMessage
from src.config import COMPANY_NAME, SENDER_EMAIL, SENDER_PASSWORD, SMTP_SERVER

def generate_quote_request_content(shipment_details):
    """Generates the subject and body for an initial quote request."""
    subject = f"Quote Request - Shipment #{shipment_details['shipment_id']}"
    body = f"""
Hello,

Please provide a quote for the following shipment:
- Pallets (Spots): {shipment_details['spots']}
- Weight (lbs): {shipment_details['weight']}
- Destination ZIP: {shipment_details['destination_zip']}

To help us process this automatically, please reply with the price on a line by itself formatted like this:
Quote: $1234.56

Thank you,
{COMPANY_NAME}
"""
    return {'subject': subject, 'body': body}

def generate_negotiation_content(shipment_id, lowest_bid):
    """Generates the subject and body for a negotiation email."""
    subject = f"Final Offer Request - Shipment #{shipment_id}"
    body = f"""
Hello,

Regarding shipment #{shipment_id}, we have received a competing quote of ${lowest_bid:.2f}.

We value your service and would like to give you the opportunity to provide a final, more competitive offer.

Please reply with your best and final offer in the same format as before:
Quote: $1234.56

Thank you,
{COMPANY_NAME}
"""
    return {'subject': subject, 'body': body}


def send_email(recipient_email, subject, body):
    """A centralized function to send any email."""
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent successfully to {recipient_email}.")
        return True
    except Exception as e:
        print(f"❌ FAILED to send email to {recipient_email}: {e}")
        return False
