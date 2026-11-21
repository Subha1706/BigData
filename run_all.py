#!/usr/bin/env python3
"""
run_all.py -- regenerates EVERY number, table and plot needed by report_revised.tex
from the corrected data (contests_modeling.csv + transactions_fpm.csv).

Usage (from the project root):
    python run_all.py --stage all
    python run_all.py --stage desc plots dic closet knn agnes      # without Spark
    python run_all.py --stage spark --cores 2 --runs 3 --scales 1 5 10 20

Outputs:  outputs/tables/*.csv, outputs/plots/*.png, outputs/results_summary.md
Seed:     42 everywhere.  Nothing here is hard-coded: all results come from execution.
"""
import argparse, itertools, math, os, sys, time, platform
from collections import Counter, defaultdict
from operator import add
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

SEED = 42
OUT = "outputs"
LOG = []


def path(*p):
    f = os.path.join(OUT, *p)
    os.makedirs(os.path.dirname(f), exist_ok=True)
    return f


def say(s=""):
    print(s)
    LOG.append(str(s))


def table(df, name, index=False, show=True):
    df.to_csv(path("tables", name), index=index)
    if show:
        say(f"\n### {name}\n```\n{df.to_string(index=index)}\n```")


# ----------------------------------------------------------------------------- loading
def load(args):
    c = pd.read_csv(args.contests)
    need = ["office", "year", "state_po", "party_simplified", "party_votes", "total_votes",
            "party_share_pct", "margin_pct", "is_contest_winner", "us_region", "election_era",
            "log_total_votes", "log_party_votes", "num_candidates", "writein_share_pct"]
    miss = [x for x in need if x not in c.columns]
    if miss:
        sys.exit(f"Missing columns {miss}\nAvailable columns: {list(c.columns)}\n"
                 "Rename the columns in load() or in your CSV and rerun.")
    cid = c["office"].astype(str) + "|" + c["year"].astype(str) + "|" + c["state_po"].astype(str)
    if "special" in c.columns:
        cid = cid + "|" + c["special"].astype(str)
    c["contest_id"] = cid
    return c


def load_tx(p):
    t = pd.read_csv(p)
    col = None
    for k in t.columns:
        if t[k].astype(str).str.contains(";").mean() > 0.5:
            col = k
            break
    if col is None:
        sys.exit(f"No semicolon-delimited column in {p}. Columns: {list(t.columns)}")
    return [frozenset(s.strip() for s in str(v).split(";") if s.strip()) for v in t[col]]


def contest_level(c):
    return c.drop_duplicates("contest_id").copy()


# ----------------------------------------------------------------------------- descriptive
def stage_desc(c, args):
    say("\n## DESCRIPTIVE ANALYTICS")
    say(f"Modeling rows: {len(c)}; distinct contests: {c['contest_id'].nunique()}")
    cols = ["party_votes", "total_votes", "party_share_pct", "margin_pct"]
    rows = []
    for k in cols:
        s = c[k]
        mode = s.mode().iloc[0] if k.endswith("pct") is False else np.nan
        rows.append(dict(attribute=k, mean=s.mean(), median=s.median(), sd=s.std(), variance=s.var(),
                         min=s.min(), q1=s.quantile(.25), q3=s.quantile(.75), max=s.max(),
                         iqr=s.quantile(.75) - s.quantile(.25), skew=s.skew()))
    table(pd.DataFrame(rows).round(2), "numeric_summary.csv")
    for k in ["party_simplified", "office", "us_region", "election_era", "is_contest_winner"]:
        vc = c[k].value_counts()
        df = pd.DataFrame({"count": vc, "percent": (vc / vc.sum() * 100).round(2)}).reset_index()
        df.columns = [k, "count", "percent"]
        table(df, f"freq_{k}.csv")
    w = c["is_contest_winner"].value_counts()
    say(f"Class imbalance (non-winner : winner) = {w.max() / w.min():.2f} : 1")
    corr = c[["party_share_pct", "margin_pct", "log_total_votes", "log_party_votes"]].corr().round(3)
    table(corr, "correlation_matrix.csv", index=True)
    cl = contest_level(c)
    for g in ["office", "us_region", "election_era"]:
        table(cl.groupby(g)["margin_pct"].agg(["count", "mean", "median", "std"]).round(2),
              f"margin_by_{g}.csv", index=True)
    pres = cl[cl["office"].str.contains("PRESIDENT")]
    table(pres.groupby("year")["total_votes"].sum().to_frame("pres_total_votes"), "pres_votes_by_year.csv", index=True)
    st = cl.groupby("state_po")["margin_pct"].mean().sort_values().round(2)
    say("Tightest 5 states (mean margin): " + ", ".join(f"{i}={v}" for i, v in st.head(5).items()))
    say("Widest 5 states (mean margin): " + ", ".join(f"{i}={v}" for i, v in st.tail(5).items()))
    # pie angles
    pv = c.groupby("party_simplified")["party_votes"].sum()
    pie = pd.DataFrame({"votes": pv, "percent": (pv / pv.sum() * 100).round(2)})
    pie["angle_deg"] = (pie["percent"] / 100 * 360).round(2)
    pie["contest_wins"] = c[c.is_contest_winner == 1].groupby("party_simplified").size().reindex(pie.index).fillna(0).astype(int)
    table(pie, "pie_angles.csv", index=True)
    # scaling before/after for log_total_votes
    v = c["log_total_votes"]
    mm = (v - v.min()) / (v.max() - v.min())
    z = (v - v.mean()) / v.std()
    j = int(np.floor(np.log10(v.abs().max()))) + 1
    ds = v / 10 ** j
    sc = pd.DataFrame({"raw": v, "minmax": mm, "zscore": z, f"decimal(j={j})": ds}).agg(["min", "max", "mean", "std"]).round(4)
    table(sc, "scaling_before_after.csv", index=True)
    # tertile cut points of total_votes and region membership
    say("Tertile cut points of total_votes: " + str(c["total_votes"].quantile([1 / 3, 2 / 3]).round(0).tolist()))
    table(c.groupby("us_region")["state_po"].agg(lambda s: ", ".join(sorted(s.unique()))).to_frame("states"),
          "region_hierarchy.csv", index=True)
    q = c["total_votes"]
    for k in ["party_votes", "total_votes"]:
        s = c[k]; q1, q3 = s.quantile(.25), s.quantile(.75); i = q3 - q1
        say(f"{k} (modeling table): rows above upper fence {q3 + 1.5 * i:,.1f}: {(s > q3 + 1.5 * i).sum()}")
    say("Rows with total_votes < 1000 (investigate): " + str((c.total_votes < 1000).sum()))


