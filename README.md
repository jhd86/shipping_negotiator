# Shipping Negotiator

A Python and Electron-based desktop application for automating the process of collecting, negotiating, and analyzing shipping quotes from multiple carriers. The project uses the Gemini API for intelligent, format-free email parsing and leverages machine learning to predict and optimize negotiation outcomes.

## Features

-   **Automated Quote Requests:** Sends quote requests to carriers via email or API.
-   **AI-Powered Email Parsing:** Uses Google's Gemini API to intelligently parse prices from carrier emails, removing the need for a fixed format.
-   **Negotiation Automation:** Initiates negotiation rounds with non-leading carriers to encourage better offers.
-   **Machine Learning:** Trains models to predict final offers from carriers based on historical data.
-   **Interactive Dashboard:** A custom web-based front end to log new shipments and monitor progress.
-   **Database-Backed:** Uses SQLite to store all shipment and quote history.

## Project Structure

```
shipping_negotiator/
│
├── app.py                   # Flask backend server
├── worker.py                # Background worker for email processing and negotiation
├── main.js                  # Main Electron script
├── preload.js               # Electron preload script
├── package.json             # Node.js dependencies and scripts
├── Procfile                 # Process declarations for honcho
├── run_app.sh               # Helper script for starting Python backend
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
├── models/                  # Directory for saved ML models
│   └── (Trained .joblib models)
│
├── static/
│   ├── app.js
│   └── style.css
│
└── templates/
    └── index.html
```

## Setup

1.  **Clone the repository** and create a Python virtual environment:
    ```bash
    git clone <your-repo-url>
    cd shipping_negotiator
    python -m venv venv
    source venv/bin/activate
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

4.  **Configure your secrets:**
    -   Create a file `src/config.py` (you can copy `src/config.py.template` if you have one).
    -   Add your `GEMINI_API_KEY`, email credentials, carrier details, etc.

5.  **Set up the database:**
    ```bash
    python src/database_setup.py
    ```

## Usage

You can run the entire desktop application with a single command:

```bash
npm start
```
This will launch the Electron window and automatically start the Python Flask server and background worker.

## Utilities

- **Reset the database:**
  ```bash
  python reset_database.py
  ```

- **(IN PROGRESS) Train machine learning models:**
  Edit and run the relevant functions in `src/ml_model.py` to train models for each carrier using your data.

## Security Note

- **Credentials:** Your secret keys and passwords in `src/config.py` are ignored by Git via the `.gitignore` file to prevent them from being committed to your repository.
