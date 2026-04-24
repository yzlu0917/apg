#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]

ACTION_COLORS = {
    "continue": "#1f77b4",
    "revise_1": "#ff7f0e",
    "abstain": "#2ca02c",
}

ACTION_MARKERS = {
    "continue": "o",
    "revise_1": "s",
    "abstain": "D",
}

BASELINE_COLORS = {
    "ordered_scalar_mu": "#6f4e7c",
    "learned_1d_linear": "#e17c05",
    "direct_policy": "#1f77b4",
    "factorized_exact_state": "#2ca02c",
    "factorized_predicted_state_selected": "#d62728",
}

BASELINE_LABELS = {
    "ordered_scalar_mu": "Ordered scalar",
    "learned_1d_linear": "Learned-1D",
    "direct_policy": "Direct policy",
    "factorized_exact_state": "TriVer exact-state",
    "factorized_predicted_state_selected": "TriVer predicted-state",
}


def read_json(path: Path) -> dict:
    with path.open() as f:
        return json.load(f)


def render_benchmark(output_dir: Path) -> None:
    sources = [
        (
            "Linear equations",
            ROOT / "outputs/week2_linear_8b_data_v2/prefix_oracle_records.csv",
            ROOT / "outputs/week2_linear_8b_data_v2/summary.json",
        ),
        (
            "Arithmetic",
            ROOT / "outputs/week2_arithmetic_8b_data_v2/prefix_oracle_records.csv",
            ROOT / "outputs/week2_arithmetic_8b_data_v2/summary.json",
        ),
    ]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.7), sharex=True, sharey=True)

    for ax, (title, csv_path, summary_path) in zip(axes, sources):
        df = pd.read_csv(csv_path)
        summary = read_json(summary_path)
        for action, group in df.groupby("oracle_action"):
            ax.scatter(
                group["mu_continue"],
                group["q_t"],
                s=42,
                alpha=0.85,
                c=ACTION_COLORS.get(action, "#333333"),
                marker=ACTION_MARKERS.get(action, "o"),
                label=action,
                edgecolors="white",
                linewidths=0.4,
            )

        ax.set_title(title)
        ax.set_xlabel(r"$\mu_{\mathrm{continue}}$")
        ax.set_ylabel(r"$q_t$")
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.05, 1.05)
        ax.text(
            0.03,
            0.97,
            (
                f"determinacy={summary['oracle_determinacy_rate']:.3f}\n"
                f"crossing={summary['crossing_mass_all']:.3f}\n"
                f"high-det={summary['crossing_mass_high_determinacy']:.3f}"
            ),
            transform=ax.transAxes,
            va="top",
            ha="left",
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.25", "fc": "white", "ec": "#bbbbbb", "alpha": 0.9},
        )

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.03), ncol=3, frameon=False)
    fig.suptitle("Oracle action atlas on exact-checker domains", y=1.08, fontsize=12)
    fig.tight_layout()

    fig.savefig(output_dir / "benchmark_atlas.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "benchmark_atlas.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def render_deployment_gap(output_dir: Path) -> None:
    df = pd.read_csv(ROOT / "outputs/week2_factorized_state_id_diagnostics.csv")
    df = df[df["embedding_pooling"] == "last_generation_prompt"].copy()

    domains = [
        ("linear_equations", "Linear equations"),
        ("arithmetic", "Arithmetic"),
    ]
    baseline_order = [
        "factorized_exact_state",
        "factorized_predicted_state_exact_value",
        "factorized_predicted_state",
    ]
    pretty = {
        "factorized_exact_state": "Exact state",
        "factorized_predicted_state_exact_value": "Pred. state + exact value",
        "factorized_predicted_state": "Pred. state",
    }
    colors = {
        "factorized_exact_state": "#2ca02c",
        "factorized_predicted_state_exact_value": "#ffbf00",
        "factorized_predicted_state": "#d62728",
    }

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.8), sharey=True)

    for ax, (domain_key, title) in zip(axes, domains):
        sub = df[df["env"] == domain_key].set_index("baseline")
        values = [float(sub.loc[b, "mean_action_regret"]) for b in baseline_order]
        bars = ax.bar(
            range(len(values)),
            values,
            color=[colors[b] for b in baseline_order],
            edgecolor="white",
            linewidth=0.6,
        )
        ax.set_title(title)
        ax.set_xticks(range(len(values)))
        ax.set_xticklabels([pretty[b] for b in baseline_order], rotation=15, ha="right")
        ax.set_ylabel("Mean action regret")
        for bar, value in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, value + 0.01, f"{value:.3f}", ha="center", va="bottom", fontsize=9)

    fig.suptitle("Deployment gap decomposition", y=1.03, fontsize=12)
    fig.tight_layout()
    fig.savefig(output_dir / "deployment_gap.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "deployment_gap.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def render_budget(output_dir: Path) -> None:
    regret = pd.read_csv(ROOT / "outputs/week2_budget_axis_v1/action_regret_at_budget_by_domain.csv")
    frontier = pd.read_csv(ROOT / "outputs/week2_budget_axis_v1/equal_token_frontier_by_domain.csv")

    domains = [("arithmetic", "Arithmetic"), ("linear", "Linear equations")]
    baseline_order = [
        "ordered_scalar_mu",
        "learned_1d_linear",
        "direct_policy",
        "factorized_exact_state",
        "factorized_predicted_state_selected",
    ]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(10.0, 6.6), sharex="col")

    for col, (domain_key, title) in enumerate(domains):
        ax_regret = axes[0, col]
        ax_frontier = axes[1, col]

        sub_regret = regret[regret["domain_tag"] == domain_key]
        sub_frontier = frontier[frontier["domain_tag"] == domain_key]

        for baseline in baseline_order:
            rg = sub_regret[sub_regret["baseline"] == baseline].sort_values("budget_tokens")
            fr = sub_frontier[sub_frontier["baseline"] == baseline].sort_values("budget_tokens")
            if rg.empty or fr.empty:
                continue
            color = BASELINE_COLORS[baseline]
            label = BASELINE_LABELS[baseline]
            ax_regret.plot(rg["budget_tokens"], rg["mean_action_regret"], marker="o", ms=3.5, lw=1.8, color=color, label=label)
            ax_frontier.plot(fr["budget_tokens"], fr["oracle_action_accuracy"], marker="o", ms=3.5, lw=1.8, color=color, label=label)

        ax_regret.set_title(title)
        ax_regret.set_ylabel("Action regret")
        ax_frontier.set_ylabel("Oracle action accuracy")
        ax_frontier.set_xlabel("Budget tokens")

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 1.02), ncol=3, frameon=False)
    fig.suptitle("Budgeted decision quality", y=1.06, fontsize=12)
    fig.tight_layout()
    fig.savefig(output_dir / "budget_quality.pdf", bbox_inches="tight")
    fig.savefig(output_dir / "budget_quality.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="paper/figures", help="Output directory for rendered paper figures")
    args = parser.parse_args()

    output_dir = (ROOT / args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    render_benchmark(output_dir)
    render_deployment_gap(output_dir)
    render_budget(output_dir)

    print(f"Rendered paper figures to {output_dir}")


if __name__ == "__main__":
    main()
