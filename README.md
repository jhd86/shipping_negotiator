# Shipping Negotiator

A Python system for automating the process of collecting, negotiating, and analyzing shipping quotes from multiple carriers. The project supports both API and email-based carriers, and leverages machine learning to predict and optimize negotiation outcomes.

## Features

- **Automated Quote Requests:** Sends quote requests to carriers via email or API.
- **Email Parsing:** Automatically checks and parses carrier email replies for quotes.
- **Negotiation Automation:** Initiates negotiation rounds with non-leading carriers to encourage better offers.
- **Machine Learning:** Trains models to predict final offers from carriers based on historical data.
- **Database-Backed:** Uses SQLite to store shipments, quotes, and negotiation history.
- **Sample Data Generation:** Includes tools to generate realistic sample shipment and quote data for testing and model training.

## Project Structure

```
shipping_negotiator/
│
├── worker.py                # Orchestrates the end-to-end quoting and negotiation process
├── app.py                   # Dashboard for tracking shipments and negotiations
├── generate_sample_data.py  # Script to generate synthetic shipment and quote data
├── reset_database.py        # Utility to reset the database
├── sample_shipment_data.csv # Example generated data
│
├── data/
│   └── shipping_quotes.db   # SQLite database file
│
├── src/
│   ├── database_setup.py    # Database schema and setup logic
│   ├── quoting.py           # Functions for sending quote requests (API/email)
│   ├── email_parser.py      # Functions for parsing incoming quote emails
│   ├── negotiation.py       # Functions for sending negotiation requests
│   ├── ml_model.py          # Machine learning model training and prediction
│   └── config.py            # Template for configuration settings - FILL THIS OUT
│
├── models/                  # Trained ML models (created at runtime)
├── emails/                  # (Optional) For storing email templates or logs
└── venv/                    # Python virtual environment
```

## Setup

1. **Clone the repository** and create a virtual environment:
   ```bash
   git clone https://github.com/jhd86/shipping_negotiator
   cd shipping_negotiator
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database:**
   ```bash
   python src/database_setup.py
   ```

4. **(Optional) Generate sample data:**
   ```bash
   python generate_sample_data.py
   ```

## Usage

- **Running the program:**
  Set up the front end:
  ```bash
  # Navigate to your project directory
  cd /path/to/shipping_negotiator

  # Activate your virtual environment
  source venv/bin/activate

  # Run the Streamlit app
  python -m streamlit run app.py
  ```

  In a seperate terminal window, run the backend:
  ```bash
  # Navigate to your project directory
  cd /path/to/shipping_negotiator

  # Activate your virtual environment
  source venv/bin/activate

  # Run the worker script
  python worker.py
  ```



- **Reset the database (Utility):**
  ```bash
  python reset_database.py
  ```

- **(IN PROGRESS) Train machine learning models:**
  Edit and run the relevant functions in `src/ml_model.py` to train models for each carrier using your data.

## Configuration

- **Carriers:** Edit the `CARRIERS` dictionary in `config.py` to add or modify carriers and their contact methods.
- **Email Credentials:** Update `SENDER_EMAIL`, `SENDER_PASSWORD` in `config.py` with your own (use app passwords for Gmail/Outlook). Update `IMAP_SERVER` and `SMTP_SERVER` with server addresses that correspond to your email provider (Gmail is imap.gmail.com, smtp.gmail.com).
- **Polling Intervals:** Adjust `POLLING_INTERVAL_SECONDS` and `POLLING_TIMEOUT_MINUTES` in `main.py` as needed.

## How It Works

1. **Shipment Entry:** User provides shipment details via web application.
2. **Quote Requests:** System logs the shipment and requests quotes from all configured carriers.
3. **Email/API Handling:** Waits for and parses incoming quotes (via email or API).
4. **Negotiation:** Identifies the lowest bid and asks other carriers to beat it.
5. **Machine Learning (WORK IN PROGRESS):** Predicts which carriers are likely to negotiate and by how much, using historical data.
6. **Database Logging:** All actions and quotes are logged for analysis and model training.

## Security Note

- **Credentials:** Do not commit real email credentials to version control. Use `config.py` and `.gitignore` for sensitive information in production.
