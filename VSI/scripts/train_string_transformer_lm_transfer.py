#!/usr/bin/env python3
"""Decoder-only transformer LM transfer probe for semantic string families."""

from __future__ import annotations

import argparse
import json
import random
import string
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import torch
import torch.nn.functional as F


PAD = 0
EOS = 1
UNK = 2
MAX_LEN = 256
MAX_GEN = 40
ALPHABET = string.ascii_lowercase + string.ascii_uppercase + "!*_-:+[]#@%<>?{}|=;,"


def reverse_suffix(token: str, text: str) -> str:
    return text[::-1] + token


def upper_wrap(token: str, text: str) -> str:
    return f"{token}{text.upper()}{token}"


def duplicate_prefix(token: str, text: str) -> str:
    return f"{token}{text}{text}"


def mirror_join(token: str, text: str) -> str:
    return f"{text}{token}{text[::-1]}"


def vowel_mask(mask: str, text: str) -> str:
    vowels = set("aeiou")
    return "".join(mask if ch in vowels else ch for ch in text)


def odd_even_join(token: str, text: str) -> str:
    even = text[::2]
    odd = text[1::2]
    return f"{even}{token}{odd}"


def half_swap(token: str, text: str) -> str:
    split = (len(text) + 1) // 2
    left = text[:split]
    right = text[split:]
    return f"{right}{token}{left}"


SPECS: Dict[str, Dict[str, Any]] = {
    "reverse_suffix": {"params": ["!", "?", "#"], "fn": reverse_suffix},
    "upper_wrap": {"params": ["[", "<", "{"], "fn": upper_wrap},
    "duplicate_prefix": {"params": ["pre_", "tag-", "id:"], "fn": duplicate_prefix},
    "mirror_join": {"params": ["::", "--", "++"], "fn": mirror_join},
    "vowel_mask": {"params": ["*", "_", "-"], "fn": vowel_mask},
    "odd_even_join": {"params": ["::", "--", "++"], "fn": odd_even_join},
    "half_swap": {"params": ["#", "@", "%"], "fn": half_swap},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--repeats", type=int, default=24)
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--modes", type=str, default="full_coverage_reference,v1_to_v2_transfer")
    return parser.parse_args()


def rand_word(rng: random.Random, min_len: int = 5, max_len: int = 9) -> str:
    return "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(min_len, max_len)))


def serialize_prompt(visible_tests: Sequence[Sequence[str]], query: str) -> str:
    return "|".join(f"IN={inp};OUT={out}" for inp, out in visible_tests) + f"|QUERY={query}|ANS="


def build_examples(families: Sequence[str], repeats: int, seed: int = 7) -> List[Dict[str, str]]:
    rng = random.Random(seed)
    examples: List[Dict[str, str]] = []
    for _ in range(repeats):
        for family in families:
            spec = SPECS[family]
            for param in spec["params"]:
                visible_inputs = [rand_word(rng) for _ in range(3)]
                hidden_inputs = [rand_word(rng) for _ in range(2)]
                visible_tests = [[item, spec["fn"](param, item)] for item in visible_inputs]
                for query in hidden_inputs:
                    examples.append(
                        {
                            "prompt": serialize_prompt(visible_tests, query),
                            "target": spec["fn"](param, query),
                        }
                    )
    random.shuffle(examples)
    return examples


def build_vocab() -> Dict[str, int]:
    return {ch: idx + 3 for idx, ch in enumerate(ALPHABET)}


def encode_chars(text: str, stoi: Dict[str, int]) -> List[int]:
    return [stoi.get(ch, UNK) for ch in text]


def make_lm_example(example: Dict[str, str], stoi: Dict[str, int]) -> Tuple[torch.Tensor, torch.Tensor]:
    prompt_tokens = encode_chars(example["prompt"], stoi)
    target_tokens = encode_chars(example["target"], stoi) + [EOS]
    full = prompt_tokens + target_tokens
    full = full[:MAX_LEN]
    input_ids = torch.full((MAX_LEN,), PAD, dtype=torch.long)
    labels = torch.full((MAX_LEN,), -100, dtype=torch.long)
    for idx, tok in enumerate(full[:-1]):
        input_ids[idx] = tok
    prompt_len = min(len(prompt_tokens), MAX_LEN - 1)
    full_len = min(len(full), MAX_LEN)
    for idx in range(prompt_len - 1, full_len - 1):
        if idx >= 0:
            labels[idx] = full[idx + 1]
    return input_ids, labels


class TinyCausalTransformer(torch.nn.Module):
    def __init__(self, vocab_size: int, d_model: int = 192, n_head: int = 6, n_layer: int = 4) -> None:
        super().__init__()
        self.token_embed = torch.nn.Embedding(vocab_size, d_model, padding_idx=PAD)
        self.pos_embed = torch.nn.Embedding(MAX_LEN, d_model)
        layer = torch.nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_head,
            dim_feedforward=4 * d_model,
            dropout=0.0,
            batch_first=True,
            activation="gelu",
        )
        self.blocks = torch.nn.TransformerEncoder(layer, num_layers=n_layer)
        self.ln = torch.nn.LayerNorm(d_model)
        self.head = torch.nn.Linear(d_model, vocab_size)

    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        bsz, seq_len = input_ids.shape
        pos = torch.arange(seq_len, device=input_ids.device).unsqueeze(0).expand(bsz, seq_len)
        h = self.token_embed(input_ids) + self.pos_embed(pos)
        mask = torch.triu(torch.ones(seq_len, seq_len, device=input_ids.device, dtype=torch.bool), diagonal=1)
        key_padding_mask = input_ids.eq(PAD)
        h = self.blocks(h, mask=mask, src_key_padding_mask=key_padding_mask)
        return self.head(self.ln(h))


