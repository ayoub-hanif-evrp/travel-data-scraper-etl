/** Atlas application bootstrap. */

import { NovaChat } from "./chat.js";
import { Explorer } from "./explorer.js";
import { AtlasMap } from "./map.js";
import { $, detectModKeyHint, readQueryState, writeQueryState } from "./ui.js";

const state = {
  listings: [],
  byId: new Map(),
};

async function loadListings() {
  const res = await fetch("data/listings.json", { headers: { Accept: "application/json" } });
  if (!res.ok) {
    throw new Error("Could not load place data. Run the demo pipeline first.");
  }
  const data = await res.json();
  if (!Array.isArray(data)) throw new Error("Place data file is malformed.");
  return data;
}

function buildSuggestions(listings) {
  const cities = [...new Set(listings.map((r) => r.destination).filter(Boolean))];
  const picks = [];
  if (cities.includes("Paris")) picks.push("Places to eat in Paris");
  if (cities.includes("Marrakech")) picks.push("Things to see in Marrakech");
  if (cities.includes("Bangkok")) picks.push("Explore Bangkok");
  if (cities.includes("Rome")) picks.push("Show stays in Rome");
  if (cities.includes("Tokyo")) picks.push("Find things to do in Tokyo");
  if (cities.includes("Sydney")) picks.push("What can I visit in Sydney?");
  return picks.slice(0, 4);
}

function setupKeyboard(searchInput) {
  const hint = $("search-hint");
  if (hint) hint.textContent = detectModKeyHint();
  document.addEventListener("keydown", (event) => {
    const mod = event.metaKey || event.ctrlKey;
    if (mod && event.key.toLowerCase() === "k") {
      event.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
    if (event.key === "Escape" && document.activeElement === searchInput) {
      searchInput.value = "";
      searchInput.dispatchEvent(new Event("input", { bubbles: true }));
      searchInput.blur();
    }
  });
}

function setupMobileNav(map) {
  const workspace = document.querySelector(".workspace");
  const btn = $("btn-mobile-nav");
  const label = $("mobile-nav-label");
  btn?.addEventListener("click", () => {
    const next = workspace.dataset.mobileView === "list" ? "map" : "list";
    workspace.dataset.mobileView = next;
    label.textContent = next === "list" ? "Map" : "List";
    if (next === "map") {
      requestAnimationFrame(() => map.resize());
    }
  });
  window.addEventListener("resize", () => map.resize());
}

async function main() {
  const mapStatus = $("map-status");
  mapStatus.hidden = false;
  mapStatus.textContent = "Loading map…";

  let listings;
  try {
    listings = await loadListings();
  } catch (error) {
    $("cards").innerHTML = `<div class="empty-state">${error.message}</div>`;
    mapStatus.textContent = "Place data unavailable";
    return;
  }

  state.listings = listings;
  state.byId = new Map(listings.map((row) => [row.id, row]));

  const map = new AtlasMap({
    containerId: "map",
    onSelect: (id) => explorer.selectById(id, { fromMap: true }),
  });

  const explorer = new Explorer({
    onSelect: (place, options) => {
      map.selectPlace(place, { fly: Boolean(options?.fromCard || options?.fromAi || options?.fromMap) });
    },
    onFilterChange: (publicState, filtered, meta) => {
      writeQueryState(publicState);
      map.setPlaces(filtered, { fit: Boolean(meta?.fitMap) });
    },
  });

  const nova = new NovaChat({
    onShowPlace: (id) => {
      document.querySelector(".workspace").dataset.mobileView = "map";
      $("mobile-nav-label").textContent = "List";
      map.resize();
      explorer.selectById(id, { fromAi: true });
    },
    onShowAll: (ids) => {
      document.querySelector(".workspace").dataset.mobileView = "map";
      $("mobile-nav-label").textContent = "List";
      map.resize();
      explorer.filterToIds(ids);
    },
  });

  setupKeyboard($("search-input"));
  setupMobileNav(map);
  $("btn-explore")?.addEventListener("click", () => {
    explorer.clearFilters();
    $("search-input").focus();
  });

  try {
    await map.init();
    mapStatus.hidden = true;
  } catch (error) {
    mapStatus.hidden = false;
    mapStatus.textContent = "Map unavailable — list exploration still works";
    console.error(error);
  }

  explorer.init(listings, readQueryState());
  nova.init(buildSuggestions(listings));
}

main().catch((error) => {
  console.error(error);
  $("cards").innerHTML = `<div class="empty-state">Atlas failed to start.</div>`;
});
