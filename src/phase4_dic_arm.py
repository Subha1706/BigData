"""
Phase 4: Dynamic Itemset Counting (DIC) from Scratch + Association Rule Mining
Course: CS5002 / CS5004 - Analytics & Systems of Big Data
"""

import os
import time
import json
import math
from itertools import combinations
import pandas as pd

PROC_DIR = os.path.join("data", "processed")
RULES_DIR = os.path.join("outputs", "rules")
ITEMSETS_DIR = os.path.join("outputs", "itemsets")
TABLES_DIR = os.path.join("outputs", "tables")

os.makedirs(RULES_DIR, exist_ok=True)
os.makedirs(ITEMSETS_DIR, exist_ok=True)
os.makedirs(TABLES_DIR, exist_ok=True)


def load_transactions(csv_path: str) -> list[frozenset[str]]:
    df = pd.read_csv(csv_path)
    txns = []
    for raw_items in df["items"].astype(str):
        items = frozenset(tok.strip() for tok in raw_items.split(";") if tok.strip())
        txns.append(items)
    return txns


def generate_candidates_from_frequent(prev_frequent: set[frozenset[str]], k: int, confirmed_frequent_or_ds: set[frozenset[str]]) -> set[frozenset[str]]:
    """
    Apriori/DIC join + subset check:
    Generate k-itemsets from (k-1)-frequent itemsets whose (k-1)-subsets are known.
    """
    candidates = set()
    prev_list = sorted(prev_frequent, key=lambda s: sorted(s))
    n = len(prev_list)
    for i in range(n):
        for j in range(i + 1, n):
            union_set = prev_list[i] | prev_list[j]
            if len(union_set) == k:
                # Every (k-1)-subset must be in frequent set (anti-monotonicity)
                all_subs_freq = all(
                    frozenset(sub) in prev_frequent
                    for sub in combinations(union_set, k - 1)
                )
                if all_subs_freq:
                    candidates.add(union_set)
    return candidates


def run_dic(
    transactions: list[frozenset[str]],
    min_support: float = 0.15,
    min_confidence: float = 0.70,
    interval_size: int = 800,
    max_k: int = 3,
):
    """
    From-scratch Dynamic Itemset Counting (DIC) algorithm.
    States:
      DC = dashed circle (counting, count < min_count)
      DS = dashed square (counting, count >= min_count)
      SC = solid circle  (done full pass, count < min_count)
      SS = solid square  (done full pass, count >= min_count)
    """
    t0 = time.perf_counter()
    n_txns = len(transactions)
    min_count = math.ceil(min_support * n_txns)

    # Collect all distinct 1-items
    all_1_items = sorted({item for txn in transactions for item in txn})

    # State dictionary: itemset -> dict(state, count, txns_seen)
    item_meta: dict[frozenset[str], dict] = {}
    for item in all_1_items:
        fs = frozenset([item])
        item_meta[fs] = {"state": "DC", "count": 0, "txns_seen": 0}

    interval_logs = []
    step_idx = 0
    start_idx = 0

    # Continue until no active counting itemsets (DC or DS) remain
    while any(meta["state"] in ("DC", "DS") for meta in item_meta.values()):
        end_idx = min(start_idx + interval_size, n_txns)
        batch = transactions[start_idx:end_idx]
        batch_len = len(batch)

        active_itemsets = [fs for fs, meta in item_meta.items() if meta["state"] in ("DC", "DS")]

        # Count occurrences of currently active (DC/DS) itemsets in this M-transaction interval
        for txn in batch:
            for fs in active_itemsets:
                if fs.issubset(txn):
                    item_meta[fs]["count"] += 1

        for fs in active_itemsets:
            item_meta[fs]["txns_seen"] += batch_len
            meta = item_meta[fs]

            if meta["txns_seen"] >= n_txns:
                # Completed a full pass over all N transactions
                meta["state"] = "SS" if meta["count"] >= min_count else "SC"
            else:
                # Still counting across remaining intervals
                meta["state"] = "DS" if meta["count"] >= min_count else "DC"

        # At interval boundary, check if new k-itemset candidates can be opened (DC)
        newly_added = 0
        for k in range(2, max_k + 1):
            ss_km1 = {fs for fs, meta in item_meta.items() if len(fs) == k - 1 and meta["state"] == "SS"}
            if len(ss_km1) >= 2:
                cands = generate_candidates_from_frequent(ss_km1, k, ss_km1)
                for cand in cands:
                    if cand not in item_meta:
                        # All (k-1)-subsets are in SS, so candidate starts in DC
                        item_meta[cand] = {"state": "DC", "count": 0, "txns_seen": 0}
                        newly_added += 1

        state_counts = {"DC": 0, "DS": 0, "SC": 0, "SS": 0}
        for meta in item_meta.values():
            state_counts[meta["state"]] += 1

        step_idx += 1
        interval_logs.append({
            "step": step_idx,
            "txn_start": start_idx,
            "txn_end": end_idx,
            "batch_size": batch_len,
            "newly_added_candidates": newly_added,
            "DC_count": state_counts["DC"],
            "DS_count": state_counts["DS"],
            "SC_count": state_counts["SC"],
            "SS_count": state_counts["SS"],
        })

        start_idx = end_idx if end_idx < n_txns else 0

    # Extract all confirmed frequent itemsets (state == 'SS')
    freq_records = []
    freq_support_map: dict[frozenset[str], float] = {}
    for fs, meta in item_meta.items():
        if meta["state"] == "SS":
            supp = meta["count"] / n_txns
            freq_support_map[fs] = supp
            freq_records.append({
                "itemset": " & ".join(sorted(fs)),
                "size_k": len(fs),
                "support_count": meta["count"],
                "support": round(supp, 4),
            })

    freq_df = pd.DataFrame(freq_records).sort_values(
        by=["size_k", "support_count", "itemset"], ascending=[True, False, True]
    ).reset_index(drop=True)

    # Generate association rules A -> B from frequent itemsets of size >= 2
    rules = []
    for fs, supp_ab in freq_support_map.items():
        if len(fs) < 2:
            continue
        items_sorted = sorted(fs)
        for r in range(1, len(fs)):
            for ant_tuple in combinations(items_sorted, r):
                antecedent = frozenset(ant_tuple)
                consequent = fs - antecedent
                if antecedent in freq_support_map and consequent in freq_support_map:
                    supp_a = freq_support_map[antecedent]
                    supp_b = freq_support_map[consequent]
                    conf = supp_ab / supp_a if supp_a > 0 else 0.0
                    lift = conf / supp_b if supp_b > 0 else 0.0
                    if conf >= min_confidence:
                        rules.append({
                            "antecedent": " & ".join(sorted(antecedent)),
                            "consequent": " & ".join(sorted(consequent)),
                            "rule": f"{' & '.join(sorted(antecedent))} => {' & '.join(sorted(consequent))}",
                            "support": round(supp_ab, 4),
                            "confidence": round(conf, 4),
                            "lift": round(lift, 4),
                        })

    rules_df = pd.DataFrame(rules)
    if not rules_df.empty:
        rules_df = rules_df.sort_values(by=["lift", "confidence", "support"], ascending=[False, False, False]).reset_index(drop=True)

    elapsed_sec = time.perf_counter() - t0
    intervals_df = pd.DataFrame(interval_logs)

    return {
        "runtime_sec": round(elapsed_sec, 4),
        "n_transactions": n_txns,
        "min_support": min_support,
        "min_count": min_count,
        "min_confidence": min_confidence,
        "interval_size_M": interval_size,
        "total_steps": step_idx,
        "frequent_itemsets_count": len(freq_df),
        "rules_count": len(rules_df),
        "intervals_df": intervals_df,
        "freq_df": freq_df,
        "rules_df": rules_df,
    }


