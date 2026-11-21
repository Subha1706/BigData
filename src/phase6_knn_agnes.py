"""
Phase 6: KNN Classification & Hierarchical AGNES Clustering
Course: CS5002 / CS5004 - Analytics & Systems of Big Data
"""

import os
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import (
    confusion_matrix,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    roc_curve,
)
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster, cophenet
from scipy.spatial.distance import pdist

PROC_DIR = os.path.join("data", "processed")
PLOTS_DIR = os.path.join("outputs", "plots")
TABLES_DIR = os.path.join("outputs", "tables")
CLUST_DIR = os.path.join("outputs", "clustering")
PRED_DIR = os.path.join("outputs", "predictions")

for d in (PLOTS_DIR, TABLES_DIR, CLUST_DIR, PRED_DIR):
    os.makedirs(d, exist_ok=True)

plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False


def run_knn_classification(df: pd.DataFrame, random_state: int = 42) -> dict:
    num_features = ["year", "log_total_votes", "log_party_votes", "num_candidates", "writein_share_pct"]
    cat_features = ["office", "party_simplified", "us_region"]
    target_col = "is_contest_winner"

    X_raw = pd.get_dummies(df[num_features + cat_features], columns=cat_features, drop_first=False, dtype=float)
    y = df[target_col].astype(int).values

    # Stratified 80/20 split to prevent data leakage
    X_train_raw, X_test_raw, y_train, y_test, idx_train, idx_test = train_test_split(
        X_raw.values,
        y,
        df.index.values,
        test_size=0.20,
        stratify=y,
        random_state=random_state,
    )

    # Fit scaler strictly on training split
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_raw)
    X_test = scaler.transform(X_test_raw)

    # Tune k using 5-fold stratified CV on training split only
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
    k_candidates = [3, 5, 7, 9, 11]
    cv_scores = []
    for k in k_candidates:
        knn_tmp = KNeighborsClassifier(n_neighbors=k, metric="euclidean")
        scores = cross_val_score(knn_tmp, X_train, y_train, cv=cv, scoring="f1")
        cv_scores.append({
            "k": k,
            "cv_mean_f1": round(float(scores.mean()), 4),
            "cv_std_f1": round(float(scores.std()), 4),
        })

    cv_df = pd.DataFrame(cv_scores)
    best_k = int(cv_df.sort_values(["cv_mean_f1", "k"], ascending=[False, True]).iloc[0]["k"])

    best_knn = KNeighborsClassifier(n_neighbors=best_k, metric="euclidean")
    best_knn.fit(X_train, y_train)

    y_pred = best_knn.predict(X_test)
    y_prob = best_knn.predict_proba(X_test)[:, 1]

    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    auc = roc_auc_score(y_test, y_prob)

    # Save sample test predictions & nearest-neighbor confidence
    preds_out = df.loc[idx_test, ["office", "year", "state_po", "party_simplified", "party_share_pct", "is_contest_winner"]].copy()
    preds_out["knn_pred_winner"] = y_pred
    preds_out["knn_win_prob"] = np.round(y_prob, 4)
    preds_out.to_csv(os.path.join(PRED_DIR, "phase6_knn_test_predictions.csv"), index=False)
    cv_df.to_csv(os.path.join(TABLES_DIR, "phase6_knn_cv_results.csv"), index=False)

    # Plot ROC Curve
    fpr, tpr, _ = roc_curve(y_test, y_prob)
    plt.figure(figsize=(7.2, 5.0))
    plt.plot(fpr, tpr, color="#2b6cb0", linewidth=2, label=f"KNN (k={best_k}, AUC={auc:.4f})")
    plt.plot([0, 1], [0, 1], linestyle="--", color="#718096", label="Random Classifier (AUC=0.5000)")
    plt.xlabel("False Positive Rate (1 - Specificity)")
    plt.ylabel("True Positive Rate (Recall / Sensitivity)")
    plt.title(f"Plot 12: ROC Curve for KNN Winner Classification (k={best_k})")
    plt.legend(loc="lower right", frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "plot12_knn_roc_curve.png"), dpi=300, bbox_inches="tight")
    plt.close()

    return {
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "best_k": best_k,
        "confusion_matrix": {"TN": int(tn), "FP": int(fp), "FN": int(fn), "TP": int(tp)},
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall_sensitivity": round(float(rec), 4),
        "specificity": round(float(spec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(auc), 4),
        "cv_table": cv_df,
        "sample_predictions": preds_out.head(10),
    }


def run_agnes_clustering(df: pd.DataFrame, sample_size: int = 600, n_clusters: int = 4, random_state: int = 42) -> dict:
    # Stratified sample across is_contest_winner so both outcomes are represented
    sample_df, _ = train_test_split(
        df,
        train_size=min(sample_size, len(df)),
        stratify=df["is_contest_winner"],
        random_state=random_state,
    )
    sample_df = sample_df.reset_index(drop=True)

    cluster_cols = [
        "party_share_pct_zscore",
        "margin_pct_zscore",
        "log_total_votes_zscore",
        "log_party_votes_zscore",
    ]
    X_clust = sample_df[cluster_cols].values
    pairwise_dist = pdist(X_clust, metric="euclidean")

    linkage_methods = ["single", "complete", "average"]
    linkage_comp = []
    Z_map = {}

    for method in linkage_methods:
        Z = linkage(X_clust, method=method, metric="euclidean")
        Z_map[method] = Z
        coph_corr, _ = cophenet(Z, pairwise_dist)
        linkage_comp.append({
            "linkage_method": method,
            "cophenetic_correlation": round(float(coph_corr), 4),
            "max_merge_height": round(float(Z[:, 2].max()), 4),
        })

    comp_df = pd.DataFrame(linkage_comp).sort_values("cophenetic_correlation", ascending=False).reset_index(drop=True)
    comp_df.to_csv(os.path.join(TABLES_DIR, "phase6_agnes_linkage_comparison.csv"), index=False)

    # Use average linkage (strong hierarchical balance & high cophenetic correlation) for primary clusters
    Z_avg = Z_map["average"]
    cluster_labels = fcluster(Z_avg, t=n_clusters, criterion="maxclust")
    sample_df["agnes_cluster"] = cluster_labels

    # Compute cluster sizes and profiles on original interpretable metrics
    profiles = (
        sample_df.groupby("agnes_cluster", as_index=False)
        .agg(
            size=("party_share_pct", "count"),
            share_of_sample_pct=("party_share_pct", lambda s: len(s) / len(sample_df) * 100.0),
            mean_party_share_pct=("party_share_pct", "mean"),
            mean_margin_pct=("margin_pct", "mean"),
            mean_total_votes=("total_votes", "mean"),
            winner_rate_pct=("is_contest_winner", lambda s: s.mean() * 100.0),
            dominant_party=("party_simplified", lambda s: s.mode().iloc[0] if not s.mode().empty else "N/A"),
        )
        .sort_values("agnes_cluster")
        .round(2)
    )
    profiles.to_csv(os.path.join(CLUST_DIR, "phase6_agnes_cluster_profiles.csv"), index=False)
    sample_df[["office", "year", "state_po", "party_simplified", "party_share_pct", "margin_pct", "total_votes", "agnes_cluster"]].to_csv(
        os.path.join(CLUST_DIR, "phase6_agnes_sample_assignments.csv"), index=False
    )

    # Compute K-cluster lifetimes (gap between consecutive merge heights for K=2..8)
    merge_heights = np.sort(Z_avg[:, 2])[::-1]  # largest merges correspond to smallest K
    lifetimes = []
    for k in range(2, min(8, len(merge_heights))):
        # Moving from k+1 clusters to k clusters merges at index (k-1)
        h_merge_to_k = merge_heights[k - 1]
        h_merge_to_km1 = merge_heights[k] if k < len(merge_heights) else 0.0
        lifetime = float(h_merge_to_k - h_merge_to_km1)
        lifetimes.append({
            "K_clusters": k,
            "merge_height_to_K": round(float(h_merge_to_k), 4),
            "next_merge_height": round(float(h_merge_to_km1), 4),
            "lifetime": round(lifetime, 4),
        })
    life_df = pd.DataFrame(lifetimes)
    life_df.to_csv(os.path.join(TABLES_DIR, "phase6_agnes_cluster_lifetimes.csv"), index=False)

    # Plot 13: Dendrogram (truncated to show top merges clearly)
    plt.figure(figsize=(10.5, 5.2))
    dendrogram(Z_avg, truncate_mode="lastp", p=30, leaf_rotation=90.0, leaf_font_size=8.5, show_contracted=True)
    plt.xlabel("Cluster / Sample Leaf Group (Truncated Top 30 Merges)")
    plt.ylabel("Euclidean Linkage Distance (Average Linkage)")
    plt.title(f"Plot 13: AGNES Hierarchical Dendrogram (n={len(sample_df)}, Average Linkage)")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "plot13_agnes_dendrogram.png"), dpi=300, bbox_inches="tight")
    plt.close()

    # Plot 14: K-Cluster Lifetimes Plot
    plt.figure(figsize=(8.0, 4.6))
    plt.bar(life_df["K_clusters"].astype(str), life_df["lifetime"], color="#319795", width=0.55)
    plt.xlabel("Number of Clusters (K)")
    plt.ylabel("Cluster Lifetime (Merge Distance Gap)")
    plt.title("Plot 14: K-Cluster Lifetimes Across Merge Levels (AGNES Average Linkage)")
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "plot14_agnes_lifetimes.png"), dpi=300, bbox_inches="tight")
    plt.close()

    return {
        "sample_size": int(len(sample_df)),
        "distance_metric": "euclidean",
        "primary_linkage": "average",
        "n_clusters": n_clusters,
        "linkage_comparison": comp_df,
        "cluster_profiles": profiles,
        "cluster_lifetimes": life_df,
    }


