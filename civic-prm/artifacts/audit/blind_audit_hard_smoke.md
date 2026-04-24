# Blind Audit Packet

The labels are intentionally hidden. Reviewers should judge whether either trace looks artificially templated or obviously synthetic.

## algebra-hard-0000
Domain: algebra
Problem: Determine x if 4(x + 3) - 7 = -11.

### Trace 1
Reasoning 1: after isolating terms, we have 4(x + 3) = -4.
Reasoning 2: after isolating terms, we have x + 3 = -1.
Reasoning 3: after isolating terms, we have x = -4.
Hence x equals -4.

### Trace 2
Reasoning 1: after isolating terms, we have 4(x + 3) = -4.
Reasoning 2: after isolating terms, we have x + 3 = -1.
Reasoning 3: after isolating terms, we have x = -6.
Hence x equals -4.

## algebra-hard-0001
Domain: algebra
Problem: Determine x if 4(x - 4) + 8 = 4.

### Trace 1
Reasoning 1: after isolating terms, we have 4(x - 4) = -4.
Reasoning 2: after isolating terms, we have x - 4 = -1.
Reasoning 3: after isolating terms, we have x = 3.
Hence x equals 3.

### Trace 2
Reasoning 1: after isolating terms, we have 4(x - 4) = -12.
Reasoning 2: after isolating terms, we have x - 4 = -3.
Reasoning 3: after isolating terms, we have x = 1.
Hence x equals 3.

## algebra-hard-0002
Domain: algebra
Problem: Determine x if 5(x - 3) - 1 = -16.

### Trace 1
Reasoning 1: after isolating terms, we have 5(x - 3) = -15.
Reasoning 2: after isolating terms, we have x - 3 = -3.
Reasoning 3: after isolating terms, we have x = 0.
Hence x equals 0.

### Trace 2
Reasoning 1: after isolating terms, we have 5(x - 3) = -15.
Reasoning 2: after isolating terms, we have x - 3 = -3.
Reasoning 3: after isolating terms, we have x = 2.
Hence x equals 0.

## algebra-hard-0003
Domain: algebra
Problem: Determine x if 2(x - 3) - 1 = -1.

### Trace 1
Reasoning 1: after isolating terms, we have 2(x - 3) = 0.
Reasoning 2: after isolating terms, we have x - 3 = 0.
Reasoning 3: after isolating terms, we have x = 3.
Hence x equals 3.

### Trace 2
Reasoning 1: after isolating terms, we have 2(x - 3) = 0.
Reasoning 2: after isolating terms, we have x - 3 = 0.
Reasoning 3: after isolating terms, we have x = 1.
Hence x equals 3.

## blocksworld-hard-0000
Domain: blocksworld
Problem: Transform [B] [C A] [D] into [C D A B] using legal top-block moves.

### Trace 1
Reasoning 1: move block A onto block B, reaching state [B A] [C] [D].
Reasoning 2: move block D onto block C, reaching state [B A] [C D].
Reasoning 3: move block A onto block D, reaching state [B] [C D A].
Reasoning 4: move block B onto block A, reaching state [C D A B].
Hence the target state is [C D A B].

### Trace 2
Reasoning 1: move block B onto block D, reaching state [C A] [D B].
Reasoning 2: move block A to the table, reaching state [A] [C] [D B].
Reasoning 3: move block B onto block C, reaching state [A] [C B] [D].
Reasoning 4: move block A onto block B, reaching state [C B A] [D].
Hence the target state is [C D A B].

## blocksworld-hard-0001
Domain: blocksworld
Problem: Transform [C A D B] into [B] [C D A] using legal top-block moves.

### Trace 1
Reasoning 1: move block B to the table, reaching state [B] [C A D].
Reasoning 2: move block D onto block B, reaching state [B D] [C A].
Reasoning 3: move block A to the table, reaching state [A] [B D] [C].
Reasoning 4: move block D onto block C, reaching state [A] [B] [C D].
Reasoning 5: move block A onto block D, reaching state [B] [C D A].
Hence the target state is [B] [C D A].

### Trace 2
Reasoning 1: move block B to the table, reaching state [B] [C A D].
Reasoning 2: move block D onto block B, reaching state [B D] [C A].
Reasoning 3: move block A to the table, reaching state [A] [B D] [C].
Reasoning 4: move block A onto block C, reaching state [B D] [C A].
Reasoning 5: move block D onto block A, reaching state [B] [C A D].
Hence the target state is [B] [C D A].