def train_model(
    examples: Sequence[Dict[str, str]],
    stoi: Dict[str, int],
    epochs: int,
    batch_size: int,
    device: torch.device,
) -> Tuple[TinyCausalTransformer, List[float]]:
    data = [make_lm_example(example, stoi) for example in examples]
    model = TinyCausalTransformer(vocab_size=max(stoi.values()) + 1).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=2e-4, weight_decay=1e-2)
    losses: List[float] = []
    for _ in range(epochs):
        random.shuffle(data)
        epoch_loss = 0.0
        for start in range(0, len(data), batch_size):
            batch = data[start : start + batch_size]
            xs = torch.stack([item[0] for item in batch]).to(device)
            ys = torch.stack([item[1] for item in batch]).to(device)
            opt.zero_grad()
            logits = model(xs)
            loss = F.cross_entropy(logits.reshape(-1, logits.shape[-1]), ys.reshape(-1), ignore_index=-100)
            loss.backward()
            opt.step()
            epoch_loss += float(loss.item())
        losses.append(epoch_loss / max(1, (len(data) + batch_size - 1) // batch_size))
    return model, losses


def greedy_generate(model: TinyCausalTransformer, prompt: str, stoi: Dict[str, int], itos: Dict[int, str], device: torch.device) -> str:
    prompt_tokens = encode_chars(prompt, stoi)
    seq = prompt_tokens[: MAX_LEN - 1]
    while len(seq) < MAX_LEN and len(seq) < len(prompt_tokens) + MAX_GEN:
        input_ids = torch.full((1, MAX_LEN), PAD, dtype=torch.long, device=device)
        input_ids[0, : len(seq)] = torch.tensor(seq, dtype=torch.long, device=device)
        with torch.no_grad():
            logits = model(input_ids)[0, len(seq) - 1]
        next_tok = int(torch.argmax(logits).item())
        if next_tok == EOS:
            break
        seq.append(next_tok)
    gen = seq[len(prompt_tokens) :]
    chars = [itos.get(tok, "?") for tok in gen if tok not in (PAD, EOS)]
    return "".join(chars)


def eval_examples(model: TinyCausalTransformer, examples: Sequence[Dict[str, str]], stoi: Dict[str, int], itos: Dict[int, str], device: torch.device) -> Dict[str, float]:
    exact = 0
    for example in examples:
        pred = greedy_generate(model, example["prompt"], stoi, itos, device)
        if pred == example["target"]:
            exact += 1
    return {"examples": len(examples), "exact_output_match_rate": round(exact / len(examples), 3)}


def load_eval_examples(artifact_path: Path) -> Tuple[List[Dict[str, str]], Dict[str, List[Dict[str, str]]]]:
    artifact = json.loads(artifact_path.read_text())
    flat: List[Dict[str, str]] = []
    by_task: Dict[str, List[Dict[str, str]]] = {}
    for task in artifact["tasks"]:
        scores = task["attempts"][0]["scores"]
        visible_tests = [[item["input"], item["expected"]] for item in scores["visible_results"]]
        examples = []
        for item in scores["hidden_results"]:
            ex = {"prompt": serialize_prompt(visible_tests, str(item["input"])), "target": str(item["expected"])}
            flat.append(ex)
            examples.append(ex)
        by_task[task["task_id"]] = examples
    return flat, by_task


def eval_task_exact(
    model: TinyCausalTransformer,
    by_task: Dict[str, List[Dict[str, str]]],
    stoi: Dict[str, int],
    itos: Dict[int, str],
    device: torch.device,
    prefixes: Sequence[str] | None = None,
) -> Dict[str, float]:
    items = list(by_task.items())
    if prefixes is not None:
        items = [(task_id, exs) for task_id, exs in items if any(task_id.startswith(prefix) for prefix in prefixes)]
    exact = 0
    for _, examples in items:
        ok = True
        for example in examples:
            pred = greedy_generate(model, example["prompt"], stoi, itos, device)
            if pred != example["target"]:
                ok = False
                break
        exact += 1 if ok else 0
    return {"tasks": len(items), "exact_hidden_match_rate": round(exact / len(items), 3)}


def visible_baseline(artifact_path: Path, prefixes: Sequence[str] | None = None) -> Dict[str, float]:
    artifact = json.loads(artifact_path.read_text())
    tasks = artifact["tasks"]
    if prefixes is not None:
        tasks = [task for task in tasks if any(task["task_id"].startswith(prefix) for prefix in prefixes)]
    exact = 0
    for task in tasks:
        best = max(task["attempts"], key=lambda attempt: float(attempt["scores"]["visible_score"]))
        hidden = best["scores"]["hidden_results"]
        exact += 1 if all(item.get("pass", False) for item in hidden) else 0
    return {"tasks": len(tasks), "exact_hidden_match_rate": round(exact / len(tasks), 3)}


def summarize_regime(
    train_families: Sequence[str],
    eval_by_task: Dict[str, List[Dict[str, str]]],
    stoi: Dict[str, int],
    itos: Dict[int, str],
    device: torch.device,
    repeats: int,
    epochs: int,
    batch_size: int,
    prefixes: Sequence[str] | None = None,
) -> Dict[str, Any]:
    examples = build_examples(train_families, repeats=repeats)
    split = int(0.8 * len(examples))
    train_examples = examples[:split]
    val_examples = examples[split:]
    model, losses = train_model(train_examples, stoi, epochs=epochs, batch_size=batch_size, device=device)
    return {
        "train_families": list(train_families),
        "train_examples": len(train_examples),
        "val_examples": len(val_examples),
        "final_train_loss": round(losses[-1], 6),
        "validation": eval_examples(model, val_examples, stoi, itos, device),
        "eval_tasks": eval_task_exact(model, eval_by_task, stoi, itos, device, prefixes=prefixes),
    }


def main() -> None:
    args = parse_args()
    random.seed(7)
    torch.manual_seed(7)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    stoi = build_vocab()
    itos = {idx: ch for ch, idx in stoi.items()}
    _, eval_by_task = load_eval_examples(args.artifact)
    modes = {item.strip() for item in args.modes.split(",") if item.strip()}

    payload: Dict[str, Any] = {"device": str(device)}
    if "full_coverage_reference" in modes:
        payload["full_coverage_reference"] = summarize_regime(
            ["reverse_suffix", "upper_wrap", "duplicate_prefix", "odd_even_join", "half_swap"],
            eval_by_task,
            stoi,
            itos,
            device,
            repeats=args.repeats,
            epochs=args.epochs,
            batch_size=args.batch_size,
        )
    if "v1_to_v2_transfer" in modes:
        payload["v1_to_v2_transfer"] = summarize_regime(
            ["reverse_suffix", "upper_wrap", "duplicate_prefix", "mirror_join", "vowel_mask"],
            eval_by_task,
            stoi,
            itos,
            device,
            repeats=args.repeats,
            epochs=args.epochs,
            batch_size=args.batch_size,
        )
    if "odd_to_half_transfer" in modes:
        payload["odd_to_half_transfer"] = summarize_regime(
            ["reverse_suffix", "upper_wrap", "duplicate_prefix", "odd_even_join"],
            eval_by_task,
            stoi,
            itos,
            device,
            repeats=args.repeats,
            epochs=args.epochs,
            batch_size=args.batch_size,
            prefixes=["half_swap"],
        )
    if "half_to_odd_transfer" in modes:
        payload["half_to_odd_transfer"] = summarize_regime(
            ["reverse_suffix", "upper_wrap", "duplicate_prefix", "half_swap"],
            eval_by_task,
            stoi,
            itos,
            device,
            repeats=args.repeats,
            epochs=args.epochs,
            batch_size=args.batch_size,
            prefixes=["odd_even_join"],
        )
    payload["visible_attempt_baseline_full"] = visible_baseline(args.artifact)
    payload["visible_attempt_baseline_odd"] = visible_baseline(args.artifact, prefixes=["odd_even_join"])
    payload["visible_attempt_baseline_half"] = visible_baseline(args.artifact, prefixes=["half_swap"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
