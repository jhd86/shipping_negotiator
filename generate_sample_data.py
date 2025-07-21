# generate_sample_data.py

import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# --- Configuration ---
NUM_SHIPMENTS = 500
CARRIERS = ["Budget Freight", "Premium Express", "Regional Pro"]
START_DATE = datetime(2024, 1, 1)

# Define carrier "personalities" for pricing and negotiation
CARRIER_PROFILES = {
    "Budget Freight": {
        "base_rate": 150,
        "weight_rate": 0.15,
        "spot_rate": 50,
        "negotiation_chance": 0.3, # Low chance to negotiate
        "negotiation_strength": 0.98 # But only offers a small discount (2%)
    },
    "Premium Express": {
        "base_rate": 300,
        "weight_rate": 0.25,
        "spot_rate": 75,
        "negotiation_chance": 0.85, # High chance to negotiate
        "negotiation_strength": 0.96 # Offers a good discount (4%)
    },
    "Regional Pro": {
        "base_rate": 200,
        "weight_rate": 0.20,
        "spot_rate": 65,
        "negotiation_chance": 0.6,
        "negotiation_strength": 0.97,
        "preferred_zips": ["0", "1"] # Prefers Northeast (zips starting with 0 or 1)
    }
}

def generate_initial_quote(carrier, weight, spots, zip_code):
    """Calculates an initial quote based on carrier profile."""
    profile = CARRIER_PROFILES[carrier]

    # Base price calculation
    price = profile["base_rate"] + (weight * profile["weight_rate"]) + (spots * profile["spot_rate"])

    # Apply regional discount for Regional Pro
    if carrier == "Regional Pro" and any(zip_code.startswith(p) for p in profile["preferred_zips"]):
        price *= 0.85 # 15% discount for preferred region

    # Add some random noise to make it realistic
    price *= np.random.uniform(0.95, 1.05)

    return round(price, 2)

def generate_final_offer(carrier, initial_quote, lowest_bid, zip_code):
    """Calculates if a carrier will negotiate and what their final offer is."""
    profile = CARRIER_PROFILES[carrier]

    # Don't negotiate if you already have the lowest bid
    if initial_quote == lowest_bid:
        return initial_quote

    # Regional Pro is less likely to negotiate outside its preferred region
    negotiation_chance = profile["negotiation_chance"]
    if carrier == "Regional Pro" and not any(zip_code.startswith(p) for p in profile["preferred_zips"]):
        negotiation_chance *= 0.5

    # Decide if the carrier will negotiate
    if random.random() < negotiation_chance:
        # Final offer is a discount on the competitor's lowest bid
        final_offer = lowest_bid * profile["negotiation_strength"]
        final_offer *= np.random.uniform(0.99, 1.01) # Add slight variance
        return round(final_offer, 2)
    else:
        # No negotiation, price stays the same
        return initial_quote

def generate_data(num_shipments):
    """Generates the full dataset and saves it to a CSV."""
    print(f"Generating {num_shipments} sample shipments...")
    data = []

    for i in range(num_shipments):
        # 1. Generate base shipment details
        shipment_date = START_DATE + timedelta(days=i)
        spots = random.randint(1, 12)
        weight = random.randint(500, 15000)
        zip_code = str(random.randint(501, 99950)).zfill(5)

        # 2. Get initial quotes from all carriers
        initial_quotes = {
            carrier: generate_initial_quote(carrier, weight, spots, zip_code)
            for carrier in CARRIERS
        }

        # 3. Find the initial low bidder
        lowest_initial_bid = min(initial_quotes.values())

        # 4. Get final negotiated offers
        final_offers = {
            carrier: generate_final_offer(carrier, initial_quotes[carrier], lowest_initial_bid, zip_code)
            for carrier in CARRIERS
        }

        # 5. Determine the final winner
        final_price = min(final_offers.values())
        final_winner = [carrier for carrier, price in final_offers.items() if price == final_price][0]

        # 6. Append to our dataset
        record = {
            "shipment_id": 1000 + i,
            "request_date": shipment_date.strftime('%Y-%m-%d'),
            "spots": spots,
            "weight": weight,
            "destination_zip": zip_code,
            "lowest_initial_bid": lowest_initial_bid
        }
        # Add initial and final quotes for each carrier
        for carrier in CARRIERS:
            record[f"{carrier.replace(' ', '_')}_initial"] = initial_quotes[carrier]
            record[f"{carrier.replace(' ', '_')}_final"] = final_offers[carrier]

        record["final_winner"] = final_winner
        record["final_price"] = final_price

        data.append(record)

    df = pd.DataFrame(data)
    df.to_csv("sample_shipment_data.csv", index=False)
    print("✅ Sample data saved to sample_shipment_data.csv")
    print("\nFirst 5 rows of the generated data:")
    print(df.head())

if __name__ == "__main__":
    generate_data(NUM_SHIPMENTS)
