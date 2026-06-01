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

## Decision 1 — `repeat_count` maps directly to native `.als` `LoopIterations`

**(Supersedes the original Play-Again-expansion version below, 2026-06-01, on
Phase 1 evidence.)**

A section that plays N times is authored as:

```yaml
- name: CHORUS
  length: "8.0.0"        # bars.beats.sixteenths (canonical unit TBD in Phase 2)
  repeat_count: 2         # default 1  -> writes LoopIterations = 2
  follow_action_a: Next
```

Phase 1's bridge-session probe settled the empirical question decision #1
anticipated. Findings (full evidence: PR #1 on `jobforelias1-del/ableton-bridge`,
`FOLLOW_ACTIONS_FINDINGS.md`):

- Scene follow actions are **NOT** exposed via the Python LOM at scene, clip, or
  song level (exhaustive `dir()` on AbletonOSC at the pinned commit) — so the
  bridge cannot set them over OSC at all.
- They **ARE** persisted in the `.als` XML at scene level. The write vehicle is
  therefore **offline `.als` XML injection at apply-time**, into
  `LiveSet/Scenes/Scene[Id=N]/FollowAction`, not an OSC call.
- Crucially, **`LoopIterations` is a native per-scene repeat count** in that XML.

So `repeat_count: N` maps **directly** to `LoopIterations = N`. **No Play-Again /
Next-chain expansion is needed** — this is the "even cleaner, use the native
field" branch the original decision called for. `jump_target` still stays
reserved for genuine structural jumps (that half of the original decision holds).

Persistent `.als` follow-action schema the apply layer will write (action enum
0–9, UI-order anchored on `4=Next`; byte-level enum map pending final
confirmation): `FollowActionEnabled`, `FollowActionA`/`FollowActionB`,
`FollowChanceA`/`FollowChanceB` (integers 0–100, **not** 0–1), `FollowTime`,
`IsLinked`, `LoopIterations`, `JumpIndexA`/`JumpIndexB` (0-based scene index,
meaningful only when the corresponding action = Jump).

> **Superseded original (kept for the reasoning trail):** the first version of
> this decision expanded `repeat_count: N` into `follow_action: Play Again` for
> (N-1) iterations + the authored action, on the premise that no native
> scene-level loop count existed. That premise was correct for the LOM but wrong
> for the `.als` layer; `LoopIterations` makes the expansion unnecessary. The
> rationale for keeping `jump_target` distinct from repeats (avoiding Jump-target
> overload and audit ambiguity) carries forward unchanged.

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

## Schema as shipped (2026-06-01)

The canonical length unit is **beats** (a plain float), not bars.beats.sixteenths
— it keeps `scene_start_beat` computation and the note-overflow check arithmetic,
and matches how notes are already authored. `SceneSpec` lives in
`sc_produce/models.py`; `StructureSpec.scenes` is `list[SceneSpec]` with a
validator that coerces a bare scene-name string into a default `SceneSpec`, so
every pre-existing positional spec still loads.

```yaml
enable_follow_actions: true   # global toggle (Mistral Q23)
scenes:
  - name: INTRO
    length: 38              # beats; absolute start is COMPUTED, not authored
    repeat_count: 1         # -> .als LoopIterations
    follow_action_a: Next
    chance_a: 100
    follow_action_b: No Action
    chance_b: 0
    # jump_target_a / jump_target_b: only when the action is Jump
```

The audit enforces Decisions #2/#4: jump targets must resolve to an existing
scene, scene lengths must be > 0 (degenerate total flagged), and a note may not
start at/after its scene's length. Field names map to the `.als` follow-action
schema Phase 1 confirmed (see Decision #1).

## Decision 5 — audio cues resolve to project-local `samples/` (Elias, 2026-06-01)

A `CueSpec.sample` is a hint, not a path. It resolves against:

```
projects/<project>/samples/<hint>.<ext>
```

- **Extension-agnostic** (`.wav`, `.aif`, `.mp3`, …): match `<hint>.*`.
- **Fail gracefully:** a hint that resolves to no file is a **warn + skip the
  cue**, never an abort of the apply pass (same posture as a bad cell).
- **The project folder is the canonical sample home.** Projects are
  self-contained and portable — stemming, archiving, and remix must not depend on
  which external drive is mounted. The Splice library (or any source) is where
  fresh sounds are *pulled from*, but a project copies files *into* its own
  `samples/` before apply-time; apply never reaches outside the project.
- **Manifest layer is optional** — a future `samples/` manifest could pin
  versions, but is not required.

This is implemented by the Phase 3 bridge cue-loader (see
[`../briefs/phase3_bridge_session_2026-06-01.md`](../briefs/phase3_bridge_session_2026-06-01.md)).

---

See also: [pipeline-doctrine.md](pipeline-doctrine.md) ·
[ableton-bridge-onboarding.md](ableton-bridge-onboarding.md) ·
[architecture.md](architecture.md)
