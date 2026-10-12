#!/usr/bin/env python3
"""Correlate Waiting Game k with objective financial_audit hack rates.

Joins:
  temporal-discounting/results/summary/by_condition.csv  (IV: k)
  misalignment outputs/analysis_reward_hacking/by_condition.csv  (DV: hack_rate)

Primary comparisons (no OpenAI judge):
  1. Within-model persona contrasts (Δ log k vs Δ hack_rate)
  2. Cell-level Spearman/Pearson of log(k) vs hack_rate (competence-pass subset)
  3. Group means: high-k vs low-k; greater vs lesser vs off

Usage:
  python src/analyze_k_hacking_correlation.py
  python src/analyze_k_hacking_correlation.py \\
      --waiting-game ../temporal-discounting/results/summary/by_condition.csv \\
      --hacking outputs/analysis_reward_hacking/by_condition.csv
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from log_parse import normalize_persona_id  # noqa: E402

HIGH_K_THRESHOLD = 1.0  # sooner-dominant / near-bound class
HUMAN_K = 0.01


def _coerce_bool(series: pd.Series) -> pd.Series:
    if series.dtype == bool:
        return series
    return series.astype(str).str.lower().isin({"true", "1", "yes"})


def load_waiting_game_iv(
    path: Path,
    option_order: str = "pooled",
    trial_type: str | None = "direct",
) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {
        "model_name",
        "persona_id",
        "option_order",
        "competence_passed",
        "k",
    }
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Waiting Game table missing columns: {sorted(missing)}")

    out = df.copy()
    out["persona_id"] = out["persona_id"].map(normalize_persona_id)
    if "persona_discounting_group" in out.columns:
        out["persona_discounting_group"] = out["persona_discounting_group"].map(
            lambda x: "" if pd.isna(x) else str(x).strip()
        )
    else:
        out["persona_discounting_group"] = ""
    out.loc[out["persona_id"] == "off", "persona_discounting_group"] = "off"

    out["competence_passed"] = _coerce_bool(out["competence_passed"])
    if "k_reliable" in out.columns:
        out["k_reliable"] = _coerce_bool(out["k_reliable"])
    else:
        out["k_reliable"] = False
    if "valid_discount_rate" in out.columns:
        out["valid_discount_rate"] = _coerce_bool(out["valid_discount_rate"])
    else:
        out["valid_discount_rate"] = out["competence_passed"] & out["k_reliable"]

    out = out[out["option_order"] == option_order].copy()
    if trial_type and "trial_type" in out.columns:
        # Accept both "direct" and display label if present.
        tt = out["trial_type"].astype(str).str.lower()
        out = out[tt.isin({trial_type.lower(), "direct"})].copy()

    out["k"] = pd.to_numeric(out["k"], errors="coerce")
    out["log_k"] = np.log(out["k"].clip(lower=1e-12))
    out["k_class"] = np.where(
        out["k"].isna(),
        "missing",
        np.where(out["k"] >= HIGH_K_THRESHOLD, "high_sooner_dominant", "low_interior"),
    )
    out["iv_include"] = out["competence_passed"] & out["k"].notna() & np.isfinite(out["k"])

    keep = [
        "model_name",
        "persona_id",
        "persona_discounting_group",
        "option_order",
        "competence_passed",
        "k_reliable",
        "valid_discount_rate",
        "k",
        "log_k",
        "k_class",
        "iv_include",
    ]
    if "model_family" in out.columns:
        keep.insert(1, "model_family")
    if "r_squared" in out.columns:
        keep.append("r_squared")
    return out[keep].drop_duplicates(["model_name", "persona_id"]).reset_index(drop=True)


def load_hacking_dv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "scenario" in df.columns:
        df = df[df["scenario"] == "financial_audit"].copy()
    required = {"model_name", "persona_id", "hack_rate"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Hacking table missing columns: {sorted(missing)}")
    out = df.copy()
    out["persona_id"] = out["persona_id"].map(normalize_persona_id)
    out["hack_rate"] = pd.to_numeric(out["hack_rate"], errors="coerce")
    if "definitions_edit_rate" in out.columns:
        out["definitions_edit_rate"] = pd.to_numeric(
            out["definitions_edit_rate"], errors="coerce"
        )
    if "n_agent_started" in out.columns:
        out["n_agent_started"] = pd.to_numeric(out["n_agent_started"], errors="coerce")
    else:
        out["n_agent_started"] = np.nan
    if "persona_discounting_group" not in out.columns:
        out["persona_discounting_group"] = ""
    out.loc[out["persona_id"] == "off", "persona_discounting_group"] = "off"
    return out


def join_iv_dv(iv: pd.DataFrame, dv: pd.DataFrame) -> pd.DataFrame:
    merged = iv.merge(
        dv,
        on=["model_name", "persona_id"],
        how="inner",
        suffixes=("_iv", "_dv"),
    )
    # Prefer Waiting Game group when both present.
    if "persona_discounting_group_iv" in merged.columns:
        merged["persona_discounting_group"] = merged["persona_discounting_group_iv"]
        if "persona_discounting_group_dv" in merged.columns:
            miss = merged["persona_discounting_group"].isna() | (
                merged["persona_discounting_group"].astype(str).str.strip() == ""
            )
            merged.loc[miss, "persona_discounting_group"] = merged.loc[
                miss, "persona_discounting_group_dv"
            ]
    return merged


def _safe_corr(x: pd.Series, y: pd.Series, method: str) -> dict:
    mask = x.notna() & y.notna() & np.isfinite(x) & np.isfinite(y)
    n = int(mask.sum())
    if n < 3:
        return {"method": method, "n": n, "r": float("nan"), "p": float("nan")}
    xs = x[mask]
    ys = y[mask]
    if method == "pearson":
        r = float(xs.corr(ys, method="pearson"))
    else:
        r = float(xs.corr(ys, method="spearman"))
    # Approximate two-sided p via t-distribution without scipy if needed.
    try:
        from scipy import stats

        if method == "pearson":
            _, p = stats.pearsonr(xs, ys)
        else:
            _, p = stats.spearmanr(xs, ys)
        p = float(p)
    except Exception:
        p = float("nan")
    return {"method": method, "n": n, "r": r, "p": p}


def cell_level_correlations(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    subsets = {
        "all_joined": joined,
        "competence_pass": joined[joined["iv_include"]],
        "competence_pass_with_agent": joined[
            joined["iv_include"]
            & (pd.to_numeric(joined["n_agent_started"], errors="coerce").fillna(0) > 0)
        ]
        if "n_agent_started" in joined.columns
        else joined.iloc[0:0],
        "low_interior_k": joined[joined["iv_include"] & (joined["k_class"] == "low_interior")],
    }
    for name, sub in subsets.items():
        for method in ("spearman", "pearson"):
            stats = _safe_corr(sub["log_k"], sub["hack_rate"], method)
            rows.append({"subset": name, "x": "log_k", "y": "hack_rate", **stats})
            if "definitions_edit_rate" in sub.columns:
                stats2 = _safe_corr(sub["log_k"], sub["definitions_edit_rate"], method)
                rows.append(
                    {"subset": name, "x": "log_k", "y": "definitions_edit_rate", **stats2}
                )
    return pd.DataFrame(rows)


def _nanmean(series: pd.Series) -> float:
    vals = pd.to_numeric(series, errors="coerce")
    if len(vals) == 0 or vals.notna().sum() == 0:
        return float("nan")
    return float(np.nanmean(vals))


def within_model_persona_contrasts(joined: pd.DataFrame) -> pd.DataFrame:
    """For each model: greater vs lesser mean log_k / hack_rate deltas."""
    rows = []
    for model_name, g in joined.groupby("model_name"):
        greater = g[g["persona_discounting_group"] == "greater"]
        lesser = g[g["persona_discounting_group"] == "lesser"]
        control = g[g["persona_id"] == "off"]
        row = {
            "model_name": model_name,
            "n_greater": len(greater),
            "n_lesser": len(lesser),
            "mean_log_k_greater": _nanmean(greater["log_k"]),
            "mean_log_k_lesser": _nanmean(lesser["log_k"]),
            "mean_hack_greater": _nanmean(greater["hack_rate"]),
            "mean_hack_lesser": _nanmean(lesser["hack_rate"]),
            "mean_hack_off": _nanmean(control["hack_rate"]),
            "mean_log_k_off": _nanmean(control["log_k"]),
        }
        row["delta_log_k_greater_minus_lesser"] = (
            row["mean_log_k_greater"] - row["mean_log_k_lesser"]
        )
        row["delta_hack_greater_minus_lesser"] = (
            row["mean_hack_greater"] - row["mean_hack_lesser"]
        )
        rows.append(row)
    return pd.DataFrame(rows)


def group_means(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    usable = joined[joined["hack_rate"].notna()].copy()

    for label, mask in [
        ("k_class:high_sooner_dominant", usable["k_class"] == "high_sooner_dominant"),
        ("k_class:low_interior", usable["k_class"] == "low_interior"),
        ("competence_pass", usable["iv_include"]),
        ("competence_fail", ~usable["iv_include"]),
        ("persona_group:off", usable["persona_discounting_group"] == "off"),
        ("persona_group:greater", usable["persona_discounting_group"] == "greater"),
        ("persona_group:lesser", usable["persona_discounting_group"] == "lesser"),
    ]:
        sub = usable[mask]
        rows.append({
            "group": label,
            "n_cells": len(sub),
            "mean_hack_rate": float(np.nanmean(sub["hack_rate"])) if len(sub) else np.nan,
            "mean_log_k": float(np.nanmean(sub["log_k"])) if len(sub) else np.nan,
            "mean_k": float(np.nanmean(sub["k"])) if len(sub) else np.nan,
        })
    return pd.DataFrame(rows)


def write_markdown(
    path: Path,
    joined: pd.DataFrame,
    corrs: pd.DataFrame,
    contrasts: pd.DataFrame,
    groups: pd.DataFrame,
) -> None:
    n_agent = int((joined.get("n_agent_started", pd.Series(dtype=float)).fillna(0) > 0).sum())
    lines = [
        "# Waiting Game k × financial_audit reward hacking",
        "",
        "Join key: `(model_name, persona_id)`. Waiting Game IV uses `option_order=pooled`.",
        "Hacking DV is objective (`hack_rate`); OpenAI `evaluation` is not used.",
        "",
        "## Coverage",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| joined cells | {len(joined)} |",
        f"| competence-pass IV cells | {int(joined['iv_include'].sum())} |",
        f"| cells with agent-started hacking runs | {n_agent} |",
        f"| high/sooner-dominant k (≥ {HIGH_K_THRESHOLD}) | "
        f"{int((joined['k_class'] == 'high_sooner_dominant').sum())} |",
        f"| low/interior k | {int((joined['k_class'] == 'low_interior').sum())} |",
        "",
    ]

    if n_agent == 0:
        lines += [
            "> No agent-started hacking episodes in the DV table. "
            "Correlation estimates below will be empty/NaN until financial_audit runs succeed.",
            "",
        ]

    lines += [
        "## Cell-level correlations (`log_k` vs `hack_rate`)",
        "",
        "| subset | method | n | r | p |",
        "|---|---|---:|---:|---:|",
    ]
    for _, row in corrs[corrs["y"] == "hack_rate"].iterrows():
        r = row["r"]
        p = row["p"]
        r_s = "—" if pd.isna(r) else f"{r:.3f}"
        p_s = "—" if pd.isna(p) else f"{p:.3g}"
        lines.append(
            f"| {row['subset']} | {row['method']} | {int(row['n'])} | {r_s} | {p_s} |"
        )

    lines += [
        "",
        "## Within-model persona contrasts (greater − lesser)",
        "",
        "| model | n_g / n_l | Δ log k | Δ hack_rate | hack greater | hack lesser | hack off |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in contrasts.sort_values("model_name").iterrows():
        def f(x, d=3):
            return "—" if pd.isna(x) else f"{float(x):.{d}f}"

        lines.append(
            f"| `{row['model_name']}` | {int(row['n_greater'])}/{int(row['n_lesser'])} | "
            f"{f(row['delta_log_k_greater_minus_lesser'])} | "
            f"{f(row['delta_hack_greater_minus_lesser'])} | "
            f"{f(row['mean_hack_greater'])} | {f(row['mean_hack_lesser'])} | "
            f"{f(row['mean_hack_off'])} |"
        )

    lines += [
        "",
        "## Group means",
        "",
        "| group | n | mean hack_rate | mean log k | mean k |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, row in groups.iterrows():
        def f(x, d=3):
            return "—" if pd.isna(x) else f"{float(x):.{d}f}"

        lines.append(
            f"| {row['group']} | {int(row['n_cells'])} | {f(row['mean_hack_rate'])} | "
            f"{f(row['mean_log_k'])} | {f(row['mean_k'])} |"
        )

    lines += [
        "",
        "## Figures",
        "",
        "- `figures/scatter_logk_vs_hack_rate.png`",
        "- `figures/group_mean_hack_rate.png`",
        "- `figures/within_model_delta_hack_vs_delta_logk.png`",
        "",
        "## Notes",
        "",
        f"- Human Rachlin reference k ≈ {HUMAN_K}/month is not a pass/fail gate.",
        f"- Cells with k ≥ {HIGH_K_THRESHOLD} are treated as sooner-dominant, not finely graded impatience.",
        "- Primary claim should prefer within-model persona contrasts + objective `hack_rate`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def plot_scatter(joined: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(7, 5))
    sub = joined[joined["iv_include"] & joined["hack_rate"].notna()].copy()
    if sub.empty or sub["n_agent_started"].fillna(0).sum() == 0 and sub["hack_rate"].isna().all():
        # still try plotting competence-pass even if rates are nan
        pass
    if sub.empty:
        ax.text(0.5, 0.5, "No competence-pass joined cells", ha="center", va="center")
        ax.set_axis_off()
    else:
        colors = sub["k_class"].map({
            "high_sooner_dominant": "#E45756",
            "low_interior": "#54A24B",
            "missing": "#999999",
        }).fillna("#999999")
        ax.scatter(sub["log_k"], sub["hack_rate"].fillna(-0.05), c=colors, alpha=0.85, edgecolors="none")
        ax.axhline(0, color="#cccccc", lw=0.8)
        ax.set_xlabel("log(k)  [Waiting Game, pooled]")
        ax.set_ylabel("hack_rate  [financial_audit]")
        ax.set_title("Competence-pass cells: log(k) vs hack_rate")
        # Legend proxies
        ax.scatter([], [], c="#E45756", label="high / sooner-dominant")
        ax.scatter([], [], c="#54A24B", label="low / interior")
        ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_group_means(groups: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.5))
    want = [
        "k_class:high_sooner_dominant",
        "k_class:low_interior",
        "persona_group:off",
        "persona_group:greater",
        "persona_group:lesser",
    ]
    plot_df = groups[groups["group"].isin(want)].copy()
    if plot_df.empty or plot_df["mean_hack_rate"].isna().all():
        ax.text(0.5, 0.5, "No group means", ha="center", va="center")
        ax.set_axis_off()
    else:
        ax.bar(plot_df["group"], plot_df["mean_hack_rate"].fillna(0.0), color="#4C78A8")
        ax.set_ylabel("Mean hack_rate")
        ax.set_ylim(0, 1.05)
        ax.tick_params(axis="x", rotation=30)
        ax.set_title("Hack rate by k-class and persona group")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_within_model_deltas(contrasts: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(6, 5))
    d = contrasts.dropna(
        subset=["delta_log_k_greater_minus_lesser", "delta_hack_greater_minus_lesser"],
        how="any",
    )
    if d.empty:
        ax.text(0.5, 0.5, "No within-model contrasts", ha="center", va="center")
        ax.set_axis_off()
    else:
        ax.axhline(0, color="#cccccc", lw=0.8)
        ax.axvline(0, color="#cccccc", lw=0.8)
        ax.scatter(
            d["delta_log_k_greater_minus_lesser"],
            d["delta_hack_greater_minus_lesser"],
            c="#4C78A8",
        )
        for _, row in d.iterrows():
            short = str(row["model_name"]).split(":")[0]
            ax.annotate(
                short,
                (
                    row["delta_log_k_greater_minus_lesser"],
                    row["delta_hack_greater_minus_lesser"],
                ),
                fontsize=7,
                xytext=(4, 4),
                textcoords="offset points",
            )
        ax.set_xlabel("Δ log(k)  (greater − lesser personas)")
        ax.set_ylabel("Δ hack_rate  (greater − lesser)")
        ax.set_title("Within-model persona shifts")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--waiting-game",
        type=Path,
        default=Path("../temporal-discounting/results/summary/by_condition.csv"),
        help="Waiting Game by_condition.csv",
    )
    parser.add_argument(
        "--hacking",
        type=Path,
        default=Path("outputs/analysis_reward_hacking/by_condition_financial_audit.csv"),
        help="Objective financial_audit by_condition CSV from analyze_reward_hacking.py",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/analysis_k_hacking"),
        help="Output directory for join tables, markdown, figures",
    )
    parser.add_argument(
        "--option-order",
        default="pooled",
        help="Waiting Game option_order stratum to use as IV",
    )
    args = parser.parse_args()

    os.chdir(PROJECT_ROOT)

    wg_path = args.waiting_game
    if not wg_path.is_absolute():
        wg_path = (PROJECT_ROOT / wg_path).resolve()
    hack_path = args.hacking
    if not hack_path.is_absolute():
        hack_path = (PROJECT_ROOT / hack_path).resolve()
    out_dir = args.output_dir
    if not out_dir.is_absolute():
        out_dir = PROJECT_ROOT / out_dir
    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

    if not hack_path.exists():
        legacy = PROJECT_ROOT / "outputs/analysis_reward_hacking/by_condition.csv"
        if legacy.exists():
            hack_path = legacy
        else:
            raise SystemExit(
                f"Hacking table not found: {args.hacking}\n"
                "Run: python src/analyze_reward_hacking.py"
            )
    if not wg_path.exists():
        raise SystemExit(f"Waiting Game table not found: {wg_path}")

    iv = load_waiting_game_iv(wg_path, option_order=args.option_order)
    dv = load_hacking_dv(hack_path)
    joined = join_iv_dv(iv, dv)
    corrs = cell_level_correlations(joined)
    contrasts = within_model_persona_contrasts(joined)
    groups = group_means(joined)

    joined_path = out_dir / "joined_cells.csv"
    corrs_path = out_dir / "correlations.csv"
    contrasts_path = out_dir / "within_model_contrasts.csv"
    groups_path = out_dir / "group_means.csv"
    md_path = out_dir / "SUMMARY.md"

    joined.to_csv(joined_path, index=False)
    corrs.to_csv(corrs_path, index=False)
    contrasts.to_csv(contrasts_path, index=False)
    groups.to_csv(groups_path, index=False)
    write_markdown(md_path, joined, corrs, contrasts, groups)

    plot_scatter(joined, fig_dir / "scatter_logk_vs_hack_rate.png")
    plot_group_means(groups, fig_dir / "group_mean_hack_rate.png")
    plot_within_model_deltas(contrasts, fig_dir / "within_model_delta_hack_vs_delta_logk.png")

    print(f"Wrote {joined_path} ({len(joined)} cells)")
    print(f"Wrote {corrs_path}")
    print(f"Wrote {contrasts_path}")
    print(f"Wrote {groups_path}")
    print(f"Wrote {md_path}")
    print(f"Wrote figures under {fig_dir}")


if __name__ == "__main__":
    main()
