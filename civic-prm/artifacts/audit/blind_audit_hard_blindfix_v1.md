# Blind Audit Packet

The labels are intentionally hidden.

Review prompt:
- Do not judge which trace is correct.
- Only judge whether either trace looks artificially templated, hand-edited, or obviously synthetic.
- For each item, mark one option: `Trace 1`, `Trace 2`, `Both`, or `Neither`.
- Add a short note only if something looked suspicious.

## item-01 | algebra-hard-0008
Domain: algebra
Problem: Determine x if 6(x + 4) + 2 = 14.

### Trace 1
Reasoning 1: after isolating terms, we have 6(x + 4) = 12.
Reasoning 2: after isolating terms, we have x + 4 = 2.
Reasoning 3: after isolating terms, we have x = -2.
Hence x equals -2.

### Trace 2
Reasoning 1: after isolating terms, we have 6(x + 4) = 12.
Reasoning 2: after isolating terms, we have x + 4 = 3.
Reasoning 3: after isolating terms, we have x = -2.
Hence x equals -2.

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-02 | blocksworld-hard-0002
Domain: blocksworld
Problem: Plan block moves from start [A B D C] to goal [C A B] [D].

### Trace 1
Move 1: move block C to the table, reaching state [A B D] [C].
Move 2: move block D to the table, reaching state [A B] [C] [D].
Move 3: move block B onto block D, reaching state [A] [C] [D B].
Move 4: move block A onto block C, reaching state [C A] [D B].
Move 5: move block B onto block A, reaching state [C A B] [D].
So the final state is [C A B] [D].

### Trace 2
Move 1: move block C to the table, reaching state [A B D] [C].
Move 2: move block D to the table, reaching state [A B] [C] [D].
Move 3: move block B to the table, reaching state [A] [B] [C] [D].
Move 4: move block A onto block C, reaching state [B] [C A] [D].
Move 5: move block B onto block A, reaching state [C A B] [D].
So the final state is [C A B] [D].

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-03 | graph-hard-0003
Domain: graph_path
Problem: Check the candidate three-edge routes from S to T: S->C has weight 6, C->D has weight 6, D->T has weight 1; S->A has weight 5, A->B has weight 5, B->T has weight 6; S->E has weight 4, E->F has weight 7, F->T has weight 7; S->G has weight 7, G->H has weight 6, H->T has weight 7.

### Trace 1
Candidate 1: The route S -> C -> D -> T costs 6 + 6 + 1 = 13.
Candidate 2: The route S -> A -> B -> T costs 5 + 5 + 6 = 16.
Candidate 3: The route S -> E -> F -> T costs 4 + 7 + 7 = 18.
Candidate 4: The route S -> G -> H -> T costs 7 + 6 + 7 = 20.
Candidate 5: Comparing totals C-D:13, A-B:16, E-F:18, G-H:22, the cheapest route is S -> C -> D -> T.
So the best route is S -> C -> D -> T with total cost 13.

### Trace 2
Candidate 1: The route S -> C -> D -> T costs 6 + 6 + 1 = 13.
Candidate 2: The route S -> A -> B -> T costs 5 + 5 + 6 = 16.
Candidate 3: The route S -> E -> F -> T costs 4 + 7 + 7 = 18.
Candidate 4: The route S -> G -> H -> T costs 7 + 6 + 7 = 20.
Candidate 5: Comparing totals C-D:13, A-B:16, E-F:18, G-H:20, the cheapest route is S -> C -> D -> T.
So the best route is S -> C -> D -> T with total cost 13.

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-04 | algebra-hard-0006
Domain: algebra
Problem: Determine x if 6(x + 4) + 5 = 11.

### Trace 1
Reasoning 1: after isolating terms, we have 6(x + 4) = 6.
Reasoning 2: after isolating terms, we have x + 4 = 1.
Reasoning 3: after isolating terms, we have x = -3.
Hence x equals -3.

### Trace 2
Reasoning 1: after isolating terms, we have 6(x + 4) = 6.
Reasoning 2: after isolating terms, we have x + 4 = 3.
Reasoning 3: after isolating terms, we have x = -3.
Hence x equals -3.

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-05 | blocksworld-hard-0003
Domain: blocksworld
Problem: Starting from [A D] [B C], reach the goal state [C B A] [D].

### Trace 1
Step 1: move block C to the table, reaching state [A D] [B] [C].
Step 2: move block B onto block C, reaching state [A D] [C B].
Step 3: move block D to the table, reaching state [A] [C B] [D].
Step 4: move block A onto block B, reaching state [C B A] [D].
Final answer: the plan reaches [C B A] [D].

