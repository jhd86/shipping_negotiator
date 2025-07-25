from src.email_utils import send_email, generate_negotiation_content

def send_negotiation_request(carrier_email, shipment_id, lowest_bid):
    """Builds and sends the negotiation email."""
    print(f"Sending negotiation email to {carrier_email} for shipment {shipment_id}...")
    content = generate_negotiation_content(shipment_id, lowest_bid)
    send_email(carrier_email, content['subject'], content['body'])