def main():
    txn_path = os.path.join(PROC_DIR, "transactions_fpm.csv")
    transactions = load_transactions(txn_path)

    res = run_dic(
        transactions=transactions,
        min_support=0.15,
        min_confidence=0.70,
        interval_size=800,
        max_k=3,
    )

    res["intervals_df"].to_csv(os.path.join(TABLES_DIR, "phase4_dic_intervals.csv"), index=False)
    res["freq_df"].to_csv(os.path.join(ITEMSETS_DIR, "phase4_dic_frequent_itemsets.csv"), index=False)
    res["rules_df"].to_csv(os.path.join(RULES_DIR, "phase4_dic_association_rules.csv"), index=False)

    meta_summary = {k: v for k, v in res.items() if not isinstance(v, pd.DataFrame)}
    with open(os.path.join(TABLES_DIR, "phase4_dic_summary.json"), "w", encoding="utf-8") as f:
        json.dump(meta_summary, f, indent=2)

    print("=== PHASE 4: DIC & ASSOCIATION RULE MINING COMPLETE ===")
    print(f"Transactions         : {res['n_transactions']:,}")
    print(f"Min Support / Count  : {res['min_support']:.2f} ({res['min_count']:,} txns)")
    print(f"Min Confidence       : {res['min_confidence']:.2f}")
    print(f"Interval Size (M)    : {res['interval_size_M']}")
    print(f"Total DIC Steps      : {res['total_steps']}")
    print(f"Runtime (sec)        : {res['runtime_sec']:.4f} s")
    print(f"Frequent Itemsets    : {res['frequent_itemsets_count']}")
    print(f"Strong Rules Found   : {res['rules_count']}")

    print("\n--- DIC INTERVAL LOG ---")
    print(res["intervals_df"].to_string(index=False))

    print("\n--- TOP 15 FREQUENT ITEMSETS (BY SIZE & SUPPORT) ---")
    print(res["freq_df"].head(15).to_string(index=False))

    print("\n--- TOP 15 STRONG ASSOCIATION RULES (BY LIFT) ---")
    if not res["rules_df"].empty:
        print(res["rules_df"].head(15).to_string(index=False))
    else:
        print("No rules met min_confidence threshold.")


if __name__ == "__main__":
    main()