def main():
    df = pd.read_csv(os.path.join(PROC_DIR, "contests_modeling.csv"))

    knn_res = run_knn_classification(df, random_state=42)
    agnes_res = run_agnes_clustering(df, sample_size=600, n_clusters=4, random_state=42)

    summary = {
        "knn": {k: v for k, v in knn_res.items() if not isinstance(v, pd.DataFrame)},
        "agnes": {k: v for k, v in agnes_res.items() if not isinstance(v, pd.DataFrame)},
    }
    with open(os.path.join(TABLES_DIR, "phase6_knn_agnes_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=== PHASE 6: KNN CLASSIFICATION & AGNES CLUSTERING COMPLETE ===")
    print("\n--- KNN 5-FOLD CV TUNING (ON TRAIN SPLIT) ---")
    print(knn_res["cv_table"].to_string(index=False))

    print(f"\n--- KNN TEST SET EVALUATION (best k={knn_res['best_k']}, test n={knn_res['test_rows']}) ---")
    print(f"Confusion Matrix : {knn_res['confusion_matrix']}")
    print(f"Accuracy         : {knn_res['accuracy']:.4f}")
    print(f"Precision        : {knn_res['precision']:.4f}")
    print(f"Recall (Sens.)   : {knn_res['recall_sensitivity']:.4f}")
    print(f"Specificity      : {knn_res['specificity']:.4f}")
    print(f"F1-Score         : {knn_res['f1_score']:.4f}")
    print(f"ROC-AUC          : {knn_res['roc_auc']:.4f}")

    print("\n--- SAMPLE KNN TEST PREDICTIONS ---")
    print(knn_res["sample_predictions"].to_string(index=False))

    print(f"\n--- AGNES LINKAGE COMPARISON (sample n={agnes_res['sample_size']}, Euclidean) ---")
    print(agnes_res["linkage_comparison"].to_string(index=False))

    print(f"\n--- AGNES CLUSTER PROFILES (K={agnes_res['n_clusters']}, Average Linkage) ---")
    print(agnes_res["cluster_profiles"].to_string(index=False))

    print("\n--- AGNES K-CLUSTER LIFETIMES ---")
    print(agnes_res["cluster_lifetimes"].to_string(index=False))


if __name__ == "__main__":
    main()