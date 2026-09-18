(() => {
  "use strict";

  const state = {
    listings: [],
    quality: null,
    filtered: [],
    map: null,
  };

  const DETAIL_FIELDS = [
    ["name", "Name"],
    ["destination", "Destination"],
    ["country", "Country"],
    ["category", "Category"],
    ["subcategory", "Subcategory"],
    ["address", "Address"],
    ["phone", "Phone"],
    ["email", "Email"],
    ["website", "Website"],
    ["opening_hours", "Opening hours"],
    ["price", "Price"],
    ["description", "Description"],
    ["source_url", "Source page"],
    ["scraped_at", "Scraped timestamp"],
  ];

  const COMPLETE_FIELDS = [
    ["address", "Address"],
    ["phone", "Phone"],
    ["email", "Email"],
    ["website", "Website"],
    ["opening_hours", "Opening Hours"],
    ["price", "Price"],
    ["coordinates", "Coordinates"],
  ];

  function $(id) {
    return document.getElementById(id);
  }

  function selectedValues(selectEl) {
    return Array.from(selectEl.selectedOptions).map((opt) => opt.value);
  }

  function fillSelect(selectEl, values) {
    selectEl.innerHTML = "";
    values.forEach((value) => {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      selectEl.appendChild(option);
    });
  }

  function uniqueSorted(items, key) {
    return [...new Set(items.map((row) => row[key]).filter(Boolean))].sort((a, b) =>
      String(a).localeCompare(String(b))
    );
  }

  function formatNumber(value) {
    if (value === null || value === undefined || value === "") return "—";
    return Number(value).toLocaleString("en-US");
  }

  function hasCoordinates(row) {
    if (row.latitude === null || row.latitude === undefined || row.latitude === "") {
      return false;
    }
    if (row.longitude === null || row.longitude === undefined || row.longitude === "") {
      return false;
    }
    const lat = Number(row.latitude);
    const lon = Number(row.longitude);
    return Number.isFinite(lat) && Number.isFinite(lon);
  }

  function createKpi(label, value) {
    const card = document.createElement("article");
    card.className = "kpi";
    card.innerHTML = `<span class="kpi-label">${label}</span><span class="kpi-value">${value}</span>`;
    return card;
  }

  function createMeta(label, value) {
    const item = document.createElement("div");
    item.className = "meta-item";
    item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    return item;
  }

  function renderOverview() {
    const q = state.quality;
    const listings = state.listings;
    const withCoords = listings.filter(hasCoordinates).length;
    const withWebsite = listings.filter((r) => Boolean(r.website)).length;
    const destinations = uniqueSorted(listings, "destination").length;
    const countries = uniqueSorted(listings, "country").length;
    const categories = uniqueSorted(listings, "category").length;

    const kpis = [
      ["Final Records", formatNumber(q.final_records ?? listings.length)],
      ["Destinations", formatNumber(destinations)],
      ["Countries", formatNumber(countries)],
      ["Categories", formatNumber(categories)],
      ["Geocoded Records", formatNumber(withCoords)],
      ["Records With Website", formatNumber(withWebsite)],
    ];

    const kpiRoot = $("overview-kpis");
    kpiRoot.innerHTML = "";
    kpis.forEach(([label, value]) => kpiRoot.appendChild(createKpi(label, value)));

    $("run-meta").textContent = `Latest ETL run: ${q.run_timestamp || "n/a"} · Representative demonstration crawl (not a full-site scrape).`;

    const metaRoot = $("overview-meta");
    metaRoot.innerHTML = "";
    [
      ["Pages processed", formatNumber(q.pages_successfully_processed)],
      ["Failed pages", formatNumber(q.failed_pages)],
      ["Duplicates removed", formatNumber(q.duplicates_removed)],
      ["Invalid records", formatNumber(q.invalid_records)],
      ["Raw records", formatNumber(q.raw_records)],
      ["Configured destinations", (q.configured_destinations || []).join(", ") || "—"],
    ].forEach(([label, value]) => metaRoot.appendChild(createMeta(label, value)));
  }

  function matchesFilters(row) {
    const search = $("search").value.trim().toLowerCase();
    const countries = selectedValues($("filter-country"));
    const destinations = selectedValues($("filter-destination"));
    const categories = selectedValues($("filter-category"));

    if (countries.length && !countries.includes(row.country)) return false;
    if (destinations.length && !destinations.includes(row.destination)) return false;
    if (categories.length && !categories.includes(row.category)) return false;

    if (search) {
      const haystack = [
        row.name,
        row.address,
        row.description,
        row.destination,
        row.country,
        row.category,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      if (!haystack.includes(search)) return false;
    }
    return true;
  }

  function applyFilters() {
    state.filtered = state.listings.filter(matchesFilters);
    renderTable();
    $("result-count").textContent = `${state.filtered.length.toLocaleString("en-US")} record${
      state.filtered.length === 1 ? "" : "s"
    }`;
  }

  function renderTable() {
    const body = $("listings-body");
    body.innerHTML = "";

    if (!state.filtered.length) {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td colspan="7">No listings match the current filters.</td>`;
      body.appendChild(tr);
      return;
    }

    state.filtered.forEach((row) => {
      const tr = document.createElement("tr");
      tr.tabIndex = 0;
      tr.dataset.id = row.id;
      tr.innerHTML = `
        <td>${escapeHtml(row.name || "")}</td>
        <td>${escapeHtml(row.destination || "")}</td>
        <td>${escapeHtml(row.country || "")}</td>
        <td>${escapeHtml(row.category || "")}</td>
        <td class="${row.address ? "" : "cell-muted"}">${escapeHtml(row.address || "—")}</td>
        <td class="${row.price ? "" : "cell-muted"}">${escapeHtml(row.price || "—")}</td>
        <td class="${row.website ? "" : "cell-muted"}">${
          row.website
            ? `<a href="${escapeAttr(row.website)}" target="_blank" rel="noopener noreferrer">Website</a>`
            : "—"
        }</td>
      `;
      tr.addEventListener("click", (event) => {
        if (event.target.closest("a")) return;
        openDetails(row);
      });
      tr.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          openDetails(row);
        }
      });
      body.appendChild(tr);
    });
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function escapeAttr(value) {
    return escapeHtml(value).replaceAll("'", "&#39;");
  }

  function openDetails(row) {
    const dialog = $("detail-dialog");
    const title = $("detail-title");
    const body = $("detail-body");
    title.textContent = row.name || "Listing details";
    body.innerHTML = "";

    const dl = document.createElement("dl");
    DETAIL_FIELDS.forEach(([key, label]) => {
      const value = row[key];
      if (value === null || value === undefined || value === "") return;
      const rowEl = document.createElement("div");
      rowEl.className = "detail-row";
      let content = escapeHtml(value);
      if (key === "website" || key === "source_url") {
        content = `<a href="${escapeAttr(value)}" target="_blank" rel="noopener noreferrer">${
          key === "website" ? "Open website" : "Open source page"
        }</a>`;
      } else if (key === "email") {
        content = `<a href="mailto:${escapeAttr(value)}">${escapeHtml(value)}</a>`;
      }
      rowEl.innerHTML = `<dt>${label}</dt><dd>${content}</dd>`;
      dl.appendChild(rowEl);
    });

    const lat = Number(row.latitude);
    const lon = Number(row.longitude);
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      const rowEl = document.createElement("div");
      rowEl.className = "detail-row";
      rowEl.innerHTML = `<dt>Coordinates</dt><dd>${lat.toFixed(5)}, ${lon.toFixed(5)}</dd>`;
      dl.appendChild(rowEl);
    }

    body.appendChild(dl);
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    }
  }

  function csvEscape(value) {
    if (value === null || value === undefined) return "";
    const text = String(value);
    if (/[",\n\r]/.test(text)) {
      return `"${text.replaceAll('"', '""')}"`;
    }
    return text;
  }

  function downloadFilteredCsv() {
    const headers = [
      "id",
      "name",
      "destination",
      "country",
      "category",
      "subcategory",
      "address",
      "price",
      "website",
      "phone",
      "email",
      "opening_hours",
      "latitude",
      "longitude",
      "source_url",
      "scraped_at",
    ];
    const lines = [headers.join(",")];
    state.filtered.forEach((row) => {
      lines.push(headers.map((key) => csvEscape(row[key])).join(","));
    });
    const blob = new Blob(["\uFEFF" + lines.join("\n")], {
      type: "text/csv;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "travel_listings_filtered.csv";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  }

  function renderMap() {
    const points = state.listings.filter(hasCoordinates);
    $("map-note").textContent = `${points.length.toLocaleString("en-US")} geocoded listings plotted.`;

    if (!window.L) {
      $("map-note").textContent = "Leaflet failed to load; map unavailable.";
      return;
    }

    if (state.map) {
      state.map.remove();
      state.map = null;
    }

    const map = L.map("coverage-map", { scrollWheelZoom: false }).setView([25, 20], 2);
    state.map = map;

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(map);

    if (!points.length) {
      $("map-note").textContent = "No valid coordinates available in this dataset.";
      return;
    }

    const bounds = [];
    points.forEach((row) => {
      const lat = Number(row.latitude);
      const lon = Number(row.longitude);
      bounds.push([lat, lon]);
      const marker = L.marker([lat, lon]).addTo(map);
      marker.bindPopup(
        `<strong>${escapeHtml(row.name || "")}</strong><br>${escapeHtml(
          row.destination || ""
        )}, ${escapeHtml(row.country || "")}<br>${escapeHtml(row.category || "")}`
      );
    });
    map.fitBounds(bounds, { padding: [24, 24], maxZoom: 5 });
  }

  function renderQuality() {
    const q = state.quality;
    const root = $("quality-kpis");
    root.innerHTML = "";
    [
      ["Raw Records", q.raw_records],
      ["Valid Records", q.valid_records],
      ["Invalid Records", q.invalid_records],
      ["Duplicates Detected", q.duplicates_detected],
      ["Duplicates Removed", q.duplicates_removed],
      ["Final Records", q.final_records],
    ].forEach(([label, value]) => root.appendChild(createKpi(label, formatNumber(value))));

    const bars = $("completeness-bars");
    bars.innerHTML = "";
    const completeness = q.field_completeness || {};
    COMPLETE_FIELDS.forEach(([key, label]) => {
      const stats = completeness[key] || {};
      const pct = Number(stats.completeness_pct || 0);
      const row = document.createElement("div");
      row.className = "completeness-row";
      row.innerHTML = `
        <span>${label}</span>
        <div class="bar-track" aria-hidden="true"><div class="bar-fill" style="width:${pct}%"></div></div>
        <span>${pct.toFixed(1)}%</span>
      `;
      bars.appendChild(row);
    });

    fillStatList($("by-country"), q.records_by_country || {});
    fillStatList($("by-destination"), q.records_by_destination || {});
    fillStatList($("by-category"), q.records_by_category || {});
  }

  function fillStatList(el, mapping) {
    el.innerHTML = "";
    Object.entries(mapping).forEach(([key, value]) => {
      const li = document.createElement("li");
      li.innerHTML = `<span>${escapeHtml(key)}</span><strong>${formatNumber(value)}</strong>`;
      el.appendChild(li);
    });
  }

  function showFatal(message) {
    const banner = document.createElement("div");
    banner.className = "error-banner";
    banner.textContent = message;
    $("overview").querySelector(".section-inner").prepend(banner);
  }

  function wireEvents() {
    ["search", "filter-country", "filter-destination", "filter-category"].forEach((id) => {
      $(id).addEventListener("input", applyFilters);
      $(id).addEventListener("change", applyFilters);
    });
    $("reset-filters").addEventListener("click", () => {
      $("search").value = "";
      ["filter-country", "filter-destination", "filter-category"].forEach((id) => {
        Array.from($(id).options).forEach((opt) => {
          opt.selected = false;
        });
      });
      applyFilters();
    });
    $("download-csv").addEventListener("click", downloadFilteredCsv);
  }

  function selectOptionByValue(selectEl, value) {
    Array.from(selectEl.options).forEach((opt) => {
      opt.selected = opt.value === value;
    });
  }

  function applyPresentationFocus() {
    const params = new URLSearchParams(window.location.search);
    const focus = params.get("focus");
    const country = params.get("country");
    const category = params.get("category");

    if (country) {
      selectOptionByValue($("filter-country"), country);
    }
    if (category) {
      selectOptionByValue($("filter-category"), category);
    }
    if (country || category) {
      applyFilters();
    }

    const targetId =
      focus === "explorer"
        ? "explorer"
        : focus === "quality"
          ? "quality"
          : focus === "map"
            ? "map"
            : focus === "pipeline"
              ? "pipeline"
              : null;

    if (targetId) {
      const target = $(targetId);
      if (target) {
        target.scrollIntoView({ behavior: "auto", block: "start" });
      }
    }

    if (params.get("details") === "1" && state.filtered.length) {
      openDetails(state.filtered[0]);
    }
  }

  async function init() {
    try {
      const [listingsRes, qualityRes] = await Promise.all([
        fetch("data/listings.json"),
        fetch("data/quality.json"),
      ]);
      if (!listingsRes.ok || !qualityRes.ok) {
        throw new Error("Could not load dashboard data files. Run scripts/build_dashboard_data.py first.");
      }
      state.listings = await listingsRes.json();
      state.quality = await qualityRes.json();
      if (!Array.isArray(state.listings) || !state.quality || typeof state.quality !== "object") {
        throw new Error("Dashboard data files are malformed.");
      }

      fillSelect($("filter-country"), uniqueSorted(state.listings, "country"));
      fillSelect($("filter-destination"), uniqueSorted(state.listings, "destination"));
      fillSelect($("filter-category"), uniqueSorted(state.listings, "category"));

      renderOverview();
      applyFilters();
      renderQuality();
      wireEvents();
      renderMap();
      applyPresentationFocus();
    } catch (error) {
      console.error(error);
      showFatal(error.message || "Failed to initialize dashboard.");
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
