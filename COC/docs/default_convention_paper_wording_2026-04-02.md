# Default-Convention Boundary Paper Wording 2026-04-02

## Abstract-Scale Option

We identify a narrow frontier-hard evaluator boundary in which the judge rewards answers that silently adopt common source-unit or date-format defaults, instead of rewarding answers that surface the missing convention.

## Intro-Scale Option

Average judge accuracy can hide a narrower failure mode: even strong judges may over-reward direct answers that rely on culturally common but unstated conventions. We isolate this boundary in prompts where the missing convention changes the concrete output, such as source-unit defaults and compact ambiguous date formats.

## Short Claim Option

Strong judges can still fail when correctness depends on refusing an unstated default convention.

## Caption-Scale Option

`default-convention boundary`: paired items where the direct answer relies on a common but unstated source-unit or date-format convention, while the better answer first exposes the missing convention.

## Anti-Overclaim Reminder

Avoid saying:
- judges broadly fail to clarify ambiguity
- all underspecification is hard
- multi-judge already solves this boundary

Prefer saying:
- we identify a narrow audited boundary
- the strongest current judge still misses non-trivially on this slice
- current evidence is strongest for `source_unit_missing` and compact `date_convention_missing`


## Updated Read After v8

Current safest one-sentence version:

> We identify a narrow frontier-hard evaluator boundary in which even strong judges reward direct answers that silently adopt common source-unit or date-format defaults, rather than answers that surface the missing convention.

Current safest short evidence tag:

- strongest current evidence: `source_unit_missing` plus compact `date_convention_missing`
