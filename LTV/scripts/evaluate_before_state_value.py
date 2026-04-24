#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from extract_boundary_states_smoke import build_prefix, encode_last_token_states, load_jsonl, resolve_layers
from run_object_gate_baselines import auroc_score, brier_score


TIER_TO_ORDINAL = {
    "neutral": 0,
    "weak_partial": 1,
    "strong_partial": 2,
    "solved": 3,
}


def flatten_states(entry: Dict[str, torch.Tensor]) -> torch.Tensor:
    layer_items = sorted(entry.items(), key=lambda kv: int(kv[0]))
    return torch.cat([tensor.to(torch.float32) for _, tensor in layer_items], dim=0)


def load_state_index(generated_path: Path, replayed_path: Path) -> Dict[str, Dict]:
    generated_rows = {row["state_id"]: row for row in load_jsonl(generated_path)}
    replayed_rows = {row["state_id"]: row for row in load_jsonl(replayed_path)}
    merged = {}
    for state_id, replayed in replayed_rows.items():
        generated = generated_rows[state_id]
        merged[state_id] = {
            **replayed,
            "header": generated["header"],
            "prefix_steps": generated["prefix_steps"],
        }
    return merged


def standardize(x_train: torch.Tensor, x_test: torch.Tensor):
    mean = x_train.mean(dim=0, keepdim=True)
    std = x_train.std(dim=0, keepdim=True)
    std = torch.where(std < 1e-6, torch.ones_like(std), std)
    return (x_train - mean) / std, (x_test - mean) / std


def fit_linear_classifier(x_train, y_train, x_test, epochs=400, lr=0.05, weight_decay=1e-3):
    if int(y_train.sum().item()) == 0 or int(y_train.sum().item()) == len(y_train):
        prior = y_train.float().mean().clamp(1e-4, 1 - 1e-4)
        return torch.full((len(x_test),), float(prior.item()), dtype=torch.float32)
    x_train, x_test = standardize(x_train, x_test)
    model = torch.nn.Linear(x_train.shape[1], 1)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    for _ in range(epochs):
        opt.zero_grad()
        logits = model(x_train).squeeze(-1)
        loss = loss_fn(logits, y_train.float())
        loss.backward()
        opt.step()
    with torch.no_grad():
        return torch.sigmoid(model(x_test).squeeze(-1)).cpu()


def fit_linear_regressor(x_train, y_train, x_test, epochs=400, lr=0.05, weight_decay=1e-3):
    x_train, x_test = standardize(x_train, x_test)
    model = torch.nn.Linear(x_train.shape[1], 1)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    for _ in range(epochs):
        opt.zero_grad()
        preds = model(x_train).squeeze(-1)
        loss = torch.mean((preds - y_train) ** 2)
        loss.backward()
        opt.step()
    with torch.no_grad():
        return model(x_test).squeeze(-1).cpu()


def pearson(x: torch.Tensor, y: torch.Tensor) -> float:
    if len(x) <= 1:
        return float("nan")
    xm = x - x.mean()
    ym = y - y.mean()
    denom = torch.sqrt(torch.sum(xm ** 2) * torch.sum(ym ** 2))
    if float(denom.item()) < 1e-8:
        return float("nan")
    return float((torch.sum(xm * ym) / denom).item())


def rankdata(vals: List[float]) -> List[float]:
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1
    return ranks


def spearman(x: torch.Tensor, y: torch.Tensor) -> float:
    xr = torch.tensor(rankdata(x.tolist()), dtype=torch.float32)
    yr = torch.tensor(rankdata(y.tolist()), dtype=torch.float32)
    return pearson(xr, yr)


def binary_metrics(y_true: torch.Tensor, y_prob: torch.Tensor):
    preds = (y_prob >= 0.5).long()
    return {
        "auroc": auroc_score(y_true, y_prob),
        "accuracy": float((preds == y_true).float().mean().item()),
        "brier": brier_score(y_true, y_prob),
        "positive_mean_prob": float(y_prob[y_true == 1].mean().item()) if int((y_true == 1).sum().item()) > 0 else None,
        "negative_mean_prob": float(y_prob[y_true == 0].mean().item()) if int((y_true == 0).sum().item()) > 0 else None,
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate before-hidden state value signal.")
    parser.add_argument("--oracle", required=True)
    parser.add_argument("--generated", required=True)
    parser.add_argument("--replayed", required=True)
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layers", default="-1,-8,-16")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()

    oracle_rows = load_jsonl(Path(args.oracle))
    replay_index = load_state_index(Path(args.generated), Path(args.replayed))

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

    xs = []
    mean_tier = []
    low_count = []
    state_ids = []
    solved_count = []
    for row in oracle_rows:
        state_id = row["state_id"]
        replay_row = replay_index[state_id]
        before_text = build_prefix(replay_row["header"], replay_row["prefix_steps"], len(replay_row["prefix_steps"]))
        before = encode_last_token_states(model, tokenizer, before_text, resolved_layers, args.device)
        x = flatten_states(before["states"])
        tiers = [TIER_TO_ORDINAL[c["progress_tier"]] for c in row["candidates"]]
        xs.append(x)
        mean_tier.append(sum(tiers) / len(tiers))
        low_count.append(sum(1 for t in tiers if t <= 1))
        solved_count.append(sum(1 for t in tiers if t == 3))
        state_ids.append(state_id)

    x = torch.stack(xs, dim=0)
    y_binary = torch.tensor([1 if c > 0 else 0 for c in low_count], dtype=torch.long)
    y_mean = torch.tensor(mean_tier, dtype=torch.float32)

    binary_probs = torch.zeros(len(state_ids), dtype=torch.float32)
    reg_preds = torch.zeros(len(state_ids), dtype=torch.float32)
    for i, sid in enumerate(state_ids):
        train_idx = [j for j in range(len(state_ids)) if j != i]
        test_idx = [i]
        binary_probs[test_idx] = fit_linear_classifier(x[train_idx], y_binary[train_idx], x[test_idx])
        reg_preds[test_idx] = fit_linear_regressor(x[train_idx], y_mean[train_idx], x[test_idx])

    output = {
        "oracle": args.oracle,
        "generated": args.generated,
        "replayed": args.replayed,
        "model_path": args.model_path,
        "resolved_layers": resolved_layers,
        "num_states": len(state_ids),
        "hardness_binary": {
            "definition": "1 iff state has at least one neutral/weak_partial candidate",
            "num_positive": int(y_binary.sum().item()),
            "num_negative": int((y_binary == 0).sum().item()),
            "metrics": binary_metrics(y_binary, binary_probs),
        },
        "mean_tier_regression": {
            "pearson": pearson(reg_preds, y_mean),
            "spearman": spearman(reg_preds, y_mean),
            "mse": float(torch.mean((reg_preds - y_mean) ** 2).item()),
        },
        "state_rows": [
            {
                "state_id": sid,
                "mean_tier": float(y_mean[i].item()),
                "low_count": int(low_count[i]),
                "solved_count": int(solved_count[i]),
                "hardness_label": int(y_binary[i].item()),
                "hardness_prob": float(binary_probs[i].item()),
                "mean_tier_pred": float(reg_preds[i].item()),
            }
            for i, sid in enumerate(state_ids)
        ],
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(out),
        "hardness_binary": output["hardness_binary"],
        "mean_tier_regression": output["mean_tier_regression"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
