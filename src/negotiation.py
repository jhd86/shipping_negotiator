import smtplib
from email.message import EmailMessage
from src.config import SENDER_EMAIL, SENDER_PASSWORD, COMPANY_NAME, SMTP_SERVER

def send_negotiation_request(carrier_email, shipment_id, lowest_bid):
    """Sends an email asking a carrier to beat a competing price."""
    print(f"Sending negotiation email to {carrier_email} for shipment {shipment_id}...")

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

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = carrier_email

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"✅ Email sent successfully to {carrier_email}.")
    except Exception as e:
        print(f"❌ FAILED to send email to {carrier_email}: {e}")
