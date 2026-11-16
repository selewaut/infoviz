"""Risk vs return for four calendar windows from the combined USD price panel."""

from __future__ import annotations

import calendar
import math
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PRICES = BASE_DIR / "data/financial_data/inputs/price_history_usd.csv"
ENRICHED = BASE_DIR / "data/financial_data/outputs/portfolio_enriched.csv"
OUT_CSV = BASE_DIR / "data/financial_data/outputs/risk_return.csv"

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


def main() -> None:
    df = build()
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)
    counts = df.groupby("window")["holding"].nunique().to_dict()
    print(f"{len(df)} rows -> {OUT_CSV.name}")
    print("holdings by window:", counts)


if __name__ == "__main__":
    main()
