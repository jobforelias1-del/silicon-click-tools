# Pression Archivée — audit report

`sc-produce audit arrangement.yml --structure structure.yml`  ->  GATE FAIL (error_count=17)

- findings: {'ok': 32, 'error': 17, 'warning': 20}
- OK cells (valid MIDI on MIDI tracks): 32
- value violations (velocity>127 etc.): 0
- unknown track/scene errors: 0
- audio-holds-MIDI errors: 17

## audio-holds-MIDI, grouped by track (the unresolved verdict)

| track | structure type | scenes with MIDI authored | count |
|---|---|---|---|
| `A_server_hum` | audio | BRIDGE, CHORUS, INTRO, OUTRO, PRE-CHORUS, VERSE 1, VERSE 2 | 7 |
| `D_clap` | audio | INTRO | 1 |
| `D_drill_roll` | audio | INTRO | 1 |
| `D_perc` | audio | INTRO | 1 |
| `F_impact` | audio | BRIDGE, CHORUS | 2 |
| `F_riser` | audio | PRE-CHORUS | 1 |
| `F_transition` | audio | CHORUS, PRE-CHORUS, VERSE 1, VERSE 2 | 4 |

Total audio-holds-MIDI cells: 17 across 7 tracks.

## OK (MIDI) cells
- `A_server_hum`: BRIDGE, CHORUS, INTRO, OUTRO, PRE-CHORUS, VERSE 1, VERSE 2
- `D_clap`: INTRO
- `D_drill_roll`: INTRO
- `D_hat`: INTRO
- `D_kick`: INTRO
- `D_perc`: INTRO
- `D_snare`: INTRO
- `F_impact`: BRIDGE, CHORUS
- `F_riser`: PRE-CHORUS
- `F_transition`: CHORUS, PRE-CHORUS, VERSE 1, VERSE 2
- `K_piano`: BRIDGE, CHORUS, OUTRO, PRE-CHORUS, VERSE 1, VERSE 2
- `S_808_clean`: CHORUS, INTRO, OUTRO, PRE-CHORUS, VERSE 1, VERSE 2
