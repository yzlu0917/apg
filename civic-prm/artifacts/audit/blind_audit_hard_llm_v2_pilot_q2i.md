# Blind Audit Packet

The labels are intentionally hidden.

Review prompt:
- Do not judge which trace is correct.
- Only judge whether either trace looks artificially templated, hand-edited, or obviously synthetic.
- For each item, mark one option: `Trace 1`, `Trace 2`, `Both`, or `Neither`.
- Add a short note only if something looked suspicious.

## item-01 | blocksworld-hard-0008
Domain: blocksworld
Problem: Transform [A D] [C B] into [C A B D] using legal top-block moves.

### Trace 1
D is moved to the table, giving [A] [C B] [D].
B is placed onto D, resulting in [A] [C] [D B].
A is moved onto C, producing [C A] [D B].
B is placed onto A, yielding [C A B] [D].
D is moved onto B, achieving the goal state [C A B D].
Hence the target state is [C A B D].

### Trace 2
D is moved to the table, resulting in [A] [C B] [D].
B is moved to the table, resulting in [A] [B] [C] [D].
A is placed onto C, resulting in [B] [C A] [D].
B is placed onto A, resulting in [C A B] [D].
D is placed onto B, reaching the goal state [C A B D].
Hence the target state is [C A B D].

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-02 | graph-hard-0007
Domain: graph_path
Problem: Check the candidate three-edge routes from S to T: S->E has weight 5, E->F has weight 3, F->T has weight 2; S->G has weight 3, G->H has weight 7, H->T has weight 2; S->A has weight 6, A->B has weight 7, B->T has weight 1; S->C has weight 6, C->D has weight 7, D->T has weight 3.

### Trace 1
Route S → E → F → T yields a total cost of 10.
Along S → G → H → T, the sum becomes 12.
For path S → A → B → T, the recorded total is 14.
Traveling S → C → D → T gives a cost of 16.
Comparing the four totals—10, 12, 14, and 16—the cheapest route is S → E → F → T.
So the best route is S -> E -> F -> T with total cost 10.

### Trace 2
The route S to T via E and F has a total cost of 10.
The route S -> G -> H -> T has a total cost of 12.
The route from S -> A -> B -> T has a total cost of 14.
The route S to T via C and D has a total cost of 17.
The three-edge routes from S to T have totals: S->E->F->T is 10, S->G->H->T is 12, S->A->B->T is 14, and S->C->D->T is 17, so the cheapest route is S -> E -> F -> T.
So the best route is S -> E -> F -> T with total cost 10.

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-03 | blocksworld-hard-0000
Domain: blocksworld
Problem: Plan block moves from start [D B A C] to goal [B] [D A C].

### Trace 1
Block C is moved to the table, resulting in [C] [D B A].
Block A is moved to the table, giving [A] [C] [D B].
Block B is moved to the table, producing [A] [B] [C] [D].
Block A is placed onto block D, leading to [B] [C] [D A].
Block C is placed onto block A, achieving the goal state [B] [D A C].
So the final state is [B] [D A C].

### Trace 2
Block C is moved to the table, producing the state [C] [D B A].
Block A is placed onto block C, giving [C A] [D B].
Block B is moved to the table, resulting in [B] [C A] [D].
Block A is moved onto block D, yielding [B] [C] [D A].
Block C is placed onto block A, achieving the goal state [B] [D A C].
So the final state is [B] [D A C].

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:

## item-04 | graph-hard-0006
Domain: graph_path
Problem: Compute the cheapest way to go from S to T among the four listed three-hop routes.

### Trace 1
First, examine the route S → C → D → T, which has a total cost of 8.
Next, consider the path S → E → F → T, whose cost sums to 10.
Looking at the route S → G → H → T, the total cost comes out to 12.
Finally, the route S → A → B → T yields a total cost of 15.
Comparing all four totals—8 for C‑D, 10 for E‑F, 12 for G‑H, and 15 for A‑B—the least expensive is S → C → D → T.
Hence the shortest path is S -> C -> D -> T with total cost 8.

### Trace 2
The route S → C → D → T has a total cost of 8.
The route S → E → F → T has a total cost of 10.
The route S → G → H → T has a total cost of 12.
The route S → A → B → T has a total cost of 16.
Comparing the totals—C‑D: 8, E‑F: 10, G‑H: 12, A‑B: 16—the cheapest route is S → C → D → T.
Hence the shortest path is S -> C -> D -> T with total cost 8.

Reviewer response:
- More artificial: `Trace 1` / `Trace 2` / `Both` / `Neither`
- Confidence: `1` / `2` / `3` / `4` / `5`
- Notes:
