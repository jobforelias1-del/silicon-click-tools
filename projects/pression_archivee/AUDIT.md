# Pression Archivée — audit report

Command:

```
sc-produce audit projects/pression_archivee/arrangement.yml \
    --structure projects/pression_archivee/structure.yml
```

**GATE: FAIL** — `error_count = 17` (exit 1).

| metric | value |
|---|---|
| cells authored | 32 |
| cells passing value checks (OK) | 32 |
| value violations (velocity > 127, bad pitch/duration) | 0 |
| unknown track / scene errors | 0 |
| **audio-holds-MIDI errors** | **17** |
| completeness warnings (empty MIDI grid cells) | 21 |

The only failures are the **audio-holds-MIDI** class — MIDI authored onto tracks
the structure declares as `audio`. This is the exact bug the tool exists to
catch; it is surfaced here **on purpose, not fixed**, pending a per-track verdict.

## audio-holds-MIDI, grouped by track (UNRESOLVED — Elias decides)

| track | scenes with MIDI authored | count | likely intent |
|---|---|---|---|
| `A_server_hum` | INTRO, VERSE 1, PRE-CHORUS, CHORUS, VERSE 2, BRIDGE, OUTRO | 7 | **MIDI** — sustained tonal pads (A3/A4, dur 8). Retype candidate. |
| `F_transition` | VERSE 1, PRE-CHORUS, CHORUS, VERSE 2 | 4 | audio cue — 1 note/scene. Cue-marker candidate. |
| `F_impact` | CHORUS, BRIDGE | 2 | audio cue — 1 note/scene. Cue-marker candidate. |
| `F_riser` | PRE-CHORUS | 1 | audio cue — sparse. Cue-marker candidate. |
| `D_clap` | INTRO | 1 | **MIDI** — drum hits. Retype candidate. |
| `D_perc` | INTRO | 1 | **MIDI** — drum hits. Retype candidate. |
| `D_drill_roll` | INTRO | 1 | **MIDI** — drum hits. Retype candidate. |

Total: **17 cells across 7 tracks.**

## OK (passed value checks) — all 32 cells

- MIDI tracks (clean, will apply): `D_kick`, `D_snare`, `D_hat` (INTRO);
  `K_piano` (VERSE 1, PRE-CHORUS, CHORUS, VERSE 2, BRIDGE, OUTRO);
  `S_808_clean` (INTRO, VERSE 1, PRE-CHORUS, CHORUS, VERSE 2, OUTRO).
- The 17 audio-track cells above also pass *value* checks (notes are well-formed);
  they fail only the *type* check.

## Intentionally empty (not fabricated)

`B_harmonics`, `A_data_air`, `A_archive_room` — Mistral was never asked for these.
No cells authored, by design.

## Notes / assumptions carried into this report

- **Drum scene placement is an assumption.** All seven drum passes (R5–R11) were
  folded per drum track into a single clip placed in `INTRO` (scenes[0] /
  "clip slot 0"). If the drum passes correspond to different sections, the
  arrangement needs a per-pass → scene map before apply. This inflates the INTRO
  drum clips (D_kick 88, D_hat 95 notes) by overlaying all passes.
- **One op dropped:** the known-unrecoverable `D_hat` modify stub at beat 32.5
  (no `from`/`to`) was filtered, matching the bridge transform.
- **0 value violations** — velocity range across the whole arrangement is 38–127.
