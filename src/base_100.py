import pandas as pd

AUM_PATH = "data/financial_data/inputs/iol_aum_twr_daily_nov2025_oct2026.csv"
IPC_PATH = "data/financial_data/inputs/ipc_indec_mensual_oct2025_sep2026.csv"
OUT_PATH = "data/financial_data/outputs/portafolio_vs_inflacion_con_usd.csv"
PRESENTATION_PATH = "data/financial_data/outputs/portafolio_ytd_presentacion.csv"

aum = pd.read_csv(AUM_PATH, parse_dates=["Date"]).sort_values("Date")
ipc = pd.read_csv(IPC_PATH)

aum["YearMonth"] = aum["Date"].dt.to_period("M")
monthly = (
    aum.groupby("YearMonth")
    .agg(
        twr_end=("TWR_Accumulated", "last"),
        mep_value=("Valuation_MEP", "last"),
        mep_fx=("Exchange_MEP", "last"),
    )
    .reset_index()
)
monthly["ym"] = monthly["YearMonth"].astype(str)
monthly["twr_end"] = monthly["twr_end"] / 100

# Retorno mensual ARS: último día del mes vs último día del mes anterior.
monthly["portfolio_return"] = (
    (1 + monthly["twr_end"]) / (1 + monthly["twr_end"].shift(1)) - 1
)
monthly.loc[monthly.index[0], "portfolio_return"] = monthly["twr_end"].iloc[0]

# Retorno mensual del MEP: variación del tipo de cambio.
# El primer dato de FX disponible (01-ene-2026) se usa como base de enero.
fx = aum.dropna(subset=["Exchange_MEP"]).sort_values("Date")
fx_base = fx.iloc[0]["Exchange_MEP"]
monthly["fx_return"] = (
    (1 + monthly["mep_fx"]) / (1 + monthly["mep_fx"].shift(1)) - 1
)
monthly.loc[monthly["ym"] == "2026-01", "fx_return"] = (
    monthly.loc[monthly["ym"] == "2026-01", "mep_fx"] / fx_base - 1
)
monthly["mep_return"] = (
    (1 + monthly["portfolio_return"]) / (1 + monthly["fx_return"]) - 1
)

# Serie YTD: desde enero 2026. Se conserva octubre aunque el IPC llegue a septiembre.
df = monthly[monthly["ym"] >= "2026-01"].copy()
df["YearMonth"] = df["YearMonth"].astype(str)
df = df.merge(ipc[["YearMonth", "Monthly_Pct"]], on="YearMonth", how="left")
df = df.rename(columns={"Monthly_Pct": "IPC_pct"})
df["IPC_monthly"] = df["IPC_pct"] / 100

df["TWR_acumulado"] = (1 + df["portfolio_return"]).cumprod() - 1
df["MEP_acumulado"] = (1 + df["mep_return"]).cumprod() - 1
df["IPC_acumulado"] = (1 + df["IPC_monthly"]).cumprod() - 1
df["real_acumulado"] = (1 + df["TWR_acumulado"]) / (1 + df["IPC_acumulado"]) - 1
df["MEP_base100"] = 100 * (1 + df["MEP_acumulado"])

out = df[
    [
        "YearMonth",
        "TWR_acumulado",
        "MEP_acumulado",
        "IPC_acumulado",
        "real_acumulado",
        "MEP_base100",
        "mep_value",
        "mep_fx",
    ]
].rename(columns={"mep_value": "MEP", "mep_fx": "MEP_fx"})
out["YearMonth"] = out["YearMonth"].astype(str)

for column in ["TWR_acumulado", "MEP_acumulado", "IPC_acumulado", "real_acumulado"]:
    out[column] = (out[column] * 100).round(2)
out["MEP_base100"] = out["MEP_base100"].round(2)

print(out.to_string(index=False))
out.to_csv(OUT_PATH, index=False)

presentation = out[
    ["YearMonth", "TWR_acumulado", "IPC_acumulado", "real_acumulado", "MEP_base100"]
].rename(
    columns={
        "TWR_acumulado": "Rendimiento Nominal",
        "IPC_acumulado": "IPC acumulado",
        "real_acumulado": "Rendimiento Real",
    }
)
for column in ["Rendimiento Nominal", "IPC acumulado", "Rendimiento Real"]:
    presentation[column] = presentation[column].map(
        lambda value: "" if pd.isna(value) else f"{value:+.2f}%"
    )
presentation["MEP_base100"] = presentation["MEP_base100"].map(
    lambda value: f"{value:.2f}"
)
presentation.to_csv(PRESENTATION_PATH, index=False)

print("\nResumen presentable:")
print(presentation.to_string(index=False))

last = out.iloc[-1]
last_inflation = out.dropna(subset=["IPC_acumulado"]).iloc[-1]
print(f"\nYTD {last['YearMonth']}: ARS {last['TWR_acumulado']:+.2f}%")
print(f"YTD {last['YearMonth']}: MEP {last['MEP_acumulado']:+.2f}%")
print(
    f"YTD {last_inflation['YearMonth']}: inflación {last_inflation['IPC_acumulado']:+.2f}%"
    f" | real {last_inflation['real_acumulado']:+.2f}%"
)
print(f"\nGuardado en: {OUT_PATH}")
print(f"Guardado en: {PRESENTATION_PATH}")
