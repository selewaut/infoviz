import pandas as pd

AUM_PATH = "data/financial_data/inputs/iol_aum_twr_daily_nov2025_oct2026.csv"
IPC_PATH = "data/financial_data/inputs/ipc_indec_mensual_oct2025_sep2026.csv"
OUT_PATH = "data/financial_data/outputs/comparacion_portafolio_vs_inflacion.csv"

aum = pd.read_csv(AUM_PATH, parse_dates=["Date"]).sort_values("Date")
ipc = pd.read_csv(IPC_PATH)

# Nivel TWR acumulado al último día de cada mes. El retorno mensual se calcula
# contra el último dato del mes anterior (no contra el primer dato del mes).
aum["YearMonth"] = aum["Date"].dt.to_period("M")
monthly = (
    aum.groupby("YearMonth")
    .agg(twr_end=("TWR_Accumulated", "last"))
    .reset_index()
)
monthly["twr_end"] = monthly["twr_end"] / 100
monthly["portfolio_return"] = (
    (1 + monthly["twr_end"]) / (1 + monthly["twr_end"].shift(1)) - 1
)
monthly.loc[monthly.index[0], "portfolio_return"] = monthly["twr_end"].iloc[0]
monthly["YearMonth"] = monthly["YearMonth"].astype(str)

ipc["inflation"] = ipc["Monthly_Pct"] / 100

df = monthly[["YearMonth", "portfolio_return"]].merge(
    ipc[["YearMonth", "inflation"]], on="YearMonth", how="left"
)
df["real_return"] = (1 + df["portfolio_return"]) / (1 + df["inflation"]) - 1

# Acumulados desde el inicio del portafolio (Oct-2025)
df["cum_portfolio"] = (1 + df["portfolio_return"]).cumprod() - 1
df["cum_inflation"] = (1 + df["inflation"]).cumprod() - 1
df["cum_real"] = (1 + df["real_return"]).cumprod() - 1

# Acumulados dentro de cada año calendario (YTD)
df["year"] = df["YearMonth"].str[:4]
for source, target in [
    ("portfolio_return", "ytd_portfolio"),
    ("inflation", "ytd_inflation"),
    ("real_return", "ytd_real"),
]:
    df[target] = df.groupby("year")[source].transform(
        lambda series: (1 + series).cumprod() - 1
    )

columns = [
    "YearMonth",
    "portfolio_return",
    "inflation",
    "real_return",
    "cum_portfolio",
    "cum_inflation",
    "cum_real",
    "ytd_portfolio",
    "ytd_inflation",
    "ytd_real",
]
result = df[columns].copy()
for column in columns[1:]:
    result[column] = (result[column] * 100).round(2)

print(result.to_string(index=False))
result.to_csv(OUT_PATH, index=False)

last = result.iloc[-1]
last_inflation = result.dropna(subset=["ytd_inflation"]).iloc[-1]

fx = aum.dropna(subset=["Exchange_MEP"]).sort_values("Date")
fx_base = fx.iloc[0]["Exchange_MEP"]
fx_last = fx.iloc[-1]["Exchange_MEP"]
twr_dec = monthly.loc[monthly["YearMonth"] == "2025-12", "twr_end"].iloc[0]
twr_last = monthly["twr_end"].iloc[-1]
ars_ytd = (1 + twr_last) / (1 + twr_dec) - 1
mep_ytd = (1 + ars_ytd) / (fx_last / fx_base) - 1

print(f"\nYTD {last['YearMonth']}: ARS {last['ytd_portfolio']:+.2f}%")
print(f"YTD {last['YearMonth']}: MEP {mep_ytd * 100:+.2f}%")
print(
    f"YTD {last_inflation['YearMonth']}: inflación {last_inflation['ytd_inflation']:+.2f}%"
    f" | real {last_inflation['ytd_real']:+.2f}%"
)
print(f"\nGuardado en: {OUT_PATH}")
