/** MapLibre map layer for Atlas. */

import { categoryColor, escapeHtml, hasCoordinates } from "./ui.js";

const STYLE_URL = "https://tiles.openfreemap.org/styles/liberty";

export class AtlasMap {
  constructor({ containerId, onSelect, onClusterClick }) {
    this.map = null;
    this.onSelect = onSelect;
    this.onClusterClick = onClusterClick;
    this.selectedId = null;
    this.ready = false;
    this._fitToken = 0;
    this.containerId = containerId;
  }

  async init() {
    if (!window.maplibregl) {
      throw new Error("MapLibre failed to load");
    }

    this.map = new maplibregl.Map({
      container: this.containerId,
      style: STYLE_URL,
      center: [10, 20],
      zoom: 1.4,
      attributionControl: true,
    });

    this.map.addControl(new maplibregl.NavigationControl({ visualizePitch: false }), "top-left");
    this.map.addControl(new maplibregl.ScaleControl({ maxWidth: 100 }), "bottom-left");

    await new Promise((resolve, reject) => {
      this.map.on("load", resolve);
      this.map.on("error", (event) => {
        if (!this.ready) reject(event.error || new Error("Map failed to load"));
      });
    });

    try {
      if (this.map.getProjection && this.map.setProjection) {
        this.map.setProjection({ type: "globe" });
      }
    } catch {
      // Globe projection is optional.
    }

    this._setupLayers();
    this._bindEvents();
    this.ready = true;
    this.map.resize();
  }

  _setupLayers() {
    this.map.addSource("places", {
      type: "geojson",
      data: emptyCollection(),
      cluster: true,
      clusterMaxZoom: 12,
      clusterRadius: 52,
    });

    this.map.addLayer({
      id: "clusters",
      type: "circle",
      source: "places",
      filter: ["has", "point_count"],
      paint: {
        "circle-color": [
          "step",
          ["get", "point_count"],
          "#99f6e4",
          15,
          "#5eead4",
          40,
          "#0f766e",
        ],
        "circle-radius": ["step", ["get", "point_count"], 18, 15, 22, 40, 28],
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
        "circle-opacity": 0.92,
      },
    });

    this.map.addLayer({
      id: "cluster-count",
      type: "symbol",
      source: "places",
      filter: ["has", "point_count"],
      layout: {
        "text-field": "{point_count_abbreviated}",
        "text-size": 12,
        "text-font": ["Noto Sans Regular"],
      },
      paint: {
        "text-color": "#134e4a",
      },
    });

    this.map.addLayer({
      id: "unclustered-point",
      type: "circle",
      source: "places",
      filter: ["!", ["has", "point_count"]],
      paint: {
        "circle-color": [
          "match",
          ["get", "category"],
          "see",
          categoryColor("see"),
          "do",
          categoryColor("do"),
          "eat",
          categoryColor("eat"),
          "drink",
          categoryColor("drink"),
          "sleep",
          categoryColor("sleep"),
          "buy",
          categoryColor("buy"),
          categoryColor("see"),
        ],
        "circle-radius": 7,
        "circle-stroke-width": 2,
        "circle-stroke-color": "#ffffff",
        "circle-opacity": 0.95,
      },
    });

    this.map.addLayer({
      id: "selected-point",
      type: "circle",
      source: "places",
      filter: ["==", ["get", "id"], ""],
      paint: {
        "circle-radius": 13,
        "circle-color": "#f59e0b",
        "circle-opacity": 0.25,
        "circle-stroke-width": 3,
        "circle-stroke-color": "#f59e0b",
      },
    });
  }

  _bindEvents() {
    this.map.on("click", "clusters", (event) => {
      const features = this.map.queryRenderedFeatures(event.point, { layers: ["clusters"] });
      const clusterId = features[0].properties.cluster_id;
      const source = this.map.getSource("places");
      source.getClusterExpansionZoom(clusterId).then((zoom) => {
        this.map.easeTo({
          center: features[0].geometry.coordinates,
          zoom,
          duration: 650,
        });
      });
      if (this.onClusterClick) this.onClusterClick();
    });

    this.map.on("click", "unclustered-point", (event) => {
      const feature = event.features?.[0];
      if (!feature) return;
      const id = feature.properties.id;
      if (this.onSelect) this.onSelect(id, { fromMap: true });
    });

    this.map.on("mouseenter", "clusters", () => {
      this.map.getCanvas().style.cursor = "pointer";
    });
    this.map.on("mouseleave", "clusters", () => {
      this.map.getCanvas().style.cursor = "";
    });
    this.map.on("mouseenter", "unclustered-point", () => {
      this.map.getCanvas().style.cursor = "pointer";
    });
    this.map.on("mouseleave", "unclustered-point", () => {
      this.map.getCanvas().style.cursor = "";
    });
  }

  setPlaces(listings, { fit = true } = {}) {
    if (!this.ready) return;
    const features = listings.filter(hasCoordinates).map((row) => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [Number(row.longitude), Number(row.latitude)],
      },
      properties: {
        id: row.id,
        name: row.name || "",
        category: row.category || "",
        destination: row.destination || "",
        country: row.country || "",
      },
    }));

    this.map.getSource("places").setData({
      type: "FeatureCollection",
      features,
    });

    if (fit) this.fitToFeatures(features);
  }

  fitToFeatures(features) {
    if (!features.length) return;
    const token = ++this._fitToken;
    const bounds = new maplibregl.LngLatBounds();
    features.forEach((feature) => bounds.extend(feature.geometry.coordinates));
    requestAnimationFrame(() => {
      if (token !== this._fitToken) return;
      this.map.fitBounds(bounds, {
        padding: { top: 60, bottom: 60, left: 60, right: 60 },
        maxZoom: features.length === 1 ? 12 : 4.8,
        duration: 850,
      });
    });
  }

  selectPlace(place, { fly = true } = {}) {
    this.selectedId = place?.id || null;
    if (!this.ready) return;
    this.map.setFilter("selected-point", ["==", ["get", "id"], this.selectedId || ""]);
    if (fly && place && hasCoordinates(place)) {
      this.map.flyTo({
        center: [Number(place.longitude), Number(place.latitude)],
        zoom: Math.max(this.map.getZoom(), 11.5),
        essential: true,
        duration: 900,
      });
    }
  }

  highlightHover(placeId) {
    if (!this.ready || !placeId) return;
    // Soft cue via popup is avoided; selection halo handles emphasis.
  }

  resize() {
    if (this.map) this.map.resize();
  }

  showPopup(place) {
    if (!this.ready || !place || !hasCoordinates(place)) return;
    new maplibregl.Popup({ offset: 14, closeButton: true })
      .setLngLat([Number(place.longitude), Number(place.latitude)])
      .setHTML(
        `<strong>${escapeHtml(place.name || "")}</strong><br>${escapeHtml(
          place.destination || ""
        )}, ${escapeHtml(place.country || "")}`
      )
      .addTo(this.map);
  }
}

function emptyCollection() {
  return { type: "FeatureCollection", features: [] };
}
