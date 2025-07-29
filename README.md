# Shipping Negotiator

A Python system for automating the process of collecting, negotiating, and analyzing shipping quotes from multiple carriers. The project uses the Gemini API for intelligent, format-free email parsing and leverages machine learning to predict and optimize negotiation outcomes.

## Features

- **Automated Quote Requests:** Sends quote requests to carriers via email or API.
- **AI-Powered Email Parsing:** Uses Google's Gemini API to intelligently parse prices from carrier emails, removing the need for a fixed format.
- **Negotiation Automation:** Initiates negotiation rounds with non-leading carriers to encourage better offers.
- **[IN PROGRESS] Machine Learning:** Trains models to predict final offers from carriers based on historical data.
- **Interactive Dashboard:** A Streamlit-based web interface to log new shipments, monitor progress, and preview emails.
- **Database-Backed:** Uses SQLite to store shipments, quotes, and negotiation history.

## Project Structure

```
shipping_negotiator/
│
├── app.py                   # Streamlit front-end dashboard
├── worker.py                # Background worker for email processing and negotiation
├── Procfile                 # Process declarations for honcho
├── run_app.sh               # Executable script to start the application
├── requirements.txt         # Project dependencies
├── reset_database.py        # Utility to wipe the database
│
├── data/
│   └── shipping_quotes.db   # SQLite database file
│
├── src/
│   ├── database_setup.py    # Database schema and setup logic
│   ├── quoting.py           # Functions for sending quote requests
│   ├── email_parser.py      # Main email fetching and processing logic
│   ├── ai_parser.py         # AI logic for parsing email content with Gemini
│   ├── negotiation.py       # Functions for sending negotiation requests
│   ├── ml_model.py          # Machine learning model training and prediction
│   └── config.py            # Configuration for secrets and settings
│
└── models/                  # Directory for saved ML models
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
3. **Configure your secrets:**
- Rename `src/config.py.template` to `src/config.py`.
- Carriers: Edit the `CARRIERS` dictionary in `config.py` to add or modify carriers and their contact methods.
- Email Credentials: Update `SENDER_EMAIL`, `SENDER_PASSWORD` in `config.py` with your own (use app passwords for Gmail/Outlook). Update `IMAP_SERVER` and `SMTP_SERVER` with server addresses that correspond to your email provider (Gmail is imap.gmail.com, smtp.gmail.com).
- API Keys: Obtain and update `GEMINI_API_KEY` in `config.py` with your API keys for each carrier.
- Polling Intervals: Adjust `POLLING_INTERVAL_SECONDS` and `POLLING_TIMEOUT_MINUTES` in `main.py` as needed.

4. **Set up the database:**
   ```bash
   python src/database_setup.py
   ```

## Utilities

- **Reset the database:**
  ```bash
  python reset_database.py
  ```

- **(IN PROGRESS) Train machine learning models:**
  Edit and run the relevant functions in `src/ml_model.py` to train models for each carrier using your data.

## Security Note

- **Credentials:** Your secret keys and passwords in `src/config.py` are ignored by Git via the `.gitignore` file to prevent them from being committed to your repository.
