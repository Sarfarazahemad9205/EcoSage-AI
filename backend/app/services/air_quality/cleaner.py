
import json
import re
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd


# --------------------------------------------------
# 1. PROJECT PATHS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[4]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "openaq"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed" / "openaq"
REJECTED_DIR = PROJECT_ROOT / "data" / "rejected" / "openaq"


# --------------------------------------------------
# 2. FIND LATEST RAW JSON FILE
# --------------------------------------------------

def find_latest_raw_file():

    files = list(RAW_DIR.glob("sensor_12237600_*.json"))

    if not files:
        raise FileNotFoundError(
            f"No raw JSON files found in {RAW_DIR}"
        )

    return max(files, key=lambda file: file.stat().st_mtime)


# --------------------------------------------------
# 3. EXTRACT COLLECTION TIME FROM FILENAME
# --------------------------------------------------

def get_collection_time(file_path):

    match = re.search(
        r"_(\d{8}T\d{6}Z)\.json$",
        file_path.name
    )

    if not match:
        raise ValueError(
            "Collection timestamp missing from filename"
        )

    return datetime.strptime(
        match.group(1),
        "%Y%m%dT%H%M%SZ"
    ).replace(tzinfo=timezone.utc)


# --------------------------------------------------
# 4. EXTRACT MEASUREMENTS
# --------------------------------------------------

def extract_measurements(data, collected_at):

    records = []

    for item in data.get("results", []):

        parameter = item.get("parameter") or {}
        period = item.get("period") or {}
        datetime_from = period.get("datetimeFrom") or {}
        coverage = item.get("coverage") or {}
        flag_info = item.get("flagInfo") or {}

        records.append({

            "sensor_id": 12237600,
            "location_id": 3409388,

            "parameter": parameter.get("name"),
            "value": item.get("value"),
            "unit": parameter.get("units"),

            "observed_at": datetime_from.get("utc"),
            "interval": period.get("interval"),

            "quality_flag": flag_info.get("hasFlags"),

            "coverage_percent": coverage.get(
                "percentCoverage"
            ),

            "collected_at": collected_at

        })

    return records


# --------------------------------------------------
# 5. VALIDATE MEASUREMENTS
# --------------------------------------------------

def validate_measurements(df):

    valid_records = []
    rejected_records = []

    for _, row in df.iterrows():

        reasons = []

        if pd.isna(row["value"]):
            reasons.append("Missing measurement value")
        else:
            try:
                value = float(row["value"])

                if not pd.notna(value):
                    reasons.append("Invalid measurement value")
                elif value < 0:
                    reasons.append("Negative measurement value")

            except (ValueError, TypeError):
                reasons.append("Non-numeric measurement value")

        if not row["parameter"]:
            reasons.append("Missing parameter")

        if not row["unit"]:
            reasons.append("Missing measurement unit")

        if not row["observed_at"]:
            reasons.append("Missing observation timestamp")
        elif pd.isna(row["observed_at"]):
            reasons.append("Invalid observation timestamp")

        if row["quality_flag"] is True:
            reasons.append("Source reported quality flags")

        if reasons:
            rejected = row.to_dict()
            rejected["rejection_reason"] = "; ".join(reasons)
            rejected_records.append(rejected)

        else:
            valid_records.append(row.to_dict())

    return pd.DataFrame(valid_records), pd.DataFrame(rejected_records)


# --------------------------------------------------
# 6. MAIN CLEANING PIPELINE
# --------------------------------------------------

def main():

    print("Starting EcoSage AI Silver Pipeline...")

    raw_file = find_latest_raw_file()

    print("Raw file:", raw_file.name)

    collected_at = get_collection_time(raw_file)

    # Load original JSON
    with open(raw_file, "r", encoding="utf-8") as file:
        raw_data = json.load(file)

    # Extract records
    records = extract_measurements(
        raw_data,
        collected_at
    )

    df = pd.DataFrame(records)

    print("Records extracted:", len(df))

    if df.empty:
        print("No measurements found.")
        return

    # Normalize numeric fields
    df["value"] = pd.to_numeric(
        df["value"],
        errors="coerce"
    )

    df["coverage_percent"] = pd.to_numeric(
        df["coverage_percent"],
        errors="coerce"
    )

    # Normalize timestamps
    df["observed_at"] = pd.to_datetime(
        df["observed_at"],
        utc=True,
        errors="coerce"
    )

    # Detect duplicates
    duplicate_mask = df.duplicated(
        subset=[
            "sensor_id",
            "parameter",
            "observed_at",
            "value",
            "unit"
        ],
        keep="first"
    )

    duplicates = df[duplicate_mask].copy()

    if not duplicates.empty:
        duplicates["rejection_reason"] = "Duplicate measurement"

    df = df[~duplicate_mask].copy()

    # Validate remaining records
    valid_df, rejected_df = validate_measurements(df)

    # Combine rejected records
    if not duplicates.empty:
        rejected_df = pd.concat(
            [rejected_df, duplicates],
            ignore_index=True
        )

    # Save outputs
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REJECTED_DIR.mkdir(parents=True, exist_ok=True)

    valid_path = PROCESSED_DIR / "measurements.csv"
    rejected_path = REJECTED_DIR / "rejected_measurements.csv"

    valid_df.to_csv(valid_path, index=False)

    rejected_df.to_csv(rejected_path, index=False)

    # Final summary
    print("\n========== PIPELINE SUMMARY ==========")

    print("Original records:", len(records))
    print("Valid records:", len(valid_df))
    print("Rejected records:", len(rejected_df))
    print("Duplicates:", len(duplicates))

    print("\nProcessed file:", valid_path)
    print("Rejected file:", rejected_path)

    print("\nSilver pipeline completed!")


if __name__ == "__main__":
    main()
