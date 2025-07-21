# src/ml_model.py
import pandas as pd
import sqlite3
from sklearn.ensemble import HistGradientBoostingRegressor
import joblib
import os

def prepare_training_data(carrier_to_model):
    """Queries the DB and prepares data for training a specific carrier's model."""
    conn = sqlite3.connect("data/shipping_quotes.db")

    # This SQL query is the heart of the data preparation.
    # It finds all completed shipments and gathers the initial bid from every carrier,
    # the final offer from the carrier we are modeling, and identifies the lowest
    # competing initial bid.
    sql_query = f"""
    WITH InitialBids AS (
        -- Get all successful initial bids
        SELECT shipment_id, carrier_name, price
        FROM quotes
        WHERE quote_type = 'initial' AND status = 'received'
    ),
    FinalOffers AS (
        -- Get all successful final offers for the carrier we're modeling
        SELECT shipment_id, price AS final_offer
        FROM quotes
        WHERE quote_type = 'final' AND status = 'received' AND carrier_name = '{carrier_to_model}'
    )
    -- Main query to assemble the training data
    SELECT
        s.shipment_id,
        s.spots,
        s.weight,
        s.destination_zip,
        ib.price AS carrier_initial_bid,
        -- Find the lowest initial bid from a *competitor*
        (SELECT MIN(price) FROM InitialBids WHERE shipment_id = s.shipment_id AND carrier_name != '{carrier_to_model}') AS lowest_competing_bid,
        -- Get the final offer, if one exists
        fo.final_offer
    FROM shipments s
    JOIN InitialBids ib ON s.shipment_id = ib.shipment_id AND ib.carrier_name = '{carrier_to_model}'
    LEFT JOIN FinalOffers fo ON s.shipment_id = fo.shipment_id
    WHERE s.status = 'complete';
    """

    df = pd.read_sql_query(sql_query, conn)
    conn.close()

    # --- Feature Engineering & Cleaning ---
    # If there was no final offer, it means they didn't beat the price,
    # so their final offer is the same as their initial bid.
    df['final_offer'].fillna(df['carrier_initial_bid'], inplace=True)

    # The model can't use a raw ZIP code. Create a 'zone' feature.
    # This is a simplified example. You could make this more detailed.
    df['dest_zone'] = df['destination_zip'].str[0].astype(int)

    # Drop rows where there was no competitor
    df.dropna(subset=['lowest_competing_bid'], inplace=True)

    # Define your features (X) and the value you want to predict (y)
    features = ['spots', 'weight', 'dest_zone', 'carrier_initial_bid', 'lowest_competing_bid']
    target = 'final_offer'

    X = df[features]
    y = df[target]

    return X, y


def train_and_save_model(carrier_name):
    """Trains a model for a specific carrier and saves it to a file."""
    print(f"Training model for {carrier_name}...")
    X, y = prepare_training_data(carrier_name)

    # Handle cases with not enough data
    if len(X) < 50:
        print(f"Not enough data to train a model for {carrier_name}. Need at least 50 data points.")
        return

    model = HistGradientBoostingRegressor()
    model.fit(X, y)

    model_path = os.path.join("models", f"{carrier_name.replace(' ', '_')}_model.joblib")
    joblib.dump(model, model_path)
    print(f"Model for {carrier_name} trained and saved to {model_path}")

def predict_final_offer(carrier_name, shipment_details, lowest_bid):
    """Loads a trained model and predicts a final offer."""
    model_path = os.path.join("models", f"{carrier_name.replace(' ', '_')}_model.joblib")

    try:
        model = joblib.load(model_path)
    except FileNotFoundError:
        print(f"No model found for {carrier_name}. Cannot predict.")
        return None

    # Create a pandas DataFrame from the input, matching the training format
    input_data = pd.DataFrame([{
        'spots': shipment_details['spots'],
        'weight': shipment_details['weight'],
        'destination_zip_encoded': shipment_details['dest_zip_encoded'], # You'll need to create this feature
        'lowest_initial_bid': lowest_bid
    }])

    prediction = model.predict(input_data)
    return prediction[0]
