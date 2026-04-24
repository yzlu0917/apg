#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from evaluate_cts_mini import build_training_tensors, extract_pair_features, index_raw_rows
from evaluate_cts_scoring_audit import normalize_train_test, aggregate_metrics
from extract_boundary_states_smoke import load_jsonl, resolve_layers
from run_object_gate_baselines import tensor_from_entries


def knn_local_density_scores(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
    k: int = 5,
    gamma: float = 1.0,
) -> Tuple[torch.Tensor, torch.Tensor]:
    x_train, x_test = normalize_train_test(x_train, x_test)

    pos = x_train[y_train == 1]
    neg = x_train[y_train == 0]
    if len(pos) == 0 or len(neg) == 0:
        zeros = torch.zeros(len(x_test), dtype=torch.float32)
        return zeros, zeros

    k_pos = min(k, len(pos))
    k_neg = min(k, len(neg))

    pos_dist = torch.cdist(x_test, pos)
    neg_dist = torch.cdist(x_test, neg)

    pos_knn = pos_dist.topk(k_pos, largest=False).values
    neg_knn = neg_dist.topk(k_neg, largest=False).values

    pos_density = torch.exp(-gamma * pos_knn.pow(2)).mean(dim=1)
    neg_density = torch.exp(-gamma * neg_knn.pow(2)).mean(dim=1)
    margin = torch.log(pos_density + 1e-8) - torch.log(neg_density + 1e-8)

    train_pos_dist = torch.cdist(pos, pos)
    train_neg_dist = torch.cdist(neg, neg)
    pos_ref = train_pos_dist.topk(min(k_pos + 1, train_pos_dist.shape[1]), largest=False).values[:, 1:]
    neg_ref = train_neg_dist.topk(min(k_neg + 1, train_neg_dist.shape[1]), largest=False).values[:, 1:]
    ref_scale = torch.cat([pos_ref.reshape(-1), neg_ref.reshape(-1)], dim=0).std().item()
    ref_scale = 1.0 if ref_scale < 1e-6 else ref_scale
    probs = torch.sigmoid(margin / ref_scale)
    return probs.cpu(), margin.cpu()


def knn_local_cosine_scores(
    x_train: torch.Tensor,
    y_train: torch.Tensor,
    x_test: torch.Tensor,
    k: int = 5,
) -> Tuple[torch.Tensor, torch.Tensor]:
    x_train, x_test = normalize_train_test(x_train, x_test)

    pos = x_train[y_train == 1]
    neg = x_train[y_train == 0]
    if len(pos) == 0 or len(neg) == 0:
        zeros = torch.zeros(len(x_test), dtype=torch.float32)
        return zeros, zeros

    pos = torch.nn.functional.normalize(pos, dim=1)
    neg = torch.nn.functional.normalize(neg, dim=1)
    test = torch.nn.functional.normalize(x_test, dim=1)

    k_pos = min(k, len(pos))
    k_neg = min(k, len(neg))

    pos_sim = torch.matmul(test, pos.t())
    neg_sim = torch.matmul(test, neg.t())

    pos_topk = pos_sim.topk(k_pos, largest=True).values
    neg_topk = neg_sim.topk(k_neg, largest=True).values

    margin = pos_topk.mean(dim=1) - neg_topk.mean(dim=1)

    ref_scale = torch.cat([pos_topk.reshape(-1), neg_topk.reshape(-1)], dim=0).std().item()
    ref_scale = 1.0 if ref_scale < 1e-6 else ref_scale
    probs = torch.sigmoid(margin / ref_scale)
    return probs.cpu(), margin.cpu()


def score_representation(
    train_entries: List[Dict],
    train_labels: torch.Tensor,
    pair_features: Dict[str, Dict],
    field: str,
    k: int,
    gamma: float,
) -> Dict[str, Tuple[float, float]]:
    train_x = tensor_from_entries(train_entries, field)
    test_x = tensor_from_entries(
        [
            {field: pair_features['source'][field]},
            {field: pair_features['variant'][field]},
        ],
        field,
    )
    rbf_probs, rbf_margins = knn_local_density_scores(train_x, train_labels, test_x, k=k, gamma=gamma)
    cosine_probs, cosine_margins = knn_local_cosine_scores(train_x, train_labels, test_x, k=k)
    return {
        'knn_local_prob': (float(rbf_probs[0].item()), float(rbf_probs[1].item())),
        'knn_local_margin': (float(rbf_margins[0].item()), float(rbf_margins[1].item())),
        'knn_local_cosine_prob': (float(cosine_probs[0].item()), float(cosine_probs[1].item())),
        'knn_local_cosine_margin': (float(cosine_margins[0].item()), float(cosine_margins[1].item())),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description='Evaluate CTS with local neighborhood scorers.')
    parser.add_argument('--train-features', required=True)
    parser.add_argument('--raw-jsonl', required=True)
    parser.add_argument('--cts-seed', required=True)
    parser.add_argument('--model-path', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--layers', default='-1,-8,-16')
    parser.add_argument('--device', default='cuda:0')
    parser.add_argument('--k', type=int, default=5)
    parser.add_argument('--gamma', type=float, default=1.0)
    args = parser.parse_args()

    feature_entries = torch.load(args.train_features)
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

    baseline_names = [
        'post_knn_local_prob',
        'post_knn_local_margin',
        'post_knn_local_cosine_prob',
        'post_knn_local_cosine_margin',
        'transition_knn_local_prob',
        'transition_knn_local_margin',
        'transition_knn_local_cosine_prob',
        'transition_knn_local_cosine_margin',
    ]

    results = []
    for row in cts_rows:
        theorem_id = row['source_theorem_id']
        raw_row = raw_index[theorem_id]
        train_entries, train_labels, _, _ = build_training_tensors(feature_entries, theorem_id)
        pair_features = extract_pair_features(
            model=model,
            tokenizer=tokenizer,
            row=raw_row,
            step_index=row['source_step_index'],
            variant_step=row['variant_step'],
            resolved_layers=resolved_layers,
            device=args.device,
        )

        post_scores = score_representation(train_entries, train_labels, pair_features, 'h_plus', args.k, args.gamma)
        transition_scores = score_representation(train_entries, train_labels, pair_features, 'delta_h', args.k, args.gamma)

        source_scores = {}
        variant_scores = {}
        for scorer_name, (s, v) in post_scores.items():
            source_scores[f'post_{scorer_name}'] = s
            variant_scores[f'post_{scorer_name}'] = v
        for scorer_name, (s, v) in transition_scores.items():
            source_scores[f'transition_{scorer_name}'] = s
            variant_scores[f'transition_{scorer_name}'] = v

        results.append(
            {
                'pair_id': row['pair_id'],
                'type': row['type'],
                'source_theorem_id': theorem_id,
                'source_step_index': row['source_step_index'],
                'expected_label_change': row['expected_label_change'],
                'source_scores': source_scores,
                'variant_scores': variant_scores,
            }
        )

    output = {
        'train_features': args.train_features,
        'raw_jsonl': args.raw_jsonl,
        'cts_seed': args.cts_seed,
        'model_path': args.model_path,
        'resolved_layers': resolved_layers,
        'k': args.k,
        'gamma': args.gamma,
        'metrics': aggregate_metrics(results, baseline_names),
        'pairs': results,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
