# Object Gate Review Queue

Pairs: 6

Review each pair against the checklist below.

## Checklist

- `label_clear`: Is the gold action objectively defensible from the checker?
- `localizable`: Is the fail span local enough for suffix-style repair?
- `repair_plausible`: Is the proposed repair suffix plausible and minimal?
- `not_plain_correctness`: Does this test verifier-mediated action rather than only answer correctness?

## code_pair_0

### keep_0

- Domain: `code`
- Action: `keep`
- Question: Write a function that returns the sum of the squares of two numbers.
- Fail span: ``
- Repair suffix: (empty)
- Checker: `unit_test` / `assert sum_of_squares(3, 4) == 25
assert sum_of_squares(0, 5) == 25`
- Notes: Correct implementation.

### revise_0

- Domain: `code`
- Action: `revise`
- Question: Write a function that returns the sum of the squares of two numbers.
- Fail span: `b`
- Repair suffix: **2
- Checker: `unit_test` / `assert sum_of_squares(3, 4) == 25
assert sum_of_squares(0, 5) == 25`
- Notes: Missing exponent on b, local fix by adding **2.

Reviewer verdict:

- `label_clear`: pending
- `localizable`: pending
- `repair_plausible`: pending
- `not_plain_correctness`: pending
- Notes: 


## code_pair_1_seed_32

### keep_example_1

- Domain: `code`
- Action: `keep`
- Question: Write a function `is_positive_even` that takes an integer and returns True if it is both positive and even, otherwise False.
- Fail span: ``
- Repair suffix: (empty)
- Checker: `unit_test` / `assert is_positive_even(2) == True
assert is_positive_even(1) == False
assert is_positive_even(-2) == False
assert is_positive_even(0) == False`
- Notes: Correct implementation.

### revise_example_1

- Domain: `code`
- Action: `revise`
- Question: Write a function `is_positive_even` that takes an integer and returns True if it is both positive and even, otherwise False.
- Fail span: `n % 2 != 0`
- Repair suffix: == 0
- Checker: `unit_test` / `assert is_positive_even(2) == True
assert is_positive_even(1) == False
assert is_positive_even(-2) == False
assert is_positive_even(0) == False`
- Notes: Bug: uses '!=' instead of '==', making it check for odd numbers. Local fix: change '!=' to '=='.

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
- Question: You are a chef preparing a three-course meal: appetizer, main course, and dessert. The appetizer must be served first, the main course second, and the dessert last. You have the following tasks: 1. Prepare salad (appetizer), 2. Cook steak (main course), 3. Bake cake (dessert), 4. Serve salad, 5. Serve steak, 6. Serve cake. Provide a valid sequence of these tasks respecting the course order.
- Fail span: ``
- Repair suffix: (empty)
- Checker: `constraint_check` / `Tasks must be ordered such that each course's preparation (if any) occurs before its serving, and courses are served in order: appetizer (salad), main (steak), dessert (cake).`
- Notes: Valid sequence: all preparations before corresponding servings, and serving order matches course order.

### plan_revise_0

- Domain: `plan`
- Action: `revise`
- Question: You are a chef preparing a three-course meal: appetizer, main course, and dessert. The appetizer must be served first, the main course second, and the dessert last. You have the following tasks: 1. Prepare salad (appetizer), 2. Cook steak (main course), 3. Bake cake (dessert), 4. Serve salad, 5. Serve steak, 6. Serve cake. Provide a valid sequence of these tasks respecting the course order.
- Fail span: `Serve steak`
- Repair suffix: 4. Serve salad
5. Serve steak
6. Serve cake
- Checker: `constraint_check` / `Tasks must be ordered such that each course's preparation (if any) occurs before its serving, and courses are served in order: appetizer (salad), main (steak), dessert (cake).`
- Notes: Local fix: swap 'Serve steak' and 'Serve salad' to correct the appetizer/main serving order.

Reviewer verdict:

- `label_clear`: pending
- `localizable`: pending
- `repair_plausible`: pending
- `not_plain_correctness`: pending
- Notes: 


## plan_pair_1_seed_32

### plan_keep_1

- Domain: `plan`
- Action: `keep`
- Question: Plan the morning routine for getting ready for school. The routine must include: wake up, eat breakfast, brush teeth, pack backpack, and leave house. The correct order must satisfy: wake up first, eat breakfast before brushing teeth, and pack backpack before leaving house.
- Fail span: ``
- Repair suffix: (empty)
- Checker: `constraint_check` / `wake up first; eat breakfast before brush teeth; pack backpack before leave house`
- Notes: All ordering constraints are satisfied.

### plan_revise_1

- Domain: `plan`
- Action: `revise`
- Question: Plan the morning routine for getting ready for school. The routine must include: wake up, eat breakfast, brush teeth, pack backpack, and leave house. The correct order must satisfy: wake up first, eat breakfast before brushing teeth, and pack backpack before leaving house.
- Fail span: `brush teeth
3. eat breakfast`
- Repair suffix: 2. eat breakfast
3. brush teeth
- Checker: `constraint_check` / `wake up first; eat breakfast before brush teeth; pack backpack before leave house`
- Notes: Local swap of steps 2 and 3 fixes the ordering violation; other constraints remain satisfied.

Reviewer verdict:

- `label_clear`: pending
- `localizable`: pending
- `repair_plausible`: pending
- `not_plain_correctness`: pending
- Notes: 


## sym_0_31

### sym_0_31_keep

- Domain: `sym`
- Action: `keep`
- Question: What is the result of (8 + 4) * 2 - 10?
- Fail span: ``
- Repair suffix: (empty)
- Checker: `exact_match` / `14`
- Notes: Correct arithmetic steps.

### sym_0_31_revise

- Domain: `sym`
- Action: `revise`
- Question: What is the result of (8 + 4) * 2 - 10?
- Fail span: `24 - 10 = 16`
- Repair suffix: 24 - 10 = 14. The answer is 14.
- Checker: `exact_match` / `14`
- Notes: Local arithmetic error in subtraction (24 - 10 = 16 instead of 14).

Reviewer verdict:

- `label_clear`: pending
- `localizable`: pending
- `repair_plausible`: pending
- `not_plain_correctness`: pending
- Notes: 


## sym_1_32

### sym_1_32_keep

- Domain: `sym`
- Action: `keep`
- Question: What is the result of (15 + 7) * 2?
- Fail span: ``
- Repair suffix: (empty)
- Checker: `exact_match` / `44`
- Notes: Correct arithmetic steps.

### sym_1_32_revise

- Domain: `sym`
- Action: `revise`
- Question: What is the result of (15 + 7) * 2?
- Fail span: `22 * 2 = 46`
- Repair suffix: should be 44.
- Checker: `exact_match` / `44`
- Notes: Local arithmetic error: 22 * 2 is 44, not 46.

Reviewer verdict:

- `label_clear`: pending
- `localizable`: pending
- `repair_plausible`: pending
- `not_plain_correctness`: pending
- Notes: 

