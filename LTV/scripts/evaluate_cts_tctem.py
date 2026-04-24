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


def flatten_entry_all(entry: Dict) -> torch.Tensor:
    return torch.cat(
        [
            flatten_state_dict(entry['h_minus']),
            flatten_state_dict(entry['h_plus']),
            flatten_state_dict(entry['delta_h']),
        ],
        dim=0,
    )


def aggregate_metrics(rows: List[Dict], baselines: List[str]) -> Dict[str, Dict]:
    metrics = {}
    for baseline in baselines:
        same_gaps = [
            abs(row['source_scores'][baseline] - row['variant_scores'][baseline])
            for row in rows
            if row['type'] == 'same_semantics'
        ]
        flip_diffs = [
            row['source_scores'][baseline] - row['variant_scores'][baseline]
            for row in rows
            if row['type'] == 'semantic_flip'
        ]
        metrics[baseline] = {
            'num_same_pairs': len(same_gaps),
            'num_flip_pairs': len(flip_diffs),
            'invariance_gap': None if not same_gaps else float(sum(same_gaps) / len(same_gaps)),
            'semantic_sensitivity': None if not flip_diffs else float(sum(flip_diffs) / len(flip_diffs)),
        }
    return metrics


def combine_with_goal(x: torch.Tensor, goal: torch.Tensor) -> torch.Tensor:
    if goal.shape[1] == x.shape[1]:
        goal_tiled = goal
    else:
        repeat_factor = (x.shape[1] + goal.shape[1] - 1) // goal.shape[1]
        goal_tiled = goal.repeat(1, repeat_factor)[:, : x.shape[1]]
    return torch.cat([x, goal_tiled, x * goal_tiled], dim=1)


class TCTEM(torch.nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 256, embed_dim: int = 64) -> None:
        super().__init__()
        self.backbone = torch.nn.Sequential(
            torch.nn.Linear(input_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, hidden_dim),
            torch.nn.ReLU(),
        )
        self.embed_head = torch.nn.Linear(hidden_dim, embed_dim)
        self.logit_head = torch.nn.Linear(hidden_dim, 1)

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        h = self.backbone(x)
        z = torch.nn.functional.normalize(self.embed_head(h), dim=1)
        logits = self.logit_head(h).squeeze(-1)
        return z, logits


