"""Build a reduced analytical extract from a private customer master CSV.

The source file is deliberately not committed. The published extract removes
names, original customer identifiers, city/state, and literal postal codes.
Rows are shuffled, and new analysis-only IDs are assigned. This reduces direct
identifiers but is NOT a guarantee of anonymity or permission to publish.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "public" / "customer_analytics.csv"
POSTAL_FORMATS = {
    "Australia": r"^\d{4}$",
    "Canada": r"^[A-Z]\d[A-Z]\s?\d[A-Z]\d$",
    "Germany": r"^\d{5}$",
    "India": r"^\d{6}$",
    "UK": r"^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$",
    "USA": r"^\d{5}(?:-\d{4})?$",
}
COLUMNS = [
    "record_id", "customer_age", "gender", "customer_segment",
    "customer_country", "region", "customer_acquisition_cost", "postal_format_check",
]


def prepare(source: Path, output: Path = TARGET) -> pd.DataFrame:
    """Prepare a privacy-reduced analytical extract without modifying source."""
    df = pd.read_csv(source, dtype={"customer_postal_code": "string"})
    required = {
        "customer_id", "customer_name", "customer_city", "customer_state",
        "customer_postal_code", "customer_age", "gender", "customer_segment",
        "customer_country", "region", "customer_acquisition_cost",
    }
    if required - set(df.columns):
        raise ValueError(f"Missing columns: {sorted(required - set(df.columns))}")
    if df["customer_id"].isna().any() or df["customer_id"].duplicated().any():
        raise ValueError("Missing or duplicated customer IDs; check source first")

    status = pd.Series("not_checked", index=df.index, dtype="string")
    postal = df["customer_postal_code"].astype("string").str.strip().str.upper()
    for country, regex in POSTAL_FORMATS.items():
        matching_country = df["customer_country"].eq(country)
        status.loc[matching_country] = np.where(
            postal[matching_country].str.fullmatch(regex, na=False),
            "matches_pattern", "format_mismatch",
        )
    keep = [
        "customer_age", "gender", "customer_segment", "customer_country",
        "region", "customer_acquisition_cost",
    ]
    public = df[keep].copy()
    public["postal_format_check"] = status
    # Shuffle to avoid preserving source-order/customer-ID linkages.
    public = public.sample(frac=1, random_state=42).reset_index(drop=True)
    public.insert(0, "record_id", [f"ANON-{n:06d}" for n in range(1, len(public) + 1)])
    assert list(public.columns) == COLUMNS
    output.parent.mkdir(parents=True, exist_ok=True)
    public.to_csv(output, index=False)
    return public


def main() -> None:
    p = argparse.ArgumentParser(description="Reduce identifiers for a reviewable public dataset")
    p.add_argument("source", type=Path, help="PRIVATE original customer master CSV")
    p.add_argument("--output", type=Path, default=TARGET)
    args = p.parse_args()
    prepared = prepare(args.source, args.output)
    print(f"Prepared {len(prepared):,} rows at {args.output}")
    print("Review data rights and residual re-identification risk BEFORE publication.")


if __name__ == "__main__":
    main()
