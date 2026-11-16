"""Publish the risk/return scatter plot to Datawrapper, one chart per window.

Usage:
    python src/datawrapper_risk_return.py              # all four windows
    python src/datawrapper_risk_return.py --window ytd # a single window

Requires DATAWRAPPER_API_TOKEN in the environment or in .env. Each run creates
new charts; the published versions are managed directly in Datawrapper.
"""

from __future__ import annotations

import argparse
import io
import os
from pathlib import Path

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parent.parent
RISK_RETURN = BASE_DIR / "data/financial_data/outputs/risk_return.csv"
API = "https://api.datawrapper.de/v3"

# Same blue as the "Resto" bars in images/industry_group.svg.
SERIES_COLOR = "#2563eb"

# Sectors with little weight are folded into "Otros" to keep the legend readable.
MERGE_INTO_OTROS = {"Materiales", "Utilities", "Financiero", "FCI", "Deuda soberana"}
SECTOR_COLORS = {
    "Tecnología": "#2563eb",
    "Energía": "#c2410c",
    "ETF / Mercado amplio": "#0f766e",
    "Consumo discrecional": "#7c3aed",
    "Comunicaciones": "#be185d",
    "Consumo básico": "#b45309",
    "Otros": "#94a3b8",
}
SECTOR_ORDER = list(SECTOR_COLORS)

WINDOW_LABELS = {
    "full": "12 meses",
    "ytd": "YTD",
    "6m": "6 meses",
    "30d": "30 días",
}


def load_token() -> str:
    token = os.environ.get("DATAWRAPPER_API_TOKEN")
    if token:
        return token.strip()
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "DATAWRAPPER_API_TOKEN":
                return value.strip().strip('"').strip("'")
    raise SystemExit(
        "DATAWRAPPER_API_TOKEN not found. Add it to .env, e.g.\n"
        "DATAWRAPPER_API_TOKEN=dw_xxxxxxxxxxxx"
    )


def build_frame(window: str) -> pd.DataFrame:
    df = pd.read_csv(RISK_RETURN)
    part = df[df["window"] == window].copy()
    if part.empty:
        raise SystemExit(f"No rows for window={window!r}")
    part = part.dropna(subset=["vol_ann", "total_return", "Weight_Pct"])
    part = part.sort_values("Weight_Pct", ascending=False)

    def pct(series: pd.Series) -> pd.Series:
        return (series.astype(float) * 100).round(2)

    return pd.DataFrame(
        {
            "Activo": part["holding"].astype(str),
            "Descripción": part["Description"].fillna(part["holding"]).astype(str),
            "Volatilidad anualizada (%)": pct(part["vol_ann"]),
            "Retorno (%)": pct(part["total_return"]),
            "Peso (%)": part["Weight_Pct"].astype(float).round(2),
            "Sector": part["Sector"].fillna("Sin datos").astype(str),
            "Tipo": part["Type"].fillna("Sin datos").astype(str),
            "sector_chart": part["Sector"]
            .fillna("Otros")
            .map(lambda value: value if value in SECTOR_COLORS else "Otros"),
            # Lowercase duplicates used by the Datawrapper tooltip expressions.
            "activo": part["holding"].astype(str),
            "descripcion": part["Description"].fillna(part["holding"]).astype(str),
            "vol_pct": pct(part["vol_ann"]),
            "retorno_pct": pct(part["total_return"]),
            "peso_pct": part["Weight_Pct"].astype(float).round(2),
            "sector": part["Sector"].fillna("Sin datos").astype(str),
            "tipo": part["Type"].fillna("Sin datos").astype(str),
        }
    )


def to_csv(frame: pd.DataFrame) -> bytes:
    buffer = io.StringIO()
    frame.to_csv(buffer, index=False)
    return buffer.getvalue().encode("utf-8")


def api_headers(token: str, content_type: str = "application/json") -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": content_type}


def check(response: requests.Response, action: str) -> dict:
    if not response.ok:
        raise SystemExit(f"{action} failed ({response.status_code}): {response.text}")
    return response.json() if response.content else {}


