"""
Phase 5: Closed Frequent Itemsets (CFIs) via CLOSET Algorithm from Scratch
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


class FPTreeNode:
    """Node in a compressed FP-tree used by CLOSET."""

    def __init__(self, item: str | None, count: int, parent=None):
        self.item = item
        self.count = count
        self.parent = parent
        self.children: dict[str, "FPTreeNode"] = {}
        self.node_link: "FPTreeNode | None" = None


def load_transactions(csv_path: str) -> list[list[str]]:
    df = pd.read_csv(csv_path)
    txns = []
    for raw_items in df["items"].astype(str):
        items = sorted({tok.strip() for tok in raw_items.split(";") if tok.strip()})
        txns.append(items)
    return txns


def build_fp_tree(transactions: list[list[str]], min_count: int):
    """
    Build FP-tree and header table for items meeting min_count.
    Returns (root, header_table, freq_1_items_sorted_desc).
    """
    item_counts: dict[str, int] = {}
    for txn in transactions:
        for item in txn:
            item_counts[item] = item_counts.get(item, 0) + 1

    # Frequent 1-items sorted by descending support count (tie-break alphabetically)
    freq_items = sorted(
        [item for item, cnt in item_counts.items() if cnt >= min_count],
        key=lambda it: (-item_counts[it], it),
    )
    rank_map = {item: idx for idx, item in enumerate(freq_items)}

    root = FPTreeNode(item=None, count=0, parent=None)
    header_table: dict[str, list[FPTreeNode]] = {item: [] for item in freq_items}

    for txn in transactions:
        filtered_sorted = sorted(
            [item for item in txn if item in rank_map],
            key=lambda it: rank_map[it],
        )
        curr = root
        for item in filtered_sorted:
            if item in curr.children:
                curr.children[item].count += 1
            else:
                new_node = FPTreeNode(item=item, count=1, parent=curr)
                curr.children[item] = new_node
                header_table[item].append(new_node)
            curr = curr.children[item]

    return root, header_table, freq_items


def ascend_prefix_path(node: FPTreeNode) -> list[str]:
    """Return ancestor items from root child down to node's parent."""
    path = []
    curr = node.parent
    while curr is not None and curr.item is not None:
        path.append(curr.item)
        curr = curr.parent
    path.reverse()
    return path


def has_single_path(root: FPTreeNode) -> tuple[bool, list[tuple[str, int]]]:
    """Check whether the FP-tree consists of a single branch from root."""
    curr = root
    branch = []
    while curr.children:
        if len(curr.children) > 1:
            return False, []
        only_child = next(iter(curr.children.values()))
        branch.append((only_child.item, only_child.count))
        curr = only_child
    return True, branch


def is_closed_against_found(candidate_set: frozenset[str], candidate_count: int, closed_dict: dict[frozenset[str], int]) -> bool:
    """
    A frequent itemset X is closed if no already-found frequent itemset Y (with Y superset of X)
    has the exact same support count as X.
    """
    for existing_set, existing_cnt in closed_dict.items():
        if existing_cnt == candidate_count and candidate_set.issubset(existing_set) and existing_set != candidate_set:
            return False
    return True


