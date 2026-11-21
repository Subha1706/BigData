"""
Phase 2: Data Preprocessing (Cleaning, Selection, Transformation)  -- CORRECTED VERSION
Course: CS5002 / CS5004 - Analytics & Systems of Big Data
Dataset: tunguz/us-elections-dataset (1976-2020-president.csv & 1976-2020-senate.csv)

KEY FIX vs. the earlier version
-------------------------------
A "contest" is now identified by CONTEST_KEY = (office, year, state, special).
Previously `special` was missing, so a regular and a special Senate race held in the
same state-year (e.g. GA 2020, MS 2018) were merged into one contest. That produced
party shares above 100%, a wrong denominator, and a wrongly flagged winner.
"""

import os
import glob
import json
import numpy as np
import pandas as pd

RAW_DIR = os.path.join("data", "raw")
PROC_DIR = os.path.join("data", "processed")
TABLES_DIR = os.path.join("outputs", "tables")

os.makedirs(PROC_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

# One contest = one office, in one year, in one state, regular OR special.
CONTEST_KEY = ["office", "year", "state", "special"]

# Concept hierarchy: state_po -> us_region (US Census regions)
STATE_TO_REGION = {
    "CT": "Northeast", "ME": "Northeast", "MA": "Northeast", "NH": "Northeast",
    "RI": "Northeast", "VT": "Northeast", "NJ": "Northeast", "NY": "Northeast",
    "PA": "Northeast",
    "IL": "Midwest", "IN": "Midwest", "MI": "Midwest", "OH": "Midwest",
    "WI": "Midwest", "IA": "Midwest", "KS": "Midwest", "MN": "Midwest",
    "MO": "Midwest", "NE": "Midwest", "ND": "Midwest", "SD": "Midwest",
    "DE": "South", "FL": "South", "GA": "South", "MD": "South",
    "NC": "South", "SC": "South", "VA": "South", "DC": "South",
    "WV": "South", "AL": "South", "KY": "South", "MS": "South",
    "TN": "South", "AR": "South", "LA": "South", "OK": "South",
    "TX": "South",
    "AZ": "West", "CO": "West", "ID": "West", "MT": "West",
    "NV": "West", "NM": "West", "UT": "West", "WY": "West",
    "AK": "West", "CA": "West", "HI": "West", "OR": "West",
    "WA": "West",
}


def read_csv_safe(path: str) -> tuple[pd.DataFrame, str]:
    """Read CSV trying UTF-8 first, then CP1252 / Latin-1."""
    for enc in ("utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(path, low_memory=False, encoding=enc), enc
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode file: {path}")


def decimal_scaling(series: pd.Series) -> pd.Series:
    """Course transformation: v' = v / 10^j, j = smallest integer with max(|v'|) < 1."""
    max_abs = series.abs().max()
    if pd.isna(max_abs) or max_abs == 0:
        return series.astype(float)
    j = int(np.floor(np.log10(max_abs))) + 1
    return series.astype(float) / (10 ** j)


def iqr_outlier_summary(series: pd.Series) -> dict:
    """Compute IQR bounds and count outliers (reported, not removed)."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    outliers = series[(series < lower) | (series > upper)]
    return {
        "Q1": round(float(q1), 2),
        "Q3": round(float(q3), 2),
        "IQR": round(float(iqr), 2),
        "Lower_Fence": round(float(lower), 2),
        "Upper_Fence": round(float(upper), 2),
        "Outlier_Count": int(len(outliers)),
        "Outlier_Pct": round(float(len(outliers) / len(series) * 100), 2) if len(series) else 0.0,
    }


def main():
    csv_files = sorted(glob.glob(os.path.join(RAW_DIR, "**", "*.csv"), recursive=True))
    pres_path = next((f for f in csv_files if "president" in os.path.basename(f).lower()), None)
    senate_path = next((f for f in csv_files if "senate" in os.path.basename(f).lower()), None)

    if not pres_path or not senate_path:
        raise FileNotFoundError("Expected both 1976-2020-president.csv and 1976-2020-senate.csv in data/raw.")

    df_pres_raw, pres_enc = read_csv_safe(pres_path)
    df_sen_raw, sen_enc = read_csv_safe(senate_path)

    before_stats = {
        "pres_rows": int(len(df_pres_raw)),
        "pres_cols": int(df_pres_raw.shape[1]),
        "pres_encoding": pres_enc,
        "pres_nulls_total": int(df_pres_raw.isnull().sum().sum()),
        "pres_dups": int(df_pres_raw.duplicated().sum()),
        "senate_rows": int(len(df_sen_raw)),
        "senate_cols": int(df_sen_raw.shape[1]),
        "senate_encoding": sen_enc,
        "senate_nulls_total": int(df_sen_raw.isnull().sum().sum()),
        "senate_dups": int(df_sen_raw.duplicated().sum()),
        "combined_raw_rows": int(len(df_pres_raw) + len(df_sen_raw)),
    }

    # =====================================================================
    # (i) DATA CLEANING
    # =====================================================================
    df_pres = df_pres_raw.copy()
    # The presidential file has no stage/special/unofficial columns: add them so schemas align.
    df_pres["stage"] = "gen"
    df_pres["special"] = False
    df_pres["unofficial"] = False

    df_sen = df_sen_raw.copy()

    # Drop empty / constant / redundant columns
    drop_cols = ["notes", "version", "district", "mode", "state_cen", "state_ic"]
    df_pres = df_pres.drop(columns=[c for c in drop_cols if c in df_pres.columns])
    df_sen = df_sen.drop(columns=[c for c in drop_cols if c in df_sen.columns])

    combined = pd.concat([df_pres, df_sen], ignore_index=True)
    rows_after_concat = len(combined)

    combined = combined.drop_duplicates().reset_index(drop=True)
    rows_after_dedup = len(combined)

    # Standardize text columns (strip whitespace; upper-case everything except candidate names)
    for col in ["state", "state_po", "office", "candidate", "party_detailed", "party_simplified", "stage"]:
        if col in combined.columns:
            combined[col] = combined[col].astype("string").str.strip()
            if col != "candidate":
                combined[col] = combined[col].str.upper()

    # Missing categorical labels get explicit categories (they are mostly write-in / scattering rows)
    combined["candidate"] = combined["candidate"].fillna("UNSPECIFIED_OR_WRITEIN")
    combined["party_detailed"] = combined["party_detailed"].fillna("UNSPECIFIED")
    combined["party_simplified"] = combined["party_simplified"].fillna("OTHER")

    # Standardize boolean flags (writein has 3 NaN in the presidential file)
    for bcol in ["writein", "special", "unofficial"]:
        combined[bcol] = (
            combined[bcol]
            .astype("string").str.strip().str.lower()
            .map({"true": True, "false": False, "1": True, "0": False})
            .astype("boolean")      # nullable boolean: avoids the object-downcasting FutureWarning
            .fillna(False)
            .astype(bool)
        )

    # Row-level validity rules
    invalid_mask = (
        (combined["totalvotes"] <= 0)
        | (combined["candidatevotes"] < 0)
        | (combined["candidatevotes"] > combined["totalvotes"])
    )
    invalid_count = int(invalid_mask.sum())
    cleaned = combined[~invalid_mask].copy().reset_index(drop=True)

    non_gen_count = int((cleaned["stage"] != "GEN").sum())
    cleaned_gen = cleaned[cleaned["stage"] == "GEN"].copy().reset_index(drop=True)

    # Suspiciously small denominators (e.g. totalvotes = 1): flagged and exported for manual review.
    # In the data these are Louisiana rows with candidatevotes = totalvotes = 1: a placeholder
    # convention for uncontested races where no ballots were counted, NOT real turnout.
    # They are exported for the report, then excluded so they cannot distort shares,
    # log-features, scatter plots, KNN or AGNES.
    placeholder_mask = cleaned_gen["totalvotes"] < 1000
    low_total = cleaned_gen[placeholder_mask].copy()
    low_total.to_csv(os.path.join(TABLES_DIR, "phase2_low_totalvotes_rows.csv"), index=False)
    cleaned_gen = cleaned_gen[~placeholder_mask].copy().reset_index(drop=True)

    outlier_report = {
        "candidatevotes_all_cleaned": iqr_outlier_summary(cleaned["candidatevotes"]),
        "totalvotes_all_cleaned": iqr_outlier_summary(cleaned["totalvotes"]),
        "candidatevotes_gen": iqr_outlier_summary(cleaned_gen["candidatevotes"]),
        "totalvotes_gen": iqr_outlier_summary(cleaned_gen["totalvotes"]),
    }

    # =====================================================================
    # (ii) DATA SELECTION & (iii) DATA TRANSFORMATION
    # =====================================================================
    cleaned_gen["us_region"] = cleaned_gen["state_po"].map(STATE_TO_REGION).fillna("OTHER_REGION")

    cleaned_gen["election_era"] = pd.cut(
        cleaned_gen["year"],
        bins=[1970, 1989, 2004, 2025],
        labels=["Era1_1976_1988", "Era2_1990_2004", "Era3_2005_2021"],
    ).astype(str)

    cleaned_gen["vote_share_pct"] = (cleaned_gen["candidatevotes"] / cleaned_gen["totalvotes"]) * 100.0
    cleaned_gen["writein_votes_row"] = np.where(cleaned_gen["writein"], cleaned_gen["candidatevotes"], 0)

    # ---- Diagnostics: how many state-years have more than one contest? ----
    multi_contest = (
        cleaned_gen.groupby(["office", "year", "state"])["special"].nunique().loc[lambda s: s > 1]
    )
    multi_contest.rename("n_distinct_special_flags").reset_index().to_csv(
        os.path.join(TABLES_DIR, "phase2_multi_contest_state_years.csv"), index=False
    )

    # ---- Guard: each contest should have ONE denominator (totalvotes) ----
    tv_per_contest = cleaned_gen.groupby(CONTEST_KEY)["totalvotes"].nunique()
    inconsistent_contests = int((tv_per_contest > 1).sum())
    if inconsistent_contests:
        print(f"[WARN] {inconsistent_contests} contests have >1 distinct totalvotes; using max() as denominator.")

    # ---- Contest x party aggregation (CORRECTED KEY) ----
    contest_party = (
        cleaned_gen.groupby(
            CONTEST_KEY + ["election_era", "state_po", "state_fips", "us_region", "party_simplified"],
            as_index=False,
        )
        .agg(
            party_votes=("candidatevotes", "sum"),
            total_votes=("totalvotes", "max"),
            num_candidates=("candidate", "count"),
            writein_votes=("writein_votes_row", "sum"),
        )
    )

    contest_party["party_share_pct"] = (contest_party["party_votes"] / contest_party["total_votes"]) * 100.0
    contest_party["writein_share_pct"] = (contest_party["writein_votes"] / contest_party["total_votes"]) * 100.0

    # ---- Deterministic ranking within each contest (ties broken alphabetically by party) ----
    sorted_cp = contest_party.sort_values(
        CONTEST_KEY + ["party_votes", "party_simplified"],
        ascending=[True, True, True, True, False, True],
    ).reset_index(drop=True)
    sorted_cp["rank_in_contest"] = sorted_cp.groupby(CONTEST_KEY).cumcount() + 1
    sorted_cp["is_contest_winner"] = (sorted_cp["rank_in_contest"] == 1).astype(int)

    # ---- Winner party and margin (top-1 share minus top-2 share) ----
    top1 = (
        sorted_cp[sorted_cp["rank_in_contest"] == 1][CONTEST_KEY + ["party_share_pct", "party_simplified"]]
        .rename(columns={"party_share_pct": "top1_share", "party_simplified": "winner_party"})
    )
    top2 = (
        sorted_cp[sorted_cp["rank_in_contest"] == 2][CONTEST_KEY + ["party_share_pct"]]
        .rename(columns={"party_share_pct": "top2_share"})
    )
    top_shares = top1.merge(top2, on=CONTEST_KEY, how="left")
    top_shares["top2_share"] = top_shares["top2_share"].fillna(0.0)
    top_shares["margin_pct"] = top_shares["top1_share"] - top_shares["top2_share"]
    top_shares["is_close_race_lt5pct"] = (top_shares["margin_pct"] < 5.0).astype(int)

    contests_df = sorted_cp.merge(
        top_shares[CONTEST_KEY + ["winner_party", "margin_pct", "is_close_race_lt5pct"]],
        on=CONTEST_KEY,
        how="left",
    )

    # ---- Validation assertions (these would have caught the original bug) ----
    assert contests_df["party_share_pct"].max() <= 100.0 + 1e-9, \
        f"party_share_pct > 100 found: {contests_df['party_share_pct'].max():.2f}"
    assert contests_df.groupby(CONTEST_KEY)["is_contest_winner"].sum().eq(1).all(), \
        "Each contest must have exactly one winner row."
    assert contests_df["margin_pct"].between(0, 100 + 1e-9).all(), "margin_pct out of [0, 100]."

    # ---- Log features ----
    contests_df["log_total_votes"] = np.log1p(contests_df["total_votes"])
    contests_df["log_party_votes"] = np.log1p(contests_df["party_votes"])

    # ---- Course transformations: min-max, z-score, decimal scaling ----
    # NOTE: fitted on the full table. Fine for AGNES (unsupervised). For KNN, refit the
    # scaler on the TRAIN split only (do not reuse these columns).
    for col in ["party_share_pct", "margin_pct", "log_total_votes", "log_party_votes"]:
        s = contests_df[col].astype(float)
        min_v, max_v = s.min(), s.max()
        rng = max_v - min_v if max_v != min_v else 1.0
        std_v = s.std() if s.std() != 0 else 1.0
        contests_df[f"{col}_minmax"] = (s - min_v) / rng
        contests_df[f"{col}_zscore"] = (s - s.mean()) / std_v
        contests_df[f"{col}_decscale"] = decimal_scaling(s)

    # ---- Discretization for DIC / CLOSET ----
    contests_df["share_bin"] = pd.cut(
        contests_df["party_share_pct"],
        bins=[-0.01, 5.0, 35.0, 50.0, 100.01],
        labels=["Share_Negligible_0_5", "Share_Minor_5_35", "Share_Competitive_35_50", "Share_Majority_50_100"],
    ).astype(str)

    contests_df["turnout_bin"] = pd.qcut(
        contests_df["total_votes"],
        q=3,
        labels=["Turnout_Low_Tertile", "Turnout_Mid_Tertile", "Turnout_High_Tertile"],
    ).astype(str)

    contests_df["margin_bin"] = pd.cut(
        contests_df["margin_pct"],
        bins=[-0.01, 5.0, 15.0, 100.01],
        labels=["Margin_Close_lt5", "Margin_Moderate_5_15", "Margin_Safe_gt15"],
    ).astype(str)

    # No NaN-derived items may leak into the transactions
    for b in ["share_bin", "turnout_bin", "margin_bin"]:
        assert contests_df[b].ne("nan").all(), f"{b} contains 'nan' items."

    # ---- Transactions: one per contest-party observation ----
    transactions_df = pd.DataFrame({
        "tid": [f"T{i + 1:05d}" for i in range(len(contests_df))],
        "items": contests_df.apply(
            lambda r: ";".join([
                f"Office={str(r['office']).replace(' ', '_')}",
                f"Contest={'Special' if r['special'] else 'Regular'}",
                f"Era={r['election_era']}",
                f"Region={r['us_region']}",
                f"Party={r['party_simplified']}",
                f"Share={r['share_bin']}",
                f"Turnout={r['turnout_bin']}",
                f"Margin={r['margin_bin']}",
                f"Winner={'Yes' if r['is_contest_winner'] == 1 else 'No'}",
            ]),
            axis=1,
        ),
    })

    # =====================================================================
    # SAVE OUTPUTS
    # =====================================================================
    cleaned_gen.drop(columns=["writein_votes_row"]).to_csv(
        os.path.join(PROC_DIR, "elections_cleaned_gen.csv"), index=False
    )
    contests_df.to_csv(os.path.join(PROC_DIR, "contests_modeling.csv"), index=False)
    transactions_df.to_csv(os.path.join(PROC_DIR, "transactions_fpm.csv"), index=False)

    n_contests = int(contests_df.groupby(CONTEST_KEY).ngroups)
    after_summary = {
        "rows_after_concat": int(rows_after_concat),
        "rows_after_dedup": int(rows_after_dedup),
        "invalid_vote_rows_removed": int(invalid_count),
        "non_general_stage_rows_filtered": int(non_gen_count),
        "cleaned_gen_rows": int(len(cleaned_gen)),
        "cleaned_gen_cols": int(cleaned_gen.shape[1]),
        "cleaned_gen_nulls_remaining": int(cleaned_gen.isnull().sum().sum()),
        "low_totalvotes_rows_flagged_lt1000": int(len(low_total)),
        "state_years_with_multiple_contests": int(len(multi_contest)),
        "contests_with_inconsistent_totalvotes": inconsistent_contests,
        "distinct_contests": n_contests,
        "contests_modeling_rows": int(len(contests_df)),
        "contests_modeling_cols": int(contests_df.shape[1]),
        "max_party_share_pct": round(float(contests_df["party_share_pct"].max()), 4),
        "transactions_count": int(len(transactions_df)),
    }

    quality_report = {
        "contest_key": CONTEST_KEY,
        "before_cleaning": before_stats,
        "after_cleaning_and_transformation": after_summary,
        "outlier_investigation_iqr": outlier_report,
    }
    with open(os.path.join(TABLES_DIR, "phase2_quality_summary.json"), "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)

    comp_table = pd.DataFrame([
        {"Stage": "Raw Presidential CSV", "Rows": before_stats["pres_rows"], "Cols": before_stats["pres_cols"], "Total_Nulls": before_stats["pres_nulls_total"]},
        {"Stage": "Raw Senate CSV", "Rows": before_stats["senate_rows"], "Cols": before_stats["senate_cols"], "Total_Nulls": before_stats["senate_nulls_total"]},
        {"Stage": "After Invalid Row Removal", "Rows": len(cleaned), "Cols": cleaned.shape[1], "Total_Nulls": int(cleaned.isnull().sum().sum())},
        {"Stage": "Cleaned General Elections (EDA)", "Rows": len(cleaned_gen), "Cols": cleaned_gen.shape[1], "Total_Nulls": int(cleaned_gen.isnull().sum().sum())},
        {"Stage": "Contest-Party Modeling Table", "Rows": len(contests_df), "Cols": contests_df.shape[1], "Total_Nulls": int(contests_df.isnull().sum().sum())},
        {"Stage": "Transactional Table (DIC/CLOSET)", "Rows": len(transactions_df), "Cols": transactions_df.shape[1], "Total_Nulls": int(transactions_df.isnull().sum().sum())},
    ])
    comp_table.to_csv(os.path.join(TABLES_DIR, "phase2_before_after_table.csv"), index=False)

    # =====================================================================
    # CONSOLE REPORT
    # =====================================================================
    print("=== PHASE 2 PREPROCESSING COMPLETE (CORRECTED CONTEST KEY) ===")
    print(f"Contest key: {CONTEST_KEY}")

    print("\n--- BEFORE / AFTER TABLE ---")
    print(comp_table.to_string(index=False))

    print("\n--- CONTEST-KEY DIAGNOSTICS ---")
    print(f"State-years with >1 contest (regular + special): {len(multi_contest)}")
    if len(multi_contest):
        print(multi_contest.reset_index().to_string(index=False))
    print(f"Distinct contests: {n_contests}")
    print(f"Max party_share_pct after fix: {contests_df['party_share_pct'].max():.4f}  (must be <= 100)")
    print(f"Rows with totalvotes < 1000 (exported for review): {len(low_total)}")
    if len(low_total):
        print(low_total[["office", "year", "state_po", "candidate", "candidatevotes", "totalvotes"]]
              .to_string(index=False))

    print("\n--- party_share_pct DESCRIBE ---")
    print(contests_df["party_share_pct"].describe().round(2).to_string())

    print("\n--- IQR OUTLIER INVESTIGATION (RETAINED, NOT DROPPED) ---")
    for k, v in outlier_report.items():
        print(f"{k}: {v}")

    print("\n--- SAMPLE CONTESTS MODELING ROWS ---")
    sample_cols = [
        "office", "year", "state_po", "special", "us_region", "party_simplified",
        "party_share_pct", "party_share_pct_minmax", "party_share_pct_zscore",
        "margin_pct", "is_contest_winner", "share_bin",
    ]
    print(contests_df[sample_cols].head(8).to_string(index=False))

    print("\n--- SAMPLE TRANSACTIONS (FIRST 5) ---")
    print(transactions_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()