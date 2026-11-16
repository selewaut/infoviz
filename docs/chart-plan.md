# Chart Plan — Portfolio Visualizations

## Current state

- `index.html`: KPIs -> RAWGraphs treemap (`images/FINANCE2.svg`) -> Flourish YTD line.
- Holdings snapshot: 25 positions, ARS 131,630,986.95, dated 2026-10-30.
- MCP metadata file: `data/financial_data/inputs/iol_asset_metadata.csv`.

## Validated data

| Check | Result |
|---|---|
| Symbol coverage | 25/25 matched |
| `IOL_Type` vs portfolio `Type` | 25/25 match |
| `Sector` / `Industry` / `Is_ETF` | All `N/A` in MCP metadata; manual mapping required |
| `Currency` | All `ARS` (trading currency, not exposure) |
| `Lot` | AL30/GD30 = 100; all others = 1 |
| Bond analytics | AL30: TIR 10.01%, duration 1.77y, parity 86.27%; GD30: TIR 8.16%, duration 1.79y, parity 88.93% |
| FCI category | PRTAVAB = renta variable; IOLCAMA = renta fija / money market |
| Descriptions | Minor punctuation differences only; use portfolio descriptions |

### Portfolio facts

- Renta variable: 96.53%; renta fija: 2.48%; fondos/liquidez: 0.99%.
- Top 3 holdings: 55.2% (AMD, SPY, VIST).
- Sectors: Tecnologia 39.61%, Energia 23.00%, ETF 14.21%, Consumo discrecional 13.17%, Comunicaciones 3.81%, Deuda soberana 2.48%, Consumo basico 1.59%, FCI 0.99%, Financiero 0.58%, Utilities 0.55%, Materiales 0.005%.
- Industry top 10: 97.21%; Otros: 2.79%.

## Taxonomy

| Tickers | AssetClass | Sector | Industry | Currency exposure |
|---|---|---|---|---|
| AMD, NVDA, INTC | Renta variable | Tecnologia | Semiconductores | USD |
| AAPL | Renta variable | Tecnologia | Hardware | USD |
| SNOW | Renta variable | Tecnologia | Software | USD |
| GOOGL, META | Renta variable | Comunicaciones | Internet | USD |
| TECO2 | Renta variable | Comunicaciones | Telecomunicaciones | ARS |
| MELI, AMZN | Renta variable | Consumo discrecional | E-commerce | USD |
| TSLA | Renta variable | Consumo discrecional | Automotriz / EV | USD |
| KO | Renta variable | Consumo basico | Bebidas | USD |
| CVX, PBR, VIST, YPFD | Renta variable | Energia | Petroleo y gas | USD |
| PAMP | Renta variable | Energia | Energia integrada | ARS |
| TGNO4 | Renta variable | Utilities | Gas / Utilities | ARS |
| GGAL | Renta variable | Financiero | Bancos | ARS |
| BIOX | Renta variable | Materiales | Agro / Materiales | USD |
| SPY | Renta variable (ETF) | ETF / Mercado amplio | ETF / Indice | USD |
| AL30, GD30 | Renta fija | Deuda soberana | Bono soberano | USD |
| PRTAVAB | Fondos / liquidez | FCI | FCI renta variable | ARS |
| IOLCAMA | Fondos / liquidez | FCI | FCI money market | ARS |

## Phase 1 — Data layer

1. Add `src/enrich_portfolio.py`.
   - Merge portfolio and MCP metadata using `MCP_*` column names.
   - Add manual taxonomy: `AssetClass`, `Sector`, `Industry`, `Industry_Group`, `Country_Exposure`, `Currency_Exposure`, `Underlying_Symbol`, `Is_ETF`.
   - Compute `Value_ARS`, `Weight_Pct`, `Daily_PnL_ARS`, `Contribution_Pct`.
   - Convert bond TIR/parity to percentages; duration in years.
   - Validate totals and mappings.
2. Output:
   - `outputs/portfolio_enriched.csv`
   - `outputs/portfolio_by_sector.csv`
   - `outputs/portfolio_by_industry.csv`
   - `outputs/portfolio_by_industry_group.csv`
3. Add `src/prepare_aum.py`.
   - Build `outputs/aum_indexed.csv` with daily AUM indexed to 100 at 2026-01-01.
   - Include deposit/withdrawal labels for annotations.

## Phase 2 — RAWGraphs industry bar

- Data: `portfolio_by_industry_group.csv`.
- Recommended: all industries with weight >= 0.5% plus `Otros` (13 named + Otros).
- RAWGraphs mapping: Y = `Industry_Group`, X = `Weight_Pct`, color = `Sector_Chart`, sort = `Sort_Order`, label = `Weight_Label`.
- Export `images/industry_bar.svg`; embed with `<object>` + `<img>` fallback.
- Title: "Mas alla del CEDEAR: exposicion por industria".

## Phase 3 — Tableau treemap rebuild

