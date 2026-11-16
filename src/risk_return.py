"""Risk vs return for four calendar windows from the combined USD price panel."""

from __future__ import annotations

import calendar
import json
import math
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PRICES = BASE_DIR / "data/financial_data/inputs/price_history_usd.csv"
ENRICHED = BASE_DIR / "data/financial_data/outputs/portfolio_enriched.csv"
OUT_CSV = BASE_DIR / "data/financial_data/outputs/risk_return.csv"
OUT_HTML = BASE_DIR / "images/risk_return.html"

META_COLS = [
    "Type",
    "AssetClass",
    "Sector",
    "Industry",
    "Industry_Group",
    "Country_Exposure",
    "Currency_Exposure",
    "Underlying_Symbol",
    "Is_ETF",
    "Description",
    "Weight_Pct",
]
COLOR_BY = [
    ("Sector", "Sector"),
    ("Industry_Group", "Industria"),
    ("AssetClass", "Clase"),
    ("Type", "Tipo"),
    ("Country_Exposure", "País"),
    ("Currency_Exposure", "Moneda"),
]
PALETTE = [
    "#1d4ed8",
    "#c2410c",
    "#0f766e",
    "#7c3aed",
    "#b45309",
    "#be185d",
    "#0369a1",
    "#4d7c0f",
    "#ea580c",
    "#2563eb",
    "#64748b",
    "#a16207",
]


def months_ago(day: date, months: int) -> date:
    month = day.month - months
    year = day.year
    while month <= 0:
        month += 12
        year -= 1
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day.day, last))


def windows_for(as_of: date, data_start: date) -> list[dict]:
    return [
        {
            "id": "full",
            "label": "12 meses",
            "start": data_start,
        },
        {
            "id": "ytd",
            "label": "YTD",
            "start": date(as_of.year, 1, 1),
        },
        {
            "id": "6m",
            "label": "6 meses",
            "start": months_ago(as_of, 6),
        },
        {
            "id": "30d",
            "label": "30 días",
            "start": as_of - timedelta(days=30),
        },
    ]


def stats(closes: pd.Series) -> dict | None:
    closes = closes.dropna()
    if len(closes) < 2:
        return None
    first = float(closes.iloc[0])
    last = float(closes.iloc[-1])
    if first <= 0:
        return None
    daily = closes.pct_change().dropna()
    daily = daily[daily.notna()]
    vol = float(daily.std(ddof=1) * math.sqrt(252)) if len(daily) >= 2 else None
    return {
        "n": int(len(closes)),
        "first_date": closes.index[0].strftime("%Y-%m-%d"),
        "last_date": closes.index[-1].strftime("%Y-%m-%d"),
        "total_return": last / first - 1,
        "vol_ann": vol,
    }


def build() -> pd.DataFrame:
    prices = pd.read_csv(PRICES, parse_dates=["date"])
    prices = prices.dropna(subset=["holding", "date", "close"])
    prices = prices.sort_values(["holding", "date"])
    as_of = prices["date"].max().date()
    data_start = prices["date"].min().date()

    meta = pd.read_csv(ENRICHED)[["Symbol"] + META_COLS].rename(columns={"Symbol": "holding"})

    rows = []
    for window in windows_for(as_of, data_start):
        sliced = prices[
            (prices["date"].dt.date >= window["start"])
            & (prices["date"].dt.date <= as_of)
        ]
        for holding, group in sliced.groupby("holding"):
            series = group.drop_duplicates("date").set_index("date")["close"].sort_index()
            computed = stats(series)
            if not computed:
                continue
            sample = group.iloc[-1]
            rows.append(
                {
                    "window": window["id"],
                    "window_label": window["label"],
                    "window_start": window["start"].isoformat(),
                    "as_of": as_of.isoformat(),
                    "holding": holding,
                    "symbol": sample["symbol"],
                    "market": sample["market"],
                    **computed,
                }
            )

    out = pd.DataFrame(rows).merge(meta, on="holding", how="left")
    spx = out["holding"] == "SPX"
    out.loc[spx, "Type"] = "INDEX"
    out.loc[spx, "Description"] = "S&P 500"
    out.loc[spx, "AssetClass"] = "Benchmark"
    out.loc[spx, "Sector"] = "Índice"
    out.loc[spx, "Industry"] = "Índice"
    out.loc[spx, "Industry_Group"] = "Índice"
    out.loc[spx, "Country_Exposure"] = "EE.UU."
    out.loc[spx, "Currency_Exposure"] = "USD"
    out.loc[spx, "Underlying_Symbol"] = "^GSPC"
    out.loc[spx, "Is_ETF"] = False
    out["is_benchmark"] = spx
    return out


