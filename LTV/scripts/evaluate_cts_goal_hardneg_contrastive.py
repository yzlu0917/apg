#!/usr/bin/env python3
import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_cts_mini import extract_pair_features, index_raw_rows
from extract_boundary_states_smoke import encode_last_token_states, load_jsonl, resolve_layers
from evaluate_cts_scoring_audit import normalize_train_test


def flatten_state_dict(state_dict: Dict[str, torch.Tensor]) -> torch.Tensor:
    layer_items = sorted(state_dict.items(), key=lambda kv: int(kv[0]))
    return torch.cat([tensor.to(torch.float32) for _, tensor in layer_items], dim=0)


def flatten_field(entry: Dict, field: str) -> torch.Tensor:
    return flatten_state_dict(entry[field])


def aggregate_metrics(rows: List[Dict], baselines: List[str]) -> Dict[str, Dict]:
    metrics = {}
    for baseline in baselines:
        same_gaps = [
            abs(row["source_scores"][baseline] - row["variant_scores"][baseline])
            for row in rows
            if row["type"] == "same_semantics"
        ]
        flip_diffs = [
            row["source_scores"][baseline] - row["variant_scores"][baseline]
            for row in rows
            if row["type"] == "semantic_flip"
        ]
        metrics[baseline] = {
            "num_same_pairs": len(same_gaps),
            "num_flip_pairs": len(flip_diffs),
            "invariance_gap": None if not same_gaps else float(sum(same_gaps) / len(same_gaps)),
            "semantic_sensitivity": None if not flip_diffs else float(sum(flip_diffs) / len(flip_diffs)),
        }
    return metrics


def combine_with_goal(x: torch.Tensor, goal: torch.Tensor) -> torch.Tensor:
    return torch.cat([x, goal, x * goal], dim=1)