def fit_tctem_scorer(
    train_source: torch.Tensor,
    train_variant: torch.Tensor,
    train_goal: torch.Tensor,
    train_types: List[str],
    test_source: torch.Tensor,
    test_variant: torch.Tensor,
    test_goal: torch.Tensor,
    same_weight: float = 1.0,
    flip_weight: float = 1.0,
    hardneg_weight: float = 1.0,
    calibration_weight: float = 0.5,
    margin: float = 1.0,
    epochs: int = 300,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
) -> Tuple[torch.Tensor, torch.Tensor]:
    train_source = combine_with_goal(train_source, train_goal)
    train_variant = combine_with_goal(train_variant, train_goal)
    test_source = combine_with_goal(test_source, test_goal)
    test_variant = combine_with_goal(test_variant, test_goal)

    train_joint = torch.cat([train_source, train_variant], dim=0)
    test_joint = torch.cat([test_source, test_variant], dim=0)
    train_joint, test_joint = normalize_train_test(train_joint, test_joint)
    train_source = train_joint[: len(train_source)]
    train_variant = train_joint[len(train_source):]
    test_source = test_joint[: len(test_source)]
    test_variant = test_joint[len(test_source):]

    if len(train_source) == 0:
        return torch.zeros(len(test_source), dtype=torch.float32), torch.zeros(len(test_variant), dtype=torch.float32)

    model = TCTEM(train_source.shape[1])
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)

    same_mask = torch.tensor([t == 'same_semantics' for t in train_types], dtype=torch.bool)
    flip_mask = ~same_mask

    for _ in range(epochs):
        optimizer.zero_grad()
        src_z, src_logits = model(train_source)
        var_z, var_logits = model(train_variant)

        item_logits = [src_logits]
        item_labels = [torch.ones(len(src_logits), dtype=torch.float32)]
        if int(same_mask.sum().item()) > 0:
            item_logits.append(var_logits[same_mask])
            item_labels.append(torch.ones(int(same_mask.sum().item()), dtype=torch.float32))
        if int(flip_mask.sum().item()) > 0:
            item_logits.append(var_logits[flip_mask])
            item_labels.append(torch.zeros(int(flip_mask.sum().item()), dtype=torch.float32))
        item_logits = torch.cat(item_logits, dim=0)
        item_labels = torch.cat(item_labels, dim=0)

        local_loss = torch.nn.functional.binary_cross_entropy_with_logits(item_logits, item_labels)
        calib_loss = torch.mean((torch.sigmoid(item_logits) - item_labels) ** 2)

        loss_terms = [local_loss, calibration_weight * calib_loss]

        if int(same_mask.sum().item()) > 0:
            same_src_z = src_z[same_mask]
            same_var_z = var_z[same_mask]
            same_src_logits = src_logits[same_mask]
            same_var_logits = var_logits[same_mask]
            embed_same = torch.mean(torch.norm(same_src_z - same_var_z, dim=1) ** 2)
            score_same = torch.mean((torch.sigmoid(same_src_logits) - torch.sigmoid(same_var_logits)) ** 2)
            loss_terms.append(same_weight * (embed_same + score_same))

        if int(flip_mask.sum().item()) > 0:
            flip_src_logits = src_logits[flip_mask]
            flip_var_logits = var_logits[flip_mask]
            flip_margin = torch.mean(torch.nn.functional.softplus(margin - (flip_src_logits - flip_var_logits)))
            loss_terms.append(flip_weight * flip_margin)

        if int(same_mask.sum().item()) > 0 and int(flip_mask.sum().item()) > 0:
            same_src_z = src_z[same_mask]
            same_var_z = var_z[same_mask]
            neg_pool = var_z[flip_mask]
            pos_dist = torch.norm(same_src_z - same_var_z, dim=1)
            hard_neg_dist = torch.cdist(same_src_z, neg_pool).min(dim=1).values
            hardneg = torch.mean(torch.nn.functional.softplus(pos_dist + margin - hard_neg_dist))
            loss_terms.append(hardneg_weight * hardneg)

        loss = sum(loss_terms)
        loss.backward()
        optimizer.step()

    with torch.no_grad():
        _, src_test_logits = model(test_source)
        _, var_test_logits = model(test_variant)
        return torch.sigmoid(src_test_logits).cpu(), torch.sigmoid(var_test_logits).cpu()


