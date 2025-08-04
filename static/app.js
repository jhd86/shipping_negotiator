document.addEventListener("DOMContentLoaded", () => {
  // --- DOM Elements ---
  const shipmentsTableBody = document.querySelector("#shipments-table tbody");
  const shipmentsEmptyState = document.getElementById("shipments-empty-state");
  const quotesTableBody = document.querySelector("#quotes-table tbody");
  const quotesEmptyState = document.getElementById("quotes-empty-state");
  const editModal = document.getElementById("edit-modal");
  const closeModalButton = document.querySelector(".close-button");
  const editQuoteForm = document.getElementById("edit-quote-form");
  const totalShipmentsStat = document.getElementById("total-shipments-stat");
  const inProgressStat = document.getElementById("in-progress-stat");
  const totalSavingsStat = document.getElementById("total-savings-stat");
  const newShipmentForm = document.getElementById("new-shipment-form");
  const filterForm = document.getElementById("filter-form");
  const detailsIdSpan = document.getElementById("details-id");
  const prevButton = document.getElementById("prev-button");
  const nextButton = document.getElementById("next-button");
  const pageSpan = document.getElementById("page-number");

  // --- State ---
  let allShipments = [];
  let currentPage = 1;
  let selectedShipmentId = null;
  const rowsPerPage = 5;

  // --- Core Functions ---
  async function refreshDashboard() {
    console.log("Refreshing dashboard data...");
    const filterParams = new URLSearchParams({
      customer: document.getElementById("filter-customer").value,
      so: document.getElementById("filter-so").value,
      po: document.getElementById("filter-po").value,
    }).toString();

    await Promise.all([fetchStats(), fetchShipments(filterParams)]);

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
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  }

  async function fetchShipments(filterParams = "") {
    try {
      const response = await fetch(`/api/shipments?${filterParams}`);
      if (!response.ok)
        throw new Error(`HTTP error! status: ${response.status}`);
      allShipments = await response.json();
    } catch (error) {
      console.error("Failed to fetch shipments:", error);
      allShipments = [];
    }
  }

  function renderShipmentsPage() {
    shipmentsTableBody.innerHTML = "";
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    const paginatedShipments = allShipments.slice(start, end);

    if (allShipments.length === 0) {
      shipmentsEmptyState.classList.add("visible");
    } else {
      shipmentsEmptyState.classList.remove("visible");
    }

    paginatedShipments.forEach((s) => {
      const row = document.createElement("tr");
      row.id = `shipment-row-${s.shipment_id}`;
      if (s.shipment_id === selectedShipmentId) {
        row.classList.add("selected-row");
      }

      const statusCell = `
          <td>
              <div class="status-cell">
                  <span class="status-dot ${s.status.toLowerCase()}"></span>
                  <span>${s.status}</span>
              </div>
          </td>`;

      row.innerHTML = `
                <td>${s.shipment_id}</td>
                <td>${s.customer_name || "N/A"}</td>
                <td>${s.sales_order || "N/A"}</td>
                <td>${s.purchase_order || "N/A"}</td>
                ${statusCell}
                <td>${s.final_winner || "N/A"}</td>
                <td>${s.final_price ? "$" + s.final_price.toFixed(2) : "N/A"}</td>
            `;
      row.addEventListener("click", () => {
        selectedShipmentId = s.shipment_id;
        renderShipmentsPage();
        fetchAndRenderQuotes(s.shipment_id);
      });
      shipmentsTableBody.appendChild(row);
    });

    updatePaginationControls();
  }

  function openEditModal(quoteId, carrierName) {
    document.getElementById("modal-quote-id").value = quoteId;
    document.getElementById("modal-carrier-name").textContent = carrierName;
    document.getElementById("modal-price").value = "";
    editModal.classList.add("visible");
  }

  function closeEditModal() {
    editModal.classList.remove("visible");
  }

  async function handleEditFormSubmit(event) {
    event.preventDefault();
    const quoteId = modalQuoteId.value;
    const price = modalPriceInput.value;

    try {
      const response = await fetch("/api/quotes/manual_update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quote_id: parseInt(quoteId),
          price: parseFloat(price),
        }),
      });
      if (!response.ok) throw new Error("Failed to update quote");

      closeEditModal();
      // Refresh the quotes to show the new price
      if (selectedShipmentId) {
        fetchAndRenderQuotes(selectedShipmentId);
      }
    } catch (error) {
      console.error("Failed to submit manual quote:", error);
      alert("Error: Could not save the new price.");
    }
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
            <td>
                <div class="status-cell">
                    <span class="status-dot ${q.status.toLowerCase()}"></span>
                    <span>${q.status}</span>
                </div>
            </td>`;
        row.innerHTML = `
            <td>${q.carrier_name}</td>
            <td>${q.quote_type}</td>
            ${statusCell}
            <td>${q.price ? "$" + q.price.toFixed(2) : "N/A"}</td>
            <td><button class="edit-button" data-quote-id="${q.quote_id}" data-carrier-name="${q.carrier_name}">Edit</button></td>
        `;
        quotesTableBody.appendChild(row);
      });
    }
  }

  quotesTableBody.addEventListener("click", (event) => {
    if (event.target && event.target.classList.contains("edit-button")) {
      const quoteId = event.target.dataset.quoteId;
      const carrierName = event.target.dataset.carrierName;
      openEditModal(quoteId, carrierName);
    }
  });

  closeModalButton.addEventListener("click", closeEditModal);
  window.addEventListener("click", (event) => {
    if (event.target == editModal) {
      closeEditModal();
    }
  });
  editQuoteForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const quoteId = document.getElementById("modal-quote-id").value;
    const price = document.getElementById("modal-price").value;

    try {
      const response = await fetch("/api/quotes/manual_update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          quote_id: parseInt(quoteId),
          price: parseFloat(price),
        }),
      });
      if (!response.ok) throw new Error("Failed to update quote");

      closeEditModal();
      if (selectedShipmentId) {
        fetchAndRenderQuotes(selectedShipmentId);
      }
    } catch (error) {
      console.error("Failed to submit manual quote:", error);
      alert("Error: Could not save the new price.");
    }
  });
  newShipmentForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const shipmentData = {
      customer_name: document.getElementById("customer-name").value,
      sales_order: document.getElementById("so-number").value,
      purchase_order: document.getElementById("po-number").value,
      spots: document.getElementById("spots").value,
      weight: document.getElementById("weight").value,
      destination_zip: document.getElementById("zip").value,
    };
    await fetch("/api/shipments", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(shipmentData),
    });
    newShipmentForm.reset();
    await refreshDashboard();
  });

  filterForm.addEventListener("input", () => {
    currentPage = 1;
    refreshDashboard();
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
