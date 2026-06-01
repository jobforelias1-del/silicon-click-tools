# Phase 3 brief — Bridge session: `.als` follow-action writer + cue sample-loader

**From:** Legion session (silicon-click-tools)
**To:** Bridge session (the both-repo session on `jobforelias1-del/ableton-bridge`)
**Date:** 2026-06-01
**Depends on:** Phase 1 (LOM + `.als` probe, PR #1) and Phase 2 (sequential schema
+ audio-cue model, now on silicon-click-tools `claude/legion-command-architecture-87TAa`).

## Why this brief exists

Phase 2 made two things **authored and audited** in silicon-click-tools, but
neither can yet be **written into a set**:

1. **Scene follow actions** — `SceneSpec` carries `length`, `repeat_count`,
   `follow_action_a/b`, `chance_a/b`, `jump_target_a/b`, and the song-level
   `enable_follow_actions`. Phase 1 proved these are *not* reachable over the LOM
   but *are* persisted in the `.als` XML.
2. **Audio cues** — `CueSpec` (`sample`, `beat`, `length`, `gain_db`) describes a
   sample trigger on an audio track. `sc-produce apply` currently records these as
   info ("materialise by hand") and writes nothing, because the bridge has no
   sample-load path.

Phase 3 builds the two executors that close that gap. Both live in the **bridge
repo** (`jobforelias1-del/ableton-bridge`), because both operate at the `.als` /
file layer that the bridge owns — not over OSC.

## Canon to read first (do not re-derive from memory)

These are committed on silicon-click-tools branch
`claude/legion-command-architecture-87TAa`; pull them, don't paraphrase from this
brief:

- **`docs/sequential-schema-decisions.md`** — Decision #1 (repeat_count →
  native `.als` `LoopIterations`, *superseded* the Play-Again expansion),
  Decision #2 (computed beats are derived+audited), Decision #4 (jump-target
  resolution + length sanity), and the **shipped schema** section (length unit =
  beats; field names).
- **`sc_produce/models.py`** — the authoritative `SceneSpec`, `CueSpec`,
  `FollowAction` enum, and `StructureSpec.scene_start_beat()` (the computed
  absolute beat position you'll need for cue placement).
- **`projects/pression_archivee/structure.yml` + `arrangement.yml`** — the real
  data both writers must consume end-to-end.
- On the **bridge repo**: PR #1 / `FOLLOW_ACTIONS_FINDINGS.md` and the probe
  evidence (`_als_follow_schema.txt`, `_als_follow_diff.txt`) — the `.als` schema
  ground truth.

## Hard constraints (carried from prior phases)

- **No mutation of a live Live session without sign-off.** Same posture as the
  Pression Archivée audit. `.als` writing is offline file manipulation on a
  **copy**; never overwrite the user's working set in place without an explicit
  output path + sign-off.
- **No patches from LOM/spec memory.** Phase 1's rule stands (the 2026-05-27
  `save_song()` failure). Confirm every `.als` element name and every cue
  write-path against a real round-tripped file before shipping.
- **Proposal then pushback.** Read the canon, propose your design (the two items
  below are scoped, not final), and *push back before you build* if anything
  conflicts with what's actually in the `.als` or the bridge's existing seams.

---

## Deliverable 1 — `.als` follow-action writer

Inject per-scene follow-action state into a saved `.als` at apply-time, mapping
the Phase 2 `SceneSpec` fields onto the `.als` XML schema Phase 1 found under
`LiveSet/Scenes/Scene[Id=N]/FollowAction`.

**Field mapping (confirm enum bytes against a real file first):**

| `SceneSpec` (silicon-click-tools) | `.als` element | notes |
|---|---|---|
| `repeat_count` | `LoopIterations` | native count; `1` = play once |
| `follow_action_a` | `FollowActionA` | `FollowAction` enum → `.als` int (UI-order, `Next == 4`) |
| `follow_action_b` | `FollowActionB` | same enum map |
| `chance_a` | `FollowChanceA` | integer 0–100 (**not** 0–1) |
| `chance_b` | `FollowChanceB` | integer 0–100 |
| `length` | `FollowTime` | unit TBC — confirm beats vs bars.beats.16ths in a round-trip |
| `jump_target_a` (scene name) | `JumpIndexA` | resolve name → 0-based scene index via the structure |
| `jump_target_b` (scene name) | `JumpIndexB` | same |
| (per-scene) | `FollowActionEnabled` | set when the scene declares follow behaviour |
| `StructureSpec.enable_follow_actions` | global enable | the song-level toggle Phase 1 located |
| — | `IsLinked` | link follow-time to launch/loop length; pick a default + document it |

