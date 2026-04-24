# Object Gate Review Queue

Pairs: 3

Review each pair against the checklist below.

## Checklist

- `label_clear`: Is the gold action objectively defensible from the checker?
- `localizable`: Is the fail span local enough for suffix-style repair?
- `repair_plausible`: Is the proposed repair suffix plausible and minimal?
- `not_plain_correctness`: Does this test verifier-mediated action rather than only answer correctness?

## code_pair_0_seed_31

### keep_example_0

- Domain: `code`
- Action: `keep`
- Question: Write a function `max_of_three` that takes three integers and returns the largest of them.
- Fail span: ``
- Repair suffix: (empty)
- Checker: `unit_test` / `assert max_of_three(1, 2, 3) == 3; assert max_of_three(-5, 0, 5) == 5`
- Notes: Correct implementation.

### revise_example_0

- Domain: `code`
- Action: `revise`
- Question: Write a function `max_of_three` that takes three integers and returns the largest of them.
- Fail span: `return a`
- Repair suffix: return c
- Checker: `unit_test` / `assert max_of_three(1, 2, 3) == 3; assert max_of_three(-5, 0, 5) == 5`
- Notes: Bug: final else returns 'a' instead of 'c'. Local fix changes one token.

Reviewer verdict:

- `label_clear`: pending
- `localizable`: pending
- `repair_plausible`: pending
- `not_plain_correctness`: pending
- Notes: 


## plan_pair_0

### plan_keep_0

- Domain: `plan`
- Action: `keep`
- Question: Arrange the steps to bake a cake in the correct order.
- Fail span: ``
- Repair suffix: (empty)
- Checker: `constraint_check` / `Preheat before mixing; mix before combining; combine before pouring; pour before baking; bake before cooling; cooling before frosting.`
- Notes: Correct ordering with no violations.

### plan_revise_0

- Domain: `plan`
- Action: `revise`
- Question: Arrange the steps to bake a cake in the correct order.
- Fail span: `Pour batter into pan.`
- Repair suffix: Combine wet and dry mixtures before pouring batter into pan.
- Checker: `constraint_check` / `Preheat before mixing; mix before combining; combine before pouring; pour before baking; bake before cooling; cooling before frosting.`
- Notes: Local swap of steps 4 and 5 violates that batter must be combined before pouring.

Reviewer verdict:

- `label_clear`: pending
- `localizable`: pending
- `repair_plausible`: pending
- `not_plain_correctness`: pending
- Notes: 


## sym_pair_0

### keep_0

- Domain: `sym`
- Action: `keep`
- Question: What is the result of 15 plus 7 multiplied by 2?
- Fail span: ``
- Repair suffix: (empty)
- Checker: `exact_match` / `29`
- Notes: Correct application of order of operations.

### revise_0

- Domain: `sym`
- Action: `revise`
- Question: What is the result of 15 plus 7 multiplied by 2?
- Fail span: `We do addition first: 15 plus 7 is 22.`
- Repair suffix: We follow the order of operations: multiplication before addition. 7 multiplied by 2 is 14. Then 15 plus 14 is 29.
- Checker: `exact_match` / `29`
- Notes: Local arithmetic/logic error: incorrect order of operations.

Reviewer verdict:

- `label_clear`: pending
- `localizable`: pending
- `repair_plausible`: pending
- `not_plain_correctness`: pending
- Notes: 

