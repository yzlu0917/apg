#!/usr/bin/env python3
"""Char-level seq2seq transfer probe for semantic string families."""

from __future__ import annotations

import argparse
import json
import random
import string
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

import torch


PAD = 0
SOS = 1
EOS = 2
UNK = 3
MAX_IN_LEN = 192
MAX_OUT_LEN = 32
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
    parser.add_argument("--repeats", type=int, default=18)
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument(
        "--modes",
        type=str,
        default="full_coverage_reference,v1_to_v2_transfer,odd_to_half_transfer,half_to_odd_transfer",
    )
    return parser.parse_args()


def rand_word(rng: random.Random, min_len: int = 5, max_len: int = 9) -> str:
    return "".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randint(min_len, max_len)))


def serialize_prompt(visible_tests: Sequence[Sequence[str]], query: str) -> str:
    pairs = [f"IN={inp};OUT={out}" for inp, out in visible_tests]
    pairs.append(f"QUERY={query}")
    return "|".join(pairs)


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
                    target = spec["fn"](param, query)
                    examples.append(
                        {
                            "family": family,
                            "param": param,
                            "prompt": serialize_prompt(visible_tests, query),
                            "target": target,
                        }
                    )
    random.shuffle(examples)
    return examples


def stoi() -> Dict[str, int]:
    return {ch: idx + 4 for idx, ch in enumerate(ALPHABET)}


def encode_input(text: str, mapping: Dict[str, int], max_len: int = MAX_IN_LEN) -> torch.Tensor:
    vec = torch.full((max_len,), PAD, dtype=torch.long)
    for idx, ch in enumerate(text[:max_len]):
        vec[idx] = mapping.get(ch, UNK)
    return vec


def encode_output(text: str, mapping: Dict[str, int], max_len: int = MAX_OUT_LEN) -> torch.Tensor:
    tokens = [SOS]
    tokens.extend(mapping.get(ch, UNK) for ch in text[: max_len - 2])
    tokens.append(EOS)
    if len(tokens) < max_len:
        tokens.extend([PAD] * (max_len - len(tokens)))
    return torch.tensor(tokens[:max_len], dtype=torch.long)


def decode_output(tokens: Sequence[int], mapping: Dict[int, str]) -> str:
    chars: List[str] = []
    for token in tokens:
        if token in (PAD, SOS):
            continue
        if token == EOS:
            break
        chars.append(mapping.get(int(token), "?"))
    return "".join(chars)


class Seq2Seq(torch.nn.Module):
    def __init__(self, vocab_size: int, hidden_size: int = 96) -> None:
        super().__init__()
        self.embed = torch.nn.Embedding(vocab_size, 48, padding_idx=PAD)
        self.encoder = torch.nn.GRU(48, hidden_size, batch_first=True)
        self.decoder = torch.nn.GRU(48, hidden_size, batch_first=True)
        self.output = torch.nn.Linear(hidden_size, vocab_size)

    def forward(self, src: torch.Tensor, tgt_in: torch.Tensor) -> torch.Tensor:
        src_emb = self.embed(src)
        _, hidden = self.encoder(src_emb)
        tgt_emb = self.embed(tgt_in)
        dec_out, _ = self.decoder(tgt_emb, hidden)
        return self.output(dec_out)

    def greedy_decode(self, src: torch.Tensor, max_len: int) -> torch.Tensor:
        src_emb = self.embed(src)
        _, hidden = self.encoder(src_emb)
        batch = src.shape[0]
        token = torch.full((batch, 1), SOS, dtype=torch.long)
        outputs: List[torch.Tensor] = []
        for _ in range(max_len - 1):
            emb = self.embed(token[:, -1:])
            dec_out, hidden = self.decoder(emb, hidden)
            logits = self.output(dec_out[:, -1, :])
            next_token = torch.argmax(logits, dim=-1, keepdim=True)
            outputs.append(next_token)
            token = torch.cat([token, next_token], dim=1)
        return torch.cat(outputs, dim=1)


def make_batch(examples: Sequence[Dict[str, str]], mapping: Dict[str, int]) -> Tuple[torch.Tensor, torch.Tensor]:
    xs = torch.stack([encode_input(example["prompt"], mapping) for example in examples])
    ys = torch.stack([encode_output(example["target"], mapping) for example in examples])
    return xs, ys


def train_model(examples: Sequence[Dict[str, str]], mapping: Dict[str, int], epochs: int) -> Tuple[Seq2Seq, List[float]]:
    xs, ys = make_batch(examples, mapping)
    model = Seq2Seq(vocab_size=max(mapping.values()) + 1)
    opt = torch.optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-3)
    loss_fn = torch.nn.CrossEntropyLoss(ignore_index=PAD)
    losses: List[float] = []
    for _ in range(epochs):
        opt.zero_grad()
        logits = model(xs, ys[:, :-1])
        loss = loss_fn(logits.reshape(-1, logits.shape[-1]), ys[:, 1:].reshape(-1))
        loss.backward()
        opt.step()
        losses.append(float(loss.item()))
    return model, losses


def eval_examples(model: Seq2Seq, examples: Sequence[Dict[str, str]], mapping: Dict[str, int]) -> Dict[str, float]:
    inv = {idx: ch for ch, idx in mapping.items()}
    xs, ys = make_batch(examples, mapping)
    with torch.no_grad():
        pred = model.greedy_decode(xs, MAX_OUT_LEN)
    exact = 0
    for example, tokens in zip(examples, pred.tolist()):
        if decode_output(tokens, inv) == example["target"]:
            exact += 1
    return {"examples": len(examples), "exact_output_match_rate": round(exact / len(examples), 3)}