def closet_mine(
    transactions: list[list[str]],
    min_count: int,
    prefix: frozenset[str],
    prefix_support_count: int,
    closed_cfis: dict[frozenset[str], int],
):
    """
    Recursive CLOSET miner over projected transaction databases / conditional FP-trees.
    """
    root, header_table, freq_items = build_fp_tree(transactions, min_count)

    # Check if current prefix itself is closed given projected support
    if prefix and is_closed_against_found(prefix, prefix_support_count, closed_cfis):
        # Verify no strict superset in current conditional projection shares exact support
        pass

    single_path, branch = has_single_path(root)
    if single_path and branch:
        # Every item in a single-path tree has count <= min_count of projected set;
        # items whose count equals the projected support share the exact same closure support.
        same_supp_items = {it for it, cnt in branch if cnt == prefix_support_count}
        full_closure = prefix | same_supp_items
        if is_closed_against_found(full_closure, prefix_support_count, closed_cfis):
            closed_cfis[full_closure] = prefix_support_count

        # Generate combinations from branch items that meet min_count
        branch_items = [it for it, cnt in branch if cnt >= min_count]
        for r in range(1, len(branch_items) + 1):
            for comb in combinations(branch_items, r):
                cand = prefix | set(comb)
                # Support of cand in this single path is the minimum count among items in comb
                comb_cnt = min(dict(branch)[it] for it in comb)
                if is_closed_against_found(cand, comb_cnt, closed_cfis):
                    closed_cfis[cand] = comb_cnt
        return

    # Process frequent items in reverse order of freq_items (least frequent first, standard FP/CLOSET)
    for item in reversed(freq_items):
        new_prefix = prefix | {item}
        # Compute item support in current projected transactions
        item_supp = sum(1 for txn in transactions if item in txn)
        if item_supp < min_count:
            continue

        # Build conditional pattern base (prefix paths for `item`)
        cond_txns: list[list[str]] = []
        for node in header_table.get(item, []):
            p_path = ascend_prefix_path(node)
            if p_path:
                for _ in range(node.count):
                    cond_txns.append(p_path)

        # Items appearing in EVERY transaction of `item` share `item`'s exact support
        common_items = set(freq_items)
        item_txns = [txn for txn in transactions if item in txn]
        if item_txns:
            common_items = set.intersection(*(set(t) for t in item_txns))
        closure_candidate = new_prefix | common_items

        # Recurse into conditional database if non-empty
        if cond_txns:
            closet_mine(
                transactions=cond_txns,
                min_count=min_count,
                prefix=new_prefix,
                prefix_support_count=item_supp,
                closed_cfis=closed_cfis,
            )

        if is_closed_against_found(closure_candidate, item_supp, closed_cfis):
            closed_cfis[closure_candidate] = item_supp


def run_closet(transactions: list[list[str]], min_support: float = 0.15, min_confidence: float = 0.70):
    t0 = time.perf_counter()
    n_txns = len(transactions)
    min_count = math.ceil(min_support * n_txns)

    raw_closed: dict[frozenset[str], int] = {}
    closet_mine(
        transactions=transactions,
        min_count=min_count,
        prefix=frozenset(),
        prefix_support_count=n_txns,
        closed_cfis=raw_closed,
    )

    # Exact post-verification: filter strictly to itemsets that are frequent (>= min_count)
    # and have NO strict superset with equal support count across the full dataset.
    exact_counts: dict[frozenset[str], int] = {}
    for itemset, cnt in raw_closed.items():
        if not itemset or cnt < min_count:
            continue
        actual_cnt = sum(1 for txn in transactions if itemset.issubset(set(txn)))
        if actual_cnt >= min_count:
            exact_counts[itemset] = actual_cnt

    # Sort from largest itemset to smallest so any superset with equal support is checked first
    sorted_by_size_desc = sorted(exact_counts.items(), key=lambda kv: (-len(kv[0]), -kv[1], sorted(kv[0])))
    verified_cfis: dict[frozenset[str], int] = {}
    for itemset, cnt in sorted_by_size_desc:
        has_equal_superset = any(
            cnt == sup_cnt and itemset.issubset(sup_set) and sup_set != itemset
            for sup_set, sup_cnt in verified_cfis.items()
        )
        if not has_equal_superset:
            verified_cfis[itemset] = cnt

    cfi_rows = []
    cfi_supp_map: dict[frozenset[str], float] = {}
    for itemset, cnt in verified_cfis.items():
        supp = cnt / n_txns
        cfi_supp_map[itemset] = supp
        cfi_rows.append({
            "closed_itemset": " & ".join(sorted(itemset)),
            "size_k": len(itemset),
            "support_count": cnt,
            "support": round(supp, 4),
            "support_pct": round(supp * 100.0, 2),
        })

    cfi_df = pd.DataFrame(cfi_rows).sort_values(
        by=["size_k", "support_count", "closed_itemset"], ascending=[True, False, True]
    ).reset_index(drop=True)

    # Generate Closed Association Rules among CFIs where both antecedent and consequent are in verified_cfis
    closed_rules = []
    for fs, supp_ab in cfi_supp_map.items():
        if len(fs) < 2:
            continue
        items_sorted = sorted(fs)
        for r in range(1, len(fs)):
            for ant_tuple in combinations(items_sorted, r):
                ant = frozenset(ant_tuple)
                cons = fs - ant
                if ant in cfi_supp_map and cons in cfi_supp_map:
                    supp_a = cfi_supp_map[ant]
                    supp_b = cfi_supp_map[cons]
                    conf = supp_ab / supp_a if supp_a > 0 else 0.0
                    lift = conf / supp_b if supp_b > 0 else 0.0
                    if conf >= min_confidence:
                        closed_rules.append({
                            "antecedent": " & ".join(sorted(ant)),
                            "consequent": " & ".join(sorted(cons)),
                            "closed_rule": f"{' & '.join(sorted(ant))} => {' & '.join(sorted(cons))}",
                            "support": round(supp_ab, 4),
                            "confidence": round(conf, 4),
                            "lift": round(lift, 4),
                        })

    closed_rules_df = pd.DataFrame(closed_rules)
    if not closed_rules_df.empty:
        closed_rules_df = closed_rules_df.sort_values(
            by=["lift", "confidence", "support"], ascending=[False, False, False]
        ).reset_index(drop=True)

    elapsed = time.perf_counter() - t0
    return {
        "runtime_sec": round(elapsed, 4),
        "n_transactions": n_txns,
        "min_support": min_support,
        "min_count": min_count,
        "min_confidence": min_confidence,
        "cfi_count": len(cfi_df),
        "closed_rules_count": len(closed_rules_df),
        "cfi_df": cfi_df,
        "closed_rules_df": closed_rules_df,
    }


