"""
Phase 1: Dataset Acquisition, File Inspection & Schema Verification
Course: CS5002 / CS5004 - Analytics & Systems of Big Data
"""

import os
import glob
import pandas as pd

RAW_DIR = os.path.join("data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)


def read_csv_with_encoding(path: str):
    """Try UTF-8 first, then fall back to cp1252 / latin1 for legacy CSV encodings."""
    for enc in ("utf-8", "cp1252", "latin1"):
        try:
            df = pd.read_csv(path, low_memory=False, encoding=enc)
            return df, enc
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path} with standard encodings.")


csv_files = sorted(glob.glob(os.path.join(RAW_DIR, "**", "*.csv"), recursive=True))

if not csv_files:
    try:
        import opendatasets as od
        dataset_url = "https://www.kaggle.com/datasets/tunguz/us-elections-dataset"
        print("Downloading dataset from Kaggle into data/raw ...")
        od.download(dataset_url, data_dir=RAW_DIR)
        csv_files = sorted(glob.glob(os.path.join(RAW_DIR, "**", "*.csv"), recursive=True))
    except ImportError:
        print("opendatasets not installed. Either run `pip install opendatasets`")
        print(f"or manually unzip the CSV files into: {os.path.abspath(RAW_DIR)}")
        raise SystemExit(1)

print(f"Found {len(csv_files)} CSV file(s):")
for f in csv_files:
    size_kb = os.path.getsize(f) / 1024
    print(f"  - {f} ({size_kb:.2f} KB)")

for file_path in csv_files:
    print("\n" + "=" * 80)
    print(f"INSPECTING FILE: {os.path.basename(file_path)}")
    print("=" * 80)

    df, used_enc = read_csv_with_encoding(file_path)
    print(f"Detected Encoding     : {used_enc}")
    print(f"Shape (Rows, Columns) : {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"Exact Duplicate Rows  : {df.duplicated().sum():,}")

    summary = pd.DataFrame({
        "Column Name": df.columns,
        "Pandas Dtype": df.dtypes.astype(str).values,
        "Non-Null Count": df.notnull().sum().values,
        "Null Count": df.isnull().sum().values,
        "Null %": (df.isnull().mean().values * 100).round(2),
        "Unique Values": df.nunique(dropna=True).values,
        "Sample Values": [df[col].dropna().unique()[:3].tolist() for col in df.columns]
    })
    print("\n--- SCHEMA, NULLS & CARDINALITY ---")
    print(summary.to_string(index=False))

    print("\n--- FIRST 5 ROWS ---")
    print(df.head(5).to_string(index=False))

    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if num_cols:
        print("\n--- RAW NUMERIC SUMMARY ---")
        print(df[num_cols].describe().round(2).to_string())

    cat_cols = [c for c in df.select_dtypes(include=["object"]).columns if df[c].nunique() <= 15]
    if cat_cols:
        print("\n--- LOW-CARDINALITY CATEGORICAL DISTRIBUTIONS ---")
        for c in cat_cols:
            print(f"\nColumn '{c}':")
            print(df[c].value_counts(dropna=False).to_string())