"""Copy the files that feed index.html charts into data/financial_data/index_charts/.

That folder is gitignored with the rest of data/. Re-run after regenerating outputs:

    uv run python src/pack_index_charts.py
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path

from datawrapper_risk_return import WINDOW_LABELS, build_frame

BASE_DIR = Path(__file__).resolve().parent.parent
DATA = BASE_DIR / "data" / "financial_data"
OUT = DATA / "index_charts"
OUTPUTS = DATA / "outputs"
IMAGES = BASE_DIR / "images"

CHARTS = [
    {
        "id": "01_kpis",
        "title": "KPIs del header",
        "on_page": "Valores hardcodeados en index.html (YTD ARS, MEP, real, 25 tickers)",
        "upload_to": "nada — copiar los números al HTML",
        "files": [
            OUTPUTS / "comparacion_portafolio_vs_inflacion.csv",
            OUTPUTS / "portafolio_vs_inflacion_con_usd.csv",
        ],
    },
    {
        "id": "02_industria_rawgraphs",
        "title": "Exposición por industria",
        "on_page": "images/industry_group.svg",
        "upload_to": "RAWGraphs (ya exportado a SVG)",
        "files": [
            OUTPUTS / "portfolio_by_industry_group.csv",
            IMAGES / "industry_group.svg",
        ],
    },
    {
        "id": "03_flourish_pesos_inflacion",
        "title": "Mis pesos: portafolio vs inflación",
        "on_page": "Flourish visualisation/30757619",
        "upload_to": "Flourish 30757619",
        "files": [OUTPUTS / "portafolio_ytd_presentacion.csv"],
    },
    {
        "id": "04_flourish_usd_sp500",
        "title": "En dólares: portafolio vs S&P 500",
        "on_page": "Flourish visualisation/30928132",
        "upload_to": "Flourish 30928132",
        "files": [OUTPUTS / "portafolio_usd_vs_sp500_presentacion.csv"],
    },
    {
        "id": "05_tableau_treemap",
        "title": "Treemap diario ARS/USD",
        "on_page": "Tableau Public Treemap_groups/DASHBOARD",
        "upload_to": "Tableau Public workbook Treemap_groups",
        "files": [OUTPUTS / "portfolio_enriched.csv"],
    },
    {
        "id": "06_datawrapper_riesgo_retorno",
        "title": "Riesgo vs retorno (USD)",
        "on_page": "Datawrapper v6pot / zsuoH / P7Gy0 / cqy0r",
        "upload_to": "Datawrapper (un CSV por ventana)",
        "files": [OUTPUTS / "risk_return.csv"],
    },
]


README = """# Chart pack — index.html

Archivos listos para Drive / Flourish / Tableau / Datawrapper / RAWGraphs.
Vive en `data/financial_data/index_charts/` (gitignored, no commitear).

Generar de nuevo: `uv run python src/pack_index_charts.py`

## Qué hay en la página

| # | Sección en index.html | Herramienta | Archivo a subir |
|---|---|---|---|
| 01 | KPIs (YTD ARS / MEP / IPC / 25 tickers) | HTML fijo | `comparacion_portafolio_vs_inflacion.csv` (origen de los %) |
| 02 | Exposición por industria | RAWGraphs → SVG | `portfolio_by_industry_group.csv` |
| 03 | Portafolio vs inflación | Flourish 30757619 | `portafolio_ytd_presentacion.csv` |
| 04 | Portafolio USD vs S&P 500 | Flourish 30928132 | `portafolio_usd_vs_sp500_presentacion.csv` |
| 05 | Treemap diario | Tableau Public `Treemap_groups` | `portfolio_enriched.csv` |
| 06 | Riesgo vs retorno | Datawrapper v6pot, zsuoH, P7Gy0, cqy0r | `dw_full.csv`, `dw_ytd.csv`, `dw_6m.csv`, `dw_30d.csv` |

## Inputs vs outputs (pipeline)

```
inputs/
  iol_portfolio_argentina.csv          snapshot 30/10/2026
  iol_asset_metadata.csv
  iol_aum_twr_daily_nov2025_oct2026.csv
  ipc_indec_mensual_oct2025_sep2026.csv
  holdings_usd_search_map.csv
  price_history_usd.csv                panel 365d (IOL + Yahoo SPX)
      └── price_history/*.csv

scripts/
  enrich_portfolio.py  → portfolio_enriched.csv
                       → portfolio_by_industry_group.csv   [02]
  returns.py / base_100.py
                       → comparacion_portafolio_vs_inflacion.csv  [01]
                       → portafolio_vs_inflacion_con_usd.csv
                       → portafolio_ytd_presentacion.csv          [03]
  usd_vs_sp500.py      → portafolio_usd_vs_sp500_presentacion.csv [04]
  risk_return.py       → risk_return.csv
  datawrapper_risk_return.py
                       → dw_*.csv (este pack) + publish API        [06]
```

`portfolio_enriched.csv` también alimenta peso y taxonomía del scatter [06]
y el treemap [05].

## No copiar a Drive (no se suben a las tools)

- `data/financial_data/inputs/price_history/` (26 series crudas)
- `MEP_FX.csv`, `holdings_usd_search_map.csv`
- `images/risk_return.html` (ya no está embebido; la home usa Datawrapper)
- `images/finance.svg`, `FINANCE2.svg`, `bumpchart.svg` (no están en index.html)

## Datawrapper IDs

| Ventana | Chart ID | CSV en 06_ |
|---|---|---|
| 12 meses | v6pot | dw_full.csv |
| YTD 2026 | zsuoH | dw_ytd.csv |
| 6 meses | P7Gy0 | dw_6m.csv |
| 30 días | cqy0r | dw_30d.csv |

SPX no entra a Datawrapper: no tiene `Weight_Pct` de cartera.
"""


def copy_into(dest: Path, src: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / src.name
    shutil.copy2(src, target)
    return target


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    manifest_rows = []
    for chart in CHARTS:
        folder = OUT / chart["id"]
        folder.mkdir()
        for src in chart["files"]:
            if not src.exists():
                raise SystemExit(f"Missing {src}")
            copy_into(folder, src)
            manifest_rows.append(
                {
                    "folder": chart["id"],
                    "title": chart["title"],
                    "on_page": chart["on_page"],
                    "upload_to": chart["upload_to"],
                    "file": src.name,
                    "bytes": src.stat().st_size,
                }
            )

        if chart["id"] == "06_datawrapper_riesgo_retorno":
            for window, label in WINDOW_LABELS.items():
                frame = build_frame(window)
                name = f"dw_{window}.csv"
                path = folder / name
                frame.to_csv(path, index=False)
                manifest_rows.append(
                    {
                        "folder": chart["id"],
                        "title": f"{chart['title']} · {label}",
                        "on_page": chart["on_page"],
                        "upload_to": chart["upload_to"],
                        "file": name,
                        "bytes": path.stat().st_size,
                    }
                )

    (OUT / "README.md").write_text(README, encoding="utf-8")
    with (OUT / "00_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["folder", "title", "on_page", "upload_to", "file", "bytes"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    print(f"{len(manifest_rows)} files -> {OUT.relative_to(BASE_DIR)}")
    for row in manifest_rows:
        print(f"  {row['folder']}/{row['file']}")


if __name__ == "__main__":
    main()
