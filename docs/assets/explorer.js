/** Results panel: filters, cards, details. */

import {
  $,
  categoryLabel,
  escapeAttr,
  escapeHtml,
  hasCoordinates,
  highlightText,
  truncate,
  uniqueSorted,
} from "./ui.js";

const DETAIL_FIELDS = [
  ["description", "About"],
  ["address", "Address"],
  ["opening_hours", "Hours"],
  ["price", "Price"],
  ["phone", "Phone"],
  ["email", "Email"],
];

export class Explorer {
  constructor({ onSelect, onFilterChange }) {
    this.onSelect = onSelect;
    this.onFilterChange = onFilterChange;
    this.listings = [];
    this.filtered = [];
    this.selectedId = null;
    this.state = {
      q: "",
      country: new Set(),
      destination: new Set(),
      category: new Set(),
      website: false,
      coords: false,
      sort: "name",
    };
  }

  init(listings, initialState = {}) {
    this.listings = listings;
    if (initialState.q) this.state.q = initialState.q;
    (initialState.country || []).forEach((v) => this.state.country.add(v));
    (initialState.destination || []).forEach((v) => this.state.destination.add(v));
    (initialState.category || []).forEach((v) => this.state.category.add(v));
    this.state.website = Boolean(initialState.website);
    this.state.coords = Boolean(initialState.coords);
    this.state.sort = initialState.sort || "name";

    $("search-input").value = this.state.q;
    $("sort-select").value = this.state.sort;
    $("toggle-website").setAttribute("aria-pressed", String(this.state.website));
    $("toggle-coords").setAttribute("aria-pressed", String(this.state.coords));

    this._buildDropdowns();
    this._wire();
    this.applyFilters({ announce: false, fitMap: false });
    this.renderMetrics();
  }