def palettes_for(df: pd.DataFrame) -> dict:
    scales = {}
    for col, _label in COLOR_BY:
        values = sorted({str(v) for v in df[col].dropna().unique()})
        scale = {value: PALETTE[i % len(PALETTE)] for i, value in enumerate(values)}
        for bench in ("INDEX", "Benchmark", "Índice"):
            if bench in scale:
                scale[bench] = "#111827"
        scales[col] = scale
    return scales


def _cell(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, bool):
        return bool(value)
    return str(value)


def chart_payload(df: pd.DataFrame) -> dict:
    as_of = df["as_of"].iloc[0]
    palettes = palettes_for(df)
    windows = []
    for window_id, label in [
        ("full", "12 meses"),
        ("ytd", "YTD"),
        ("6m", "6 meses"),
        ("30d", "30 días"),
    ]:
        part = df[df["window"] == window_id]
        points = []
        for row in part.itertuples(index=False):
            points.append(
                {
                    "holding": row.holding,
                    "symbol": row.symbol,
                    "name": row.Description if pd.notna(row.Description) else row.holding,
                    "type": _cell(row.Type),
                    "assetClass": _cell(row.AssetClass),
                    "sector": _cell(row.Sector),
                    "industry": _cell(row.Industry),
                    "industryGroup": _cell(row.Industry_Group),
                    "country": _cell(row.Country_Exposure),
                    "currency": _cell(row.Currency_Exposure),
                    "underlying": _cell(row.Underlying_Symbol),
                    "etf": bool(row.Is_ETF) if pd.notna(row.Is_ETF) else False,
                    "keys": {
                        "Type": _cell(row.Type),
                        "AssetClass": _cell(row.AssetClass),
                        "Sector": _cell(row.Sector),
                        "Industry": _cell(row.Industry),
                        "Industry_Group": _cell(row.Industry_Group),
                        "Country_Exposure": _cell(row.Country_Exposure),
                        "Currency_Exposure": _cell(row.Currency_Exposure),
                    },
                    "benchmark": bool(row.is_benchmark),
                    "n": int(row.n),
                    "first": row.first_date,
                    "last": row.last_date,
                    "ret": None if pd.isna(row.total_return) else round(float(row.total_return), 6),
                    "vol": None if pd.isna(row.vol_ann) else round(float(row.vol_ann), 6),
                    "weight": None if pd.isna(row.Weight_Pct) else round(float(row.Weight_Pct), 4),
                }
            )
        windows.append(
            {
                "id": window_id,
                "label": label,
                "start": part["window_start"].iloc[0] if len(part) else None,
                "end": as_of,
                "points": points,
            }
        )
    return {
        "as_of": as_of,
        "colorBy": [{"id": col, "label": label} for col, label in COLOR_BY],
        "palettes": palettes,
        "windows": windows,
    }


def write_html(payload: dict) -> None:
    html = HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False))
    OUT_HTML.write_text(html, encoding="utf-8")