### Trace 2
Step 1: move block D to the table, reaching state [A] [B C] [D].
Step 2: move block C to the table, reaching state [A] [B] [C] [D].
Step 3: move block B onto block C, reaching state [A] [C B] [D].
Step 4: move block A onto block B, reaching state [C B A] [D].
Final answer: the plan reaches [C B A] [D].

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-06 | graph-hard-0006
Domain: graph_path
Problem: In the weighted graph with candidate routes S-C:5, C-D:1, D-T:2, S-E:5, E-F:3, F-T:2, S-G:6, G-H:5, H-T:1, S-A:7, A-B:6, B-T:2, find the shortest path from S to T.

### Trace 1
Step 1: The route S -> C -> D -> T costs 5 + 1 + 2 = 8.
Step 2: The route S -> E -> F -> T costs 5 + 3 + 2 = 10.
Step 3: The route S -> G -> H -> T costs 6 + 5 + 1 = 12.
Step 4: The route S -> A -> B -> T costs 7 + 6 + 2 = 15.
Step 5: Comparing totals C-D:8, E-F:10, G-H:12, A-B:15, the cheapest route is S -> C -> D -> T.
Final answer: S -> C -> D -> T with total cost 8.

### Trace 2
Step 1: The route S -> C -> D -> T costs 5 + 1 + 2 = 8.
Step 2: The route S -> E -> F -> T costs 5 + 3 + 2 = 10.
Step 3: The route S -> G -> H -> T costs 6 + 5 + 1 = 12.
Step 4: The route S -> A -> B -> T costs 7 + 6 + 2 = 15.
Step 5: Comparing totals C-D:8, E-F:10, G-H:12, A-B:16, the cheapest route is S -> C -> D -> T.
Final answer: S -> C -> D -> T with total cost 8.

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-07 | algebra-hard-0004
Domain: algebra
Problem: Determine x if 4(x - 2) - 5 = -13.

### Trace 1
Reasoning 1: after isolating terms, we have 4(x - 2) = -8.
Reasoning 2: after isolating terms, we have x - 2 = -2.
Reasoning 3: after isolating terms, we have x = 0.
Hence x equals 0.

### Trace 2
Reasoning 1: after isolating terms, we have 4(x - 2) = -8.
Reasoning 2: after isolating terms, we have x - 2 = -3.
Reasoning 3: after isolating terms, we have x = 0.
Hence x equals 0.

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-08 | blocksworld-hard-0011
Domain: blocksworld
Problem: Plan block moves from start [C] [D B A] to goal [B A D] [C].

### Trace 1
Move 1: move block A onto block C, reaching state [C A] [D B].
Move 2: move block B to the table, reaching state [B] [C A] [D].
Move 3: move block A onto block B, reaching state [B A] [C] [D].
Move 4: move block D onto block A, reaching state [B A D] [C].
So the final state is [B A D] [C].

### Trace 2
Move 1: move block A to the table, reaching state [A] [C] [D B].
Move 2: move block B to the table, reaching state [A] [B] [C] [D].
Move 3: move block A onto block B, reaching state [B A] [C] [D].
Move 4: move block D onto block A, reaching state [B A D] [C].
So the final state is [B A D] [C].

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-09 | graph-hard-0010
Domain: graph_path
Problem: Compute the cheapest way to go from S to T among the four listed three-hop routes.

### Trace 1
Reasoning 1: The route S -> G -> H -> T costs 1 + 6 + 2 = 9.
Reasoning 2: The route S -> A -> B -> T costs 6 + 3 + 1 = 10.
Reasoning 3: The route S -> E -> F -> T costs 4 + 4 + 6 = 14.
Reasoning 4: The route S -> C -> D -> T costs 7 + 6 + 4 = 17.
Reasoning 5: Comparing totals G-H:9, A-B:10, E-F:14, C-D:17, the cheapest route is S -> G -> H -> T.
Hence the shortest path is S -> G -> H -> T with total cost 9.

### Trace 2
Reasoning 1: The route S -> G -> H -> T costs 1 + 6 + 2 = 9.
Reasoning 2: The route S -> A -> B -> T costs 6 + 3 + 1 = 12.
Reasoning 3: The route S -> E -> F -> T costs 4 + 4 + 6 = 14.
Reasoning 4: The route S -> C -> D -> T costs 7 + 6 + 4 = 17.
Reasoning 5: Comparing totals G-H:9, A-B:12, E-F:14, C-D:17, the cheapest route is S -> G -> H -> T.
Hence the shortest path is S -> G -> H -> T with total cost 9.

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:
