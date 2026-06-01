# Pression Archivée — Disambiguation Re-Prompt for Mistral Da Menace

**Date:** 2026-05-31
**From:** Silicon Click pipeline (Dispatch → Mistral)
**Re:** Arrangement spec `cleaned_specs.json` — ambiguities and schema mismatches found at audit
**Action:** Please answer every numbered question in the structured answer block at the end. Your answers become canon and are promoted directly into the spec — so be definitive. Where a question offers options (a)/(b)/(c), pick one; don't hedge. Where it asks for a value, give the value.

---

## Why you're getting this

The Pression Archivée arrangement you authored (`cleaned_specs.json`) was run through the new `sc-produce audit`. It is clean on values (0 velocity/pitch violations, range 38–127) — good work. But the audit surfaced **two structural ambiguities** the tooling will not resolve by guessing, because the new doctrine is: *specs that don't match the declared track type, or that leave placement ambiguous, get kicked back to the writer rather than interpreted downstream.* You are the writer and you're right here, so we're asking you directly.

Two classes of issue:

1. **17 "audio-holds-MIDI" mismatches** — you authored MIDI note-ops onto seven tracks that the structure spec declares as `type: audio`. Audio tracks cannot hold MIDI clips. We need to know, per track, what you actually meant.
2. **Drum scene placement is unspecified** — your drum rows (R5–R11) are keyed by *drum name*, not by *song section*, so we can't tell which section (INTRO / VERSE 1 / …) each drum pass belongs to.

Plus three smaller items: scene repeat/follow behaviour, the schema you want for genuinely-audio tracks, and whether three currently-empty tracks should stay silent.

For reference, the **sections and their start beats** (142 BPM, 4/4):

| # | Section | Starts at beat | Length (beats) |
|---|---|---|---|
| 0 | INTRO | 0 | 38 |
| 1 | VERSE 1 | 38 | 76 |
| 2 | PRE-CHORUS | 114 | 28 |
| 3 | CHORUS | 142 | 38 |
| 4 | VERSE 2 | 180 | 76 |
| 5 | BRIDGE | 256 | 48 |
| 6 | OUTRO | 304 | — |

---

## Section 1 — The 7 type-mismatched rows (audio track received MIDI)

For **each** row below, choose exactly one:

- **(a) MIDI** — this really is a synth/instrument part; the *track* should be re-typed to `midi` in the structure spec, and your existing note-ops stand.
- **(b) AUDIO CUE** — this is a sample/clip trigger, not notes; re-author it in the audio-cue schema (see Section 4) instead of as MIDI notes.
- **(c) OMIT** — drop this row entirely; it wasn't meant to be in the song.

Evidence is given so you can answer from what you wrote, not from memory.

**Q1 — R13 : A_server_hum** (declared `audio`, "server room hum" atmosphere bed)
7 cells, one per section, 39 notes total. Sustained long tones, e.g. INTRO: `pitch A3, beat 0, duration 8, vel 50`; `pitch A4, beat 12, duration 8`. → (a) MIDI / (b) audio cue / (c) omit?

**Q2 — R14 : F_riser** (declared `audio`, FX riser)
1 cell (PRE-CHORUS), 3 notes. → (a) / (b) / (c)?

**Q3 — R15 : F_impact** (declared `audio`, FX impact/hit)
2 cells (CHORUS, BRIDGE), 1 note each. → (a) / (b) / (c)?

**Q4 — R16 : F_transition** (declared `audio`, FX transition)
4 cells (VERSE 1, PRE-CHORUS, CHORUS, VERSE 2), 1 note each. → (a) / (b) / (c)?

**Q5 — D_clap** (declared `audio`, "Elias drops samples")
MIDI ops authored across R5/R9/R10/R11 (≈31 hits). → (a) MIDI (re-type to instrument/drum-rack) / (b) audio cue (sample) / (c) omit?

**Q6 — D_perc** (declared `audio`, sample)
MIDI ops across R5/R9/R10/R11 (≈33 hits). → (a) / (b) / (c)?

**Q7 — D_drill_roll** (declared `audio`, sample)
MIDI ops across R9/R10 (≈20 hits). → (a) / (b) / (c)?

> Note: D_kick, D_snare, D_hat are declared `midi` and audit clean — no action needed on those three.

---

## Section 2 — Drum scene placement (R5–R11)

Your drum rows are keyed by drum name, not section, so each "pass" floats. The tooling's placeholder folded **all** passes into INTRO, which is certainly wrong. Tell us which **section** each pass targets. Evidence = the beat range of each pass's notes.

