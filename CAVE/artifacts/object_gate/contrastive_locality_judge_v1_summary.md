# Contrastive Locality Judge Summary

Pairs judged: `10`
Verdicts: `{'accept': 10}`

## Per Pair

### code_contrastive_locality_0

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Good example of a simple local bug with plausible wrong fixes.

### code_contrastive_locality_1202_harder_1

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Good example of a local logical error with a clear, minimal fix. The checker's specific numeric answer disambiguates the correct repair from other plausible ones like 'and'.

### plan_contrastive_locality_0

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Strong example. The error is clear, the checker is precise, and the repair is a direct, local fix.

### plan_contrastive_locality_1202_harder

- Source: `artifacts/object_gate/batch11_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Pair cleanly instantiates the family. The error is local, the checker is clear, and there is a nearby plausible wrong repair (swap steps 2 and 3) that the checker would reject.

### code_contrastive_locality_1301_harder

- Source: `artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Pair cleanly instantiates the family. The checker does not disambiguate between '==1' and '!=0', but both are correct and local, fitting the family's requirement of at least one nearby plausible repair.

### plan_contrastive_locality_0

- Source: `artifacts/object_gate/batch12_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: The pair cleanly instantiates the family: a local optimization error with a clear, checker-disambiguated repair.

### code_1501_0

- Source: `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Good contrastive_locality example: local arithmetic operator error with multiple plausible wrong fixes.

### plan_1501_0

- Source: `artifacts/object_gate/batch14_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Pair cleanly instantiates contrastive_locality: local error, plausible alternative repairs, checker disambiguates.

### code_1601_0

- Source: `artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Well-formed contrastive locality pair with clear local error and disambiguating checker.

### plan_1601_harder_contrastive

- Source: `artifacts/object_gate/batch15_contrastive_locality_candidates.jsonl`
- Verdict: `accept`
- Checks: `{'same_task_local_error': 'pass', 'checker_disambiguates_repairs': 'pass', 'gold_repair_informative': 'pass', 'retry_vulnerable': 'pass'}`
- Blocking issues: `[]`
- Notes: Well-constructed pair with clear local error and plausible alternative repairs that are invalidated by the checker.
