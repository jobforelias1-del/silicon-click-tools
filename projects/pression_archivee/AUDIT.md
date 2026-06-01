# Pression Archivée — audit report (Phase 2, post-disambiguation)

Command:

```
sc-produce audit projects/pression_archivee/arrangement.yml \
    --structure projects/pression_archivee/structure.yml
```

**GATE: PASS** — `error_count = 0` (exit 0).

| metric | value |
|---|---|
| cells authored | 48 |
| MIDI notes | 681 |
| audio cues | 105 |
| value violations | 0 |
| unknown track / scene errors | 0 |
| audio-holds-MIDI errors | **0** (was 17 pre-disambiguation) |
| completeness warnings (empty MIDI grid cells) | 11 (all benign) |

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

## Not yet done (downstream of this audit)

- **Audio cues are recorded, not applied.** The bridge has no OSC sample-load
  API, so `apply` reports cue cells as info ("materialise by hand") and writes
  nothing for them. Loading the actual samples is a by-hand / future-loader step.
- **Sequential follow-action schema** (the structure.yml rewrite to
  `length`/`follow_action`/`repeat_count`→`LoopIterations`) is the remaining
  Phase 2 structural work; this pass covered the arrangement + audio-cue model.