def load_eval_examples(artifact_path: Path) -> Tuple[List[Dict[str, str]], Dict[str, List[Dict[str, str]]]]:
    artifact = json.loads(artifact_path.read_text())
    flat: List[Dict[str, str]] = []
    by_task: Dict[str, List[Dict[str, str]]] = {}
    for task in artifact["tasks"]:
        example_scores = task["attempts"][0]["scores"]
        visible_tests = [[item["input"], item["expected"]] for item in example_scores["visible_results"]]
        task_examples = []
        for item in example_scores["hidden_results"]:
            ex = {
                "task_id": task["task_id"],
                "prompt": serialize_prompt(visible_tests, str(item["input"])),
                "target": str(item["expected"]),
            }
            flat.append(ex)
            task_examples.append(ex)
        by_task[task["task_id"]] = task_examples
    return flat, by_task


def eval_task_exact(model: Seq2Seq, by_task: Dict[str, List[Dict[str, str]]], mapping: Dict[str, int], prefix: str | None = None) -> Dict[str, float]:
    inv = {idx: ch for ch, idx in mapping.items()}
    chosen = [(task_id, examples) for task_id, examples in by_task.items() if prefix is None or task_id.startswith(prefix)]
    exact = 0
    for _, examples in chosen:
        xs, _ = make_batch(examples, mapping)
        with torch.no_grad():
            pred = model.greedy_decode(xs, MAX_OUT_LEN)
        ok = True
        for example, tokens in zip(examples, pred.tolist()):
            if decode_output(tokens, inv) != example["target"]:
                ok = False
                break
        exact += 1 if ok else 0
    return {"tasks": len(chosen), "exact_hidden_match_rate": round(exact / len(chosen), 3)}


def visible_baseline(artifact_path: Path, prefix: str | None = None) -> Dict[str, float]:
    artifact = json.loads(artifact_path.read_text())
    chosen = artifact["tasks"]
    if prefix is not None:
        chosen = [task for task in chosen if task["task_id"].startswith(prefix)]
    exact = 0
    for task in chosen:
        best = max(task["attempts"], key=lambda attempt: float(attempt["scores"]["visible_score"]))
        hidden = best["scores"]["hidden_results"]
        exact += 1 if all(item.get("pass", False) for item in hidden) else 0
    return {"tasks": len(chosen), "exact_hidden_match_rate": round(exact / len(chosen), 3)}


def summarize_regime(
    train_families: Sequence[str],
    eval_by_task: Dict[str, List[Dict[str, str]]],
    mapping: Dict[str, int],
    repeats: int,
    epochs: int,
    prefix: str | None = None,
) -> Dict[str, Any]:
    examples = build_examples(train_families, repeats=repeats)
    split = int(0.8 * len(examples))
    train_examples = examples[:split]
    val_examples = examples[split:]
    model, losses = train_model(train_examples, mapping, epochs=epochs)
    return {
        "train_families": list(train_families),
        "train_examples": len(train_examples),
        "val_examples": len(val_examples),
        "final_train_loss": round(losses[-1], 6),
        "validation": eval_examples(model, val_examples, mapping),
        "eval_tasks": eval_task_exact(model, eval_by_task, mapping, prefix=prefix),
    }


def main() -> None:
    args = parse_args()
    random.seed(7)
    torch.manual_seed(7)
    mapping = stoi()
    _, eval_by_task = load_eval_examples(args.artifact)
    modes = {item.strip() for item in args.modes.split(",") if item.strip()}
    payload: Dict[str, Any] = {}
    if "full_coverage_reference" in modes:
        payload["full_coverage_reference"] = summarize_regime(
            ["reverse_suffix", "upper_wrap", "duplicate_prefix", "odd_even_join", "half_swap"],
            eval_by_task,
            mapping,
            repeats=args.repeats,
            epochs=args.epochs,
        )
    if "v1_to_v2_transfer" in modes:
        payload["v1_to_v2_transfer"] = summarize_regime(
            ["reverse_suffix", "upper_wrap", "duplicate_prefix", "mirror_join", "vowel_mask"],
            eval_by_task,
            mapping,
            repeats=args.repeats,
            epochs=args.epochs,
        )
    if "odd_to_half_transfer" in modes:
        payload["odd_to_half_transfer"] = summarize_regime(
            ["reverse_suffix", "upper_wrap", "duplicate_prefix", "odd_even_join"],
            eval_by_task,
            mapping,
            repeats=args.repeats,
            epochs=args.epochs,
            prefix="half_swap",
        )
    if "half_to_odd_transfer" in modes:
        payload["half_to_odd_transfer"] = summarize_regime(
            ["reverse_suffix", "upper_wrap", "duplicate_prefix", "half_swap"],
            eval_by_task,
            mapping,
            repeats=args.repeats,
            epochs=args.epochs,
            prefix="odd_even_join",
        )
    payload["visible_attempt_baseline_full"] = visible_baseline(args.artifact)
    payload["visible_attempt_baseline_odd"] = visible_baseline(args.artifact, prefix="odd_even_join")
    payload["visible_attempt_baseline_half"] = visible_baseline(args.artifact, prefix="half_swap")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