Status: in progress (data layer extended 2026-11-15; workbook not built yet).

### Data fields added

- `Value_USD`, `Value_USD_Label` (converted at CCL).
- `Daily_Change_USD_Pct`, `Daily_Change_USD_Label` = `(1 + Daily_Change_Pct / 100) / (1 + FX_CCL_Change / 100) - 1`.
- `Daily_PnL_USD`, `FX_CCL_Change_Pct`.
- CCL on 2026-10-30: 1,660.75 (+0.78% d/d). Portfolio USD value: 79,259.97.
- Caveat: derived USD move is an approximation of the underlying move, not the actual foreign close.

### Dimensions

- Hierarchy A (default): `AssetClass > Sector > Industry > Symbol`.
- Hierarchy B: `AssetClass > Industry_Group > Symbol`.
- Cross-cuts: `Currency_Exposure`, `Country_Exposure`, `Type`.

### Interactivity

- Parameter `Ver por`: AssetClass / Sector / Industry / Industry_Group / Currency / Country / Type.
- Native drill-down on the hierarchy + breadcrumb header.
- Parameter `Color por`: USD daily change (default) / ARS daily change / Sector / Currency_Exposure.
- Parameter `Tamaño`: `Value_ARS` (default) / `Value_USD`.
- Filter actions, `Type` quick filter, Top-N parameter.
- Tooltip: description, type, asset class, sector, industry, country, currency exposure, value ARS/USD, weight, daily change ARS/USD, daily P&L ARS/USD, contribution, bond analytics.

### Color

- Diverging red-green centered at 0, clipped ±3% (tunable via parameter).
- Neutral gray for rows without a meaningful daily change.

### Build order

1. [done] Extend `src/enrich_portfolio.py` with USD change/value/P&L.
2. Export Tableau-ready flat CSV.
3. Build treemap sheet with hierarchy A, size `Value_ARS`, color `Daily_Change_USD_Pct`.
4. Add drill-down, tooltip, `Ver por` / `Color por` / `Tamaño` parameters.
5. Add `Type` / `Currency` / `Country` filters and Top-N.
6. Publish to Tableau Public; replace `FINANCE2.svg` embed in `index.html`.
   - Title: "Donde esta mi plata? Mapa interactivo del portafolio".

## Phase 4 — Datawrapper chart

Recommended: AUM in ARS vs USD.

- Data: `aum_indexed.csv` (303 daily rows, base 100 = 2026-01-01).
- Line chart with `Index_ARS`, `Index_MEP`, `Index_CCL`.
- Annotate the four deposits.
- Title: "Tu patrimonio: en pesos crece mas que en dolares".
- Note: AUM includes deposits, so this is wealth evolution, not pure return.

Alternative: monthly portfolio vs inflation range/dot plot using `outputs/comparacion_portafolio_vs_inflacion.csv`.

## Phase 5 — Page integration

- New `index.html` order: KPIs -> Tableau treemap -> RAWGraphs industry bar -> Datawrapper AUM -> Flourish performance chart.
- Optional KPIs: Tecnologia 39.6%, Top 3 55.2%, Renta variable 96.5%.
- Add responsive styles, source notes, and `<noscript>` fallbacks.
- After publishing, replace placeholders with the Tableau URL and Datawrapper embed ID.

## Defaults

1. RAWGraphs bar = industry-level, weight >= 0.5% + `Otros`.
2. Datawrapper = AUM ARS/MEP/CCL indexed line.
3. Add the three new KPIs.

## Phase 1 results

Status: complete.

Generated files:

- `src/enrich_portfolio.py`
- `src/prepare_aum.py`
- `data/financial_data/outputs/portfolio_enriched.csv`
- `data/financial_data/outputs/portfolio_by_sector.csv`
- `data/financial_data/outputs/portfolio_by_industry.csv`
- `data/financial_data/outputs/portfolio_by_industry_group.csv`
- `data/financial_data/outputs/aum_indexed.csv`

Validation:

- Rows: 25.
- Total AUM: ARS 131,630,986.95.
- Weight sum: 100.000000%.
- Max value difference vs source: 0.000000.
- Type mismatches: 0.
- Industry groups: 14 (13 named + `Otros`).
- Currency exposure: USD 88.97%, ARS 11.03%.
- AUM series: 303 daily rows, 2026-01-01 to 2026-10-30.
- AUM index at 2026-10-30: ARS 141.93, MEP 133.48, CCL 128.94.
- Deposit events: 4; total deposits ARS 11,988,553.80.

### USD extension (2026-11-15)

- Added `Value_USD`, `Daily_Change_USD_Pct`, `Daily_PnL_USD`, `FX_CCL_Change_Pct` to `portfolio_enriched.csv` and the three group summaries.
- FX basis: CCL, prior trading day vs snapshot day.
- On 2026-10-30, CCL moved +0.78%, so USD changes are ~0.78pp lower than ARS changes (e.g. AMD -10.30% ARS -> -10.99% USD).
