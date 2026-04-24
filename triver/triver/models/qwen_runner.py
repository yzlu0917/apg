from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class GenerationResult:
    text: str
    new_tokens: int


class QwenRunner:
    def __init__(
        self,
        model_path: str,
        dtype: str = "bfloat16",
        device_map: str = "auto",
    ) -> None:
        self.model_path = model_path
        self.dtype = dtype
        self.device_map = device_map
        self._tokenizer = None
        self._model = None

    @property
    def tokenizer(self):
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
        return self._tokenizer

    @property
    def model(self):
        if self._model is None:
            from transformers import AutoModelForCausalLM
            import torch

            dtype = getattr(torch, self.dtype)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                dtype=dtype,
                device_map=self.device_map,
                trust_remote_code=True,
            )
            self._model.eval()
        return self._model

    def count_tokens(self, text: str) -> int:
        return len(self.tokenizer(text, add_special_tokens=False)["input_ids"])

    def _render_prompt(
        self,
        prompt: str | list[dict[str, str]],
        add_generation_prompt: bool = True,
    ) -> str:
        if isinstance(prompt, str):
            return prompt
        return self.tokenizer.apply_chat_template(
            prompt,
            tokenize=False,
            add_generation_prompt=add_generation_prompt,
            enable_thinking=False,
        )

    def generate(
        self,
        prompt: str | list[dict[str, str]],
        max_new_tokens: int,
        num_return_sequences: int = 1,
        temperature: float = 0.7,
        top_p: float = 0.9,
        seed: int | None = None,
    ) -> list[GenerationResult]:
        import torch

        if seed is not None:
            torch.manual_seed(seed)

        tokenizer = self.tokenizer
        model = self.model
        rendered_prompt = self._render_prompt(prompt, add_generation_prompt=True)
        inputs = tokenizer(rendered_prompt, return_tensors="pt").to(model.device)

        generate_kwargs = {
            "max_new_tokens": max_new_tokens,
            "num_return_sequences": num_return_sequences,
            "pad_token_id": tokenizer.eos_token_id,
            "eos_token_id": tokenizer.eos_token_id,
        }
        if temperature > 0:
            generate_kwargs.update(
                {
                    "do_sample": True,
                    "temperature": temperature,
                    "top_p": top_p,
                }
            )
        else:
            generate_kwargs["do_sample"] = False

        with torch.inference_mode():
            sequences = model.generate(**inputs, **generate_kwargs)

        prompt_length = inputs["input_ids"].shape[1]
        generated = sequences[:, prompt_length:]
        texts = tokenizer.batch_decode(
            generated,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )
        return [
            GenerationResult(
                text=text,
                new_tokens=self.count_tokens(text),
            )
            for text in texts
        ]

    def prompt_embedding(
        self,
        prompt: str | list[dict[str, str]],
        strategy: str = "last_generation_prompt",
    ) -> np.ndarray:
        import torch

        tokenizer = self.tokenizer
        model = self.model
        content_strategies = {"last_content", "mean_content", "last_and_mean_content"}
        rendered_prompt = self._render_prompt(
            prompt,
            add_generation_prompt=strategy not in content_strategies,
        )
        inputs = tokenizer(rendered_prompt, return_tensors="pt").to(model.device)
        with torch.inference_mode():
            outputs = model(**inputs, output_hidden_states=True, use_cache=False, return_dict=True)
        hidden = outputs.hidden_states[-1][0]
        attention_mask = inputs["attention_mask"][0].to(dtype=torch.bool)
        visible_hidden = hidden[attention_mask]
        if visible_hidden.numel() == 0:
            raise ValueError("Prompt produced no visible tokens")

        if strategy in {"last_generation_prompt", "last_content"}:
            embedding = visible_hidden[-1]
        elif strategy == "mean_content":
            embedding = visible_hidden.mean(dim=0)
        elif strategy == "last_and_mean_content":
            embedding = torch.cat([visible_hidden[-1], visible_hidden.mean(dim=0)], dim=0)
        else:
            raise ValueError(f"Unsupported embedding strategy: {strategy}")
        return embedding.detach().float().cpu().numpy()

    def last_hidden_state(self, prompt: str | list[dict[str, str]]) -> np.ndarray:
        return self.prompt_embedding(prompt, strategy="last_generation_prompt")
