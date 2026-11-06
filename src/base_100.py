import pandas as pd

# Cargar datos
aum = pd.read_csv("data/financial_data/iol_aum_twr_daily_nov2025_oct2026.csv")
ipc = pd.read_csv("data/financial_data/ipc_indec_mensual_oct2025_sep2026.csv")

aum["Date"] = pd.to_datetime(aum["Date"])
aum = aum.dropna(subset=["TWR_Accumulated", "Valuation_MEP"]).sort_values("Date")
aum["YearMonth"] = aum["Date"].dt.to_period("M")

# Monthly last values
monthly = aum.groupby("YearMonth").agg(
    TWR_pct=("TWR_Accumulated", "last"),
    MEP=("Valuation_MEP", "last")
).reset_index()
monthly["YearMonth"] = monthly["YearMonth"].astype(str)

# Merge with inflation
df = monthly.merge(ipc[["YearMonth", "Monthly_Pct"]], on="YearMonth", how="inner")
df = df.rename(columns={"Monthly_Pct": "IPC_pct"})

# Retorno mensual del portafolio (desde el TWR acumulado)
df["TWR_dec"] = df["TWR_pct"] / 100
df["portfolio_monthly"] = (1 + df["TWR_dec"]) / (1 + df["TWR_dec"].shift(1)) - 1
df.loc[0, "portfolio_monthly"] = df.loc[0, "TWR_dec"]

# Inflación mensual
df["IPC_monthly"] = df["IPC_pct"] / 100

# Retorno real mensual
df["real_monthly"] = (1 + df["portfolio_monthly"]) / (1 + df["IPC_monthly"]) - 1

# Acumulados (desde el inicio del período)
df["TWR_acumulado"] = (1 + df["portfolio_monthly"]).cumprod() - 1
df["IPC_acumulado"] = (1 + df["IPC_monthly"]).cumprod() - 1
df["real_acumulado"] = (1 + df["real_monthly"]).cumprod() - 1

# A porcentaje
for col in ["TWR_acumulado", "IPC_acumulado", "real_acumulado"]:
    df[col] = (df[col] * 100).round(2)

# USD en base 100
df["MEP_base100"] = (df["MEP"] / df["MEP"].iloc[0] * 100).round(2)

# Resultado final (todo en el mismo dataset)
out = df[[
    "YearMonth",
    "TWR_acumulado",
    "IPC_acumulado",
    "real_acumulado",
    "MEP_base100",
    "MEP"
]]

out.to_csv("data/financial_data/portafolio_vs_inflacion_con_usd.csv", index=False)
print(out.to_string(index=False))