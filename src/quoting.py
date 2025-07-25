# src/quoting.py
import smtplib
from email.message import EmailMessage
from src.config import COMPANY_NAME, SENDER_EMAIL, SENDER_PASSWORD
import requests

# --- Placeholder for API Logic ---
def get_api_quote(carrier_name, shipment_details):
    """Gets a quote from a carrier's API."""
    print(f"Requesting API quote from {carrier_name}...")
    # This is where you'd put the specific code for each carrier's API
    # Example:
    # try:
    #     api_url = "https://api.carrier.com/v1/quote"
    #     response = requests.post(api_url, json=shipment_details, auth=("user", "pass"))
    #     response.raise_for_status() # Raise an error for bad responses
    #     price = response.json().get('price')
    #     return price
    # except requests.exceptions.RequestException as e:
    #     print(f"Error getting quote from {carrier_name}: {e}")
    #     return None
    return 1234.56 # Dummy data for now

# --- Logic for Sending Email Requests ---
def send_email_quote_request(carrier_email, shipment_details):
    """Sends a standardized quote request email."""
    print(f"Sending email quote request to {carrier_email}...")

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

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = carrier_email

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {carrier_email}.")
    except Exception as e:
        print(f"Failed to send email to {carrier_email}: {e}")
