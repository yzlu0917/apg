# CaPS Object-Gate Prompt Protocol

Date: 2026-03-31
Status: frozen for the first Object-gate pilot

## Design principle

Prompt construction is split across three layers:

1. Task-instance layer:
- Procedural and reproducible.
- Source of truth is `Reasoning Gym`.
- Purpose: freeze the problem distribution and keep objective verification.

2. Trace-generation layer:
- Model-generated.
- Purpose: elicit explicit reasoning traces that can later be segmented into steps and intervened on.

3. Semantic-intervention layer:
- Model-generated first, not rule-generated.
- Purpose: create paraphrase and distractor alternatives that preserve or challenge step meaning.

This means the project is not using rules to generate the reasoning object. It uses procedural tasks for reproducible questions and models for the semantic parts that actually matter.

## Frozen family split

High-dependency families:
- `tower_of_hanoi`
- `countdown`

Shallow families:
- `basic_arithmetic`
- `gcd`

Rationale:
- `tower_of_hanoi` and `countdown` are strong candidates for genuinely multi-step dependence.
- `basic_arithmetic` and `gcd` act as shallow controls where large causal-step gains should be weaker.

## Thin wrapper with assistant prefill

Each benchmark instance keeps its original `question` text. The wrapper only standardizes output structure.

```text
You are solving a verifiable reasoning task.

Instructions:
- Think through the task inside <reasoning> tags.
- In <reasoning>, write one short step per line.
- Keep the reasoning concise and causal; avoid filler.
- Do not copy the full final answer into <reasoning>.
- Use <reasoning> for plan, decomposition, or key intermediate checks only.
- Put only the final answer inside <final> tags.
- The content inside <final> must follow the original task formatting instructions exactly.
- Do not repeat the problem statement.

Problem:
{raw_question}

Return exactly:
<reasoning>
...
</reasoning>
<final>
...
</final>
```

Generation control:
- For Qwen3, generation is prefixed from `<reasoning>\n` via the assistant channel.
- This avoids unstable native `<think>` behavior and stabilizes the opening reasoning tag.

## Why this wrapper

- It is thin enough not to rewrite the task distribution.
- It gives a stable container for trace extraction and later step deletion.
- It prevents the final answer formatter from being conflated with free-form reasoning text.
- It reduces truncation risk on long-format answers by forbidding reasoning from duplicating final content.

## What is model-generated

- The reasoning trace inside `<reasoning>`.
- Later paraphrase candidates for a selected step.
- Later distractor candidates for a selected step.

## What is not model-generated

- The underlying task instance.
- The oracle answer.
- The verifier.
- The split assignment.

## Manifest fields

Each manifest row should contain at least:
- `prompt_id`
- `split`
- `difficulty_stratum`
- `family`
- `dataset_seed`
- `source_index`
- `raw_question`
- `oracle_answer`
- `metadata`
- `prompt_template_version`
- `model_prompt`

## Non-goals for the first pilot

- No prompt optimization sweep.
- No family sweep beyond the frozen four families.
- No naturalization pass that rewrites benchmark semantics.

## When to revise this protocol

Only revise if one of the following becomes true:
- The wrapper itself is shown to create strong artifacts.
- The model systematically fails to produce separable reasoning and final-answer tags.
- The chosen families do not behave as intended for high-dependency versus shallow control.
