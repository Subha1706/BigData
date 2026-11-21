"""
Phase 7: Distributed Big Data Implementation in PySpark & 1x / 5x / 10x Scalability Benchmark
Course: CS5002 / CS5004 - Analytics & Systems of Big Data
"""

import os
import sys
import time
import json
import math
from itertools import combinations
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, roc_auc_score

# Ensure PySpark uses the exact active Python interpreter on Windows
os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

PROC_DIR = os.path.join("data", "processed")
PLOTS_DIR = os.path.join("outputs", "plots")
TABLES_DIR = os.path.join("outputs", "tables")

for d in (PLOTS_DIR, TABLES_DIR):
    os.makedirs(d, exist_ok=True)

plt.rcParams["figure.dpi"] = 300
plt.rcParams["savefig.dpi"] = 300
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False


def run_python_fpm_and_ml(
    contests_df: pd.DataFrame,
    txns_list: list[list[str]],
    min_support: float = 0.15,
    min_confidence: float = 0.70,
) -> dict:
    """Single-node Python baseline: Level-wise FPM + scikit-learn RandomForest classification."""
    t0_fpm = time.perf_counter()
    n_txns = len(txns_list)
    min_count = math.ceil(min_support * n_txns)
    txn_sets = [set(t) for t in txns_list]

    counts_1 = {}
    for t in txn_sets:
        for it in t:
            counts_1[it] = counts_1.get(it, 0) + 1
    freq_map = {frozenset([it]): c for it, c in counts_1.items() if c >= min_count}

    curr_freq = list(freq_map.keys())
    for k in (2, 3):
        cands = set()
        for i in range(len(curr_freq)):
            for j in range(i + 1, len(curr_freq)):
                u = curr_freq[i] | curr_freq[j]
                if len(u) == k:
                    cands.add(u)
        next_freq = []
        for cand in cands:
            c = sum(1 for t in txn_sets if cand.issubset(t))
            if c >= min_count:
                freq_map[cand] = c
                next_freq.append(cand)
        curr_freq = next_freq

    rules_cnt = 0
    for fs, c_ab in freq_map.items():
        if len(fs) < 2:
            continue
        for r in range(1, len(fs)):
            for ant_t in combinations(sorted(fs), r):
                ant = frozenset(ant_t)
                cons = fs - ant
                if len(cons) == 1 and ant in freq_map:
                    if (c_ab / freq_map[ant]) >= min_confidence:
                        rules_cnt += 1
    t_fpm = time.perf_counter() - t0_fpm

    t0_ml = time.perf_counter()
    num_features = ["year", "log_total_votes", "log_party_votes", "num_candidates", "writein_share_pct"]
    cat_features = ["office", "party_simplified", "us_region"]
    X = pd.get_dummies(contests_df[num_features + cat_features], columns=cat_features, dtype=float).values
    y = contests_df["is_contest_winner"].astype(int).values

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)

    clf = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42, n_jobs=1)
    clf.fit(X_tr_s, y_tr)
    y_pred = clf.predict(X_te_s)
    y_prob = clf.predict_proba(X_te_s)[:, 1]
    acc = accuracy_score(y_te, y_pred)
    auc = roc_auc_score(y_te, y_prob)
    t_ml = time.perf_counter() - t0_ml

    return {
        "python_fpm_sec": round(t_fpm, 4),
        "python_ml_sec": round(t_ml, 4),
        "python_total_sec": round(t_fpm + t_ml, 4),
        "python_freq_itemsets": len(freq_map),
        "python_single_cons_rules": rules_cnt,
        "python_ml_acc": round(float(acc), 4),
        "python_ml_auc": round(float(auc), 4),
    }