HTML = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width">
  <title>Riesgo vs retorno</title>
  <style>
    :root { color-scheme: light; }
    body {
      margin: 0;
      font-family: -apple-system, "Helvetica Neue", Arial, sans-serif;
      color: #111827;
      background: #fff;
    }
    .wrap { padding: 0.25rem 0.15rem 0.5rem; }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.4rem 0.75rem;
      margin-bottom: 0.6rem;
    }
    #tabs {
      display: flex;
      flex-wrap: wrap;
      gap: 0.4rem;
    }
    .color-by {
      margin-left: auto;
      font-size: 0.8rem;
      color: #4b5563;
      display: flex;
      align-items: center;
      gap: 0.4rem;
    }
    select {
      font: inherit;
      font-size: 0.85rem;
      border: 1px solid #d1d5db;
      border-radius: 8px;
      padding: 0.3rem 0.5rem;
      background: #fff;
    }
    button {
      border: 1px solid #d1d5db;
      background: #fff;
      border-radius: 999px;
      padding: 0.35rem 0.85rem;
      font: inherit;
      font-size: 0.85rem;
      cursor: pointer;
      color: #374151;
    }
    button[aria-pressed="true"] {
      background: #111827;
      border-color: #111827;
      color: #fff;
    }
    .meta {
      margin: 0 0 0.4rem;
      font-size: 0.8rem;
      color: #6b7280;
    }
    svg { width: 100%; height: auto; display: block; }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem 1.1rem;
      margin-top: 0.55rem;
      font-size: 0.78rem;
      color: #4b5563;
    }
    .swatch {
      display: inline-block;
      width: 9px;
      height: 9px;
      border-radius: 50%;
      margin-right: 0.35rem;
      vertical-align: middle;
    }
    .swatch.bench { border-radius: 1px; }
    #tip {
      position: absolute;
      display: none;
      pointer-events: none;
      background: #111827;
      color: #fff;
      font-size: 12px;
      line-height: 1.4;
      padding: 8px 10px;
      border-radius: 8px;
      max-width: 280px;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="toolbar">
      <div id="tabs"></div>
      <label class="color-by">Color
        <select id="colorBy"></select>
      </label>
    </div>
    <p class="meta" id="meta"></p>
    <div style="position: relative">
      <svg id="chart" viewBox="0 0 860 520" role="img"></svg>
      <div id="tip"></div>
    </div>
    <div class="legend" id="legend"></div>
  </div>
  <script>
    const DATA = __DATA__;
    const svg = document.getElementById("chart");
    const tabs = document.getElementById("tabs");
    const meta = document.getElementById("meta");
    const tip = document.getElementById("tip");
    const legend = document.getElementById("legend");
    const colorSelect = document.getElementById("colorBy");
    const NS = "http://www.w3.org/2000/svg";
    const M = { l: 62, r: 88, t: 18, b: 48 };
    const W = 860, H = 520;
    const innerW = W - M.l - M.r;
    const innerH = H - M.t - M.b;
    let current = DATA.windows[0].id;
    let colorBy = DATA.colorBy[0].id;

    function el(name, attrs) {
      const node = document.createElementNS(NS, name);
      Object.entries(attrs || {}).forEach(([k, v]) => node.setAttribute(k, v));
      return node;
    }
    function fmtPct(x) {
      if (x == null) return "—";
      return (x * 100).toLocaleString("es-AR", { maximumFractionDigits: 1, signDisplay: "exceptZero" }) + "%";
    }
    function nice(min, max, count) {
      if (min === max) { min -= 0.05; max += 0.05; }
      const span = max - min;
      const step0 = span / count;
      const mag = Math.pow(10, Math.floor(Math.log10(step0)));
      const err = step0 / mag;
      const step = mag * (err >= 7.5 ? 10 : err >= 3 ? 5 : err >= 1.5 ? 2 : 1);
      const nmin = Math.floor(min / step) * step;
      const nmax = Math.ceil(max / step) * step;
      const ticks = [];
      for (let v = nmin; v <= nmax + step * 0.5; v += step) ticks.push(v);
      return { min: nmin, max: nmax, ticks };
    }
    function windowById(id) {
      return DATA.windows.find(w => w.id === id);
    }
    function colorOf(p) {
      const key = (p.keys && p.keys[colorBy]) || "";
      return (DATA.palettes[colorBy] && DATA.palettes[colorBy][key]) || "#334155";
    }
    function renderLegend(pts) {
      const scale = DATA.palettes[colorBy] || {};
      const used = new Set(pts.map(p => (p.keys && p.keys[colorBy]) || ""));
      legend.replaceChildren();
      Object.keys(scale).forEach(name => {
        if (!used.has(name)) return;
        const item = document.createElement("span");
        const sw = document.createElement("i");
        sw.className = "swatch" + (name === "Índice" || name === "INDEX" || name === "Benchmark" ? " bench" : "");
        sw.style.background = scale[name];
        item.appendChild(sw);
        item.appendChild(document.createTextNode(name));
        legend.appendChild(item);
      });
    }
    function draw(id) {
      current = id;
      const win = windowById(id);
      const pts = win.points.filter(p => p.vol != null && p.ret != null);
      svg.replaceChildren();
      tabs.querySelectorAll("button").forEach(b => b.setAttribute("aria-pressed", b.dataset.id === id ? "true" : "false"));
      meta.textContent = win.start.split("-").reverse().join("/") + " – " + win.end.split("-").reverse().join("/") +
        " · retorno total del período vs vol. anualizada √252 · USD";
      renderLegend(pts);

      const xs = pts.map(p => p.vol);
      const ys = pts.map(p => p.ret);
      const xN = nice(0, Math.max(...xs, 0.05), 6);
      const yN = nice(Math.min(...ys, 0), Math.max(...ys, 0), 6);
      const x = v => M.l + (v - xN.min) / (xN.max - xN.min) * innerW;
      const y = v => M.t + (1 - (v - yN.min) / (yN.max - yN.min)) * innerH;

      svg.appendChild(el("rect", { width: W, height: H, fill: "#fff" }));
      xN.ticks.forEach(t => {
        svg.appendChild(el("line", { x1: x(t), x2: x(t), y1: M.t, y2: M.t + innerH, stroke: "#e5e7eb" }));
        const tx = el("text", { x: x(t), y: H - 18, "text-anchor": "middle", fill: "#6b7280", "font-size": "11" });
        tx.textContent = Math.round(t * 100) + "%";
        svg.appendChild(tx);
      });
      yN.ticks.forEach(t => {
        svg.appendChild(el("line", { x1: M.l, x2: M.l + innerW, y1: y(t), y2: y(t), stroke: t === 0 ? "#9ca3af" : "#e5e7eb" }));
        const ty = el("text", { x: M.l - 8, y: y(t) + 4, "text-anchor": "end", fill: "#6b7280", "font-size": "11" });
        ty.textContent = Math.round(t * 100) + "%";
        svg.appendChild(ty);
      });
      const xlab = el("text", { x: M.l + innerW / 2, y: H - 4, "text-anchor": "middle", fill: "#374151", "font-size": "12" });
      xlab.textContent = "Volatilidad anualizada";
      svg.appendChild(xlab);
      const ylab = el("text", { x: 16, y: M.t + innerH / 2, "text-anchor": "middle", fill: "#374151", "font-size": "12", transform: `rotate(-90 16 ${M.t + innerH / 2})` });
      ylab.textContent = "Retorno del período";
      svg.appendChild(ylab);

      const g = el("g", {});
      svg.appendChild(g);
      const ordered = [...pts].sort((a, b) => (a.benchmark ? 1 : 0) - (b.benchmark ? 1 : 0));
      ordered.forEach(p => {
        const r = p.benchmark ? 7 : Math.max(4, Math.min(14, 4 + Math.sqrt(p.weight || 0.4) * 1.6));
        const fill = colorOf(p);
        const node = p.benchmark
          ? el("rect", { x: x(p.vol) - r, y: y(p.ret) - r, width: r * 2, height: r * 2, fill, transform: `rotate(45 ${x(p.vol)} ${y(p.ret)})` })
          : el("circle", { cx: x(p.vol), cy: y(p.ret), r, fill, "fill-opacity": "0.88" });
        node.style.cursor = "pointer";
        node.addEventListener("mousemove", ev => showTip(ev, p));
        node.addEventListener("mouseleave", hideTip);
        g.appendChild(node);
        const label = el("text", {
          x: x(p.vol) + r + 3,
          y: y(p.ret) + 3,
          fill: "#111827",
          "font-size": p.benchmark ? "11" : "10",
          "font-weight": p.benchmark ? "700" : "500"
        });
        label.textContent = p.holding;
        g.appendChild(label);
      });
    }
    function showTip(ev, p) {
      tip.style.display = "block";
      tip.innerHTML = `<strong>${p.holding}</strong> · ${p.name}<br>${p.assetClass} · ${p.sector}<br>${p.industryGroup}${p.industry && p.industry !== p.industryGroup ? " · " + p.industry : ""}<br>${p.country} · ${p.currency}${p.etf ? " · ETF" : ""}<br>Retorno ${fmtPct(p.ret)} · Vol. ${fmtPct(p.vol)}<br>${p.n} ruedas`;
      const box = ev.currentTarget.ownerSVGElement.getBoundingClientRect();
      tip.style.left = (ev.clientX - box.left + 12) + "px";
      tip.style.top = (ev.clientY - box.top - 12) + "px";
    }
    function hideTip() { tip.style.display = "none"; }

    DATA.windows.forEach(w => {
      const b = document.createElement("button");
      b.type = "button";
      b.dataset.id = w.id;
      b.textContent = w.label;
      b.setAttribute("aria-pressed", w.id === current ? "true" : "false");
      b.addEventListener("click", () => draw(w.id));
      tabs.appendChild(b);
    });
    DATA.colorBy.forEach(opt => {
      const o = document.createElement("option");
      o.value = opt.id;
      o.textContent = opt.label;
      colorSelect.appendChild(o);
    });
    colorSelect.value = colorBy;
    colorSelect.addEventListener("change", () => {
      colorBy = colorSelect.value;
      draw(current);
    });
    draw(current);
  </script>
</body>
</html>
"""


def main() -> None:
    df = build()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    write_html(chart_payload(df))
    counts = df.groupby("window")["holding"].nunique().to_dict()
    print(f"{len(df)} rows -> {OUT_CSV.name}")
    print(f"html -> {OUT_HTML.relative_to(BASE_DIR)}")
    print("holdings by window:", counts)


if __name__ == "__main__":
    main()
