# Object Gate Artifact Checklist

Date: 2026-03-31

This checklist is used during review before a pair can enter the frozen dev
panel.

## Global checks

- Can the gold action be guessed from a metadata field or template phrase alone?
- Does the keep example always have a noticeably different style or length from
  the revise example?
- Is the repair suffix merely a label hint rather than a usable correction?
- Does the pair collapse to raw correctness without testing local revision
  behavior?

## `sym`

- Is the fail span a real local arithmetic or logic step, not just the final
  answer token?
- Does the repair suffix correct the local step and the downstream conclusion?
- Are we overusing trivial one-step arithmetic where revision is equivalent to
  final-answer replacement?

## `code`

- Is the fail span at least line-level or expression-level, not a single token
  that makes localization brittle?
- Does the unit test actually fail on the revise example and pass on the keep
  example?
- Is the repair suffix a real corrected line or continuation, not an isolated
  fragment that depends on hidden context?

## `plan`

- Does the checker describe explicit constraints instead of merely rephrasing
  the gold order?
- Is the violation local enough that a swap or suffix repair is plausible?
- Are we accidentally making revise identical to "sort steps into canonical
  order" without meaningful local structure?