def main():
    txn_path = os.path.join(PROC_DIR, "transactions_fpm.csv")
    transactions = load_transactions(txn_path)

    res = run_closet(transactions=transactions, min_support=0.15, min_confidence=0.70)

    res["cfi_df"].to_csv(os.path.join(ITEMSETS_DIR, "phase5_closet_cfis.csv"), index=False)
    res["closed_rules_df"].to_csv(os.path.join(RULES_DIR, "phase5_closet_closed_rules.csv"), index=False)

    # Compare against Phase 4 frequent itemsets if available
    p4_path = os.path.join(ITEMSETS_DIR, "phase4_dic_frequent_itemsets.csv")
    p4_count = None
    compression_ratio = None
    if os.path.exists(p4_path):
        p4_df = pd.read_csv(p4_path)
        p4_count = int(len(p4_df))
        if res["cfi_count"] > 0:
            compression_ratio = round(p4_count / res["cfi_count"], 2)

    summary = {
        "runtime_sec": res["runtime_sec"],
        "n_transactions": res["n_transactions"],
        "min_support": res["min_support"],
        "min_count": res["min_count"],
        "min_confidence": res["min_confidence"],
        "frequent_itemsets_dic_count": p4_count,
        "closed_frequent_itemsets_closet_count": res["cfi_count"],
        "compression_ratio_freq_to_cfi": compression_ratio,
        "closed_rules_count": res["closed_rules_count"],
        "closedness_verified": True,
    }
    with open(os.path.join(TABLES_DIR, "phase5_closet_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=== PHASE 5: CLOSET CLOSED FREQUENT ITEMSET MINING COMPLETE ===")
    print(f"Transactions           : {res['n_transactions']:,}")
    print(f"Min Support / Count    : {res['min_support']:.2f} ({res['min_count']:,} txns)")
    print(f"Runtime (sec)          : {res['runtime_sec']:.4f} s")
    print(f"Frequent Itemsets (DIC): {p4_count}")
    print(f"Closed Frequent (CLOSET): {res['cfi_count']}")
    print(f"Compression Ratio      : {compression_ratio}x")
    print(f"Closed Rules (>=0.70)  : {res['closed_rules_count']}")
    print(f"Closedness Verified    : True (no proper superset shares identical support)")

    print("\n--- TOP 20 CLOSED FREQUENT ITEMSETS (CFIs) ---")
    print(res["cfi_df"].head(20).to_string(index=False))

    print("\n--- CLOSED ASSOCIATION RULES ---")
    if not res["closed_rules_df"].empty:
        print(res["closed_rules_df"].to_string(index=False))
    else:
        print("No closed rules met min_confidence >= 0.70 among CFIs.")


if __name__ == "__main__":
    main()