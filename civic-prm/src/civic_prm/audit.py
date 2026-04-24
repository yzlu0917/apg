from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

from civic_prm.metrics import binary_accuracy, binary_auroc, binary_f1


def load_records(path: str | Path) -> list[dict]:
    with Path(path).open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def _normalize_style(text: str) -> str:
    text = re.sub(r"\[[^\]]+\]", "[STATE]", text)
    text = re.sub(r"\b\d+(?:\.\d+)?\b", "<NUM>", text)
    text = re.sub(r"\b[A-Z]\b", "<SYM>", text)
    return text


def _split(records: list[dict], label_key: str) -> tuple[list[dict], list[dict]]:
    grouped: dict[object, list[dict]] = {}
    for record in records:
        grouped.setdefault(record[label_key], []).append(record)
    train_records: list[dict] = []
    test_records: list[dict] = []
    rng = np.random.default_rng(13)
    for rows in grouped.values():
        order = rng.permutation(len(rows))
        cut = max(1, int(round(len(rows) * 0.7)))
        train_rows = [rows[index] for index in order[:cut]]
        test_rows = [rows[index] for index in order[cut:]]
        if not test_rows:
            test_rows = train_rows[-1:]
            train_rows = train_rows[:-1]
        train_records.extend(train_rows)
        test_records.extend(test_rows)
    return train_records, test_records


def _char_ngrams(text: str, min_n: int = 3, max_n: int = 5) -> Counter[str]:
    padded = f"  {text.lower()}  "
    grams: Counter[str] = Counter()
    for n in range(min_n, max_n + 1):
        for idx in range(len(padded) - n + 1):
            grams[padded[idx : idx + n]] += 1
    return grams


def _train_binary_nb(texts: list[str], labels: list[int]) -> dict:
    per_class = {
        0: Counter(),
        1: Counter(),
    }
    total_counts = {0: 0, 1: 0}
    class_sizes = {0: 0, 1: 0}
    vocab = set()
    for text, label in zip(texts, labels, strict=True):
        grams = _char_ngrams(text)
        per_class[label].update(grams)
        total_counts[label] += sum(grams.values())
        class_sizes[label] += 1
        vocab.update(grams)
    return {
        "counts": per_class,
        "totals": total_counts,
        "class_sizes": class_sizes,
        "vocab_size": max(1, len(vocab)),
        "num_examples": max(1, len(texts)),
    }


def _predict_binary_nb(model: dict, texts: list[str]) -> tuple[list[int], list[float]]:
    predictions: list[int] = []
    scores: list[float] = []
    for text in texts:
        grams = _char_ngrams(text)
        class_logits = {}
        for label in [0, 1]:
            prior = np.log((model["class_sizes"][label] + 1) / (model["num_examples"] + 2))
            denom = model["totals"][label] + model["vocab_size"]
            log_prob = prior
            for gram, count in grams.items():
                numer = model["counts"][label][gram] + 1
                log_prob += count * np.log(numer / denom)
            class_logits[label] = log_prob
        margin = class_logits[1] - class_logits[0]
        probability = 1.0 / (1.0 + np.exp(-margin))
        predictions.append(int(probability >= 0.5))
        scores.append(float(probability))
    return predictions, scores

def _fit_length_centroid(train_rows: list[dict], labels: list[int]) -> dict:
    features = _length_features(train_rows)
    labels_array = np.array(labels)
    centroids = {
        label: features[labels_array == label].mean(axis=0)
        for label in [0, 1]
    }
    return {"centroids": centroids}


def _length_features(rows: list[dict]) -> np.ndarray:
    return np.array(
        [
            [
                len(row["trace_text"]),
                len(row["trace_text"].split()),
                len(row["step_texts"]),
            ]
            for row in rows
        ],
        dtype=float,
    )


def _predict_length_centroid(model: dict, rows: list[dict]) -> tuple[list[int], list[float]]:
    features = _length_features(rows)
    predictions: list[int] = []
    scores: list[float] = []
    for feature in features:
        dist0 = np.linalg.norm(feature - model["centroids"][0])
        dist1 = np.linalg.norm(feature - model["centroids"][1])
        margin = dist0 - dist1
        probability = 1.0 / (1.0 + np.exp(-margin))
        predictions.append(int(probability >= 0.5))
        scores.append(float(probability))
    return predictions, scores


def run_artifact_audit(records: list[dict]) -> dict:
    train_records, test_records = _split(records, "is_valid_process")
    train_texts = [_normalize_style(record["trace_text"]) for record in train_records]
    test_texts = [_normalize_style(record["trace_text"]) for record in test_records]
    train_valid_labels = [int(record["is_valid_process"]) for record in train_records]
    test_valid_labels = [int(record["is_valid_process"]) for record in test_records]

    valid_model = _train_binary_nb(train_texts, train_valid_labels)
    valid_predictions, valid_scores = _predict_binary_nb(valid_model, test_texts)

    train_answer_labels = [int(record["answer_is_correct"]) for record in train_records]
    test_answer_labels = [int(record["answer_is_correct"]) for record in test_records]
    answer_model = _train_binary_nb(train_texts, train_answer_labels)
    answer_predictions, _ = _predict_binary_nb(answer_model, test_texts)

    length_model = _fit_length_centroid(train_records, train_valid_labels)
    length_predictions, length_scores = _predict_length_centroid(length_model, test_records)

    return {
        "num_records": len(records),
        "validity_style_accuracy": round(binary_accuracy(test_valid_labels, valid_predictions), 4),
        "validity_style_f1": round(binary_f1(test_valid_labels, valid_predictions), 4),
        "validity_style_auroc": round(binary_auroc(test_valid_labels, valid_scores), 4),
        "answer_style_accuracy": round(binary_accuracy(test_answer_labels, answer_predictions), 4),
        "answer_style_f1": round(binary_f1(test_answer_labels, answer_predictions), 4),
        "length_only_validity_accuracy": round(binary_accuracy(test_valid_labels, length_predictions), 4),
        "length_only_validity_auroc": round(binary_auroc(test_valid_labels, length_scores), 4),
        "flag_high_style_leakage": bool(binary_accuracy(test_valid_labels, valid_predictions) >= 0.8),
        "flag_high_length_leakage": bool(binary_accuracy(test_valid_labels, length_predictions) >= 0.75),
    }


def save_audit_summary(summary: dict, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
