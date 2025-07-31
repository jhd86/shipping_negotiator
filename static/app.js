document.addEventListener("DOMContentLoaded", () => {
  const shipmentsTableBody = document.querySelector("#shipments-table tbody");
  const quotesTableBody = document.querySelector("#quotes-table tbody");
  const form = document.getElementById("new-shipment-form");
  const detailsIdSpan = document.getElementById("details-id");

  async function fetchAndRenderShipments() {
    const response = await fetch("/api/shipments");
    const shipments = await response.json();
    shipmentsTableBody.innerHTML = "";
    shipments.forEach((s) => {
      const row = document.createElement("tr");
      row.innerHTML = `
                <td>${s.shipment_id}</td>
                <td>${s.status}</td>
                <td>${s.final_winner || ""}</td>
                <td>${s.final_price ? "$" + s.final_price.toFixed(2) : ""}</td>
                <td>${s.spots}</td>
                <td>${s.weight}</td>
                <td>${s.destination_zip}</td>
                <td>${new Date(s.request_date).toLocaleString()}</td>
            `;
      row.addEventListener("click", () => fetchAndRenderQuotes(s.shipment_id));
      shipmentsTableBody.appendChild(row);
    });
  }

  async function fetchAndRenderQuotes(shipmentId) {
    detailsIdSpan.textContent = shipmentId;
    const response = await fetch(`/api/quotes/${shipmentId}`);
    const quotes = await response.json();
    quotesTableBody.innerHTML = "";
    quotes.forEach((q) => {
      const row = document.createElement("tr");
      row.innerHTML = `
                <td>${q.carrier_name}</td>
                <td>${q.quote_type}</td>
                <td>${q.status}</td>
                <td>${q.price ? "$" + q.price.toFixed(2) : ""}</td>
                <td>${q.received_at ? new Date(q.received_at).toLocaleString() : ""}</td>
            `;
      quotesTableBody.appendChild(row);
    });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const shipmentData = {
      spots: document.getElementById("spots").value,
      weight: document.getElementById("weight").value,
      destination_zip: document.getElementById("zip").value,
    };
    await fetch("/api/shipments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(shipmentData),
    });
    form.reset();
    fetchAndRenderShipments();
  });

  fetchAndRenderShipments();
  setInterval(fetchAndRenderShipments, 5000); // Auto-refresh every 5 seconds
});
