# Codex Tasking Brief — Ableton Live Manual Recon
### SC Live Knowledge Corpus · Phase 0 (reconnaissance)

| | |
|---|---|
| **To** | Codex (Inspector General) |
| **From** | Corpus Code (Claude), via Elias |
| **You receive** | the Ableton Live manual as a TXT file |
| **You deliver** | one JSONL file of located, quoted, tagged findings (`live-manual-findings.jsonl`) |

---

## Why you, and what this is

Silicon Click (SC) is a music-production pipeline that drives Ableton Live
programmatically (over AbletonOSC). We're building a durable, queryable **Live
Knowledge Corpus** so the AI agents working this pipeline have master-level Live
understanding as ground truth — instead of guessing, or doing one-off web
lookups that fail on the constraint nobody knew to ask about.

This is a **two-phase** job for you:

1. **Now — scout.** Read the manual TXT and extract a structured findings file
   (this brief).
2. **Later — audit.** After Corpus Code builds the prose corpus from your
   findings, you verify that corpus against this same source.

You're the right operator for it on two counts. The work is *structured and
auditable by shape* — verbatim quotes, locators, confidence flags — which is
Inspector-General work. And you're GPT-lineage while the corpus builder is
Claude-lineage: for knowledge work, independent blind spots are a feature. Where
two same-lineage passes miss the same thing, two different lineages miss
different things.

**One rule above all: you locate and quote; you do not invent.** If the manual
doesn't say it, don't assert it — flag it. Never fill a gap from memory. An
absence is a finding, not a failure.

## Source handling — read this first

