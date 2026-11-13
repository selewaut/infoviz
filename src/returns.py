import pandas as pd
import numpy as np

# 1. Cargar los datos
# Ajustá las rutas a donde tengas los CSV
aum_twr = pd.read_csv("data/financial_data/inputs/iol_aum_twr_daily_nov2025_oct2026.csv")
ipc = pd.read_csv("data/financial_data/inputs/ipc_indec_mensual_oct2025_sep2026.csv")

# 2. Preparar TWR diario
aum_twr["Date"] = pd.to_datetime(aum_twr["Date"])
aum_twr = aum_twr.sort_values("Date")
aum_twr["TWR"] = aum_twr["TWR_Accumulated"] / 100  # pasar a decimal

# 3. Calcular retorno mensual del portafolio (desde el TWR acumulado)
aum_twr["YearMonth"] = aum_twr["Date"].dt.to_period("M")
monthly_twr = aum_twr.groupby("YearMonth").agg(
    twr_start=("TWR", "first"),
    twr_end=("TWR", "last")
).reset_index()

monthly_twr["portfolio_return"] = (1 + monthly_twr["twr_end"]) / (1 + monthly_twr["twr_start"]) - 1
monthly_twr["YearMonth"] = monthly_twr["YearMonth"].astype(str)

# 4. Preparar inflación
ipc["YearMonth"] = ipc["YearMonth"]
ipc["inflation"] = ipc["Monthly_Pct"] / 100

# 5. Unir y calcular retorno real
df = monthly_twr.merge(ipc[["YearMonth", "inflation"]], on="YearMonth", how="left")
df["real_return"] = (1 + df["portfolio_return"]) / (1 + df["inflation"]) - 1

# 6. Acumulados
df["cum_portfolio"] = (1 + df["portfolio_return"]).cumprod() - 1
df["cum_inflation"] = (1 + df["inflation"]).cumprod() - 1
df["cum_real"] = (1 + df["real_return"]).cumprod() - 1

# 7. Resultado final
result = df[["YearMonth", "portfolio_return", "inflation", "real_return", 
             "cum_portfolio", "cum_inflation", "cum_real"]].copy()

# Pasar a porcentaje para que sea más legible
for col in ["portfolio_return", "inflation", "real_return", "cum_portfolio", "cum_inflation", "cum_real"]:
    result[col] = (result[col] * 100).round(2)

print(result.to_string(index=False))

# Guardar
result.to_csv("data/financial_data/outputs/comparacion_portafolio_vs_inflacion.csv", index=False)
print("\nGuardado en: data/financial_data/outputs/comparacion_portafolio_vs_inflacion.csv")