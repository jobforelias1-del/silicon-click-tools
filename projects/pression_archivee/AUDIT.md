# Pression Archivée — audit report (Phase 2, post-disambiguation)

Command:

```
sc-produce audit projects/pression_archivee/arrangement.yml \
    --structure projects/pression_archivee/structure.yml
```

**GATE: PASS** — `error_count = 0` (exit 0).

| metric | value |
|---|---|
| cells authored | 43 |
| MIDI notes | 665 |
| audio cues | 90 |
| value violations | 0 |
| unknown track / scene errors | 0 |
| audio-holds-MIDI errors | **0** (was 17 pre-disambiguation) |
| sequence errors (jump/length/overflow) | 0 |
| completeness warnings (empty MIDI grid cells) | 14 (all benign) |

> Counts shifted from the previous pass (48 cells / 681 notes / 105 cues) because
> drum passes that span sections are now **stretched** across the span and split
> at section boundaries (Elias 2026-06-01), and same-`(pitch,beat)` collisions are
> deduped higher-R-wins (Q15) — so overlapping passes no longer double-count.

## How the 17 errors were resolved

The earlier pass had 17 audio-holds-MIDI errors. Mistral's 2026-05-31
disambiguation answers resolved every one — **upstream re-authoring, not
downstream interpretation**, per doctrine:

| rows | Mistral verdict | action taken |
|---|---|---|
| R13 `A_server_hum` | **(a) MIDI** | re-typed `audio → midi` in structure.yml; its sustained-pad notes stand |
| R14 `F_riser`, R15 `F_impact`, R16 `F_transition` | **(b) audio cue** | stay `audio`; MIDI ops re-encoded as `cues` (sample hints from Q25) |
| `D_clap`, `D_perc`, `D_drill_roll` | **(b) audio cue** | stay `audio`; re-encoded as `cues` |

The tooling was extended (not bypassed) to support this: `ClipSpec` now carries
either `notes` (MIDI) **or** `cues` (audio sample triggers), and the audit
cross-checks each kind against the track's declared type — notes-on-audio and
cues-on-MIDI are both rejected, with the finding stating the upstream fix.

## Drum placement (Q8–Q14)

Drum passes are no longer all-folded-into-INTRO. Each pass is placed in its
Mistral-assigned section(s); R10 spans PRE-CHORUS..CHORUS, R11 spans
INTRO..VERSE 1. Collisions resolve higher-R-index-wins (Q15=yes).

## The 11 warnings (all benign)

Incomplete-grid notices for MIDI cells the section legitimately omits — drums
absent in VERSE 2 / BRIDGE / OUTRO (no drum pass placed there), and K_piano
silent in INTRO. These are correct sparse-arrangement gaps, not defects. Do
**not** run `--strict` (it would fail on these by design).

## Intentionally empty (not fabricated)

`B_harmonics`, `A_data_air`, `A_archive_room` — Mistral Q26/Q27/Q28 = silent.
No cells authored, by design.

## Sequential scene model (this pass)

`structure.yml` is now sequential: each scene declares `length` +
`follow_action` (+ `repeat_count` → native `.als` `LoopIterations`), and absolute
beat positions are **computed** (INTRO@0 … CHORUS@142 … OUTRO@304, matching the
blueprint). Per Mistral Q16–Q23 every section plays once → Next, OUTRO → Stop,
`enable_follow_actions: true`. The audit now also validates jump-target
resolution, scene-length sanity, and note-within-section-length (Decisions #2/#4).
Old positional specs (bare scene-name lists) still load via a coercion validator.

## Not yet done (downstream of this audit)

- **Audio cues are recorded, not applied.** The bridge has no OSC sample-load
  API, so `apply` reports cue cells as info ("materialise by hand") and writes
  nothing for them. Loading the actual samples is a by-hand / future-loader step.
- **Follow actions write at the `.als` layer, not over OSC.** Phase 1 found scene
  follow actions are unreachable via the LOM but persisted in the `.als` XML; the
  apply-time `.als` injection that writes them (and `LoopIterations`) is the next
  bridge-side piece, tracked on the ableton-bridge repo.
