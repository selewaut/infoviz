"""Download daily OHLCV from the IOL REST API (api.iolinversiones.com).

Reads Fetch=yes rows in holdings_usd_search_map.csv.
Credentials: IOL_USERNAME / IOL_PASSWORD in the environment or a repo-root .env.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
MAP_PATH = BASE_DIR / "data/financial_data/inputs/holdings_usd_search_map.csv"
OUT_DIR = BASE_DIR / "data/financial_data/inputs/price_history"
COMBINED_PATH = BASE_DIR / "data/financial_data/inputs/price_history_usd.csv"
SKIP_COMBINE = {"MEP_FX.csv"}
ENV_PATH = BASE_DIR / ".env"
TOKEN_PATH = BASE_DIR / ".iol-token.json"

API = "https://api.iolinversiones.com"
MARKETS = {"BCBA", "NYSE", "NASDAQ"}
PAUSE_S = 0.3
TIMEOUT_S = 30
# Cloudflare 1010 blocks library default User-Agents (urllib, python-requests).
USER_AGENT = "infoviz/0.1"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def credentials() -> tuple[str, str]:
    load_dotenv(ENV_PATH)
    user = os.environ.get("IOL_USERNAME", "").strip()
    password = os.environ.get("IOL_PASSWORD", "").strip()
    if not user or not password:
        raise SystemExit(
            "Missing IOL_USERNAME / IOL_PASSWORD. "
            "Copy env.example to .env and fill them in."
        )
    return user, password


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
    )
    return session


def error_text(payload: object, fallback: str) -> str:
    if isinstance(payload, dict):
        err = payload.get("error")
        if isinstance(err, dict):
            code = err.get("code") or ""
            message = err.get("message") or err
            return f"{code}: {message}".strip(": ")
        if err:
            return str(err)
        return json.dumps(payload, ensure_ascii=False)[:300]
    return fallback[:300]


def unwrap(payload: dict) -> dict:
    if payload.get("error"):
        raise ValueError(error_text(payload, "IOL error"))
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError(f"missing data: {error_text(payload, str(payload))}")
    return data


def read_json(resp: requests.Response) -> dict:
    try:
        payload = resp.json()
    except ValueError:
        payload = None
    if resp.status_code >= 400:
        detail = error_text(payload, resp.text) if payload is not None else resp.text[:300]
        raise requests.HTTPError(
            f"{resp.status_code} {detail}",
            response=resp,
        )
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object, got {resp.text[:200]}")
    return payload


def post_token(session: requests.Session, payload: dict) -> dict:
    resp = session.post(f"{API}/auth/token", json=payload, timeout=TIMEOUT_S)
    try:
        token = unwrap(read_json(resp))
    except requests.HTTPError as exc:
        raise SystemExit(f"IOL token error {exc}") from exc
    if "access_token" not in token:
        raise SystemExit(f"Unexpected token data: {token}")
    TOKEN_PATH.write_text(json.dumps(token), encoding="utf-8")
    return token


def login(session: requests.Session) -> dict:
    user, password = credentials()
    return post_token(
        session,
        {"grant_type": "password", "username": user, "password": password},
    )


def refresh(session: requests.Session, token: dict) -> dict:
    return post_token(
        session,
        {"grant_type": "refresh_token", "refresh_token": token["refresh_token"]},
    )


def load_token(session: requests.Session) -> dict:
    if TOKEN_PATH.exists():
        cached = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
        if cached.get("access_token"):
            return cached
    return login(session)


def get_json(
    session: requests.Session,
    url: str,
    token: dict,
    params: dict | None = None,
) -> tuple[dict, dict]:
    def fetch(access: str) -> requests.Response:
        return session.get(
            url,
            params=params,
            headers={"Authorization": f"Bearer {access}"},
            timeout=TIMEOUT_S,
        )

    resp = fetch(token["access_token"])
    if resp.status_code == 401:
        token = refresh(session, token) if token.get("refresh_token") else login(session)
        resp = fetch(token["access_token"])
    return unwrap(read_json(resp)), token


def bars_url(symbol: str) -> str:
    return f"{API}/broker/market-data/{symbol}/bars"


def bars_params(market: str, from_date: str, to_date: str) -> dict:
    return {
        "market": market,
        "from": f"{from_date} 00:00:00",
        "to": f"{to_date} 23:59:59",
    }


def yahoo_chart(session: requests.Session, symbol: str, from_date: str, to_date: str) -> dict:
    """S&P 500 cash index (^GSPC). IOL has SPY, not the index."""
    start = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(to_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + quote(symbol, safe="")
    resp = session.get(
        url,
        params={
            "interval": "1d",
            "period1": int(start.timestamp()),
            "period2": int(end.timestamp()),
            "events": "history",
        },
        timeout=TIMEOUT_S,
    )
    payload = read_json(resp)
    chart = payload.get("chart") or {}
    if chart.get("error"):
        raise ValueError(chart["error"])
    results = chart.get("result") or []
    if not results:
        raise ValueError(f"Yahoo returned no series for {symbol}")
    return results[0]


def rows_from_yahoo(holding: str, symbol: str, chart: dict) -> list[dict]:
    timestamps = chart.get("timestamp") or []
    quote = (chart.get("indicators") or {}).get("quote") or []
    if not quote:
        raise ValueError(f"Yahoo quote missing for {symbol}")
    series = quote[0]
    opens = series.get("open") or []
    highs = series.get("high") or []
    lows = series.get("low") or []
    closes = series.get("close") or []
    volumes = series.get("volume") or []
    rows = []
    for i, ts in enumerate(timestamps):
        close = closes[i] if i < len(closes) else None
        if close is None:
            continue
        day = datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
        rows.append(
            {
                "holding": holding,
                "symbol": symbol,
                "market": "INDEX",
                "date": day,
                "open": opens[i] if i < len(opens) else None,
                "high": highs[i] if i < len(highs) else None,
                "low": lows[i] if i < len(lows) else None,
                "close": close,
                "volume": volumes[i] if i < len(volumes) else None,
            }
        )
    return to_daily(rows)


def rows_from_data(holding: str, data: dict) -> list[dict]:
    bars = data.get("bars")
    if not isinstance(bars, list):
        raise ValueError(f"expected bars list, got {data}")
    symbol = data.get("symbol") or ""
    market = data.get("market") or ""
    raw = []
    for bar in bars:
        dt = bar.get("datetime") or ""
        raw.append(
            {
                "holding": holding,
                "symbol": symbol,
                "market": market,
                "date": dt[:10],
                "datetime": dt,
                "open": bar.get("open"),
                "high": bar.get("high"),
                "low": bar.get("low"),
                "close": bar.get("close"),
                "volume": bar.get("volume"),
            }
        )
    raw.sort(key=lambda row: (row["date"], row["datetime"]))
    return to_daily(raw)


def _floats(bars: list[dict], key: str) -> list[float]:
    values = []
    for bar in bars:
        value = bar.get(key)
        if value is None or value == "":
            continue
        values.append(float(value))
    return values


def to_daily(rows: list[dict]) -> list[dict]:
    """IOL sometimes appends intraday ticks on recent sessions. Keep one OHLC bar per date."""
    by_date: dict[str, list[dict]] = {}
    for row in rows:
        if row["date"]:
            by_date.setdefault(row["date"], []).append(row)
    daily = []
    for day in sorted(by_date):
        bars = by_date[day]
        highs = _floats(bars, "high")
        lows = _floats(bars, "low")
        daily.append(
            {
                "holding": bars[0]["holding"],
                "symbol": bars[0]["symbol"],
                "market": bars[0]["market"],
                "date": day,
                "open": bars[0]["open"],
                "high": max(highs) if highs else bars[0]["high"],
                "low": min(lows) if lows else bars[0]["low"],
                "close": bars[-1]["close"],
                "volume": bars[-1]["volume"],
            }
        )
    return daily


def closes_by_date(holding: str, data: dict) -> dict[str, float]:
    return {
        row["date"]: float(row["close"])
        for row in rows_from_data(holding, data)
        if row.get("date") and row.get("close") not in (None, "")
    }


def load_mep(session: requests.Session, token: dict, from_date: str, to_date: str) -> tuple[dict[str, float], dict, list[dict]]:
    """Implied MEP = AL30 ARS / AL30D USD.

    MCP get_aum_evolution returns exchange_rate_mep, but REST
    /broker/accounts/AR/portfolio/history is not enabled for this account.
    """
    ars_data, token = get_json(
        session,
        bars_url("AL30"),
        token,
        params=bars_params("BCBA", from_date, to_date),
    )
    usd_data, token = get_json(
        session,
        bars_url("AL30D"),
        token,
        params=bars_params("BCBA", from_date, to_date),
    )
    ars = closes_by_date("AL30", ars_data)
    usd = closes_by_date("AL30D", usd_data)
    mep: dict[str, float] = {}
    fx_rows = []
    for day in sorted(set(ars) & set(usd)):
        if usd[day] == 0:
            continue
        rate = ars[day] / usd[day]
        mep[day] = rate
        fx_rows.append({"date": day, "mep": rate, "al30_ars": ars[day], "al30d_usd": usd[day]})
    return mep, token, fx_rows


def mep_on_or_before(mep: dict[str, float], day: str) -> float | None:
    if day in mep:
        return mep[day]
    prior = [d for d in mep if d <= day]
    if not prior:
        return None
    return mep[max(prior)]


def convert_ars_to_mep(rows: list[dict], mep: dict[str, float]) -> list[dict]:
    out = []
    for row in rows:
        rate = mep_on_or_before(mep, row["date"])
        if not rate:
            raise ValueError(f"no MEP rate on or before {row['date']}")
        converted = dict(row)
        for key in ("open", "high", "low", "close"):
            value = row.get(key)
            if value is None or value == "":
                continue
            converted[key] = float(value) / rate
        out.append(converted)
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "holding",
        "symbol",
        "market",
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def combine_prices() -> Path:
    rows = []
    files = []
    for path in sorted(OUT_DIR.glob("*.csv")):
        if path.name in SKIP_COMBINE:
            continue
        files.append(path.name)
        with path.open(encoding="utf-8", newline="") as handle:
            rows.extend(csv.DictReader(handle))
    if not files:
        raise SystemExit(f"No price files in {OUT_DIR}")
    rows.sort(key=lambda row: (row.get("holding") or "", row.get("date") or ""))
    write_csv(COMBINED_PATH, rows)
    holdings = {row.get("holding") for row in rows}
    print(f"combined {len(files)} files, {len(holdings)} holdings, {len(rows)} rows -> {COMBINED_PATH.name}")
    return COMBINED_PATH


def load_jobs(only: str | None) -> list[dict]:
    with MAP_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    jobs = [
        row
        for row in rows
        if row["Fetch"].strip().lower() == "yes" and row["Search_Symbol"].strip()
    ]
    if only:
        jobs = [row for row in jobs if row["Holding_Symbol"] == only]
        if not jobs:
            raise SystemExit(f"No Fetch=yes row for holding {only}")
    return jobs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-date",
        default=(date.today() - timedelta(days=365)).isoformat(),
    )
    parser.add_argument("--to-date", default=date.today().isoformat())
    parser.add_argument("--only", help="Single Holding_Symbol, e.g. AMD")
    parser.add_argument(
        "--combine-only",
        action="store_true",
        help="Stack existing per-ticker CSVs; skip the download.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.combine_only:
        combine_prices()
        return
    jobs = load_jobs(args.only)
    session = make_session()
    needs_iol = any(job["IOL_Market"].strip().upper() in MARKETS for job in jobs)
    token = load_token(session) if needs_iol else None
    failures = 0
    mep: dict[str, float] | None = None
    needs_mep = any(job["IOL_Currency"].strip().upper() == "ARS" for job in jobs)
    if needs_mep:
        mep, token, fx_rows = load_mep(session, token, args.from_date, args.to_date)
        fx_path = OUT_DIR / "MEP_FX.csv"
        fx_path.parent.mkdir(parents=True, exist_ok=True)
        with fx_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["date", "mep", "al30_ars", "al30d_usd"]
            )
            writer.writeheader()
            writer.writerows(fx_rows)
        print(f"MEP FX: {len(mep)} days -> {fx_path.name}")

    for i, job in enumerate(jobs):
        holding = job["Holding_Symbol"]
        symbol = job["Search_Symbol"].strip()
        market = job["IOL_Market"].strip().upper()
        currency = job["IOL_Currency"].strip().upper()
        label = f"{holding} -> {symbol} {market}"
        try:
            note = ""
            if market == "YAHOO":
                chart = yahoo_chart(session, symbol, args.from_date, args.to_date)
                rows = rows_from_yahoo(holding, symbol, chart)
            elif market not in MARKETS:
                print(f"{label}: market {market} is not in {sorted(MARKETS)} or YAHOO")
                failures += 1
                continue
            else:
                data, token = get_json(
                    session,
                    bars_url(symbol),
                    token,
                    params=bars_params(market, args.from_date, args.to_date),
                )
                rows = rows_from_data(holding, data)
                if currency == "ARS":
                    if not mep:
                        raise ValueError("ARS series needs MEP rates")
                    rows = convert_ars_to_mep(rows, mep)
                    note = " ARS/MEP"
        except requests.HTTPError as exc:
            print(f"{label}: {exc}")
            failures += 1
        except (requests.RequestException, ValueError, KeyError) as exc:
            print(f"{label}: {exc}")
            failures += 1
        else:
            out = OUT_DIR / f"{holding}_{symbol.lstrip('^')}_{market}.csv"
            write_csv(out, rows)
            first = rows[0]["date"] if rows else "-"
            last = rows[-1]["date"] if rows else "-"
            print(f"{label}: {len(rows)} bars {first} -> {last}{note}")
        if i + 1 < len(jobs):
            time.sleep(PAUSE_S)

    combine_prices()
    if failures:
        raise SystemExit(f"Finished with {failures} failure(s) of {len(jobs)}")


if __name__ == "__main__":
    main()
