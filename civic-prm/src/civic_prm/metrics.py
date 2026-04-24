from __future__ import annotations

import math


def binary_accuracy(labels: list[int], predictions: list[int]) -> float:
    if not labels:
        return math.nan
    return sum(int(a == b) for a, b in zip(labels, predictions, strict=True)) / len(labels)


def binary_f1(labels: list[int], predictions: list[int]) -> float:
    tp = sum(int(label == 1 and pred == 1) for label, pred in zip(labels, predictions, strict=True))
    fp = sum(int(label == 0 and pred == 1) for label, pred in zip(labels, predictions, strict=True))
    fn = sum(int(label == 1 and pred == 0) for label, pred in zip(labels, predictions, strict=True))
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall)


def binary_auroc(labels: list[int], scores: list[float]) -> float:
    positives = [score for label, score in zip(labels, scores, strict=True) if label == 1]
    negatives = [score for label, score in zip(labels, scores, strict=True) if label == 0]
    total_pairs = len(positives) * len(negatives)
    if total_pairs == 0:
        return 0.5
    wins = 0.0
    for positive in positives:
        for negative in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / total_pairs
