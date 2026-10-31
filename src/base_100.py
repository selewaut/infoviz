import pandas as pd

# Cargar datos
aum = pd.read_csv("data/iol_aum_twr_daily_nov2025_oct2026.csv")
ipc = pd.read_csv("data/ipc_indec_mensual_oct2025_sep2026.csv")

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

# --- Base 100 series ---
# 1. TWR (portafolio en ARS)
df["TWR_base100"] = (1 + df["TWR_pct"]/100) / (1 + df["TWR_pct"].iloc[0]/100) * 100

# 2. Inflación (IPC)
df["IPC_base100"] = (1 + df["IPC_pct"]/100).cumprod() / (1 + df["IPC_pct"].iloc[0]/100) * 100

# 3. Retorno real
df["real_return"] = (1 + df["TWR_pct"]/100) / (1 + df["IPC_pct"]/100) - 1
df["real_base100"] = (1 + df["real_return"]).cumprod() / (1 + df["real_return"].iloc[0]) * 100

# 4. USD (MEP)
df["MEP_base100"] = df["MEP"] / df["MEP"].iloc[0] * 100

# Resultado final
out = df[[
    "YearMonth",
    "TWR_base100",
    "IPC_base100",
    "real_base100",
    "MEP_base100",
    "TWR_pct",
    "IPC_pct",
    "MEP"
]].round(2)

out.to_csv("data/portafolio_base100_ars_usd_inflacion.csv", index=False)
print(out.to_string(index=False))