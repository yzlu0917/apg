from __future__ import annotations

import random
import re


def build_quartet_split_map(records: list[dict], seed: int = 17) -> dict[str, str]:
    rng = random.Random(seed)
    quartet_domains: dict[str, str] = {}
    for record in records:
        quartet_domains.setdefault(record["quartet_id"], record["domain"])

    domain_quartets: dict[str, list[str]] = {}
    for quartet_id, domain in quartet_domains.items():
        domain_quartets.setdefault(domain, []).append(quartet_id)

    split_map: dict[str, str] = {}
    for domain, quartet_ids in sorted(domain_quartets.items()):
        ordered = quartet_ids[:]
        rng.shuffle(ordered)
        num_quartets = len(ordered)
        train_cut = max(1, int(round(num_quartets * 0.67)))
        val_cut = max(train_cut + 1, int(round(num_quartets * 0.83)))
        if val_cut >= num_quartets:
            val_cut = num_quartets - 1
        for quartet_id in ordered[:train_cut]:
            split_map[quartet_id] = "train"
        for quartet_id in ordered[train_cut:val_cut]:
            split_map[quartet_id] = "val"
        for quartet_id in ordered[val_cut:]:
            split_map[quartet_id] = "test"
    return split_map


def extract_verbalizer_slot(verbalizer_id: str) -> str:
    match = re.search(r"_v(\d+)(?:_.*)?$", verbalizer_id)
    if not match:
        raise ValueError(f"cannot parse verbalizer slot from {verbalizer_id}")
    return f"v{match.group(1)}"


def list_verbalizer_slots(records: list[dict]) -> list[str]:
    return sorted({extract_verbalizer_slot(record["verbalizer_id"]) for record in records})
