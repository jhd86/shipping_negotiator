import sqlite3
from flask import Flask, jsonify, render_template, request
from datetime import datetime
from src.database_setup import DB_PATH

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # This allows accessing columns by name
    return conn

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/api/shipments', methods=['GET'])
def get_shipments():
    """API endpoint to get all shipments."""
    conn = get_db_connection()
    shipments = conn.execute('SELECT * FROM shipments ORDER BY shipment_id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in shipments])

@app.route('/api/shipments', methods=['POST'])
def add_shipment():
    """API endpoint to log a new shipment."""
    data = request.json
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO shipments (request_date, spots, weight, destination_zip, status) VALUES (?, ?, ?, ?, ?)",
            (datetime.now().isoformat(), data['spots'], data['weight'], data['destination_zip'], 'quoting')
        )
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Shipment logged."}), 201
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/quotes/<int:shipment_id>', methods=['GET'])
def get_quotes(shipment_id):
    """API endpoint to get quotes for a specific shipment."""
    conn = get_db_connection()
    quotes = conn.execute('SELECT * FROM quotes WHERE shipment_id = ?', (shipment_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in quotes])

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API endpoint to get dashboard summary statistics."""
    conn = get_db_connection()
    total_shipments = conn.execute('SELECT COUNT(*) FROM shipments').fetchone()[0]
    in_progress = conn.execute("SELECT COUNT(*) FROM shipments WHERE status NOT IN ('complete', 'failed')").fetchone()[0]

    # Calculate savings from completed shipments
    completed = conn.execute("SELECT final_price FROM shipments WHERE status = 'complete' AND final_price IS NOT NULL").fetchall()

    total_savings = 0
    # Find all completed shipments that have a final price
    completed_shipments = conn.execute(
        "SELECT shipment_id, final_price FROM shipments WHERE status = 'complete' AND final_price IS NOT NULL"
    ).fetchall()

    for shipment in completed_shipments:
        shipment_id = shipment['shipment_id']
        final_price = shipment['final_price']

        # Find the lowest initial bid for that shipment
        lowest_initial_bid_row = conn.execute(
            "SELECT MIN(price) FROM quotes WHERE shipment_id = ? AND quote_type = 'initial' AND status = 'received'",
            (shipment_id,)
        ).fetchone()

        if lowest_initial_bid_row and lowest_initial_bid_row[0] is not None:
            lowest_initial_bid = lowest_initial_bid_row[0]
            # Add the difference to total savings if we saved money
            if lowest_initial_bid > final_price:
                total_savings += (lowest_initial_bid - final_price)

    conn.close()

    return jsonify({
        "total_shipments": total_shipments,
        "in_progress": in_progress,
        "total_savings": total_savings # Placeholder
    })

if __name__ == '__main__':
    app.run(debug=True)
