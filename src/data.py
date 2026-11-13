import pandas as pd

PORTFOLIO_CSV = "data/financial_data/inputs/iol_portfolio_argentina.csv"


def add_value_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["value"] = df["Quantity"] * df["Price_ARS"]
    return df


def load_portfolio(path: str = PORTFOLIO_CSV) -> pd.DataFrame:
    df = pd.read_csv(path)
    return add_value_column(df)


def save_portfolio(df: pd.DataFrame, path: str = PORTFOLIO_CSV) -> None:
    df.to_csv(path, index=False)


if __name__ == "__main__":
    df = load_portfolio()
    save_portfolio(df)
    print(df[["Symbol", "Quantity", "Price_ARS", "value"]])