# ----------------------------------------------------------------------------- plots
def stage_plots(c, args):
    say("\n## PLOTS (saved in outputs/plots)")
    sns.set_theme(style="whitegrid")
    cl = contest_level(c)
    P = lambda n: path("plots", n)
    pal = {"DEMOCRAT": "#2b6cb0", "REPUBLICAN": "#c53030", "LIBERTARIAN": "#d69e2e", "OTHER": "#718096"}

    def pie(name, explode_small, title):
        pv = c.groupby("party_simplified")["party_votes"].sum().sort_values(ascending=False)
        pct = pv / pv.sum() * 100
        ex = [0.12 if (explode_small and p < 5) else 0 for p in pct]
        fig, ax = plt.subplots(figsize=(7, 6))
        w, _ = ax.pie(pv, explode=ex, colors=[pal.get(i, "gray") for i in pv.index], startangle=90, counterclock=False)
        ax.legend(w, [f"{i}: {p:.2f}% ({p * 3.6:.2f}\u00b0)" for i, p in pct.items()], loc="center left", bbox_to_anchor=(0.95, 0.5))
        ax.set_title(title); fig.tight_layout(); fig.savefig(P(name), dpi=300); plt.close(fig)
    pie("plot01_pie_party_share.png", False, "Plot 1: Share of total votes by simplified party")
    pie("plot02_exploded_pie_parties.png", True, "Plot 2: Exploded pie (parties under 5% pulled out)")

    d = cl.groupby(["year", "office"])["total_votes"].sum().unstack(fill_value=0) / 1e6
    ax = d.plot(kind="bar", figsize=(11, 5), width=0.8)
    ax.set_xlabel("Election year"); ax.set_ylabel("Total votes cast (millions)")
    ax.set_title(f"Plot 3: Votes by year and office ({int(cl.year.min())}-{int(cl.year.max())})")
    plt.tight_layout(); plt.savefig(P("plot03_bar_votes_by_year.png"), dpi=300); plt.close()

    s = (cl.groupby("state_po")["total_votes"].sum() / 1e6).sort_values().tail(10)
    ax = s.plot(kind="barh", figsize=(7, 5), color="#2f855a")
    ax.set_xlabel("Cumulative votes across contests (millions)"); ax.set_ylabel("State")
    ax.set_title("Plot 4: Top 10 states by cumulative votes")
    plt.tight_layout(); plt.savefig(P("plot04_hbar_top_states.png"), dpi=300); plt.close()

    plt.figure(figsize=(8, 5)); plt.hist(c.party_share_pct, bins=20, edgecolor="black", color="#4a5568")
    plt.xlabel("Party vote share in contest (%)"); plt.ylabel("Frequency (contest-party rows)")
    plt.title("Plot 5: Histogram of party vote share"); plt.tight_layout()
    plt.savefig(P("plot05_histogram_vote_share.png"), dpi=300); plt.close()

    order = [p for p in pal if p in set(c.party_simplified)]
    plt.figure(figsize=(8, 5)); sns.boxplot(data=c, x="party_simplified", y="party_share_pct", order=order, palette=pal)
    plt.xlabel("Simplified party"); plt.ylabel("Vote share (%)"); plt.title("Plot 6: Vote share by party")
    plt.tight_layout(); plt.savefig(P("plot06_boxplot_share_by_party.png"), dpi=300); plt.close()

    plt.figure(figsize=(8, 6)); sns.scatterplot(data=c, x="log_total_votes", y="log_party_votes", hue="party_simplified",
                                                 palette=pal, s=14, alpha=.5)
    plt.title("Plot 7: log party votes vs log total contest votes"); plt.tight_layout()
    plt.savefig(P("plot07_scatter_party_vs_total_votes.png"), dpi=300); plt.close()

    pr = c[c.office.str.contains("PRESIDENT") & c.party_simplified.isin(["DEMOCRAT", "REPUBLICAN"])]
    t = pr.groupby(["year", "party_simplified"])["party_share_pct"].mean().unstack()
    plt.figure(figsize=(8, 5))
    for p in t.columns:
        plt.plot(t.index, t[p], marker="o", color=pal[p], label=p)
    plt.xlabel("Presidential election year"); plt.ylabel("Mean state vote share (%)")
    plt.title("Plot 8: Mean state vote share, presidential elections"); plt.legend()
    plt.tight_layout(); plt.savefig(P("plot08_line_major_party_trend.png"), dpi=300); plt.close()

    top = cl.groupby("state_po")["total_votes"].sum().sort_values().tail(20).index
    m = cl[cl.state_po.isin(top)].groupby("state_po")["margin_pct"].mean().sort_values()
    plt.figure(figsize=(7, 7)); plt.plot(m.values, m.index, "o", color="#6b46c1")
    plt.xlabel("Mean contest victory margin (%)"); plt.ylabel("State (top 20 by votes)")
    plt.title("Plot 9: Dot plot of mean margin"); plt.grid(axis="y", ls=":")
    plt.tight_layout(); plt.savefig(P("plot09_dotplot_state_margin.png"), dpi=300); plt.close()

    # stem-and-leaf: stem = whole millions, leaf = first decimal (0.1M); empty stems kept
    y = cl[cl.office.str.contains("PRESIDENT") & (cl.year == 2020)]["total_votes"].sort_values().values
    lines = [f"Stem-and-leaf: 2020 presidential total votes, {len(y)} jurisdictions", "Key: 3 | 4 = 3.4 million", ""]
    for st in range(int(y.min() // 1e6), int(y.max() // 1e6) + 1):
        leaves = [str(int((v % 1e6) // 1e5)) for v in y if int(v // 1e6) == st]
        lines.append(f"{st:>3} | {' '.join(leaves)}")
    txt = "\n".join(lines)
    open(path("tables", "stem_and_leaf_2020.txt"), "w").write(txt)
    say("```\n" + txt + "\n```")
    fig = plt.figure(figsize=(6, 0.28 * len(lines) + 0.6)); fig.text(0.03, 0.97, txt, family="monospace", va="top", fontsize=9)
    fig.savefig(P("plot10_stem_and_leaf_pres_turnout.png"), dpi=300); plt.close(fig)

    h = c.pivot_table(index="us_region", columns="party_simplified", values="party_share_pct", aggfunc="mean")[order]
    plt.figure(figsize=(8, 5)); sns.heatmap(h, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={"label": "Mean share (%)"})
    plt.title("Plot 11: Mean vote share by region and party"); plt.tight_layout()
    plt.savefig(P("plot11_heatmap_region_party.png"), dpi=300); plt.close()

    plt.figure(figsize=(7, 5)); sns.violinplot(data=cl, x="office", y="margin_pct", cut=0, inner="quartile")
    plt.xlabel("Office"); plt.ylabel("Victory margin (%)"); plt.title("Plot 12: Margin distribution by office")
    plt.tight_layout(); plt.savefig(P("plot12_violin_margin_office.png"), dpi=300); plt.close()

    cl["margin_cat"] = pd.cut(cl.margin_pct, [-0.01, 5, 15, 101], labels=["Close (<5)", "Moderate (5-15)", "Safe (>15)"])
    plt.figure(figsize=(8, 5)); sns.countplot(data=cl, x="us_region", hue="margin_cat")
    plt.xlabel("Region"); plt.ylabel("Number of contests"); plt.title("Plot 13: Contests by margin category and region")
    plt.tight_layout(); plt.savefig(P("plot13_count_margin_region.png"), dpi=300); plt.close()

    corr = c[["party_share_pct", "margin_pct", "log_total_votes", "log_party_votes"]].corr()
    plt.figure(figsize=(6, 5)); sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1)
    plt.title("Plot 14: Correlation heatmap"); plt.tight_layout(); plt.savefig(P("plot14_corr_heatmap.png"), dpi=300); plt.close()
    say("14 plots written. Now OPEN each one and write Observation / Inferences from what you SEE and from tables/*.csv.")


# ----------------------------------------------------------------------------- DIC
def dic(tx, min_count, M, max_k):
    """Dynamic Itemset Counting. States: DC, DS (counting), SC, SS (finished)."""
    N = len(tx)
    info = {}
    for i in sorted({i for t in tx for i in t}):
        info[(i,)] = dict(fs=frozenset([i]), count=0, seen=0, state="DC")
    trace, pos, step = [], 0, 0
    while any(v["state"] in ("DC", "DS") for v in info.values()):
        step += 1
        chunk = [tx[(pos + j) % N] for j in range(M)]
        for v in info.values():
            if v["state"] in ("DC", "DS"):
                take = min(M, N - v["seen"])
                fs = v["fs"]
                v["count"] += sum(1 for t in chunk[:take] if fs <= t)
                v["seen"] += take
        for v in info.values():
            if v["state"] == "DC" and v["count"] >= min_count:
                v["state"] = "DS"
            if v["state"] in ("DC", "DS") and v["seen"] >= N:
                v["state"] = "SS" if v["count"] >= min_count else "SC"
        pos = (pos + M) % N
        alive = {k for k, v in info.items() if v["state"] in ("DS", "SS")}
        new = 0
        by_size = defaultdict(list)
        for k in alive:
            by_size[len(k)].append(k)
        for size, group in by_size.items():
            if size >= max_k:
                continue
            groups = defaultdict(list)
            for k in group:
                groups[k[:-1]].append(k[-1])
            for pre, lasts in groups.items():
                for a, b in itertools.combinations(sorted(lasts), 2):
                    cand = pre + (a, b)
                    if cand in info:
                        continue
                    if all(sub in alive for sub in itertools.combinations(cand, size) if sub != pre + (a,) and sub != pre + (b,)):
                        info[cand] = dict(fs=frozenset(cand), count=0, seen=0, state="DC")
                        new += 1
        st = Counter(v["state"] for v in info.values())
        trace.append(dict(interval=step, transactions_in_interval=M, DC=st["DC"], DS=st["DS"], SC=st["SC"], SS=st["SS"], new_candidates=new))
    freq = {k: v["count"] for k, v in info.items() if v["state"] == "SS"}
    return freq, pd.DataFrame(trace), step * M / N


def make_rules(freq, N, min_conf):
    rules = []
    for iset, c in freq.items():
        if len(iset) < 2:
            continue
        for r in range(1, len(iset)):
            for ante in itertools.combinations(iset, r):
                cons = tuple(x for x in iset if x not in ante)
                conf = c / freq[ante]
                if conf >= min_conf:
                    rules.append(dict(antecedent=" & ".join(ante), consequent=" & ".join(cons), support=c / N,
                                      confidence=conf, lift=conf / (freq[cons] / N), count=c,
                                      _items=ante + cons))
    return pd.DataFrame(rules)


def split_rules(R, def_attrs):
    attrs = lambda items: {i.split("=")[0].lower() for i in items}
    is_def = R["_items"].apply(lambda it: attrs(it) <= {a.lower() for a in def_attrs})
    return R[is_def].drop(columns="_items"), R[~is_def].drop(columns="_items")


def stage_dic(tx, args):
    say("\n## DIC")
    N = len(tx)
    mc = math.ceil(args.min_support * N)
    say(f"N={N}, min_support={args.min_support}, min_count={mc}, min_conf={args.min_conf}, M={args.M}, max_k={args.max_k}")
    t0 = time.perf_counter()
    freq, trace, passes = dic(tx, mc, args.M, args.max_k)
    dt = time.perf_counter() - t0
    say(f"DIC finished in {len(trace)} intervals (= {passes:.2f} equivalent database passes), {dt:.3f}s; frequent itemsets = {len(freq)}")
    table(trace, "dic_trace.csv")
    sizes = Counter(len(k) for k in freq)
    say("Frequent itemsets by size: " + str(dict(sorted(sizes.items()))))
    fi = pd.DataFrame([dict(itemset=" & ".join(k), size=len(k), count=v, support_pct=round(v / N * 100, 2)) for k, v in freq.items()])
    table(fi.sort_values(["size", "count"], ascending=[True, False]), "dic_frequent_itemsets.csv", show=False)
    say("Top 25 frequent itemsets (full list in tables/dic_frequent_itemsets.csv):")
    say("```\n" + fi.sort_values("count", ascending=False).head(25).to_string(index=False) + "\n```")
    R = make_rules(freq, N, args.min_conf)
    say(f"Rules with conf >= {args.min_conf}: {len(R)}")
    D, I = split_rules(R, args.def_attrs)
    for nm, df in (("definitional", D), ("informative", I)):
        df = df.sort_values(["lift", "confidence"], ascending=False).round(4)
        table(df, f"dic_rules_{nm}.csv", show=False)
        say(f"\nTop {nm} rules ({len(df)} total):\n```\n{df.head(15).to_string(index=False)}\n```")
    sens = []
    for ms in (0.10, 0.15, 0.20):
        f2, _, _ = dic(tx, math.ceil(ms * N), args.M, args.max_k)
        for mcf in (0.6, 0.7, 0.8):
            sens.append(dict(min_support=ms, min_confidence=mcf, frequent_itemsets=len(f2), rules=len(make_rules(f2, N, mcf))))
    table(pd.DataFrame(sens), "dic_sensitivity.csv")
    return freq


# ----------------------------------------------------------------------------- CLOSET
def closet(tx, min_count):
    """CLOSET-style closed itemset mining on f-list ordered conditional databases, with
    item merging and subset checking (result store indexed by support)."""
    cnt = Counter(i for t in tx for i in t)
    flist = [i for i, c in sorted(cnt.items(), key=lambda x: (-x[1], x[0])) if c >= min_count]
    rank = {i: r for r, i in enumerate(flist)}
    db = [(tuple(sorted((i for i in t if i in rank), key=rank.get)), 1) for t in tx]
    closed, by_count = {}, defaultdict(list)

    def rec(db, prefix):
        total = sum(w for _, w in db)
        local = Counter()
        for its, w in db:
            for i in its:
                local[i] += w
        merged = {i for i, c in local.items() if c == total}          # item merging
        X = prefix | frozenset(merged)
        if X:
            if X in closed or any(X < Y for Y in by_count[total]):    # subset checking
                return
            closed[X] = total
            by_count[total].append(X)
        rest = sorted([i for i, c in local.items() if c >= min_count and i not in merged], key=rank.get, reverse=True)
        for i in rest:
            cond = [(tuple(j for j in its if rank[j] < rank[i] and j not in merged), w) for its, w in db if i in its]
            rec(cond, X | {i})
    rec(db, frozenset())
    return closed, flist


def stage_closet(tx, freq, args):
    say("\n## CLOSET")
    N = len(tx)
    mc = math.ceil(args.min_support * N)
    t0 = time.perf_counter()
    closed, flist = closet(tx, mc)
    dt = time.perf_counter() - t0
    say(f"f-list (descending support): {flist}")
    say(f"CLOSET: {len(closed)} closed frequent itemsets in {dt:.3f}s")
    F = {frozenset(k): v for k, v in freq.items()}
    brute = {X for X, c in F.items() if not any(X < Y and F[Y] == c for Y in F)}
    say(f"Closedness verification (brute force over DIC frequent itemsets): sets equal = {set(closed) == brute}; "
        f"violations (CFI with equal-support superset) = {sum(1 for X, c in closed.items() if any(X < Y and F.get(Y) == c for Y in F))}")
    lossless = all(F[X] == max(c for Y, c in closed.items() if X <= Y) for X in F)
    say(f"Lossless check (support of every frequent itemset recovered from closed supersets): {lossless}")
    say(f"DIC frequent itemsets F={len(F)}, closed C={len(closed)}, reduction={(len(F) - len(closed)) / len(F) * 100:.2f}%")
    cf = pd.DataFrame([dict(itemset=" & ".join(sorted(X)), size=len(X), count=c, support_pct=round(c / N * 100, 2)) for X, c in closed.items()])
    table(cf.sort_values("count", ascending=False), "closet_cfis.csv", show=False)
    say("```\n" + cf.sort_values("count", ascending=False).to_string(index=False) + "\n```")
    sup = lambda X: max(c for Y, c in closed.items() if frozenset(X) <= Y)
    rows = []
    for Z, c in closed.items():
        if len(Z) < 2:
            continue
        for r in range(1, len(Z)):
            for ante in itertools.combinations(sorted(Z), r):
                cons = tuple(sorted(Z - set(ante)))
                conf = c / sup(ante)
                if conf >= args.min_conf:
                    rows.append(dict(antecedent=" & ".join(ante), consequent=" & ".join(cons), support=c / N, confidence=conf, lift=conf / (sup(cons) / N)))
    R = pd.DataFrame(rows).sort_values("lift", ascending=False).round(4) if rows else pd.DataFrame()
    table(R, "closet_derived_rules.csv", show=False)
    say(f"Association rules derived from CFIs (conf >= {args.min_conf}): {len(R)}\n```\n{R.head(15).to_string(index=False)}\n```")


# ----------------------------------------------------------------------------- KNN
def knn_prepare(c, feats_num, args):
    from sklearn.model_selection import GroupShuffleSplit, GroupKFold, cross_val_score
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    cats = ["office", "party_simplified", "us_region"]
    X, y, g = c[feats_num + cats], c["is_contest_winner"].astype(int), c["contest_id"]
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=SEED).split(X, y, g))
    ct = ColumnTransformer([("n", StandardScaler(), feats_num), ("c", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cats)])
    mk = lambda k: Pipeline([("t", ct), ("k", KNeighborsClassifier(n_neighbors=k, algorithm="brute"))])
    cv = GroupKFold(n_splits=5)
    res = []
    for k in range(3, 26, 2):
        s = cross_val_score(mk(k), X.iloc[tr], y.iloc[tr], groups=g.iloc[tr], cv=cv, scoring="f1")
        res.append(dict(K=k, cv_f1_mean=s.mean(), cv_f1_sd=s.std()))
    res = pd.DataFrame(res)
    best = int(res.loc[res.cv_f1_mean.idxmax(), "K"])
    return X, y, g, tr, te, res, best, mk, ct


def stage_knn(c, args):
    from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
                                 roc_auc_score, roc_curve)
    from sklearn.dummy import DummyClassifier
    say("\n## KNN (grouped split by contest; seed 42)")
    say(f"Class distribution: {c.is_contest_winner.value_counts().to_dict()}")
    variants = {"full": ["year", "log_total_votes", "log_party_votes", "num_candidates", "writein_share_pct"],
                "no_party_votes (leakage ablation)": ["year", "log_total_votes", "num_candidates", "writein_share_pct"]}
    summary = []
    for name, feats in variants.items():
        X, y, g, tr, te, res, best, mk, ct = knn_prepare(c, feats, args)
        say(f"\n### Variant: {name}\nFeatures: {feats} + one-hot office, party_simplified, us_region\n"
            f"train={len(tr)}, test={len(te)}, shared contests between train/test = {len(set(g.iloc[tr]) & set(g.iloc[te]))}")
        table(res.round(4), f"knn_cv_{name.split()[0]}.csv")
        model = mk(best).fit(X.iloc[tr], y.iloc[tr])
        pred, prob = model.predict(X.iloc[te]), model.predict_proba(X.iloc[te])[:, 1]
        yt = y.iloc[te]
        tn, fp, fn, tp = confusion_matrix(yt, pred).ravel()
        base = DummyClassifier(strategy="most_frequent").fit(X.iloc[tr], y.iloc[tr]).predict(X.iloc[te])
        row = dict(variant=name, K=best, accuracy=accuracy_score(yt, pred), precision=precision_score(yt, pred),
                   recall=recall_score(yt, pred), specificity=tn / (tn + fp), f1=f1_score(yt, pred),
                   roc_auc=roc_auc_score(yt, prob), TN=tn, FP=fp, FN=fn, TP=tp,
                   baseline_accuracy=accuracy_score(yt, base))
        summary.append(row)
        tag = "full" if name == "full" else "ablation"
        fig, ax = plt.subplots(figsize=(6, 4)); ax.errorbar(res.K, res.cv_f1_mean, yerr=res.cv_f1_sd, marker="o", capsize=3)
        ax.axvline(best, ls="--", color="gray"); ax.set_xlabel("K"); ax.set_ylabel("Grouped 5-fold CV F1")
        ax.set_title(f"K selection ({name})"); fig.tight_layout(); fig.savefig(path("plots", f"knn_k_vs_cvf1_{tag}.png"), dpi=300); plt.close(fig)
        fig, ax = plt.subplots(figsize=(4.5, 4)); sns.heatmap([[tn, fp], [fn, tp]], annot=True, fmt="d", cmap="Blues", ax=ax,
                                                              xticklabels=["Pred 0", "Pred 1"], yticklabels=["Actual 0", "Actual 1"])
        ax.set_title(f"Confusion matrix (K={best})"); fig.tight_layout(); fig.savefig(path("plots", f"knn_confusion_{tag}.png"), dpi=300); plt.close(fig)
        fpr, tpr, _ = roc_curve(yt, prob)
        fig, ax = plt.subplots(figsize=(5, 4)); ax.plot(fpr, tpr, label=f"KNN AUC={row['roc_auc']:.3f}"); ax.plot([0, 1], [0, 1], "--", color="gray")
        ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate"); ax.legend(); fig.tight_layout()
        fig.savefig(path("plots", f"knn_roc_{tag}.png"), dpi=300); plt.close(fig)
        if name == "full":
            ex = c.iloc[te][["contest_id", "party_simplified", "party_share_pct"]].copy()
            ex["actual"], ex["predicted"] = yt.values, pred
            table(ex.head(10).round(2), "knn_examples.csv")
            Xt = model.named_steps["t"].transform(X.iloc[te])
            Xtr = model.named_steps["t"].transform(X.iloc[tr])
            for i in range(3):
                d, idx = model.named_steps["k"].kneighbors(Xt[i:i + 1])
                nb = c.iloc[tr].iloc[idx[0]]
                say(f"\nNeighbour explanation for test row {i} ({c.iloc[te].iloc[i].contest_id}, {c.iloc[te].iloc[i].party_simplified}):")
                say("```\n" + pd.DataFrame({"distance": d[0].round(3), "neighbour": nb.contest_id.values,
                                            "party": nb.party_simplified.values, "label": y.iloc[tr].iloc[idx[0]].values}).to_string(index=False)
                    + f"\n-> majority vote = {int(round(y.iloc[tr].iloc[idx[0]].mean()))}, actual = {int(yt.iloc[i])}\n```")
    table(pd.DataFrame(summary).round(4), "knn_summary.csv")


# ----------------------------------------------------------------------------- AGNES
def stage_agnes(c, args):
    from scipy.cluster.hierarchy import linkage, dendrogram, cophenet, fcluster
    from scipy.spatial.distance import pdist
    say("\n## AGNES on states (presidential contests, z-scored, Euclidean)")
    cl = contest_level(c)
    pres = cl[cl.office.str.contains("PRESIDENT")]
    dem = c[c.office.str.contains("PRESIDENT") & (c.party_simplified == "DEMOCRAT")]
    f = pd.DataFrame({
        "mean_dem_share": dem.groupby("state_po")["party_share_pct"].mean(),
        "volatility_dem_share_sd": dem.groupby("state_po")["party_share_pct"].std(),
        "mean_margin": pres.groupby("state_po")["margin_pct"].mean(),
        "close_race_fraction": pres.groupby("state_po")["margin_pct"].apply(lambda s: (s < 5).mean())}).dropna()
    table(f.round(2), "agnes_state_features.csv", index=True, show=False)
    Z_ = (f - f.mean()) / f.std()
    d = pdist(Z_.values)
    say(f"n = {len(f)} states; features = {list(f.columns)}")
    best, cop = None, {}
    for m in ("single", "complete", "average"):
        L = linkage(Z_.values, method=m)
        cop[m] = cophenet(L, d)[0]
        fig, ax = plt.subplots(figsize=(13, 5)); dendrogram(L, labels=f.index.tolist(), ax=ax, leaf_font_size=9)
        ax.set_ylabel(f"Euclidean distance ({m} linkage)"); ax.set_title(f"AGNES dendrogram: {m} linkage"); fig.tight_layout()
        fig.savefig(path("plots", f"agnes_dendrogram_{m}.png"), dpi=300); plt.close(fig)
        if m == "average":
            best = L
    table(pd.DataFrame({"linkage": list(cop), "cophenetic_corr": [round(v, 4) for v in cop.values()]}), "agnes_cophenetic.csv")
    use = max(cop, key=cop.get)
    say(f"Linkage with highest cophenetic correlation: {use}. Reporting that one.")
    L = linkage(Z_.values, method=use)
    n = len(f)
    life = pd.DataFrame([dict(K=K, merge_height_before=L[n - K - 1, 2], merge_height_after=L[n - K, 2],
                              lifetime=L[n - K, 2] - L[n - K - 1, 2]) for K in range(2, 9)]).round(4)
    table(life, "agnes_lifetimes.csv")
    K = int(life[life.K >= 3].sort_values("lifetime", ascending=False).iloc[0]["K"])
    say(f"Chosen K (largest lifetime among K>=3; K=2 shown in table for reference): {K}")
    f["cluster"] = fcluster(L, K, criterion="maxclust")
    prof = f.groupby("cluster").agg(size=("mean_dem_share", "size"), mean_dem_share=("mean_dem_share", "mean"),
                                    mean_margin=("mean_margin", "mean"), volatility=("volatility_dem_share_sd", "mean"),
                                    close_frac=("close_race_fraction", "mean")).round(2)
    prof["states"] = f.groupby("cluster").apply(lambda g: ", ".join(g.index)).values
    table(prof, "agnes_cluster_profiles.csv", index=True)
    fig, ax = plt.subplots(figsize=(13, 5)); dendrogram(L, labels=f.index.tolist(), color_threshold=L[n - K, 2] - 1e-9, ax=ax)
    ax.set_title(f"AGNES ({use} linkage) cut at K={K}"); fig.tight_layout(); fig.savefig(path("plots", "agnes_dendrogram_final.png"), dpi=300); plt.close(fig)


# ----------------------------------------------------------------------------- Spark benchmark
def gen_candidates(level_keys, k):
    level = set(level_keys)
    out = set()
    for a in level:
        for b in level:
            u = tuple(sorted(set(a) | set(b)))
            if len(u) == k and all(s in level for s in itertools.combinations(u, k - 1)):
                out.add(u)
    return [frozenset(u) for u in out]


def spark_itemsets(sc, tx, mc, max_k, parts):
    rdd = sc.parallelize(tx, parts).cache()
    freq, cands, k = {}, [frozenset([i]) for i in sorted({i for t in tx for i in t})], 1
    while cands and k <= max_k:
        b = sc.broadcast(cands)
        got = rdd.flatMap(lambda t, b=b: [(c, 1) for c in b.value if c <= t]).reduceByKey(add).filter(lambda kv, mc=mc: kv[1] >= mc).collect()
        b.unpersist()
        level = {tuple(sorted(c)): n for c, n in got}
        freq.update(level)
        k += 1
        cands = gen_candidates(level.keys(), k) if level and k <= max_k else []
    rdd.unpersist()
    return freq


def spark_knn(sc, Xtr, ytr, Xte, k, parts):
    bt = sc.broadcast((Xtr, ytr, (Xtr ** 2).sum(1)))

    def part(it):
        rows = np.array(list(it))
        if len(rows) == 0:
            return iter([])
        A, y, a2 = bt.value
        d = (rows ** 2).sum(1)[:, None] + a2[None, :] - 2 * rows @ A.T
        nn = np.argpartition(d, k - 1, axis=1)[:, :k]
        return iter((y[nn].mean(1) > 0.5).astype(int).tolist())
    out = sc.parallelize(list(Xte), parts).mapPartitions(part).collect()
    bt.unpersist()
    return np.array(out)


def timeit(fn, runs):
    fn()  # warm-up (not counted)
    ts, r = [], None
    for _ in range(runs):
        t = time.perf_counter(); r = fn(); ts.append(time.perf_counter() - t)
    return r, float(np.mean(ts)), float(np.std(ts, ddof=1)) if len(ts) > 1 else 0.0


def stage_spark(c, tx, args):
    try:
        from pyspark.sql import SparkSession
    except ImportError:
        sys.exit("pip install pyspark   (Java 17+ required)")
    from sklearn.neighbors import KNeighborsClassifier
    say("\n## PYSPARK BENCHMARK")
    t0 = time.perf_counter()
    spark = (SparkSession.builder.master(f"local[{args.cores}]").appName("elections")
             .config("spark.sql.shuffle.partitions", str(args.cores * 2)).config("spark.driver.memory", args.mem)
             .config("spark.ui.enabled", "false").getOrCreate())
    sc = spark.sparkContext
    sc.setLogLevel("ERROR")
    startup = time.perf_counter() - t0
    parts = args.cores * 2
    cfg = pd.DataFrame([dict(spark_version=spark.version, master=sc.master, cores=args.cores, driver_memory=args.mem,
                             shuffle_partitions=parts, rdd_partitions=parts, jvm_startup_s=round(startup, 2),
                             python=platform.python_version(), runs=args.runs, warmup_runs=1)])
    table(cfg, "spark_config.csv")
    N = len(tx)
    X, y, g, tr, te, res, best, mk, ct = knn_prepare(c, ["year", "log_total_votes", "log_party_votes", "num_candidates", "writein_share_pct"], args)
    ct.fit(X.iloc[tr])
    Xtr, Xte = ct.transform(X.iloc[tr]).astype(float), ct.transform(X.iloc[te]).astype(float)
    ytr = y.iloc[tr].values
    rows = []
    for s in args.scales:
        txs = tx * s
        mc = math.ceil(args.min_support * len(txs))
        Ms = args.M * s
        (fp, tp_, sdp) = timeit(lambda: dic(txs, mc, Ms, args.max_k)[0], args.runs)
        (fs, ts_, sds) = timeit(lambda: spark_itemsets(sc, txs, mc, args.max_k, parts), args.runs)
        rows.append(dict(technique="Itemset counting (DIC vs Spark level-wise)", scale=s, rows=len(txs), python_s=tp_, python_sd=sdp,
                         spark_s=ts_, spark_sd=sds, same_output=(fp == fs), n_itemsets=len(fp)))
        Xq = np.tile(Xte, (s, 1))
        clf = KNeighborsClassifier(n_neighbors=best, algorithm="brute").fit(Xtr, ytr)
        (pp, tp2, sdp2) = timeit(lambda: clf.predict(Xq), args.runs)
        (ps, ts2, sds2) = timeit(lambda: spark_knn(sc, Xtr, ytr, Xq, best, parts), args.runs)
        rows.append(dict(technique=f"KNN (K={best}; test queries replicated)", scale=s, rows=len(Xq), python_s=tp2, python_sd=sdp2,
                         spark_s=ts2, spark_sd=sds2, same_output=bool((pp == ps).all()), n_itemsets=np.nan))
        say(f"scale {s}x done")
    B = pd.DataFrame(rows)
    B["speedup"] = B.python_s / B.spark_s
    B["reduction_pct"] = (B.python_s - B.spark_s) / B.python_s * 100
    table(B.round(4), "spark_benchmark.csv")
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, (tn, d) in zip(axs, B.groupby("technique", sort=False)):
        ax.errorbar(d.rows, d.python_s, yerr=d.python_sd, marker="o", label="Python", capsize=3)
        ax.errorbar(d.rows, d.spark_s, yerr=d.spark_sd, marker="s", label="PySpark", capsize=3)
        ax.set_xlabel("Rows processed"); ax.set_ylabel("Time (s), mean \u00b1 SD"); ax.set_title(tn, fontsize=9); ax.legend()
    fig.tight_layout(); fig.savefig(path("plots", "spark_time_vs_scale.png"), dpi=300); plt.close(fig)
    plt.figure(figsize=(7, 4.5))
    for tn, d in B.groupby("technique", sort=False):
        plt.plot(d.scale, d.speedup, marker="o", label=tn)
    plt.axhline(1, ls="--", color="gray"); plt.xlabel("Replication factor"); plt.ylabel("Speedup = T_python / T_spark")
    plt.legend(fontsize=7); plt.tight_layout(); plt.savefig(path("plots", "spark_speedup.png"), dpi=300); plt.close()
    spark.stop()


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contests", default="data/processed/contests_modeling.csv")
    ap.add_argument("--transactions", default="data/processed/transactions_fpm.csv")
    ap.add_argument("--stage", nargs="+", default=["all"])
    ap.add_argument("--min_support", type=float, default=0.15)
    ap.add_argument("--min_conf", type=float, default=0.70)
    ap.add_argument("--M", type=int, default=485, help="DIC interval size (~N/10)")
    ap.add_argument("--max_k", type=int, default=8, help="max itemset size (8 = effectively unlimited here)")
    ap.add_argument("--def_attrs", nargs="+", default=["Share", "Winner"], help="item attributes that define rules by construction")
    ap.add_argument("--cores", type=int, default=2)
    ap.add_argument("--mem", default="2g")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--scales", type=int, nargs="+", default=[1, 5, 10, 20])
    ap.add_argument("--out", default="outputs")
    args = ap.parse_args()
    global OUT
    OUT = args.out
    np.random.seed(SEED)
    stages = ["desc", "plots", "dic", "closet", "knn", "agnes", "spark"] if "all" in args.stage else args.stage
    c = load(args)
    tx = load_tx(args.transactions) if set(stages) & {"dic", "closet", "spark"} else None
    freq = None
    say(f"# RESULTS SUMMARY (generated {time.strftime('%Y-%m-%d %H:%M')}), python {platform.python_version()}, "
        f"pandas {pd.__version__}, numpy {np.__version__}")
    if "desc" in stages: stage_desc(c, args)
    if "plots" in stages: stage_plots(c, args)
    if "dic" in stages or "closet" in stages:
        freq = stage_dic(tx, args)
    if "closet" in stages: stage_closet(tx, freq, args)
    if "knn" in stages: stage_knn(c, args)
    if "agnes" in stages: stage_agnes(c, args)
    if "spark" in stages: stage_spark(c, tx, args)
    open(path("results_summary.md"), "w").write("\n".join(LOG))
    print(f"\nDone. Everything is in {OUT}/ ; send me {OUT}/results_summary.md")


if __name__ == "__main__":
    main()