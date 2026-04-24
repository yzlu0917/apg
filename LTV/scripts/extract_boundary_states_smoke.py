#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_jsonl(path: Path) -> List[Dict]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def resolve_layers(requested: List[int], num_hidden_layers: int) -> List[int]:
    resolved = []
    for layer in requested:
        absolute = num_hidden_layers + layer if layer < 0 else layer
        if absolute < 0 or absolute >= num_hidden_layers:
            raise ValueError(
                f"Layer {layer} resolves to {absolute}, outside [0, {num_hidden_layers - 1}]"
            )
        resolved.append(absolute)
    return resolved


def encode_last_token_states(
    model,
    tokenizer,
    text: str,
    resolved_layers: List[int],
    device: str,
) -> Dict:
    encoded = tokenizer(text, return_tensors="pt", add_special_tokens=False)
    if encoded["input_ids"].numel() == 0:
        raise ValueError("Encountered empty token sequence during boundary extraction.")
    encoded = {k: v.to(device) for k, v in encoded.items()}
    with torch.no_grad():
        outputs = model(**encoded, output_hidden_states=True, use_cache=False)
    seq_len = int(encoded["input_ids"].shape[1])
    hidden_states = outputs.hidden_states
    states = {}
    for layer in resolved_layers:
        layer_tensor = hidden_states[layer + 1][0, seq_len - 1].detach().to(torch.float32).cpu()
        states[str(layer)] = layer_tensor
    return {"seq_len": seq_len, "states": states}


def build_prefix(header: str, steps: List[str], upto: int) -> str:
    if upto <= 0:
        return header
    return header + "\n" + "\n".join(steps[:upto])


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke extraction of Lean step boundary states.")
    parser.add_argument("--input", required=True, help="Path to the JSONL smoke slice.")
    parser.add_argument("--output-dir", required=True, help="Directory for manifest and tensor dump.")
    parser.add_argument("--model-path", required=True, help="Local HF snapshot path.")
    parser.add_argument(
        "--layers",
        default="-1,-8,-16",
        help="Comma-separated layer ids; negative values are relative to the final layer.",
    )
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--max-records", type=int, default=None)
    parser.add_argument("--max-steps", type=int, default=None)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    requested_layers = [int(x) for x in args.layers.split(",") if x]
    records = load_jsonl(input_path)
    if args.max_records is not None:
        records = records[: args.max_records]

    tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        dtype=torch.bfloat16,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    model.to(args.device)
    model.eval()

    num_hidden_layers = int(model.config.num_hidden_layers)
    resolved_layers = resolve_layers(requested_layers, num_hidden_layers)

    entries = []
    step_counter = 0
    for record in records:
        header = record["header"]
        steps = record["steps"]
        labels = record["local_sound"]
        for step_index, step_text in enumerate(steps):
            if args.max_steps is not None and step_counter >= args.max_steps:
                break
            before_text = build_prefix(header, steps, step_index)
            after_text = build_prefix(header, steps, step_index + 1)

            before = encode_last_token_states(model, tokenizer, before_text, resolved_layers, args.device)
            after = encode_last_token_states(model, tokenizer, after_text, resolved_layers, args.device)

            h_minus = before["states"]
            h_plus = after["states"]
            delta_h = {layer: (h_plus[layer] - h_minus[layer]) for layer in h_minus}

            entries.append(
                {
                    "theorem_id": record["theorem_id"],
                    "split": record["split"],
                    "step_index": step_index,
                    "step_text": step_text,
                    "local_sound": int(labels[step_index]),
                    "header_token_count": before["seq_len"],
                    "after_token_count": after["seq_len"],
                    "layers": resolved_layers,
                    "h_minus": h_minus,
                    "h_plus": h_plus,
                    "delta_h": delta_h,
                }
            )
            step_counter += 1
        if args.max_steps is not None and step_counter >= args.max_steps:
            break

    feature_path = output_dir / "boundary_states.pt"
    manifest_path = output_dir / "manifest.json"
    torch.save(entries, feature_path)

    per_layer_dim = {}
    if entries:
        first_entry = entries[0]
        for layer, tensor in first_entry["h_minus"].items():
            per_layer_dim[layer] = int(tensor.shape[0])

    manifest = {
        "input_path": str(input_path),
        "output_dir": str(output_dir),
        "model_path": args.model_path,
        "device": args.device,
        "requested_layers": requested_layers,
        "resolved_layers": resolved_layers,
        "num_hidden_layers": num_hidden_layers,
        "records_loaded": len(records),
        "steps_extracted": len(entries),
        "per_layer_dim": per_layer_dim,
        "feature_path": str(feature_path),
    }
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
