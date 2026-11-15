from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
PORTFOLIO_PATH = BASE_DIR / "data/financial_data/inputs/iol_portfolio_argentina.csv"
METADATA_PATH = BASE_DIR / "data/financial_data/inputs/iol_asset_metadata.csv"
OUTPUT_DIR = BASE_DIR / "data/financial_data/outputs"

SNAPSHOT_DATE = "2026-10-30"
INDUSTRY_GROUP_THRESHOLD = 0.5

CLASSIFICATION = {
    "INTC": {
        "AssetClass": "Renta variable",
        "Sector": "Tecnología",
        "Industry": "Semiconductores",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "KO": {
        "AssetClass": "Renta variable",
        "Sector": "Consumo básico",
        "Industry": "Bebidas",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "PAMP": {
        "AssetClass": "Renta variable",
        "Sector": "Energía",
        "Industry": "Energía integrada",
        "Country_Exposure": "Argentina",
        "Currency_Exposure": "ARS",
    },
    "TECO2": {
        "AssetClass": "Renta variable",
        "Sector": "Comunicaciones",
        "Industry": "Telecomunicaciones",
        "Country_Exposure": "Argentina",
        "Currency_Exposure": "ARS",
    },
    "YPFD": {
        "AssetClass": "Renta variable",
        "Sector": "Energía",
        "Industry": "Petróleo y gas",
        "Country_Exposure": "Argentina",
        "Currency_Exposure": "ARS",
    },
    "GGAL": {
        "AssetClass": "Renta variable",
        "Sector": "Financiero",
        "Industry": "Bancos",
        "Country_Exposure": "Argentina",
        "Currency_Exposure": "ARS",
    },
    "CVX": {
        "AssetClass": "Renta variable",
        "Sector": "Energía",
        "Industry": "Petróleo y gas",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "TGNO4": {
        "AssetClass": "Renta variable",
        "Sector": "Utilities",
        "Industry": "Gas / Utilities",
        "Country_Exposure": "Argentina",
        "Currency_Exposure": "ARS",
    },
    "GOOGL": {
        "AssetClass": "Renta variable",
        "Sector": "Comunicaciones",
        "Industry": "Internet",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "MELI": {
        "AssetClass": "Renta variable",
        "Sector": "Consumo discrecional",
        "Industry": "E-commerce",
        "Country_Exposure": "LatAm",
        "Currency_Exposure": "USD",
    },
    "AAPL": {
        "AssetClass": "Renta variable",
        "Sector": "Tecnología",
        "Industry": "Hardware",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "PRTAVAB": {
        "AssetClass": "Fondos / liquidez",
        "Sector": "FCI",
        "Industry": "FCI renta variable",
        "Country_Exposure": "Argentina",
        "Currency_Exposure": "ARS",
    },
    "META": {
        "AssetClass": "Renta variable",
        "Sector": "Comunicaciones",
        "Industry": "Internet",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "AMZN": {
        "AssetClass": "Renta variable",
        "Sector": "Consumo discrecional",
        "Industry": "E-commerce",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "NVDA": {
        "AssetClass": "Renta variable",
        "Sector": "Tecnología",
        "Industry": "Semiconductores",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "TSLA": {
        "AssetClass": "Renta variable",
        "Sector": "Consumo discrecional",
        "Industry": "Automotriz / EV",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "AMD": {
        "AssetClass": "Renta variable",
        "Sector": "Tecnología",
        "Industry": "Semiconductores",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "PBR": {
        "AssetClass": "Renta variable",
        "Sector": "Energía",
        "Industry": "Petróleo y gas",
        "Country_Exposure": "Brasil",
        "Currency_Exposure": "USD",
    },
    "VIST": {
        "AssetClass": "Renta variable",
        "Sector": "Energía",
        "Industry": "Petróleo y gas",
        "Country_Exposure": "LatAm",
        "Currency_Exposure": "USD",
    },
    "AL30": {
        "AssetClass": "Renta fija",
        "Sector": "Deuda soberana",
        "Industry": "Bono soberano",
        "Country_Exposure": "Argentina",
        "Currency_Exposure": "USD",
    },
    "GD30": {
        "AssetClass": "Renta fija",
        "Sector": "Deuda soberana",
        "Industry": "Bono soberano",
        "Country_Exposure": "Argentina",
        "Currency_Exposure": "USD",
    },
    "BIOX": {
        "AssetClass": "Renta variable",
        "Sector": "Materiales",
        "Industry": "Agro / Materiales",
        "Country_Exposure": "LatAm",
        "Currency_Exposure": "USD",
    },
    "SNOW": {
        "AssetClass": "Renta variable",
        "Sector": "Tecnología",
        "Industry": "Software",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "SPY": {
        "AssetClass": "Renta variable",
        "Sector": "ETF / Mercado amplio",
        "Industry": "ETF / Índice",
        "Country_Exposure": "EE.UU.",
        "Currency_Exposure": "USD",
    },
    "IOLCAMA": {
        "AssetClass": "Fondos / liquidez",
        "Sector": "FCI",
        "Industry": "FCI money market",
        "Country_Exposure": "Argentina",
        "Currency_Exposure": "ARS",
    },
}

FCI_CATEGORY_MAP = {
    "renta_variable_pesos": "Renta variable (ARS)",
    "renta_fija_pesos": "Renta fija / money market (ARS)",
}


def pct_label(value: float) -> str:
    return f"{value:.2f}%".replace(".", ",")


def signed_pct_label(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value:+.2f}%".replace(".", ",")


def summarize_sector(df: pd.DataFrame, total: float) -> pd.DataFrame:
    rows = []
    for sector, group in df.groupby("Sector", sort=False):
        top = group.loc[group["Value_ARS"].idxmax()]
        rows.append(
            {
                "Sector": sector,
                "AssetClass": " / ".join(sorted(group["AssetClass"].dropna().unique())),
                "Value_ARS": group["Value_ARS"].sum(),
                "Weight_Pct": group["Value_ARS"].sum() / total * 100,
                "Holdings": len(group),
                "Top_Holding": top["Symbol"],
                "Top_Holding_Weight_Pct": top["Weight_Pct"],
                "Weighted_Daily_Change_Pct": (
                    (group["Value_ARS"] * group["Daily_Change_Pct"]).sum()
                    / group["Value_ARS"].sum()
                ),
                "Daily_PnL_ARS": group["Daily_PnL_ARS"].sum(),
            }
        )
    out = pd.DataFrame(rows).sort_values("Value_ARS", ascending=False).reset_index(drop=True)
    out["Sort_Order"] = range(1, len(out) + 1)
    out["Weight_Label"] = out["Weight_Pct"].map(pct_label)
    return out


def summarize_industry(df: pd.DataFrame, total: float) -> pd.DataFrame:
    rows = []
    for industry, group in df.groupby("Industry", sort=False):
        top = group.loc[group["Value_ARS"].idxmax()]
        rows.append(
            {
                "Industry": industry,
                "Industry_Group": group["Industry_Group"].iloc[0],
                "Sector": " / ".join(sorted(group["Sector"].dropna().unique())),
                "AssetClass": " / ".join(sorted(group["AssetClass"].dropna().unique())),
                "Value_ARS": group["Value_ARS"].sum(),
                "Weight_Pct": group["Value_ARS"].sum() / total * 100,
                "Holdings": len(group),
                "Top_Holding": top["Symbol"],
                "Top_Holding_Weight_Pct": top["Weight_Pct"],
                "Weighted_Daily_Change_Pct": (
                    (group["Value_ARS"] * group["Daily_Change_Pct"]).sum()
                    / group["Value_ARS"].sum()
                ),
                "Daily_PnL_ARS": group["Daily_PnL_ARS"].sum(),
            }
        )
    out = pd.DataFrame(rows).sort_values("Value_ARS", ascending=False).reset_index(drop=True)
    out["Sort_Order"] = range(1, len(out) + 1)
    out["Weight_Label"] = out["Weight_Pct"].map(pct_label)
    return out


def summarize_industry_group(df: pd.DataFrame, total: float) -> pd.DataFrame:
    rows = []
    for industry_group, group in df.groupby("Industry_Group", sort=False):
        top = group.loc[group["Value_ARS"].idxmax()]
        rows.append(
            {
                "Industry_Group": industry_group,
                "Components": " / ".join(sorted(group["Industry"].dropna().unique())),
                "Sector": " / ".join(sorted(group["Sector"].dropna().unique())),
                "AssetClass": " / ".join(sorted(group["AssetClass"].dropna().unique())),
                "Value_ARS": group["Value_ARS"].sum(),
                "Weight_Pct": group["Value_ARS"].sum() / total * 100,
                "Holdings": len(group),
                "Top_Holding": top["Symbol"],
                "Top_Holding_Weight_Pct": top["Weight_Pct"],
                "Weighted_Daily_Change_Pct": (
                    (group["Value_ARS"] * group["Daily_Change_Pct"]).sum()
                    / group["Value_ARS"].sum()
                ),
                "Daily_PnL_ARS": group["Daily_PnL_ARS"].sum(),
            }
        )
    out = pd.DataFrame(rows).sort_values("Value_ARS", ascending=False).reset_index(drop=True)
    out["Sort_Order"] = range(1, len(out) + 1)
    out["Weight_Label"] = out["Weight_Pct"].map(pct_label)
    out["Sector_Chart"] = out["Sector"].where(out["Industry_Group"] != "Otros", "Otros")
    out["Bar_Color"] = "Resto"
    out.loc[out["Sort_Order"] <= 3, "Bar_Color"] = "Top 3"
    out.loc[out["Industry_Group"] == "Otros", "Bar_Color"] = "Otros"
    return out


def main() -> None:
    portfolio = pd.read_csv(PORTFOLIO_PATH)
    metadata = pd.read_csv(METADATA_PATH)
    metadata = metadata.rename(
        columns={
            "IOL_Type": "MCP_Type",
            "Currency": "MCP_Currency",
            "Lot": "MCP_Lot",
            "Related_Symbols": "MCP_Related_Symbols",
            "Sector": "MCP_Sector",
            "Industry": "MCP_Industry",
            "Is_ETF": "MCP_Is_ETF",
            "Description": "MCP_Description",
            "TIR": "MCP_TIR",
            "Duration": "MCP_Duration",
            "Parity": "MCP_Parity",
            "FCI_Category": "MCP_FCI_Category",
            "FCI_Manager": "MCP_FCI_Manager",
        }
    )

    df = portfolio.merge(metadata, on="Symbol", how="left", validate="one_to_one")

    taxonomy = (
        pd.DataFrame.from_dict(CLASSIFICATION, orient="index")
        .rename_axis("Symbol")
        .reset_index()
    )
    df = df.merge(taxonomy, on="Symbol", how="left", validate="one_to_one")

    missing_taxonomy = df[
        ["AssetClass", "Sector", "Industry", "Country_Exposure", "Currency_Exposure"]
    ].isna().any(axis=1)
    if missing_taxonomy.any():
        missing = df.loc[missing_taxonomy, "Symbol"].tolist()
        raise ValueError(f"Missing taxonomy for: {missing}")

    df["Snapshot_Date"] = SNAPSHOT_DATE
    df["Value_ARS"] = df["Quantity"] * df["Price_ARS"]
    total = df["Value_ARS"].sum()

    df["Weight_Pct"] = df["Value_ARS"] / total * 100
    df["Weight_Label"] = df["Weight_Pct"].map(pct_label)
    df["Value_MM_ARS"] = df["Value_ARS"] / 1_000_000
    df["Value_MM_Label"] = df["Value_MM_ARS"].map(
        lambda value: f"ARS {value:.1f} M".replace(".", ",")
    )

    df["Daily_Change_Label"] = df["Daily_Change_Pct"].map(signed_pct_label)
    previous_value = df["Value_ARS"] / (1 + df["Daily_Change_Pct"] / 100)
    df["Daily_PnL_ARS"] = df["Value_ARS"] - previous_value
    df["Contribution_Pct"] = df["Daily_PnL_ARS"] / total * 100

    df["Underlying_Symbol"] = df["MCP_Related_Symbols"].str.split("|").str[0]
    df["Is_ETF"] = df["Symbol"].eq("SPY")
    df["TIR_Pct"] = df["MCP_TIR"] * 100
    df["Duration_Years"] = df["MCP_Duration"]
    df["Parity_Pct"] = df["MCP_Parity"] * 100
    df["FCI_Category_Display"] = df["MCP_FCI_Category"].map(FCI_CATEGORY_MAP)

    industry_totals = df.groupby("Industry")["Weight_Pct"].sum()
    kept_industries = industry_totals[industry_totals >= INDUSTRY_GROUP_THRESHOLD].index
    df["Industry_Group"] = df["Industry"].where(
        df["Industry"].isin(kept_industries), "Otros"
    )

    sector_summary = summarize_sector(df, total)
    industry_summary = summarize_industry(df, total)
    industry_group_summary = summarize_industry_group(df, total)

    enriched_columns = [
        "Snapshot_Date",
        "Symbol",
        "Description",
        "Type",
        "AssetClass",
        "Sector",
        "Industry",
        "Industry_Group",
        "Country_Exposure",
        "Currency_Exposure",
        "Underlying_Symbol",
        "Is_ETF",
        "Quantity",
        "Price_ARS",
        "Value_ARS",
        "Value_MM_ARS",
        "Value_MM_Label",
        "Weight_Pct",
        "Weight_Label",
        "Daily_Change_Pct",
        "Daily_Change_Label",
        "Daily_PnL_ARS",
        "Contribution_Pct",
        "TIR_Pct",
        "Duration_Years",
        "Parity_Pct",
        "FCI_Category_Display",
        "MCP_Type",
        "MCP_Currency",
        "MCP_Lot",
        "MCP_Related_Symbols",
        "MCP_Description",
        "MCP_FCI_Category",
        "MCP_FCI_Manager",
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    df[enriched_columns].to_csv(OUTPUT_DIR / "portfolio_enriched.csv", index=False)
    sector_summary.to_csv(OUTPUT_DIR / "portfolio_by_sector.csv", index=False)
    industry_summary.to_csv(OUTPUT_DIR / "portfolio_by_industry.csv", index=False)
    industry_group_summary.to_csv(
        OUTPUT_DIR / "portfolio_by_industry_group.csv", index=False
    )

    value_diff = (df["Value_ARS"] - df["value"]).abs().max()
    type_mismatches = (df["Type"].astype(str) != df["MCP_Type"].astype(str)).sum()

    print(f"Rows: {len(df)}")
    print(f"Total AUM: ARS {total:,.2f}")
    print(f"Weight sum: {df['Weight_Pct'].sum():.6f}%")
    print(f"Max value difference vs source: {value_diff:.6f}")
    print(f"Type mismatches: {type_mismatches}")
    print(f"Industry groups: {len(industry_group_summary)}")

    print("\nTop 5 holdings:")
    print(
        df.sort_values("Value_ARS", ascending=False)
        .head(5)[["Symbol", "Sector", "Industry", "Weight_Pct", "Daily_Change_Pct"]]
        .to_string(index=False)
    )

    print("\nSector summary:")
    print(
        sector_summary[["Sector", "Weight_Pct", "Holdings", "Top_Holding"]].to_string(
            index=False
        )
    )

    print("\nIndustry group summary:")
    print(
        industry_group_summary[
            ["Industry_Group", "Weight_Pct", "Holdings", "Components"]
        ].to_string(index=False)
    )

    print(f"\nSaved: {OUTPUT_DIR / 'portfolio_enriched.csv'}")
    print(f"Saved: {OUTPUT_DIR / 'portfolio_by_sector.csv'}")
    print(f"Saved: {OUTPUT_DIR / 'portfolio_by_industry.csv'}")
    print(f"Saved: {OUTPUT_DIR / 'portfolio_by_industry_group.csv'}")


if __name__ == "__main__":
    main()
