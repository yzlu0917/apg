from __future__ import annotations

from pathlib import Path

import torch
from transformers import AutoModel, AutoTokenizer


def load_encoder(model_root: str | Path):
    root = Path(model_root)
    snapshots = sorted(path for path in root.iterdir() if path.is_dir())
    if not snapshots:
        raise FileNotFoundError(f"no snapshot found under {root}")
    snapshot = snapshots[0]
    tokenizer = AutoTokenizer.from_pretrained(snapshot, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModel.from_pretrained(
        snapshot,
        dtype="auto",
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return tokenizer, model


@torch.inference_mode()
def encode_texts(
    texts: list[str],
    tokenizer,
    model,
    batch_size: int = 8,
    max_length: int = 512,
) -> torch.Tensor:
    outputs = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start : start + batch_size]
        tokenized = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=max_length,
            return_tensors="pt",
        ).to(model.device)
        encoded = model(**tokenized).last_hidden_state
        mask = tokenized["attention_mask"].unsqueeze(-1)
        pooled = (encoded * mask).sum(dim=1) / mask.sum(dim=1).clamp(min=1)
        outputs.append(pooled.detach().cpu().to(torch.float32))
    return torch.cat(outputs, dim=0)
