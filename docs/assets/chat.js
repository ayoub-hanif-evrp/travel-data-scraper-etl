/** Nova AI assistant UI. */

import { $, categoryLabel, escapeAttr, escapeHtml } from "./ui.js";

export class NovaChat {
  constructor({ onShowPlace, onShowAll }) {
    this.onShowPlace = onShowPlace;
    this.onShowAll = onShowAll;
    this.open = false;
    this.history = [];
    this.available = false;
    this.busy = false;
  }

  init(suggestions = []) {
    this._wire();
    this.setSuggestions(suggestions);
    this.resetWelcome();
    this.refreshHealth();
  }

  _wire() {
    const openers = [$("nova-launcher"), $("btn-nova-header")];
    openers.forEach((btn) => btn?.addEventListener("click", () => this.toggle()));
    $("nova-close").addEventListener("click", () => this.close());
    $("nova-clear").addEventListener("click", () => this.clear());
    $("nova-form").addEventListener("submit", (event) => {
      event.preventDefault();
      this.send();
    });
    $("nova-input").addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        this.send();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && this.open) this.close();
    });
  }

  setSuggestions(items) {
    const root = $("nova-suggestions");
    root.innerHTML = "";
    items.forEach((text) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "suggestion-chip";
      btn.textContent = text;
      btn.addEventListener("click", () => {
        $("nova-input").value = text;
        this.openPanel();
        this.send();
      });
      root.appendChild(btn);
    });
  }

  async refreshHealth() {
    const status = $("nova-status");
    try {
      const res = await fetch("/api/health", { headers: { Accept: "application/json" } });
      if (!res.ok) throw new Error("unavailable");
      const data = await res.json();
      this.available = Boolean(data.ai_configured);
      status.textContent = this.available ? "Online" : "AI unavailable";
      status.className = `nova-status ${this.available ? "is-online" : "is-offline"}`;
      document.querySelectorAll(".nova-dot").forEach((dot) => {
        dot.style.background = this.available ? "#34d399" : "#f59e0b";
      });
    } catch {
      this.available = false;
      status.textContent = "AI unavailable in static mode";
      status.className = "nova-status is-offline";
    }
  }

  toggle() {
    if (this.open) this.close();
    else this.openPanel();
  }

  openPanel() {
    this.open = true;
    $("nova-panel").hidden = false;
    $("nova-launcher").setAttribute("aria-expanded", "true");
    $("btn-nova-header")?.setAttribute("aria-expanded", "true");
    $("nova-input").focus();
  }

  close() {
    this.open = false;
    $("nova-panel").hidden = true;
    $("nova-launcher").setAttribute("aria-expanded", "false");
    $("btn-nova-header")?.setAttribute("aria-expanded", "false");
  }

  clear() {
    this.history = [];
    $("nova-messages").innerHTML = "";
    this.resetWelcome();
  }

  resetWelcome() {
    this.appendAssistant(
      "Hi, I’m Nova — your Atlas travel assistant. Ask about places in this demo dataset. I won’t invent bookings, ratings, or facts that aren’t here."
    );
  }

  appendAssistant(text, matches = []) {
    const root = $("nova-messages");
    const bubble = document.createElement("div");
    bubble.className = "bubble bubble-assistant";
    bubble.textContent = text;
    if (matches?.length) {
      const wrap = document.createElement("div");
      wrap.className = "ai-cards";
      matches.slice(0, 8).forEach((match) => {
        const card = document.createElement("div");
        card.className = "ai-card";
        card.innerHTML = `
          <strong>${escapeHtml(match.name || "Place")}</strong>
          <span>${escapeHtml(categoryLabel(match.category))} · ${escapeHtml(
            match.destination || ""
          )}${match.country ? `, ${escapeHtml(match.country)}` : ""}</span>
          <button type="button" class="btn btn-ghost btn-sm" data-id="${escapeAttr(
            match.id
          )}">Show on map</button>`;
        wrap.appendChild(card);
      });
      if (matches.length > 1) {
        const all = document.createElement("button");
        all.type = "button";
        all.className = "btn btn-accent btn-sm";
        all.textContent = "Show all results";
        all.addEventListener("click", () => {
          if (this.onShowAll) this.onShowAll(matches.map((m) => m.id));
          this.close();
        });
        wrap.appendChild(all);
      }
      bubble.appendChild(wrap);
      wrap.querySelectorAll("button[data-id]").forEach((btn) => {
        btn.addEventListener("click", () => {
          if (this.onShowPlace) this.onShowPlace(btn.dataset.id);
          this.close();
        });
      });
    }
    root.appendChild(bubble);
    root.scrollTop = root.scrollHeight;
  }

  appendUser(text) {
    const root = $("nova-messages");
    const bubble = document.createElement("div");
    bubble.className = "bubble bubble-user";
    bubble.textContent = text;
    root.appendChild(bubble);
    root.scrollTop = root.scrollHeight;
  }

  appendError(text, retryPayload = null) {
    const root = $("nova-messages");
    const bubble = document.createElement("div");
    bubble.className = "bubble bubble-assistant bubble-error";
    bubble.textContent = text;
    if (retryPayload) {
      const retry = document.createElement("button");
      retry.type = "button";
      retry.className = "btn btn-ghost btn-sm";
      retry.textContent = "Retry";
      retry.addEventListener("click", () => this.send(retryPayload));
      bubble.appendChild(document.createElement("br"));
      bubble.appendChild(retry);
    }
    root.appendChild(bubble);
    root.scrollTop = root.scrollHeight;
  }

  showTyping() {
    const root = $("nova-messages");
    const bubble = document.createElement("div");
    bubble.className = "bubble bubble-assistant";
    bubble.id = "nova-typing";
    bubble.innerHTML = `<span class="typing" aria-label="Nova is typing"><i></i><i></i><i></i></span>`;
    root.appendChild(bubble);
    root.scrollTop = root.scrollHeight;
  }

  hideTyping() {
    $("nova-typing")?.remove();
  }

  async send(preset = null) {
    if (this.busy) return;
    const input = $("nova-input");
    const message = (preset ?? input.value).trim();
    if (!message) return;
    if (message.length > 1400) {
      this.appendError("Please keep messages under 1400 characters.");
      return;
    }
    input.value = "";
    this.appendUser(message);
    this.history.push({ role: "user", content: message });
    if (!this.available) {
      this.appendError(
        "AI assistant unavailable. Start the app with `python server.py` and configure GROQ_API_KEY in your local .env."
      );
      return;
    }

    this.busy = true;
    this.showTyping();
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          message,
          history: this.history.slice(-8),
        }),
      });
      const data = await res.json().catch(() => ({}));
      this.hideTyping();
      if (!res.ok) {
        this.appendError(data.detail || data.error || "Nova could not answer right now.", message);
        return;
      }
      const answer = data.answer || "I could not find a useful answer in this dataset.";
      const matches = Array.isArray(data.matches) ? data.matches : [];
      this.history.push({ role: "assistant", content: answer });
      this.appendAssistant(answer, matches);
    } catch {
      this.hideTyping();
      this.appendError("Network error while contacting Nova.", message);
    } finally {
      this.busy = false;
    }
  }
}
