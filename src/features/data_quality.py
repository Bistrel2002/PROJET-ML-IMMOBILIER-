import pandas as pd

# ---------------------------------------------------------------------------
# Constraints applied to the raw CSV column names (before data_cleaner renames)
# ---------------------------------------------------------------------------
DATA_CONSTRAINTS = {
    "price":    lambda v: v > 0,
    "surface":  lambda v: v > 0,
    "price_m2": lambda v: v < 50000,
    "city":     lambda v: v is not None and str(v).strip() != "",
    "type":     lambda v: v is not None and str(v).strip() != "",
}


def extract_m2(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 2a — Ensures the 'surface' and 'price_m2' columns are populated.

    Strategy:
    - If the CSV already has a 'surface' column (from the scraper), use it.
    - For rows where surface is NaN, try to extract the value from the
      listing title (e.g. "Appartement 90 m²").
    - Compute 'price_m2' = price / surface.

    :param df: raw DataFrame from data_ingest.load_raw()
    :return: DataFrame with 'surface' and 'price_m2' columns guaranteed
    """
    df = df.copy()

    # If 'surface' doesn't exist at all, create it as NaN
    if "surface" not in df.columns:
        df["surface"] = float("nan")

    # Fill missing surface values from the title column
    if "title" in df.columns:
        extracted = df["title"].str.extract(r"(?P<area>\d+)\s*m[²2]").area
        df["surface"] = df["surface"].fillna(pd.to_numeric(extracted, errors="coerce"))

    df["surface"] = pd.to_numeric(df["surface"], errors="coerce")

    # Compute price per m² (only where surface is valid)
    if "price" in df.columns:
        df["price_m2"] = df["price"] / df["surface"]
    else:
        df["price_m2"] = float("nan")

    return df


def validate_constraints(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 2b — Filters out rows that violate quality constraints.

    Rows are dropped when:
    - price  ≤ 0 or missing
    - surface ≤ 0 or missing
    - price_m2 ≥ 50 000 (unrealistic)
    - city or type is null / empty

    :param df: DataFrame after extract_m2()
    :return: filtered DataFrame
    """
    df = df.copy()
    for column, condition in DATA_CONSTRAINTS.items():
        if column in df.columns:
            # Drop rows that are NaN OR fail the condition
            df = df[df[column].notna() & df[column].map(condition)]
    return df


def data_quality(df: pd.DataFrame) -> pd.DataFrame:
    """
    Step 2 of the pipeline — quality checks on the raw DataFrame.

    Chains: extract_m2 → validate_constraints

    :param df: raw DataFrame from data_ingest.load_raw()
    :return: quality-filtered DataFrame, still with raw column names,
             ready for data_cleaner.clean_leboncoin_data()
    """
    df = extract_m2(df)
    df = validate_constraints(df)
    return df
