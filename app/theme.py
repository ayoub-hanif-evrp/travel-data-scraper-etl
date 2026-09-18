"""Shared visual theme for Travel Data Explorer."""

from __future__ import annotations

from nicegui import ui

# Chart palette — teal / slate / amber (no purple defaults)
CHART_COLORS = [
    "#0f766e",
    "#0369a1",
    "#b45309",
    "#475569",
    "#0e7490",
    "#a16207",
]

PAGE_SHELL = "tde-page w-full max-w-6xl mx-auto px-5 py-8 gap-6"
SECTION_CARD = "tde-card w-full"
PANEL_CARD = "tde-card flex-1 min-w-[280px]"


def apply_theme() -> None:
    ui.add_head_html(
        """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap" rel="stylesheet">
        """,
        shared=True,
    )
    ui.add_css(
        """
:root {
  --tde-ink: #0f172a;
  --tde-muted: #64748b;
  --tde-teal: #0f766e;
  --tde-teal-deep: #115e59;
  --tde-sky: #0369a1;
  --tde-sand: #f0f7f6;
  --tde-card: #ffffff;
  --tde-line: #d8e4e2;
  --tde-header: #0b3d3a;
}

body {
  margin: 0;
  color: var(--tde-ink);
  font-family: "DM Sans", "Segoe UI", sans-serif;
  background:
    radial-gradient(1200px 500px at 10% -10%, #d7efe9 0%, transparent 55%),
    radial-gradient(900px 400px at 100% 0%, #dbeafe 0%, transparent 50%),
    linear-gradient(180deg, #f4faf8 0%, #eef2f6 100%);
  min-height: 100vh;
}

a { color: var(--tde-sky); }

.tde-header {
  background: linear-gradient(135deg, #0b3d3a 0%, #0f5c56 55%, #0e7490 100%);
  border-bottom: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 8px 24px rgba(11, 61, 58, 0.25);
}

.tde-brand {
  font-family: "Fraunces", Georgia, serif;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.15;
}

.tde-nav-link {
  color: rgba(255,255,255,0.82) !important;
  text-decoration: none !important;
  padding: 0.4rem 0.85rem;
  border-radius: 999px;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background 0.15s ease, color 0.15s ease;
}

.tde-nav-link:hover {
  background: rgba(255,255,255,0.12);
  color: #fff !important;
}

.tde-nav-link.active {
  background: rgba(255,255,255,0.2);
  color: #fff !important;
  font-weight: 600;
}

.tde-page-title {
  font-family: "Fraunces", Georgia, serif;
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--tde-ink);
  letter-spacing: -0.02em;
  margin: 0;
}

.tde-page-sub {
  color: var(--tde-muted);
  font-size: 0.9rem;
  margin-top: -0.35rem;
}

.tde-card {
  background: var(--tde-card);
  border: 1px solid var(--tde-line);
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.04);
  padding: 1.15rem 1.25rem;
}

.tde-metric {
  position: relative;
  overflow: hidden;
  background: linear-gradient(180deg, #ffffff 0%, #f7fbfa 100%);
  border: 1px solid var(--tde-line);
  border-radius: 16px;
  padding: 1rem 1.1rem 1rem 1.2rem;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.035);
  min-width: 150px;
  flex: 1;
}

.tde-metric::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, var(--tde-teal), var(--tde-sky));
}

.tde-metric-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--tde-muted);
  font-weight: 600;
}

.tde-metric-value {
  font-family: "Fraunces", Georgia, serif;
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--tde-ink);
  margin-top: 0.2rem;
  line-height: 1.1;
}

.tde-etl-banner {
  background: linear-gradient(90deg, #ecfdf5 0%, #f0f9ff 100%);
  border: 1px solid #cce7e1;
  border-radius: 14px;
  padding: 0.9rem 1.1rem;
}

.tde-section-title {
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 0.65rem;
  font-size: 0.95rem;
}

.tde-step-num {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--tde-teal-deep), var(--tde-sky));
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 700;
  flex-shrink: 0;
}

.tde-empty {
  background: white;
  border: 1px dashed #b6cdc8;
  border-radius: 18px;
  padding: 2.5rem;
  text-align: center;
  max-width: 36rem;
  margin: 4rem auto 0;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.04);
}

.q-field--outlined .q-field__control {
  border-radius: 12px !important;
  background: white;
}

.q-btn {
  border-radius: 10px !important;
  font-weight: 600 !important;
  text-transform: none !important;
}
        """,
        shared=True,
    )


def page_heading(title: str, subtitle: str | None = None) -> None:
    ui.label(title).classes("tde-page-title")
    if subtitle:
        ui.label(subtitle).classes("tde-page-sub")
