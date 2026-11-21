"""
Phase 3: Exhaustive Descriptive Statistics & 11 Course-Aligned Visualizations
Course: CS5002 / CS5004 - Analytics & Systems of Big Data
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROC_DIR = os.path.join("data", "processed")
PLOTS_DIR = os.path.join("outputs", "plots")
TABLES_DIR = os.path.join("outputs", "tables")

os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)

plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False


def save_fig(filename: str) -> str:
    path = os.path.join(PLOTS_DIR, filename)
    plt.tight_layout()
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.close()
    return path


def main():
    df_cand = pd.read_csv(os.path.join(PROC_DIR, "elections_cleaned_gen.csv"))
    df_cont = pd.read_csv(os.path.join(PROC_DIR, "contests_modeling.csv"))

    # --- 1. EXHAUSTIVE DESCRIPTIVE STATISTICS ---
    num_cols = ["candidatevotes", "totalvotes", "vote_share_pct"]
    desc_cand = df_cand[num_cols].agg(["count", "mean", "std", "min", "median", "max"]).T
    desc_cand["q25"] = df_cand[num_cols].quantile(0.25)
    desc_cand["q75"] = df_cand[num_cols].quantile(0.75)
    desc_cand["iqr"] = desc_cand["q75"] - desc_cand["q25"]
    desc_cand = desc_cand.round(2)
    desc_cand.to_csv(os.path.join(TABLES_DIR, "phase3_desc_candidate_numeric.csv"))

    cont_cols = ["party_votes", "total_votes", "party_share_pct", "margin_pct"]
    desc_cont = df_cont[cont_cols].agg(["count", "mean", "std", "min", "median", "max"]).T
    desc_cont["q25"] = df_cont[cont_cols].quantile(0.25)
    desc_cont["q75"] = df_cont[cont_cols].quantile(0.75)
    desc_cont["iqr"] = desc_cont["q75"] - desc_cont["q25"]
    desc_cont = desc_cont.round(2)
    desc_cont.to_csv(os.path.join(TABLES_DIR, "phase3_desc_contest_numeric.csv"))

    party_freq = (
        df_cont.groupby("party_simplified", as_index=False)
        .agg(
            contest_party_rows=("party_votes", "count"),
            total_party_votes=("party_votes", "sum"),
            mean_share_pct=("party_share_pct", "mean"),
            median_share_pct=("party_share_pct", "median"),
            wins=("is_contest_winner", "sum"),
        )
    )
    grand_votes = party_freq["total_party_votes"].sum()
    party_freq["vote_share_of_all_votes_pct"] = (party_freq["total_party_votes"] / grand_votes) * 100.0
    party_freq["sector_angle_deg"] = (party_freq["vote_share_of_all_votes_pct"] / 100.0) * 360.0
    party_freq = party_freq.sort_values("total_party_votes", ascending=False).round(2)
    party_freq.to_csv(os.path.join(TABLES_DIR, "phase3_party_summary.csv"), index=False)

    office_freq = (
        df_cont.groupby("office", as_index=False)
        .agg(
            rows=("party_votes", "count"),
            total_votes=("party_votes", "sum"),
            mean_margin_pct=("margin_pct", "mean"),
            close_races_lt5pct=("is_close_race_lt5pct", "sum"),
        )
        .round(2)
    )
    office_freq.to_csv(os.path.join(TABLES_DIR, "phase3_office_summary.csv"), index=False)

    region_freq = (
        df_cont.groupby("us_region", as_index=False)
        .agg(
            rows=("party_votes", "count"),
            total_votes=("party_votes", "sum"),
            mean_share_pct=("party_share_pct", "mean"),
            mean_margin_pct=("margin_pct", "mean"),
        )
        .sort_values("total_votes", ascending=False)
        .round(2)
    )
    region_freq.to_csv(os.path.join(TABLES_DIR, "phase3_region_summary.csv"), index=False)

    generated_plots = []

    # --- PLOT 1: Pie Chart (4 simplified party categories <= 5 categories) ---
    plt.figure(figsize=(7.5, 5.5))
    plt.pie(
        party_freq["total_party_votes"],
        labels=[f"{p}\n({pct:.1f}%)" for p, pct in zip(party_freq["party_simplified"], party_freq["vote_share_of_all_votes_pct"])],
        autopct="%1.1f%%",
        startangle=140,
        colors=["#2b6cb0", "#c53030", "#d69e2e", "#718096"],
    )
    plt.title("Plot 1: Total Vote Share by Simplified Party (Cleaned General Elections)")
    generated_plots.append(save_fig("plot01_pie_party_share.png"))

    # --- PLOT 2: Exploded Pie Chart (Party share with minor/third parties exploded) ---
    plt.figure(figsize=(7.5, 5.5))
    explode = [0.03 if p in ("DEMOCRAT", "REPUBLICAN") else 0.14 for p in party_freq["party_simplified"]]
    plt.pie(
        party_freq["total_party_votes"],
        explode=explode,
        labels=party_freq["party_simplified"],
        autopct="%1.2f%%",
        startangle=90,
        colors=["#3182ce", "#e53e3e", "#ecc94b", "#a0aec0"],
    )
    plt.title("Plot 2: Exploded Pie Chart Highlighting Non-Duopoly Vote Share")
    generated_plots.append(save_fig("plot02_exploded_pie_parties.png"))

    # --- PLOT 3: Vertical Bar Chart (Votes by Election Year, >5 discrete years) ---
    year_votes = df_cont.groupby("year", as_index=False)["party_votes"].sum().sort_values("year")
    plt.figure(figsize=(10.5, 4.8))
    plt.bar(year_votes["year"].astype(str), year_votes["party_votes"] / 1e6, color="#2c5282", width=0.65)
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Election Year")
    plt.ylabel("Total Votes Cast (Millions)")
    plt.title("Plot 3: Total General-Election Votes Cast by Year (1976-2021)")
    generated_plots.append(save_fig("plot03_bar_votes_by_year.png"))

    # --- PLOT 4: Horizontal Bar Chart (Top 10 States by Total Votes) ---
    state_votes = (
        df_cont.groupby("state", as_index=False)["party_votes"]
        .sum()
        .sort_values("party_votes", ascending=False)
        .head(10)
        .sort_values("party_votes", ascending=True)
    )
    plt.figure(figsize=(8.5, 5.0))
    plt.barh(state_votes["state"], state_votes["party_votes"] / 1e6, color="#2f855a")
    plt.xlabel("Cumulative Votes Cast (Millions)")
    plt.ylabel("State")
    plt.title("Plot 4: Top 10 States by Cumulative General-Election Votes")
    generated_plots.append(save_fig("plot04_hbar_top_states.png"))

    # --- PLOT 5: Histogram (Continuous Vote Share % without gaps) ---
    plt.figure(figsize=(8.5, 4.8))
    plt.hist(df_cand["vote_share_pct"], bins=25, color="#4a5568", edgecolor="black", linewidth=0.6)
    plt.xlabel("Candidate Vote Share (%)")
    plt.ylabel("Frequency (Candidate Records)")
    plt.title("Plot 5: Histogram of Candidate Vote Share Percentage")
    generated_plots.append(save_fig("plot05_histogram_vote_share.png"))

    # --- PLOT 6: Box-and-Whisker Plot (Contest Party Share % by Party) ---
    parties_order = ["DEMOCRAT", "REPUBLICAN", "LIBERTARIAN", "OTHER"]
    box_data = [df_cont.loc[df_cont["party_simplified"] == p, "party_share_pct"].values for p in parties_order]
    plt.figure(figsize=(8.5, 5.0))
    plt.boxplot(box_data, tick_labels=parties_order, patch_artist=True)
    plt.xlabel("Simplified Party")
    plt.ylabel("Contest Party Vote Share (%)")
    plt.title("Plot 6: Box-and-Whisker Plot of Party Vote Share Across Contests")
    generated_plots.append(save_fig("plot06_boxplot_share_by_party.png"))

    # --- PLOT 7: Scatter Plot (Log Total Votes vs. Log Party Votes) ---
    plt.figure(figsize=(8.5, 5.0))
    for p, grp in df_cont.groupby("party_simplified"):
        plt.scatter(
            grp["log_total_votes"],
            grp["log_party_votes"],
            label=p,
            alpha=0.45,
            s=18,
        )
    plt.xlabel("Log(1 + Total Contest Votes)")
    plt.ylabel("Log(1 + Party Votes)")
    plt.title("Plot 7: Scatter Plot of Log Party Votes vs. Log Total Contest Votes")
    plt.legend(frameon=True, fontsize=8.5)
    generated_plots.append(save_fig("plot07_scatter_party_vs_total_votes.png"))

    # --- PLOT 8: Line Plot (Presidential Major-Party Vote Share Trend Over Time) ---
    pres_trend = (
        df_cont[(df_cont["office"] == "US PRESIDENT") & (df_cont["party_simplified"].isin(["DEMOCRAT", "REPUBLICAN"]))]
        .groupby(["year", "party_simplified"], as_index=False)["party_share_pct"]
        .mean()
    )
    plt.figure(figsize=(9.0, 4.8))
    for party, color in [("DEMOCRAT", "#2b6cb0"), ("REPUBLICAN", "#c53030")]:
        sub = pres_trend[pres_trend["party_simplified"] == party].sort_values("year")
        plt.plot(sub["year"], sub["party_share_pct"], marker="o", linewidth=2, color=color, label=party)
    plt.xlabel("Presidential Election Year")
    plt.ylabel("Mean State Vote Share (%)")
    plt.title("Plot 8: Mean State Vote Share Trend in US Presidential Elections (1976-2020)")
    plt.legend(frameon=True)
    generated_plots.append(save_fig("plot08_line_major_party_trend.png"))

    # --- PLOT 9: Dot Plot (State-Level Mean Victory Margin % Across Top 20 States by Volume) ---
    top20_states = (
        df_cont.groupby("state_po", as_index=False)["party_votes"]
        .sum()
        .sort_values("party_votes", ascending=False)
        .head(20)["state_po"]
        .tolist()
    )
    state_margin = (
        df_cont[df_cont["state_po"].isin(top20_states)]
        .groupby("state_po", as_index=False)["margin_pct"]
        .mean()
        .sort_values("margin_pct", ascending=True)
    )
    plt.figure(figsize=(8.5, 5.5))
    plt.scatter(state_margin["margin_pct"], state_margin["state_po"], color="#805ad5", s=65)
    plt.xlabel("Mean Contest Victory Margin (%)")
    plt.ylabel("State Postal Code (Top 20 States by Vote Volume)")
    plt.title("Plot 9: Dot Plot of Mean Victory Margin Across Top 20 States")
    generated_plots.append(save_fig("plot09_dotplot_state_margin.png"))

    # --- PLOT 10: Stem-and-Leaf Plot (2020 Presidential State Turnout in Hundred-Thousands) ---
    pres_2020 = (
        df_cont[(df_cont["office"] == "US PRESIDENT") & (df_cont["year"] == 2020)]
        .drop_duplicates(subset=["state_po"])
        .sort_values("total_votes")
    )
    # Represent votes in units of 100,000 (stem = millions, leaf = hundred-thousands digit)
    scaled_100k = (pres_2020["total_votes"] / 100_000.0).round(1)
    stems = {}
    for val in scaled_100k:
        stem = int(np.floor(val))
        leaf = int(np.round((val - stem) * 10)) % 10
        stems.setdefault(stem, []).append(str(leaf))

    stem_lines = ["Stem (Millions) | Leaves (x0.1M votes, 2020 Presidential states)", "-" * 62]
    for s in sorted(stems.keys()):
        stem_lines.append(f"      {s:2d}        | {' '.join(stems[s])}")
    stem_text = "\n".join(stem_lines)

    with open(os.path.join(TABLES_DIR, "phase3_stem_and_leaf_2020_pres.txt"), "w", encoding="utf-8") as f:
        f.write(stem_text + "\n")

    plt.figure(figsize=(8.5, 5.2))
    plt.axis("off")
    plt.text(
        0.03,
        0.95,
        "Plot 10: Stem-and-Leaf Plot — 2020 Presidential State Turnout\n\n" + stem_text,
        va="top",
        ha="left",
        family="monospace",
        fontsize=9.5,
        bbox=dict(boxstyle="round,pad=0.6", facecolor="#f7fafc", edgecolor="#cbd5e0"),
    )
    generated_plots.append(save_fig("plot10_stem_and_leaf_pres_turnout.png"))

    # --- PLOT 11: Heatmap (Mean Party Share % by US Region and Simplified Party) ---
    pivot_hm = df_cont.pivot_table(
        index="us_region",
        columns="party_simplified",
        values="party_share_pct",
        aggfunc="mean",
    ).reindex(columns=["DEMOCRAT", "REPUBLICAN", "LIBERTARIAN", "OTHER"])

    plt.figure(figsize=(8.0, 4.8))
    im = plt.imshow(pivot_hm.values, cmap="YlGnBu", aspect="auto")
    plt.colorbar(im, label="Mean Party Vote Share (%)")
    plt.xticks(range(len(pivot_hm.columns)), pivot_hm.columns)
    plt.yticks(range(len(pivot_hm.index)), pivot_hm.index)
    for i in range(pivot_hm.shape[0]):
        for j in range(pivot_hm.shape[1]):
            val = pivot_hm.values[i, j]
            if not np.isnan(val):
                plt.text(j, i, f"{val:.1f}%", ha="center", va="center", color="#1a202c", fontsize=9, fontweight="bold")
    plt.xlabel("Simplified Party")
    plt.ylabel("US Region")
    plt.title("Plot 11: Heatmap of Mean Contest Vote Share by Region and Party")
    generated_plots.append(save_fig("plot11_heatmap_region_party.png"))

    # Save JSON summary of key descriptive metrics
    phase3_summary = {
        "generated_plots_count": len(generated_plots),
        "plots": [os.path.basename(p) for p in generated_plots],
        "party_summary": party_freq.to_dict(orient="records"),
        "office_summary": office_freq.to_dict(orient="records"),
        "region_summary": region_freq.to_dict(orient="records"),
    }
    with open(os.path.join(TABLES_DIR, "phase3_eda_summary.json"), "w", encoding="utf-8") as f:
        json.dump(phase3_summary, f, indent=2)

    print("=== PHASE 3 DESCRIPTIVE ANALYTICS & VISUALIZATIONS COMPLETE ===")
    print(f"Generated {len(generated_plots)} plots in {PLOTS_DIR}:")
    for p in generated_plots:
        print(f"  - {p}")

    print("\n--- CONTEST NUMERIC DESCRIPTIVE STATS ---")
    print(desc_cont.to_string())

    print("\n--- PARTY SUMMARY & PIE SECTOR ANGLES ---")
    print(party_freq.to_string(index=False))

    print("\n--- OFFICE SUMMARY ---")
    print(office_freq.to_string(index=False))

    print("\n--- REGION SUMMARY ---")
    print(region_freq.to_string(index=False))

    print("\n--- STEM-AND-LEAF (PLOT 10) ---")
    print(stem_text)


if __name__ == "__main__":
    main()