def main():
    contests_base = pd.read_csv(os.path.join(PROC_DIR, "contests_modeling.csv"))
    txns_df_base = pd.read_csv(os.path.join(PROC_DIR, "transactions_fpm.csv"))
    txns_base_list = [
        sorted({tok.strip() for tok in raw.split(";") if tok.strip()})
        for raw in txns_df_base["items"].astype(str)
    ]

    t0_spark_init = time.perf_counter()
    from pyspark.sql import SparkSession
    from pyspark.ml.fpm import FPGrowth
    from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler, StandardScaler as SparkStandardScaler
    from pyspark.ml.classification import RandomForestClassifier as SparkRandomForest
    from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator
    from pyspark.ml import Pipeline

    spark = (
        SparkSession.builder
        .appName("USElectionsBigDataBenchmark")
        .master("local[2]")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.sql.execution.arrow.pyspark.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    spark_startup_sec = round(time.perf_counter() - t0_spark_init, 4)
    spark_version = spark.version
    default_parallelism = spark.sparkContext.defaultParallelism

    scale_factors = [1, 5, 10]
    benchmark_rows = []
    validation_1x = {}

    for scale in scale_factors:
        scaled_contests = pd.concat([contests_base] * scale, ignore_index=True)
        scaled_txns = txns_base_list * scale
        n_rows = len(scaled_contests)

        py_res = run_python_fpm_and_ml(scaled_contests, scaled_txns, min_support=0.15, min_confidence=0.70)

        # Technique 1: PySpark MLlib FPGrowth
        t0_sp_fpm = time.perf_counter()
        spark_txn_rows = [(i, items) for i, items in enumerate(scaled_txns)]
        sdf_txns = spark.createDataFrame(spark_txn_rows, ["id", "items"]).repartition(4).cache()
        _ = sdf_txns.count()

        fp = FPGrowth(itemsCol="items", minSupport=0.15, minConfidence=0.70)
        fp_model = fp.fit(sdf_txns)
        sp_freq_count = fp_model.freqItemsets.count()
        sp_rules_count = fp_model.associationRules.count()
        t_sp_fpm = time.perf_counter() - t0_sp_fpm
        sdf_txns.unpersist()

        # Technique 2: PySpark MLlib Distributed Classification Pipeline
        t0_sp_ml = time.perf_counter()
        ml_cols = [
            "year", "log_total_votes", "log_party_votes", "num_candidates", "writein_share_pct",
            "office", "party_simplified", "us_region", "is_contest_winner"
        ]
        # Cast numeric columns explicitly so Spark schema is clean
        ml_pdf = scaled_contests[ml_cols].copy()
        for c in ["year", "num_candidates", "is_contest_winner"]:
            ml_pdf[c] = ml_pdf[c].astype(int)
        for c in ["log_total_votes", "log_party_votes", "writein_share_pct"]:
            ml_pdf[c] = ml_pdf[c].astype(float)

        sdf_ml = spark.createDataFrame(ml_pdf).repartition(4).cache()
        _ = sdf_ml.count()

        train_sdf, test_sdf = sdf_ml.randomSplit([0.8, 0.2], seed=42)

        idx_office = StringIndexer(inputCol="office", outputCol="office_idx", handleInvalid="keep")
        idx_party = StringIndexer(inputCol="party_simplified", outputCol="party_idx", handleInvalid="keep")
        idx_region = StringIndexer(inputCol="us_region", outputCol="region_idx", handleInvalid="keep")

        ohe = OneHotEncoder(
            inputCols=["office_idx", "party_idx", "region_idx"],
            outputCols=["office_vec", "party_vec", "region_vec"],
        )
        assembler = VectorAssembler(
            inputCols=[
                "year", "log_total_votes", "log_party_votes", "num_candidates", "writein_share_pct",
                "office_vec", "party_vec", "region_vec"
            ],
            outputCol="raw_features",
        )
        sp_scaler = SparkStandardScaler(inputCol="raw_features", outputCol="features", withMean=True, withStd=True)
        sp_rf = SparkRandomForest(
            labelCol="is_contest_winner",
            featuresCol="features",
            numTrees=50,
            maxDepth=8,
            seed=42,
        )

        pipeline = Pipeline(stages=[idx_office, idx_party, idx_region, ohe, assembler, sp_scaler, sp_rf])
        sp_model = pipeline.fit(train_sdf)
        preds_sdf = sp_model.transform(test_sdf)

        auc_eval = BinaryClassificationEvaluator(labelCol="is_contest_winner", metricName="areaUnderROC")
        acc_eval = MulticlassClassificationEvaluator(labelCol="is_contest_winner", predictionCol="prediction", metricName="accuracy")
        sp_auc = float(auc_eval.evaluate(preds_sdf))
        sp_acc = float(acc_eval.evaluate(preds_sdf))
        t_sp_ml = time.perf_counter() - t0_sp_ml
        sdf_ml.unpersist()

        sp_total = t_sp_fpm + t_sp_ml
        speedup_vs_py = py_res["python_total_sec"] / sp_total if sp_total > 0 else 0.0

        row = {
            "scale_factor": f"{scale}x",
            "rows": n_rows,
            "python_fpm_sec": py_res["python_fpm_sec"],
            "python_ml_sec": py_res["python_ml_sec"],
            "python_total_sec": py_res["python_total_sec"],
            "pyspark_fpm_sec": round(t_sp_fpm, 4),
            "pyspark_ml_sec": round(t_sp_ml, 4),
            "pyspark_total_sec": round(sp_total, 4),
            "relative_speedup_py_over_spark": round(speedup_vs_py, 4),
            "pyspark_freq_itemsets": int(sp_freq_count),
            "pyspark_rules": int(sp_rules_count),
            "pyspark_ml_acc": round(sp_acc, 4),
            "pyspark_ml_auc": round(sp_auc, 4),
        }
        benchmark_rows.append(row)

        if scale == 1:
            validation_1x = {
                "python_freq_itemsets": py_res["python_freq_itemsets"],
                "pyspark_freq_itemsets": int(sp_freq_count),
                "python_single_consequent_rules": py_res["python_single_cons_rules"],
                "pyspark_single_consequent_rules": int(sp_rules_count),
                "python_rf_acc": py_res["python_ml_acc"],
                "pyspark_rf_acc": round(sp_acc, 4),
                "python_rf_auc": py_res["python_ml_auc"],
                "pyspark_rf_auc": round(sp_auc, 4),
            }

    spark.stop()

    bench_df = pd.DataFrame(benchmark_rows)
    bench_df.to_csv(os.path.join(TABLES_DIR, "phase7_pyspark_benchmark.csv"), index=False)

    x = np.arange(len(bench_df))
    width = 0.35
    plt.figure(figsize=(8.8, 5.0))
    plt.bar(x - width / 2, bench_df["python_total_sec"], width, label="Single-Node Python (FPM + RF)", color="#2b6cb0")
    plt.bar(x + width / 2, bench_df["pyspark_total_sec"], width, label="PySpark MLlib (FPGrowth + RF)", color="#dd6b20")
    plt.xticks(x, [f"{r['scale_factor']}\n({r['rows']:,} rows)" for _, r in bench_df.iterrows()])
    plt.ylabel("Execution Time (Seconds, excl. JVM Startup)")
    plt.title("Plot 15: Single-Node Python vs. PySpark MLlib Runtime Across 1x, 5x, 10x Scale")
    plt.legend(frameon=True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOTS_DIR, "plot15_pyspark_scalability.png"), dpi=300, bbox_inches="tight")
    plt.close()

    summary = {
        "spark_version": spark_version,
        "master": "local[2]",
        "default_parallelism_cores": int(default_parallelism),
        "spark_jvm_startup_sec": spark_startup_sec,
        "validation_1x": validation_1x,
        "benchmarks": benchmark_rows,
    }
    with open(os.path.join(TABLES_DIR, "phase7_pyspark_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=== PHASE 7: PYSPARK IMPLEMENTATION & SCALABILITY BENCHMARK COMPLETE ===")
    print(f"Spark Version         : {spark_version}")
    print(f"Execution Master      : local[2] (defaultParallelism={default_parallelism})")
    print(f"JVM Startup Overhead  : {spark_startup_sec:.4f} s (one-time cost)")
    print("\n--- 1x CROSS-VALIDATION: PYTHON vs PYSPARK ---")
    for k, v in validation_1x.items():
        print(f"  {k}: {v}")

    print("\n--- 1x / 5x / 10x RUNTIME & SCALABILITY BENCHMARK ---")
    cols_show = [
        "scale_factor", "rows", "python_fpm_sec", "python_ml_sec", "python_total_sec",
        "pyspark_fpm_sec", "pyspark_ml_sec", "pyspark_total_sec", "relative_speedup_py_over_spark"
    ]
    print(bench_df[cols_show].to_string(index=False))


if __name__ == "__main__":
    main()