def main() -> None:
    parser = argparse.ArgumentParser(description='Evaluate CTS with a minimal TC-TEM scorer.')
    parser.add_argument('--raw-jsonl', required=True)
    parser.add_argument('--cts-seed', required=True)
    parser.add_argument('--model-path', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--layers', default='-1,-8,-16')
    parser.add_argument('--device', default='cuda:0')
    parser.add_argument('--same-weight', type=float, default=1.0)
    parser.add_argument('--flip-weight', type=float, default=1.0)
    parser.add_argument('--hardneg-weight', type=float, default=1.0)
    parser.add_argument('--calibration-weight', type=float, default=0.5)
    parser.add_argument('--epochs', type=int, default=300)
    parser.add_argument('--baseline-prefix', default='tctem')
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

    requested_layers = [int(x) for x in args.layers.split(',') if x]
    resolved_layers = resolve_layers(requested_layers, int(model.config.num_hidden_layers))

    goal_cache = {}
    for row in raw_rows:
        goal_cache[row['theorem_id']] = flatten_state_dict(
            encode_last_token_states(model, tokenizer, row['header'], resolved_layers, args.device)['states']
        )

    extracted_pairs = []
    for row in cts_rows:
        theorem_id = row['source_theorem_id']
        raw_row = raw_index[theorem_id]
        pair_features = extract_pair_features(
            model=model,
            tokenizer=tokenizer,
            row=raw_row,
            step_index=row['source_step_index'],
            variant_step=row['variant_step'],
            resolved_layers=resolved_layers,
            device=args.device,
        )
        extracted_pairs.append(
            {
                'pair_id': row['pair_id'],
                'type': row['type'],
                'source_theorem_id': theorem_id,
                'source_step_index': row['source_step_index'],
                'expected_label_change': row['expected_label_change'],
                'goal_vec': goal_cache[theorem_id],
                'source': pair_features['source'],
                'variant': pair_features['variant'],
            }
        )

    group_to_indices = defaultdict(list)
    for idx, row in enumerate(extracted_pairs):
        group_to_indices[row['source_theorem_id']].append(idx)

    prefix = args.baseline_prefix.strip()
    if prefix:
        prefix = f'{prefix}_'
    baselines = [f'{prefix}energy']
    source_scores = {name: torch.zeros(len(extracted_pairs), dtype=torch.float32) for name in baselines}
    variant_scores = {name: torch.zeros(len(extracted_pairs), dtype=torch.float32) for name in baselines}

    for theorem_id, test_indices in group_to_indices.items():
        train_indices = [i for i, row in enumerate(extracted_pairs) if row['source_theorem_id'] != theorem_id]
        train_types = [extracted_pairs[i]['type'] for i in train_indices]

        train_source = torch.stack([flatten_entry_all(extracted_pairs[i]['source']) for i in train_indices], dim=0)
        train_variant = torch.stack([flatten_entry_all(extracted_pairs[i]['variant']) for i in train_indices], dim=0)
        train_goal = torch.stack([extracted_pairs[i]['goal_vec'] for i in train_indices], dim=0)
        test_source = torch.stack([flatten_entry_all(extracted_pairs[i]['source']) for i in test_indices], dim=0)
        test_variant = torch.stack([flatten_entry_all(extracted_pairs[i]['variant']) for i in test_indices], dim=0)
        test_goal = torch.stack([extracted_pairs[i]['goal_vec'] for i in test_indices], dim=0)

        torch.manual_seed(0)
        src, var = fit_tctem_scorer(
            train_source=train_source,
            train_variant=train_variant,
            train_goal=train_goal,
            train_types=train_types,
            test_source=test_source,
            test_variant=test_variant,
            test_goal=test_goal,
            same_weight=args.same_weight,
            flip_weight=args.flip_weight,
            hardneg_weight=args.hardneg_weight,
            calibration_weight=args.calibration_weight,
            epochs=args.epochs,
        )
        source_scores[baselines[0]][test_indices] = src
        variant_scores[baselines[0]][test_indices] = var

    results = []
    for idx, row in enumerate(extracted_pairs):
        results.append(
            {
                'pair_id': row['pair_id'],
                'type': row['type'],
                'source_theorem_id': row['source_theorem_id'],
                'source_step_index': row['source_step_index'],
                'expected_label_change': row['expected_label_change'],
                'source_scores': {name: float(source_scores[name][idx].item()) for name in baselines},
                'variant_scores': {name: float(variant_scores[name][idx].item()) for name in baselines},
            }
        )

    output = {
        'raw_jsonl': args.raw_jsonl,
        'cts_seed': args.cts_seed,
        'model_path': args.model_path,
        'resolved_layers': resolved_layers,
        'same_weight': args.same_weight,
        'flip_weight': args.flip_weight,
        'hardneg_weight': args.hardneg_weight,
        'calibration_weight': args.calibration_weight,
        'epochs': args.epochs,
        'baseline_prefix': args.baseline_prefix,
        'metrics': aggregate_metrics(results, baselines),
        'pairs': results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