**Open questions to settle empirically (don't assume):**
- The `FollowAction` → int enum map. Anchor on `Next == 4` from Phase 1, but
  confirm the full 0–9 mapping byte-for-byte; a wrong enum silently mis-sequences.
- `FollowTime` unit. silicon-click-tools authors `length` in **beats**; if the
  `.als` wants bars.beats.sixteenths, the writer converts using the structure's
  `time_signature`. Confirm by writing a known value and reopening.
- Jump-target index base (0-based assumed) and what `JumpIndexA/B` hold when the
  action is *not* Jump (leave untouched vs. write a sentinel).

**Deliverable shape:** a bridge function that takes the structure's scene list
(names + the `SceneSpec` fields) and writes a new `.als`, plus a smoke test that
round-trips the Pression Archivée structure (INTRO 38→Next … OUTRO 38→Stop,
`enable_follow_actions: true`) and re-reads to confirm every scene's action,
chance, time, and `LoopIterations` survived. Draft PR on the bridge repo.

## Deliverable 2 — cue sample-loader

Materialise `CueSpec` rows into real audio clips in the correct scene slots, so
the six (b) tracks (`F_riser`, `F_impact`, `F_transition`, `D_clap`, `D_perc`,
`D_drill_roll`) stop being "by-hand" placeholders.

**Inputs per cue (from `CueSpec`):** `sample` (name/hint, e.g. `fx_riser_01`),
`beat` (start *within the scene*), `length` (beats), optional `gain_db`. The
target clip slot is the scene's index in the structure (same rule the MIDI apply
uses); the audio track is the cell's track.

**The two real unknowns — settle these before building:**
1. **Sample resolution.** `CueSpec.sample` is a *hint*, not a path. Where do the
   files live (the 30TB drive? a project samples dir?), and how does a hint map to
   a file? Propose a resolver (e.g. a `samples/` manifest mapping hint → path) and
   push back if the hint→file mapping needs Elias to define a convention first.
   **Do not invent file paths.**
2. **Write path: OSC vs `.als`.** Phase 1 established there's no OSC sample-load.
   So this is almost certainly `.als` injection too (a clip referencing a sample
   file in the audio track's clip slot). Confirm the `.als` audio-clip element
   shape against a real file the same way as Deliverable 1 — *do not* hand-author
   clip XML from memory.

**Deliverable shape:** a bridge function that, given the resolved sample files and
the arrangement's cue cells, writes audio clips into the right (track, scene-slot)
positions of an `.als`, honoring `beat`/`length`/`gain_db`; plus a smoke test on a
scratch set with one or two stub WAVs. Draft PR on the bridge repo.

**Note on `beat`:** `CueSpec.beat` is relative to the scene start. If you ever
need an absolute timeline position, `StructureSpec.scene_start_beat(scene)` in
silicon-click-tools already computes it from the sequential lengths — mirror that
logic rather than re-deriving.

---

## How this stitches back together

When both land, the end-to-end path is: silicon-click-tools authors + audits
(structure.yml + arrangement.yml, gate green) → bridge `.als` writer stamps scene
follow actions + `LoopIterations` → bridge cue loader places the audio clips →
the MIDI apply (already shipped) writes the note clips. The result is a set that
sequences itself and has its sample triggers in place — the first fully
tool-built Pression Archivée skeleton, ready for the by-hand instrument/mix pass.

**Report back to Legion** when each deliverable's PR is up (with the confirmed
enum map + `FollowTime` unit for D1, and the sample-resolution convention for D2),
so silicon-click-tools can reconcile any field-name or unit specifics into the
canon docs.