| Pass | Tracks touched | Op profile | Beat range seen | **Which section?** |
|---|---|---|---|---|
| **R5** | all 6 | base pattern (mostly modify) | 0–37 | Q8 = ? |
| **R6** | D_kick, D_snare | velocity sculpt only (114 modify) | 0–37.5 | Q9 = ? |
| **R7** | D_hat | hat detail (87 modify) | 0–32 | Q10 = ? |
| **R8** | D_kick, D_snare | 37 add, spans 0–73 | 0–73 | Q11 = ? |
| **R9** | D_hat, D_clap, D_perc, D_drill_roll | texture pass (86 add) | 0–31 | Q12 = ? |
| **R10** | all 6 | full pass (45 add), supersedes R6 kick/snare | 0–26 | Q13 = ? |
| **R11** | all 6 | light overlay (6 add) | 0–13 | Q14 = ? |

For each: name the section, **or** say "spans sections X–Y" if a pass deliberately covers more than one. (Implementation-doc hunch, *not* an assumption to accept: R8 may span VERSE 1's full 76 beats; R9 may be the CHORUS texture; R10 the PRE-CHORUS+CHORUS full pass; R11 an overlay. Confirm or correct.)

**Q15** — When two passes touch the same drum in the same section (e.g. R6 vs R10 on kick/snare), confirm the rule: *higher R-index wins on a (pitch, beat) collision.* Yes / No (if No, state the rule).

---

## Section 3 — Scene repeats & follow actions

The current spec is positional (absolute start beats). We're moving to a **sequential** model that uses Live's scene follow-actions, so a section can repeat and hand off to the next. For **each section**, tell us:

- **plays:** how many times the scene fires before moving on (repeat count, default 1)
- **then:** the follow action — one of `Next`, `Stop`, `Play Again`, `First`, `Last`, `Previous`, `Any`, `Other`, `Jump:<scene>`
- **(optional) chance split:** if you want probabilistic behaviour, give `A% action / B% action`

**Q16 INTRO** — plays ___ , then ___
**Q17 VERSE 1** — plays ___ , then ___
**Q18 PRE-CHORUS** — plays ___ , then ___
**Q19 CHORUS** — plays ___ , then ___
**Q20 VERSE 2** — plays ___ , then ___
**Q21 BRIDGE** — plays ___ , then ___
**Q22 OUTRO** — plays ___ , then ___
**Q23** — Should "Enable Follow Actions" be ON globally for this song? Yes / No.

---

## Section 4 — Audio-track schema

For the tracks that genuinely ARE audio (atmosphere beds, FX hits, sample triggers — including any Section-1 rows you marked **(b)**), we need a spec format. Proposed shape, per cue:

```yaml
- sample: "server_room_hum_01"   # name/hint of the clip
  beat: 0                         # start position within the section
  length: 16                      # length in beats
  gain_db: -6                     # optional level
```

**Q24** — Is this shape sufficient? If you want fields added/removed/renamed (fades, warp mode, loop on/off, reverse, transpose), specify them.
**Q25** — For each track you marked **(b)** in Section 1, give the sample-name/hint you intend (so it's not a blank).

---

## Section 5 — Intentionally-empty tracks

`cleaned_specs.json` authored nothing for **B_harmonics**, **A_data_air**, **A_archive_room**.

**Q26 B_harmonics** — stay silent this song / author now (if author: MIDI or audio?)
**Q27 A_data_air** — stay silent / author now (MIDI or audio?)
**Q28 A_archive_room** — stay silent / author now (MIDI or audio?)

---

## STRUCTURED ANSWER BLOCK (fill this in and send back)

```yaml
disambiguation: pression_archivee
date_answered: 2026-__-__

# Section 1 — type-mismatched rows: a=midi(retype) / b=audio_cue / c=omit
Q1_R13_A_server_hum:
Q2_R14_F_riser:
Q3_R15_F_impact:
Q4_R16_F_transition:
Q5_D_clap:
Q6_D_perc:
Q7_D_drill_roll:

# Section 2 — drum pass -> section (name a section, or "INTRO..CHORUS" for a span)
Q8_R5:
Q9_R6:
Q10_R7:
Q11_R8:
Q12_R9:
Q13_R10:
Q14_R11:
Q15_collision_rule_higher_R_wins:   # yes / no(+rule)

# Section 3 — scene sequence: "plays: N, then: <action>"
Q16_INTRO:
Q17_VERSE_1:
Q18_PRE_CHORUS:
Q19_CHORUS:
Q20_VERSE_2:
Q21_BRIDGE:
Q22_OUTRO:
Q23_enable_follow_actions_global:   # yes / no

# Section 4 — audio schema
Q24_audio_schema_ok:                # yes / or list field changes
Q25_sample_hints:                   # per (b)-marked track: name: hint

# Section 5 — empty tracks
Q26_B_harmonics:                    # silent / midi / audio
Q27_A_data_air:                     # silent / midi / audio
Q28_A_archive_room:                 # silent / midi / audio
```

---

*Pipeline doctrine reminder (not a question): from here on, any op that mismatches its declared track type is rejected at audit and routed back to you — the writer — rather than reinterpreted by the bridge or the arrangement layer. This brief is that routing in action. Thanks for tightening it up.*