def fit_goal_hardneg_contrastive_scorer(
    train_source: torch.Tensor,
    train_variant: torch.Tensor,
    train_goal: torch.Tensor,
    train_types: List[str],
    test_source: torch.Tensor,
    test_variant: torch.Tensor,
    test_goal: torch.Tensor,
    embed_dim: int = 64,
    margin: float = 1.0,
    epochs: int = 200,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    hardneg_weight: float = 1.0,
) -> Tuple[torch.Tensor, torch.Tensor]:
    train_source_combined = combine_with_goal(train_source, train_goal)
    train_variant_combined = combine_with_goal(train_variant, train_goal)
    test_source_combined = combine_with_goal(test_source, test_goal)
    test_variant_combined = combine_with_goal(test_variant, test_goal)

    train_joint = torch.cat([train_source_combined, train_variant_combined], dim=0)
    test_joint = torch.cat([test_source_combined, test_variant_combined], dim=0)
    train_joint, test_joint = normalize_train_test(train_joint, test_joint)
    train_source = train_joint[: len(train_source_combined)]
    train_variant = train_joint[len(train_source_combined) :]
    test_source = test_joint[: len(test_source_combined)]
    test_variant = test_joint[len(test_source_combined) :]

    if len(train_source) == 0:
        return torch.zeros(len(test_source), dtype=torch.float32), torch.zeros(len(test_variant), dtype=torch.float32)

    class Encoder(torch.nn.Module):
        def __init__(self, input_dim: int, output_dim: int) -> None:
            super().__init__()
            self.net = torch.nn.Sequential(
                torch.nn.Linear(input_dim, 128),
                torch.nn.ReLU(),
                torch.nn.Linear(128, output_dim),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            z = self.net(x)
            return torch.nn.functional.normalize(z, dim=1)

    encoder = Encoder(train_source.shape[1], embed_dim)
    optimizer = torch.optim.AdamW(encoder.parameters(), lr=lr, weight_decay=weight_decay)

    same_mask = torch.tensor([t == "same_semantics" for t in train_types], dtype=torch.bool)
    flip_mask = ~same_mask

    for _ in range(epochs):
        optimizer.zero_grad()
        src_z = encoder(train_source)
        var_z = encoder(train_variant)
        distances = torch.norm(src_z - var_z, dim=1)

        loss_terms = []
        if int(same_mask.sum().item()) > 0:
            loss_terms.append(torch.mean(distances[same_mask] ** 2))
        if int(flip_mask.sum().item()) > 0:
            loss_terms.append(torch.mean(torch.nn.functional.softplus(margin - distances[flip_mask])))

        if int(same_mask.sum().item()) > 0 and int(flip_mask.sum().item()) > 0:
            same_src = src_z[same_mask]
            same_var = var_z[same_mask]
            neg_pool = var_z[flip_mask]
            pos_dist = torch.norm(same_src - same_var, dim=1)
            hard_neg_dist = torch.cdist(same_src, neg_pool).min(dim=1).values
            triplet_like = torch.nn.functional.softplus(pos_dist + margin - hard_neg_dist)
            loss_terms.append(hardneg_weight * torch.mean(triplet_like))

        loss = sum(loss_terms)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        src_z = encoder(train_source)
        var_z = encoder(train_variant)

        item_embeds = [src_z]
        item_labels = [torch.ones(len(src_z), dtype=torch.long)]

        same_variant = var_z[same_mask]
        if len(same_variant) > 0:
            item_embeds.append(same_variant)
            item_labels.append(torch.ones(len(same_variant), dtype=torch.long))

        flip_variant = var_z[flip_mask]
        if len(flip_variant) > 0:
            item_embeds.append(flip_variant)
            item_labels.append(torch.zeros(len(flip_variant), dtype=torch.long))

        item_embeds = torch.cat(item_embeds, dim=0)
        item_labels = torch.cat(item_labels, dim=0)

        pos_centroid = item_embeds[item_labels == 1].mean(dim=0, keepdim=True)
        neg_centroid = item_embeds[item_labels == 0].mean(dim=0, keepdim=True)

        def score_items(x: torch.Tensor) -> torch.Tensor:
            z = encoder(x)
            pos_dist = torch.norm(z - pos_centroid, dim=1)
            neg_dist = torch.norm(z - neg_centroid, dim=1)
            return torch.sigmoid(neg_dist - pos_dist).cpu()

        return score_items(test_source), score_items(test_variant)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate CTS with goal-conditioned hard-negative contrastive scorers.")
    parser.add_argument("--raw-jsonl", required=True)
    parser.add_argument("--cts-seed", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--hardneg-weight", type=float, default=1.0)
    parser.add_argument("--baseline-prefix", default="goalhardneg")
    parser.add_argument("--epochs", type=int, default=200)
    args = parser.parse_args()

    raw_rows = load_jsonl(Path(args.raw_jsonl))
    cts_rows = load_jsonl(Path(args.cts_seed))
    raw_index = index_raw_rows(raw_rows)

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    model.to(args.device)
    model.eval()

    requested_layers = [int(x) for x in args.layers.split(",") if x]
    resolved_layers = resolve_layers(requested_layers, int(model.config.num_hidden_layers))

    goal_cache = {}
    for row in raw_rows:
        goal_cache[row["theorem_id"]] = flatten_state_dict(
            encode_last_token_states(model, tokenizer, row["header"], resolved_layers, args.device)["states"]
        )

    extracted_pairs = []
    for row in cts_rows:
        theorem_id = row["source_theorem_id"]
        raw_row = raw_index[theorem_id]
        pair_features = extract_pair_features(
            model=model,
            tokenizer=tokenizer,
            row=raw_row,
            step_index=row["source_step_index"],
            variant_step=row["variant_step"],
            resolved_layers=resolved_layers,
            device=args.device,
        )
        extracted_pairs.append(
            {
                "pair_id": row["pair_id"],
                "type": row["type"],
                "source_theorem_id": theorem_id,
                "source_step_index": row["source_step_index"],
                "expected_label_change": row["expected_label_change"],
                "goal_vec": goal_cache[theorem_id],
                "source": pair_features["source"],
                "variant": pair_features["variant"],
            }
        )

    group_to_indices = defaultdict(list)
    for idx, row in enumerate(extracted_pairs):
        group_to_indices[row["source_theorem_id"]].append(idx)

    prefix = args.baseline_prefix.strip()
    if prefix:
        prefix = f"{prefix}_"
    baselines = [f"{prefix}post_contrastive", f"{prefix}transition_contrastive"]
    source_scores = {name: torch.zeros(len(extracted_pairs), dtype=torch.float32) for name in baselines}
    variant_scores = {name: torch.zeros(len(extracted_pairs), dtype=torch.float32) for name in baselines}

    for theorem_id, test_indices in group_to_indices.items():
        train_indices = [i for i, row in enumerate(extracted_pairs) if row["source_theorem_id"] != theorem_id]
        train_types = [extracted_pairs[i]["type"] for i in train_indices]

        for field, baseline_name in [("h_plus", "post_contrastive"), ("delta_h", "transition_contrastive")]:
            if prefix:
                baseline_name = f"{prefix}{baseline_name}"
            train_source = torch.stack([flatten_field(extracted_pairs[i]["source"], field) for i in train_indices], dim=0)
            train_variant = torch.stack([flatten_field(extracted_pairs[i]["variant"], field) for i in train_indices], dim=0)
            train_goal = torch.stack([extracted_pairs[i]["goal_vec"] for i in train_indices], dim=0)
            test_source = torch.stack([flatten_field(extracted_pairs[i]["source"], field) for i in test_indices], dim=0)
            test_variant = torch.stack([flatten_field(extracted_pairs[i]["variant"], field) for i in test_indices], dim=0)
            test_goal = torch.stack([extracted_pairs[i]["goal_vec"] for i in test_indices], dim=0)

            torch.manual_seed(0)
            src, var = fit_goal_hardneg_contrastive_scorer(
                train_source=train_source,
                train_variant=train_variant,
                train_goal=train_goal,
                train_types=train_types,
                test_source=test_source,
                test_variant=test_variant,
                test_goal=test_goal,
                epochs=args.epochs,
                hardneg_weight=args.hardneg_weight,
            )
            source_scores[baseline_name][test_indices] = src
            variant_scores[baseline_name][test_indices] = var

    results = []
    for idx, row in enumerate(extracted_pairs):
        results.append(
            {
                "pair_id": row["pair_id"],
                "type": row["type"],
                "source_theorem_id": row["source_theorem_id"],
                "source_step_index": row["source_step_index"],
                "expected_label_change": row["expected_label_change"],
                "source_scores": {name: float(source_scores[name][idx].item()) for name in baselines},
                "variant_scores": {name: float(variant_scores[name][idx].item()) for name in baselines},
            }
        )

    output = {
        "raw_jsonl": args.raw_jsonl,
        "cts_seed": args.cts_seed,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "hardneg_weight": args.hardneg_weight,
        "epochs": args.epochs,
        "baseline_prefix": args.baseline_prefix,
        "goal_conditioning": "header_last_token_states_concat_and_interaction",
        "metrics": aggregate_metrics(results, baselines),
        "pairs": results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
