import pandas as pd

PORTFOLIO_PATH = "data/financial_data/outputs/portafolio_vs_inflacion_con_usd.csv"
SPX_PATH = "data/financial_data/inputs/price_history/SPX_GSPC_YAHOO.csv"
OUT_PATH = "data/financial_data/outputs/portafolio_usd_vs_sp500.csv"
PRESENTATION_PATH = (
    "data/financial_data/outputs/portafolio_usd_vs_sp500_presentacion.csv"
)

portfolio = pd.read_csv(PORTFOLIO_PATH)
portfolio = portfolio[["YearMonth", "MEP_acumulado"]].rename(
    columns={"MEP_acumulado": "Portafolio USD"}
)

spx = pd.read_csv(SPX_PATH, parse_dates=["date"]).sort_values("date")
spx["YearMonth"] = spx["date"].dt.to_period("M")
monthly = (
    spx.groupby("YearMonth")
    .agg(close=("close", "last"))
    .reset_index()
)
monthly["YearMonth"] = monthly["YearMonth"].astype(str)

# Acumulado desde el cierre de diciembre 2025, igual que la serie del portafolio.
base = monthly.loc[monthly["YearMonth"] == "2025-12", "close"].iloc[0]
monthly["S&P 500"] = (monthly["close"] / base - 1) * 100

df = portfolio.merge(
    monthly[["YearMonth", "S&P 500"]], on="YearMonth", how="left"
)

# Retorno mensual derivado de la serie acumulada.
for column in ["Portafolio USD", "S&P 500"]:
    df[f"{column} mensual"] = (
        (1 + df[column] / 100).pct_change() * 100
    )
    df.loc[df.index[0], f"{column} mensual"] = df.loc[df.index[0], column]

columns = [
    "YearMonth",
    "Portafolio USD",
    "S&P 500",
    "Portafolio USD mensual",
    "S&P 500 mensual",
]
df = df[columns].round(2)
df.to_csv(OUT_PATH, index=False)

presentation = df[["YearMonth", "Portafolio USD", "S&P 500"]].copy()
for column in ["Portafolio USD", "S&P 500"]:
    presentation[column] = presentation[column].map(
        lambda value: "" if pd.isna(value) else f"{value:+.2f}%"
    )
presentation.to_csv(PRESENTATION_PATH, index=False)

print(df.to_string(index=False))
print("\nResumen presentable:")
print(presentation.to_string(index=False))
print(f"\nGuardado en: {OUT_PATH}")
print(f"Guardado en: {PRESENTATION_PATH}")
