# Pression Archivée — samples

Canonical, project-local home for the audio-cue sample files (Decision #5 in
[`docs/sequential-schema-decisions.md`](../../../docs/sequential-schema-decisions.md)).

The Phase 3 bridge cue-loader resolves each `CueSpec.sample` hint against this
folder: `projects/pression_archivee/samples/<hint>.<ext>` (extension-agnostic —
`.wav` / `.aif` / `.mp3`). A hint that resolves to no file is **warned and
skipped**, not a hard failure.

Projects are self-contained: pull sounds in here (from Splice or anywhere) before
apply-time so the project stays portable across drives.

## Hints this project expects (Mistral Q25)

These are the sample hints authored into `arrangement.yml` for the six audio-cue
tracks. Drop a matching file (any supported extension) for each:

| hint | track | used in |
|---|---|---|
| `fx_riser_01` | F_riser | PRE-CHORUS |
| `fx_impact_01` | F_impact | CHORUS, BRIDGE |
| `fx_transition_01` | F_transition | VERSE 1, PRE-CHORUS, CHORUS, VERSE 2 |
| `clap_sample_01` | D_clap | INTRO, PRE-CHORUS, CHORUS |
| `perc_sample_01` | D_perc | INTRO, PRE-CHORUS, CHORUS |
| `drill_roll_sample_01` | D_drill_roll | PRE-CHORUS, CHORUS |

Until a file is present for a hint, that cue is skipped at apply-time (with a
warning) — the rest of the apply still runs.
