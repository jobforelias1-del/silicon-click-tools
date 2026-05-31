# Sequential arrangement schema — architecture decisions

> Decisions locked for the Pression Archivée schema rewrite (mission Phase 2),
> greenlit 2026-05-31. Phase 2 builds from *this file*, not from chat memory.
> Phase 1 (bridge follow-action plumbing) feeds decision #1 with an empirical
> answer before Phase 2 commits code.

## Context

The arrangement model is moving from **positional** (every note carries an
absolute `start` beat; sections are implicit) to **sequential** (each section
declares a `length` and a `follow_action`; absolute beat positions are
*computed*). This mirrors how Ableton Live's Session view actually sequences a
song via scene follow-actions, and it lets a section repeat or branch without
re-authoring note positions.

## Decision 1 — `repeat_count` is tooling-expanded, NOT authored as Jump-to-self

A section that plays N times is authored as:

```yaml
- name: CHORUS
  length: "8.0.0"        # bars.beats.sixteenths (canonical unit TBD in Phase 2)
  repeat_count: 2         # default 1
  follow_action_a: Next
```

The **tooling expands** `repeat_count: N` at apply-time into Live's native
mechanism — `follow_action: Play Again` for (N-1) iterations, then the authored
`follow_action_a`. The authored schema never contains a self-Jump.

Rationale: the manual's "repeat a scene" trick (a self-Jump with a loop counter)
overloads the Jump target, collides with genuine structural jumps, and makes the
audit's "do jump targets resolve?" check ambiguous (structural jump vs.
repeat-counter artifact). Keeping `repeat_count` as a first-class authored field
and `jump_target` reserved for **genuine structural jumps only** keeps both
unambiguous.

**Empirical refinement (Phase 1 answers first):** introspect whether the LOM
exposes a real **scene-level loop/repeat count**. If it does, `repeat_count` maps
directly to that property and no Play-Again expansion is needed — even cleaner.
If it does **not**, use the Play-Again expansion above. Do not assume; Phase 1's
live introspection decides which branch ships.

## Decision 2 — computed beat positions are a DERIVED, AUDITED value

`sc-produce` computes each section's absolute start beat (and therefore each
note's absolute position) from the sequential `length` chain. This computed value
is **not** authored, but it **is** retained and audited.

The audit must cross-check: a note whose `start` lands beyond its section's
`length` is a bug (a note at beat 80 inside a 38-beat section). The positional
model caught this implicitly; the sequential model must catch it explicitly, or
the error hides. So: compute positions → validate every note fits its section →
flag overflows as findings.

## Decision 3 — reject mismatched-type ops; the audit finding IS the bug report

Per the kick-back-to-writer doctrine, the audit does **not** interpret an op that
mismatches its declared track type (MIDI on an `audio` track, etc.). It rejects
it. Crucially, each rejection finding carries the **upstream fix** inline:

- the offending `(scene/section, track)`,
- the track's declared type,
- what the writer must do (re-type the track, re-author as an audio cue, or omit).

So the audit's output can be handed to the writer (Mistral) verbatim as the bug
report — no human re-typing the findings into a prose brief. (The Phase 0
disambiguation brief did this by hand once; from here the audit emits it.)

## Decision 4 — sequential length sanity + jump-target resolution

The audit also validates:
- the sequential `length`s sum to a sensible total song length (flag absurd
  totals — e.g. a section length of 0, or a song that's 4 bars or 4 hours);
- every `jump_target` (and `follow_action: Jump`/`Other` target) names an
  **existing** section; dangling targets are errors.

## Schema sketch (subject to Phase 0 answers + Phase 1 property names)

```yaml
sections:
  - name: INTRO
    length: "9.2.0"          # canonical unit decided in Phase 2 (bars.beats.16ths leading candidate)
    repeat_count: 1
    follow_action_a: Next
    chance_a: 100
    follow_action_b: No Action
    chance_b: 0
    # jump_target_a / jump_target_b: only when follow_action is Jump
enable_follow_actions: true   # global toggle (Mistral Q23)
```

Field names will be reconciled with the **actual** AbletonOSC/LOM property names
that Phase 1 confirms, so the spec vocabulary matches the write path 1:1.

---

See also: [pipeline-doctrine.md](pipeline-doctrine.md) ·
[ableton-bridge-onboarding.md](ableton-bridge-onboarding.md) ·
[architecture.md](architecture.md)
