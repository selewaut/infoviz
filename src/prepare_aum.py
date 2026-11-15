from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
AUM_PATH = BASE_DIR / "data/financial_data/iol_aum_daily_full_nov2025_oct2026.csv"
OUTPUT_PATH = BASE_DIR / "data/financial_data/outputs/aum_indexed.csv"


def money_label(value: float, prefix: str) -> str:
    if pd.isna(value) or value <= 0:
        return ""
    return f"{prefix} ARS {value / 1_000_000:.1f}M".replace(".", ",")


def main() -> None:
    aum = pd.read_csv(AUM_PATH, parse_dates=["Date"]).sort_values("Date")
    aum = aum.dropna(subset=["Valuation_ARS"]).reset_index(drop=True)
    base = aum.iloc[0]

    for column in ["Valuation_ARS", "Valuation_MEP", "Valuation_CCL"]:
        index_column = f"Index_{column.replace('Valuation_', '')}"
        aum[index_column] = aum[column] / base[column] * 100

    aum["Month"] = aum["Date"].dt.strftime("%Y-%m")
    aum["Deposit_Label"] = aum["Deposit_ARS"].map(
        lambda value: money_label(value, "Aporte")
    )
    aum["Withdrawal_Label"] = aum["Withdrawal_ARS"].map(
        lambda value: money_label(value, "Retiro")
    )
    aum["Deposit_Label"] = aum["Deposit_Label"].fillna("")

    output_columns = [
        "Date",
        "Month",
        "Valuation_ARS",
        "Valuation_MEP",
        "Valuation_CCL",
        "Index_ARS",
        "Index_MEP",
        "Index_CCL",
        "Exchange_MEP",
        "Exchange_CCL",
        "Deposit_ARS",
        "Withdrawal_ARS",
        "Deposit_Label",
    ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    aum[output_columns].to_csv(OUTPUT_PATH, index=False)

    first = aum.iloc[0]
    last = aum.iloc[-1]
    deposits = aum[aum["Deposit_ARS"] > 0]

    print(f"Rows: {len(aum)}")
    print(f"Date range: {first['Date'].date()} -> {last['Date'].date()}")
    print(
        "Base 100: "
        f"ARS={first['Index_ARS']:.2f}, "
        f"MEP={first['Index_MEP']:.2f}, "
        f"CCL={first['Index_CCL']:.2f}"
    )
    print(
        "Latest index: "
        f"ARS={last['Index_ARS']:.2f}, "
        f"MEP={last['Index_MEP']:.2f}, "
        f"CCL={last['Index_CCL']:.2f}"
    )
    print(f"Deposit events: {len(deposits)}")
    print(f"Total deposits: ARS {deposits['Deposit_ARS'].sum():,.2f}")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
