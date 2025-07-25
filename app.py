import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from src.database_setup import DB_PATH

# Set page configuration
st.set_page_config(page_title="Shipping Negotiator", layout="wide")

# --- Database Connection Function (Defined at the top) ---
def get_db_connection():
    return sqlite3.connect(DB_PATH)

st.title("🚚 Shipping Quotes Dashboard")

# --- Form to Add New Shipments ---
st.header("Log a New Shipment")

with st.form("new_shipment_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        spots = st.number_input("Number of Pallets (Spots)", min_value=1, step=1)
    with col2:
        weight = st.number_input("Total Weight (lbs)", min_value=1, step=1)
    with col3:
        destination_zip = st.text_input("Destination ZIP Code", max_chars=5)

    submitted = st.form_submit_button("Log Shipment")
    if submitted:
        if not destination_zip.isdigit() or len(destination_zip) != 5:
            st.error("Please enter a valid 5-digit ZIP code.")
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO shipments (request_date, spots, weight, destination_zip, status) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), spots, weight, destination_zip, 'quoting')
            )
            conn.commit()
            conn.close()

            st.success(f"Shipment to {destination_zip} logged successfully!")
            st.experimental_rerun()

# --- Main Dashboard View ---
st.header("All Shipments")

conn = get_db_connection()
shipments_df = pd.read_sql_query("SELECT * FROM shipments ORDER BY shipment_id DESC", conn)
quotes_df = pd.read_sql_query("SELECT * FROM quotes", conn)
conn.close()

if shipments_df.empty:
    st.warning("No shipments found. Log a new shipment to get started.")
else:
    st.dataframe(shipments_df)

    selected_id = st.selectbox("Select a Shipment ID to see details:", shipments_df['shipment_id'])
    if selected_id:
        st.subheader(f"Quotes for Shipment #{selected_id}")

        # --- Display Quotes Table ---
        details_df = quotes_df[quotes_df['shipment_id'] == int(selected_id)] # Ensure ID is int
        if details_df.empty:
            st.info("No quotes yet for this shipment.")
        else:
            st.dataframe(details_df)

        # --- Add Email Preview Section ---
        st.subheader("Email Previews")

        # Import the generator functions
        from src.email_utils import generate_quote_request_content, generate_negotiation_content

        # Get the shipment details for the selected ID from the main dataframe
        shipment_info = shipments_df[shipments_df['shipment_id'] == int(selected_id)].iloc[0].to_dict()

        # Generate and display the initial quote request email
        st.markdown("#### Initial Quote Request Email")
        initial_content = generate_quote_request_content(shipment_info)
        st.text_input("Subject", initial_content['subject'], disabled=True)
        st.text_area("Body", initial_content['body'], height=250, disabled=True)

        # Check if there's a low bid to generate a negotiation email
        initial_quotes = details_df[(details_df['quote_type'] == 'initial') & (details_df['price'].notna())]
        if not initial_quotes.empty:
            lowest_bid = initial_quotes['price'].min()
            st.markdown("#### Negotiation Email")
            negotiation_content = generate_negotiation_content(selected_id, lowest_bid)
            st.text_input("Subject ", negotiation_content['subject'], disabled=True) # Space in label is a hack for unique key
            st.text_area("Body ", negotiation_content['body'], height=250, disabled=True) # Space in label is a hack for unique key