def metadata_for(window: str, as_of: str) -> dict:
    label = WINDOW_LABELS[window]
    return {
        "axes": {
            "x": "Volatilidad anualizada (%)",
            "y": "Retorno (%)",
            "size": "Peso (%)",
            "color": "sector_chart",
            "labels": "Activo",
        },
        "visualize": {
            "size": "dynamic",
            "max-size": 48,
            "base-color": SERIES_COLOR,
            "show-size-legend": False,
            "show-color-key": True,
            "color-by-column": True,
            "color-category": {
                "map": SECTOR_COLORS,
                "categoryOrder": SECTOR_ORDER,
                "excludeFromKey": [],
            },
            "opacity": 0.9,
            "show-outlines": True,
            "tooltip": {
                "enabled": True,
                "title": "{{ activo }} — {{ descripcion }}",
                "body": (
                    "Peso en cartera: <b>{{ peso_pct }}%</b><br>"
                    "Volatilidad anualizada: {{ vol_pct }}%<br>"
                    "Retorno del período: {{ retorno_pct }}%<br>"
                    "{{ sector }} · {{ tipo }}"
                ),
                "sticky": False,
            },
        },
        "describe": {
            "intro": (
                f"Volatilidad anualizada (desvío estándar diario × √252) vs. retorno "
                f"total del período ({label}). El tamaño del círculo representa el peso "
                f"de cada activo en la cartera y el color, su sector. Los sectores de "
                f"menor peso se agrupan en «Otros». Datos al {as_of}, en USD."
            ),
            "byline": "Fuente: IOL REST API · elaboración propia",
            "source-name": "IOL / precios de mercado",
        },
        "annotate": {
            "notes": (
                "La volatilidad se calcula sobre retornos diarios y se anualiza con 252 "
                "ruedas. El retorno es el cambio porcentual entre el primer y el último "
                "precio del período. Se excluyen activos sin peso asignado."
            )
        },
    }


def publish(token: str, window: str, frame: pd.DataFrame, as_of: str) -> dict:
    title = f"Riesgo vs. retorno de la cartera — {WINDOW_LABELS[window]}"
    created = check(
        requests.post(
            f"{API}/charts",
            headers=api_headers(token),
            json={
                "title": title,
                "type": "d3-scatter-plot",
                "language": "es-AR",
                "lastEditStep": 3,
            },
            timeout=30,
        ),
        "Create chart",
    )
    chart_id = created["id"]

    check(
        requests.put(
            f"{API}/charts/{chart_id}/data",
            headers=api_headers(token, "text/csv"),
            data=to_csv(frame),
            timeout=30,
        ),
        f"Upload data for {window}",
    )

    check(
        requests.patch(
            f"{API}/charts/{chart_id}",
            headers=api_headers(token),
            json={"metadata": metadata_for(window, as_of)},
            timeout=30,
        ),
        f"Update metadata for {window}",
    )

    published = check(
        requests.post(
            f"{API}/charts/{chart_id}/publish",
            headers=api_headers(token),
            timeout=60,
        ),
        f"Publish {window}",
    )

    return {
        "id": chart_id,
        "embed": f"https://datawrapper.dwcdn.net/{chart_id}/",
        "publicUrl": f"https://datawrapper.de/_/{chart_id}/",
        "version": published.get("version"),
        "as_of": as_of,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--window",
        nargs="+",
        choices=sorted(WINDOW_LABELS),
        help="Window(s) to publish. Defaults to all four.",
    )
    args = parser.parse_args()

    token = load_token()
    as_of = pd.read_csv(RISK_RETURN)["as_of"].iloc[0]
    windows = args.window or list(WINDOW_LABELS)

    for window in windows:
        frame = build_frame(window)
        chart = publish(token, window, frame, as_of)
        print(f"{window:4s}  id={chart['id']}  {chart['embed']}  ({len(frame)} activos)")


if __name__ == "__main__":
    main()
