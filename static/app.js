document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const shipmentsTableBody = document.querySelector("#shipments-table tbody");
  const shipmentsEmptyState = document.getElementById("shipments-empty-state");
  const quotesTableBody = document.querySelector("#quotes-table tbody");
  const quotesEmptyState = document.getElementById("quotes-empty-state");
  const totalShipmentsStat = document.getElementById("total-shipments-stat");
  const inProgressStat = document.getElementById("in-progress-stat");
  const totalSavingsStat = document.getElementById("total-savings-stat");
  const form = document.getElementById("new-shipment-form");
  const searchForm = document.getElementById("search-form");
  const searchInput = document.getElementById("search-id");
  const detailsIdSpan = document.getElementById("details-id");
  const prevButton = document.getElementById("prev-button");
  const nextButton = document.getElementById("next-button");
  const pageSpan = document.getElementById("page-number");

  // State
  let allShipments = [];
  let currentPage = 1;
  let selectedShipmentId = null;
  const DEFAULT_ROWS_PER_PAGE = 5;
  let rowsPerPage = DEFAULT_ROWS_PER_PAGE;

  // --- Main Data Fetching and Rendering ---

  async function refreshDashboard() {
    console.log("Refreshing dashboard data...");
    // Fetch stats and shipments in parallel
    await Promise.all([fetchStats(), fetchShipments()]);
    // Re-render the table and quotes for the selected shipment
    renderShipmentsPage();
    if (selectedShipmentId) {
      fetchAndRenderQuotes(selectedShipmentId);
    }
    console.log("Dashboard refresh complete.");
  }

  async function fetchStats() {
    try {
      const response = await fetch("/api/stats");
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      const stats = await response.json();

      totalShipmentsStat.textContent = stats.total_shipments;
      inProgressStat.textContent = stats.in_progress;
      totalSavingsStat.textContent = `$${stats.total_savings.toFixed(2)}`;
      console.log("Stats loaded:", stats);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  }

  async function fetchShipments() {
    try {
      const response = await fetch("/api/shipments");
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      allShipments = await response.json();
      console.log(`Loaded ${allShipments.length} total shipments.`);

      // Crucially, always render the page after fetching.
      renderShipmentsPage();
    } catch (error) {
      console.error("Failed to fetch shipments:", error);
    }
  }

  function renderShipmentsPage() {
    shipmentsTableBody.innerHTML = "";
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const paginatedShipments = allShipments.slice(start, end);

    paginatedShipments.forEach((s) => {
      const row = document.createElement("tr");
      row.id = `shipment-row-${s.shipment_id}`;
      if (s.shipment_id === selectedShipmentId) {
        row.classList.add("selected-row");
      }

      const statusCell = `
                <td class="status-cell">
                    <span class="status-dot ${s.status.toLowerCase()}"></span>
                    <span>${s.status}</span>
                </td>`;

      row.innerHTML = `
                <td>${s.shipment_id}</td>
                ${statusCell}
                <td>${s.final_winner || "N/A"}</td>
                <td>${s.final_price ? "$" + s.final_price.toFixed(2) : "N/A"}</td>
                <td>${s.spots}</td>
                <td>${s.destination_zip}</td>
            `;
      row.addEventListener("click", () => {
        selectedShipmentId = s.shipment_id;
        fetchAndRenderQuotes(s.shipment_id);
        renderShipmentsPage();
      });
      shipmentsTableBody.appendChild(row);
    });

    updatePaginationControls();
  }

  function updatePaginationControls() {
    const totalPages = Math.ceil(allShipments.length / rowsPerPage);
    pageSpan.textContent = `Page ${currentPage} of ${totalPages || 1}`;
    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage === totalPages || totalPages === 0;
  }

  async function fetchAndRenderQuotes(shipmentId) {
    detailsIdSpan.textContent = shipmentId;
    const response = await fetch(`/api/quotes/${shipmentId}`);
    const quotes = await response.json();
    quotesTableBody.innerHTML = "";

    if (quotes.length === 0) {
      quotesEmptyState.classList.add("visible");
      quotesTableBody.style.display = "none";
    } else {
      quotesEmptyState.classList.remove("visible");
      quotesTableBody.style.display = "";
      quotes.forEach((q) => {
        const row = document.createElement("tr");
        const statusCell = `
                    <td class="status-cell">
                        <span class="status-dot ${q.status.toLowerCase()}"></span>
                        <span>${q.status}</span>
                    </td>`;
        row.innerHTML = `
                    <td>${q.carrier_name}</td>
                    <td>${q.quote_type}</td>
                    ${statusCell}
                    <td>${q.price ? "$" + q.price.toFixed(2) : "N/A"}</td>
                `;
        quotesTableBody.appendChild(row);
      });
    }
  }

  // --- (Event listeners for forms and buttons are unchanged) ---
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
    await refreshDashboard();
    currentPage = 1;
    renderShipmentsPage();
  });

  searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const searchId = parseInt(searchInput.value, 10);
    if (isNaN(searchId)) return;
    const shipmentIndex = allShipments.findIndex(
      (s) => s.shipment_id === searchId,
    );
    if (shipmentIndex === -1) {
      alert(`Shipment ID #${searchId} not found.`);
      return;
    }
    const targetPage = Math.floor(shipmentIndex / rowsPerPage) + 1;
    currentPage = targetPage;
    renderShipmentsPage();
    await fetchAndRenderQuotes(searchId);
    searchInput.value = "";
  });

  prevButton.addEventListener("click", () => {
    if (currentPage > 1) {
      currentPage--;
      renderShipmentsPage();
    }
  });

  nextButton.addEventListener("click", () => {
    const totalPages = Math.ceil(allShipments.length / rowsPerPage);
    if (currentPage < totalPages) {
      currentPage++;
      renderShipmentsPage();
    }
  });

  // --- Initial Load and Auto-Refresh ---
  refreshDashboard();
  setInterval(refreshDashboard, 5000);
});