- **The TXT is canonical for this pass.** Hunt the TXT, not the live web. Corpus
  Code will build from this same TXT, and the later audit only triangulates if
  every pass covered identical ground. (If you happen to know a web URL for a
  finding you may add an optional `web_ref`, but the TXT location + verbatim
  quote is what's *required*.)
- **There is no official Live 12 PDF**, so this TXT is most likely an older
  version (11.x or earlier) or a print-to-PDF artifact. When a finding is
  version-sensitive — **Follow Actions especially changed in Live 12** — do
  *not* assert it holds for 12. Record what the TXT says, set `confidence`
  accordingly, and emit a companion `hazard` finding (`version_mismatch`).
- **OCR/layout damage is expected** — tables, key-command matrices,
  device-parameter lists, figure captions. Where text is mangled, capture what
  you can and emit a `hazard` so the builder knows to distrust that span.

## What to produce

A single file, **`live-manual-findings.jsonl`** — one JSON object per line,
append-only. JSONL, not Markdown and not prose: it survives a partial run, diffs
cleanly, and each line is independently valid, so one bad line never poisons the
file.

### Schema — fields on every line

| field | type | meaning |
|---|---|---|
| `id` | string | stable, greppable, per-kind prefix: `STRUCT-001`, `CONSTR-001`, `CROSS-001`, `HAZ-001`, `SURP-001` |
| `kind` | enum | `structure` \| `constraint` \| `crosswalk` \| `hazard` \| `surprise` |
| `claim` | string | the finding in one plain sentence |
| `quote` | string | **verbatim** TXT text supporting the claim. Mandatory — it's the trust anchor and the durable locator (anyone can string-find it). Only exception: a `crosswalk` row with `coverage:"absent"`, where there's nothing to quote. |
| `locator` | string | best stable address the TXT affords: `"Chapter > Section > Subsection"`, plus page number if the TXT preserves pagination |
| `sc_terms` | string[] | tags from the SC vocabulary below — these seed the corpus's cross-reference graph, so tag generously and consistently |
| `confidence` | enum | `high` \| `med` \| `low` |
| `needs_verify` | bool | `true` when you're unsure, when OCR is shaky, or when version-sensitive — this routes your own later audit |

Kind-specific extra fields just ride along as added keys:

- **`structure`**: `parent`, `approx_words`, `has_tables`, `figures_present`
- **`constraint`**: `priority` (`P1`–`P3`), `failure_mode` (what breaks if an agent doesn't know this)
- **`crosswalk`**: `manual_terms` (string[]), `coverage` (`full` \| `partial` \| `absent`)
- **`hazard`**: `hazard_type` (`version_mismatch` \| `ocr_damage` \| `table_garbled` \| `figure_lost` \| `toc_broken`), `severity`, `trust_source` (which source should win for this span)
- **`surprise`**: `rank`

### Worked example lines

```json
{"id":"STRUCT-016","kind":"structure","claim":"Chapter: Launching Clips","quote":"Launching Clips","locator":"Ch.16 (p.405-430)","parent":null,"approx_words":6200,"has_tables":true,"figures_present":true,"sc_terms":["session view","clip launch","follow actions"],"confidence":"high","needs_verify":false}
{"id":"CONSTR-001","kind":"constraint","priority":"P1","claim":"A clip's playback Start marker can be offset from its Loop brace, so a looping audio clip can start mid-sample","quote":"<verbatim TXT text>","locator":"Clip View > Clip Start/End and Loop (p.NNN)","failure_mode":"sampler-offset playback design picks the wrong primitive","sc_terms":["session view","audio clip","clip start","warp","loop"],"confidence":"high","needs_verify":false}
{"id":"CROSS-007","kind":"crosswalk","claim":"The .als (Live Set) file format is not documented anywhere in the manual","quote":"","manual_terms":[],"coverage":"absent","locator":"(whole manual)","sc_terms":[".als schema"],"confidence":"med","needs_verify":true}
{"id":"HAZ-003","kind":"hazard","hazard_type":"version_mismatch","claim":"Follow Actions section lacks Live 12's Linked/global controls — TXT predates 12","quote":"<verbatim TXT text>","locator":"Follow Actions section","severity":"high","trust_source":"web Live 12 manual for Follow Actions","sc_terms":["follow actions"],"confidence":"med","needs_verify":true}
```

## The SC vocabulary (controlled tag list for `sc_terms` + the crosswalk)

Tag findings with these so they map onto how the pipeline actually talks. This
is also the list to crosswalk in category 3.

- **session view / session grid** — the clip-launching matrix; rows are scenes, columns are tracks
- **arrangement view** — the linear timeline
- **scene** — a session row; launches every clip in that row
- **clip** — a piece of MIDI or audio
- **clip slot** — a cell in the session grid
- **track type** — MIDI vs audio. *Load-bearing in SC: an audio track silently cannot hold MIDI.*
- **send / return track** — aux/effect routing
- **follow actions** — per-clip / per-scene rules that fire another clip after a condition
- **warp / warp markers** — time-stretching of audio clips
- **Global Quantization** — the launch-timing grid
- **Simpler / Sampler / Drum Rack** — instruments that play samples from MIDI
- **sidechain** — compression (or other) keyed off another signal
- **.als schema** — the Ableton Live Set project file format
- **LOM / AbletonOSC** — the Live Object Model and the OSC control surface SC drives

(Expect the last two to be **absent** from the manual — confirming that is itself a useful crosswalk finding.)

## The five hunt categories

1. **`structure` — the manual's shape.** Walk the TOC/heading tree; one row per
   chapter and major section, with rough word-heft and whether it carries
   tables/figures. This becomes the builder's chunking plan. Flag where OCR broke
   the heading hierarchy (also emit a `hazard`).
2. **`constraint` — the rules that bite.** *This is the reason the corpus
   exists.* Hunt mutual-exclusivity rules, "you cannot X while Y," silent-failure
   modes, mode-dependent behavior, hardcoded limits, order-dependent operations.
   **Not definitions** — the builder writes those himself. See the priority
   targets below.
3. **`crosswalk` — SC vocabulary ↔ manual, including the silences.** For each SC
   term above, where does the manual cover it — and where is it **absent**? The
   absences are as valuable as the hits: they tell the builder what the corpus
   can't source here, which saves a fruitless search later.
4. **`hazard` — the source trust map.** Version mismatches, OCR damage, garbled
   tables, lost figures. For each, say which source should win for that span.
5. **`surprise` — optional, ranked, capped at 10.** Genuinely non-obvious things
   a master-level Live user knows that a naive read misses. Hard cap so it stays
   high-signal; locator required on each.

## Priority targets inside `constraint`

These are specific, high-value constraint questions from the bridge-engineering
side. They resolve open architecture decisions, so they're the priority within
category 2. Answer each from the manual, quote the support, set `confidence`,
and flag version-sensitivity where it applies.

- **P1 · Sample offset inside a looping session audio clip.** Can a sample hit be
  offset inside a looping clip? Cover the Clip Start marker, warp markers, clip
  envelopes, and clip-level follow actions. *(Resolves an open architecture fork —
  highest value.)*
- **P1 · Simpler / Drum Rack pitch transposition.** Does incoming MIDI pitch
  transpose the sample? Which mode plays untransposed one-shots? What's the
  pad→note layout in a Drum Rack? *(Determines whether a planned MIDI+sampler
  design is buildable.)*
- **P2 · Clip grid vs. global transport.** Does a launched session clip's
  internal beat grid lock to the global transport bar grid? What exactly does
  Global Quantization gate? *(A constraint the design hits regardless of which
  fork wins.)*
- **P1 · Live 12 scene follow actions.** Runtime semantics: fire-after-N-loop-
  iterations vs. time; what "Linked" links; whether the global Follow-Actions
  enable persists. *(De-risks a separate scene-automation decision. This is the
  most version-sensitive target — flag hard if the TXT predates 12.)*
- **P2 · Full mutual-exclusivity / precedence / capability inventory.** Beyond
  session-vs-arrangement: one-clip-per-slot, audio-vs-MIDI track capability,
  group-track behavior, return/monitor/routing constraints. *(The safety net —
  the next hard constraint we haven't hit yet.)*
- **P3 · (bonus, if cheap)** Sidechain trigger + sends routing — how a return/aux
  is driven as a sidechain source. *(The drill idiom leans on a sidechain pump.)*

**If you can only complete three deep-dives, do the first, second, and fourth**
(the two sampler/offset items and Follow Actions): they resolve the live
architecture fork and protect the scene-automation work.

## Out of scope

Don't transcribe whole chapters. Don't write definitions or prose. Don't
relevance-score every paragraph. Don't browse the web in place of the TXT. A
scout who tries to be comprehensive is just a slow second copy of the build —
hunt the high-value spans, locate them, quote them, tag them, move on.

## How to work

Read the TXT through once for orientation, then hunt in passes by category,
emitting JSONL as you go. When uncertain, lower `confidence` and set
`needs_verify` — never drop a maybe-finding silently, and never upgrade a guess
into an assertion. Nothing here is bad news: an absence or a hazard is a
finding.