  _wire() {
    $("search-input").addEventListener("input", () => {
      this.state.q = $("search-input").value;
      this.applyFilters({ fitMap: true });
    });
    $("search-form").addEventListener("submit", (event) => event.preventDefault());
    $("sort-select").addEventListener("change", () => {
      this.state.sort = $("sort-select").value;
      this.applyFilters({ fitMap: false });
    });
    $("toggle-website").addEventListener("click", () => {
      this.state.website = !this.state.website;
      $("toggle-website").setAttribute("aria-pressed", String(this.state.website));
      this.applyFilters({ fitMap: true });
    });
    $("toggle-coords").addEventListener("click", () => {
      this.state.coords = !this.state.coords;
      $("toggle-coords").setAttribute("aria-pressed", String(this.state.coords));
      this.applyFilters({ fitMap: true });
    });
    $("clear-filters").addEventListener("click", () => this.clearFilters());
    $("details-close").addEventListener("click", () => this.closeDetails());
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        this.closeDropdowns();
        if (!$("details-sheet").hidden) this.closeDetails();
      }
    });
    document.addEventListener("click", (event) => {
      if (!event.target.closest(".dropdown")) this.closeDropdowns();
    });
  }

  _buildDropdowns() {
    this._fillDropdown("country", uniqueSorted(this.listings, "country"));
    this._fillDropdown("destination", uniqueSorted(this.listings, "destination"));
    this._fillDropdown("category", uniqueSorted(this.listings, "category"));
  }

  _fillDropdown(key, values) {
    const root = document.querySelector(`.dropdown[data-filter="${key}"]`);
    const button = root.querySelector(".chip-btn");
    const menu = root.querySelector(".dropdown-menu");
    menu.innerHTML = "";
    values.forEach((value) => {
      const option = document.createElement("button");
      option.type = "button";
      option.className = "dropdown-option";
      option.setAttribute("role", "option");
      option.dataset.value = value;
      option.innerHTML = `<span>${escapeHtml(categoryLabel(value) === value ? value : categoryLabel(value))}</span>`;
      if (key === "category") {
        option.innerHTML = `<span>${escapeHtml(categoryLabel(value))}</span>`;
      } else {
        option.innerHTML = `<span>${escapeHtml(value)}</span>`;
      }
      option.addEventListener("click", (event) => {
        event.stopPropagation();
        const set = this.state[key];
        if (set.has(value)) set.delete(value);
        else set.add(value);
        option.setAttribute("aria-selected", String(set.has(value)));
        this._syncDropdownLabel(key);
        this.applyFilters({ fitMap: true });
      });
      option.setAttribute("aria-selected", String(this.state[key].has(value)));
      menu.appendChild(option);
    });
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      const open = button.getAttribute("aria-expanded") === "true";
      this.closeDropdowns();
      button.setAttribute("aria-expanded", String(!open));
      menu.hidden = open;
    });
    this._syncDropdownLabel(key);
  }

  _syncDropdownLabel(key) {
    const root = document.querySelector(`.dropdown[data-filter="${key}"]`);
    const button = root.querySelector(".chip-btn");
    const count = this.state[key].size;
    const labels = { country: "Country", destination: "City", category: "Category" };
    button.textContent = count ? `${labels[key]} · ${count}` : labels[key];
  }

  closeDropdowns() {
    document.querySelectorAll(".dropdown").forEach((root) => {
      root.querySelector(".chip-btn").setAttribute("aria-expanded", "false");
      root.querySelector(".dropdown-menu").hidden = true;
    });
  }

  clearFilters() {
    this.state.q = "";
    this.state.country.clear();
    this.state.destination.clear();
    this.state.category.clear();
    this.state.website = false;
    this.state.coords = false;
    $("search-input").value = "";
    $("toggle-website").setAttribute("aria-pressed", "false");
    $("toggle-coords").setAttribute("aria-pressed", "false");
    document.querySelectorAll(".dropdown-option").forEach((opt) => {
      opt.setAttribute("aria-selected", "false");
    });
    ["country", "destination", "category"].forEach((key) => this._syncDropdownLabel(key));
    this.applyFilters({ fitMap: true });
  }

  applyFilters({ fitMap = true, announce = true } = {}) {
    const q = this.state.q.trim().toLowerCase();
    this.filtered = this.listings.filter((row) => {
      if (this.state.country.size && !this.state.country.has(row.country)) return false;
      if (this.state.destination.size && !this.state.destination.has(row.destination)) return false;
      if (this.state.category.size && !this.state.category.has(row.category)) return false;
      if (this.state.website && !row.website) return false;
      if (this.state.coords && !hasCoordinates(row)) return false;
      if (!q) return true;
      const haystack = [
        row.name,
        row.destination,
        row.country,
        row.category,
        row.address,
        row.description,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase();
      return haystack.includes(q);
    });

    this.filtered.sort((a, b) => {
      const key = this.state.sort;
      return String(a[key] || "").localeCompare(String(b[key] || ""));
    });

    this.renderCards();
    this.renderActiveChips();
    if (announce) {
      $("result-count").textContent = `${this.filtered.length.toLocaleString("en-US")} place${
        this.filtered.length === 1 ? "" : "s"
      }`;
    }
    if (this.onFilterChange) {
      this.onFilterChange(this.getPublicState(), this.filtered, { fitMap });
    }
  }

  getPublicState() {
    return {
      q: this.state.q,
      country: [...this.state.country],
      destination: [...this.state.destination],
      category: [...this.state.category],
      website: this.state.website,
      coords: this.state.coords,
      sort: this.state.sort,
    };
  }

  renderMetrics() {
    const places = this.listings.length;
    const destinations = uniqueSorted(this.listings, "destination").length;
    const countries = uniqueSorted(this.listings, "country").length;
    const categories = uniqueSorted(this.listings, "category").length;
    $("product-metrics").innerHTML = [
      metric(places, "places"),
      metric(destinations, "destinations"),
      metric(countries, "countries"),
      metric(categories, "categories"),
    ].join("");
  }

  renderActiveChips() {
    const root = $("active-chips");
    const clear = $("clear-filters");
    const chips = [];
    this.state.country.forEach((v) => chips.push(["country", v]));
    this.state.destination.forEach((v) => chips.push(["destination", v]));
    this.state.category.forEach((v) => chips.push(["category", v]));
    if (this.state.website) chips.push(["website", "Has website"]);
    if (this.state.coords) chips.push(["coords", "On map"]);
    if (!chips.length && !this.state.q) {
      root.hidden = true;
      clear.hidden = true;
      root.innerHTML = "";
      return;
    }
    root.hidden = false;
    clear.hidden = false;
    root.innerHTML = chips
      .map(
        ([key, value]) => `
      <span class="active-chip">
        ${escapeHtml(key === "category" ? categoryLabel(value) : value)}
        <button type="button" data-key="${escapeAttr(key)}" data-value="${escapeAttr(value)}" aria-label="Remove filter">×</button>
      </span>`
      )
      .join("");
    root.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        const key = btn.dataset.key;
        const value = btn.dataset.value;
        if (key === "website") {
          this.state.website = false;
          $("toggle-website").setAttribute("aria-pressed", "false");
        } else if (key === "coords") {
          this.state.coords = false;
          $("toggle-coords").setAttribute("aria-pressed", "false");
        } else {
          this.state[key].delete(value);
          const opt = document.querySelector(
            `.dropdown[data-filter="${key}"] .dropdown-option[data-value="${CSS.escape(value)}"]`
          );
          if (opt) opt.setAttribute("aria-selected", "false");
          this._syncDropdownLabel(key);
        }
        this.applyFilters({ fitMap: true });
      });
    });
  }

  renderCards() {
    const root = $("cards");
    if (!this.filtered.length) {
      root.innerHTML = `<div class="empty-state">No places match these filters. Try clearing a filter or broadening your search.</div>`;
      return;
    }
    root.innerHTML = this.filtered
      .slice(0, 250)
      .map((row) => this._cardHtml(row))
      .join("");
    if (this.filtered.length > 250) {
      root.insertAdjacentHTML(
        "beforeend",
        `<div class="empty-state">Showing the first 250 of ${this.filtered.length.toLocaleString("en-US")} matches. Narrow filters to refine.</div>`
      );
    }
    root.querySelectorAll(".place-card").forEach((card) => {
      const id = card.dataset.id;
      card.addEventListener("click", () => this.selectById(id, { fromCard: true }));
      card.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          this.selectById(id, { fromCard: true });
        }
      });
      card.addEventListener("mouseenter", () => card.classList.add("is-hovered"));
      card.addEventListener("mouseleave", () => card.classList.remove("is-hovered"));
    });
    this._syncSelectedCard();
  }

  _cardHtml(row) {
    const selected = row.id === this.selectedId ? " is-selected" : "";
    const badges = [
      `<span class="badge badge-cat ${escapeAttr(row.category || "")}">${escapeHtml(
        categoryLabel(row.category)
      )}</span>`,
    ];
    if (row.price) badges.push(`<span class="badge">${escapeHtml(truncate(row.price, 40))}</span>`);
    if (row.website) badges.push(`<span class="badge">Website</span>`);
    if (hasCoordinates(row)) badges.push(`<span class="badge">Mapped</span>`);
    return `
      <article class="place-card${selected}" data-id="${escapeAttr(row.id)}" tabindex="0" role="button" aria-pressed="${
        row.id === this.selectedId ? "true" : "false"
      }">
        <div class="card-top">
          <div>
            <h3 class="card-title">${highlightText(row.name || "Untitled place", this.state.q)}</h3>
            <p class="card-meta">${escapeHtml(row.destination || "")}${
              row.country ? `, ${escapeHtml(row.country)}` : ""
            }</p>
          </div>
        </div>
        ${
          row.description
            ? `<p class="card-desc">${escapeHtml(truncate(row.description, 150))}</p>`
            : ""
        }
        <div class="card-footer">${badges.join("")}</div>
      </article>`;
  }

  selectById(id, options = {}) {
    const place = this.listings.find((row) => row.id === id);
    if (!place) return;
    this.selectedId = id;
    this._syncSelectedCard();
    this.openDetails(place);
    const card = document.querySelector(`.place-card[data-id="${CSS.escape(id)}"]`);
    if (card && options.fromMap) {
      card.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
    if (this.onSelect) this.onSelect(place, options);
  }

  filterToIds(ids) {
    const allow = new Set(ids);
    this.filtered = this.listings.filter((row) => allow.has(row.id));
    this.renderCards();
    $("result-count").textContent = `${this.filtered.length.toLocaleString("en-US")} place${
      this.filtered.length === 1 ? "" : "s"
    } from Nova`;
    if (this.onFilterChange) {
      this.onFilterChange(this.getPublicState(), this.filtered, { fitMap: true });
    }
  }

  openDetails(place) {
    const sheet = $("details-sheet");
    $("details-kicker").textContent = `${categoryLabel(place.category)} · ${
      place.destination || ""
    }${place.country ? `, ${place.country}` : ""}`;
    $("details-title").textContent = place.name || "Place";
    const body = $("details-body");
    body.innerHTML = "";
    DETAIL_FIELDS.forEach(([key, label]) => {
      const value = place[key];
      if (value === null || value === undefined || value === "") return;
      const row = document.createElement("div");
      row.className = "detail-row";
      let content = escapeHtml(value);
      if (key === "email") {
        content = `<a href="mailto:${escapeAttr(value)}">${escapeHtml(value)}</a>`;
      }
      row.innerHTML = `<dt>${label}</dt><dd>${content}</dd>`;
      body.appendChild(row);
    });
    if (hasCoordinates(place)) {
      const row = document.createElement("div");
      row.className = "detail-row";
      row.innerHTML = `<dt>Coordinates</dt><dd>${Number(place.latitude).toFixed(5)}, ${Number(
        place.longitude
      ).toFixed(5)}</dd>`;
      body.appendChild(row);
    }
    const actions = $("details-actions");
    actions.innerHTML = "";
    if (place.website) {
      actions.insertAdjacentHTML(
        "beforeend",
        `<a class="btn btn-accent" href="${escapeAttr(
          place.website
        )}" target="_blank" rel="noopener noreferrer">Visit website</a>`
      );
    }
    if (place.source_url) {
      actions.insertAdjacentHTML(
        "beforeend",
        `<a class="btn btn-ghost" href="${escapeAttr(
          place.source_url
        )}" target="_blank" rel="noopener noreferrer">View source</a>`
      );
    }
    sheet.hidden = false;
  }

  closeDetails() {
    $("details-sheet").hidden = true;
  }

  _syncSelectedCard() {
    document.querySelectorAll(".place-card").forEach((card) => {
      const selected = card.dataset.id === this.selectedId;
      card.classList.toggle("is-selected", selected);
      card.setAttribute("aria-pressed", String(selected));
    });
  }
}

function metric(value, label) {
  return `<span class="metric-pill"><strong>${value.toLocaleString("en-US")}</strong> ${label}</span>`;
}
