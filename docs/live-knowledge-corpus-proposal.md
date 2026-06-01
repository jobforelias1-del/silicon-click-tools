# Live Knowledge Corpus — build proposal

> A response to Dispatch's *SC Live Knowledge Corpus — Build Proposal Brief*
> (2026-06-01). Proposal only — nothing here is built yet. Pushback first,
> shape second, cost and ROI last, decisions for Elias at the end.
>
> Input read: Codex's 201-finding recon JSONL. **No web, no PDF, no HTML yet** —
> the HTML arrives at build time. Source discipline held so Codex's later audit
> stays a real triangulation.

---

## TL;DR

1. **Don't fan out per chapter.** The findings are wildly uneven across chapters
   (20 in one, 1 in several). One-agent-per-chapter wastes agents on singletons
   and under-serves the dense chapters. Cluster by finding-density instead.
2. **The load-bearing value is synthesis, not transcription — and it's already in
   the JSONL.** All 34 of the highest-relevance findings (`sc_relevance: 5`) and
   125 of 201 at `sc≥4` ship with verbatim quotes and locators *today*. The
   ranked-constraint digest and the concept hubs — the part that actually stops a
   Code session walking into a Live wall — can be built from the JSONL **with no
   HTML at all.**
3. **So tier it.** **Tier 1** = the synthesised top layer, built from the JSONL,
   ships this session. **Tier 2** = the faithful per-chapter substrate, built from
   the ABBYY HTML, deferred until the HTML lands *and* the ROI question below is
   answered. Tier 2 is where ~all the cost lives and ~least of the marginal value.
4. **Every wikilink is something I author, not something Codex found.** The recon
   has **zero `cross_reference` findings**. Cross-linking is pure synthesis — the
   main place I can introduce error, and the main thing Codex's audit will catch.
   That argues for *curated* links, not auto-generated link-soup.
5. **Follow Actions is the danger zone:** the single richest concept (8 of the 34
   crown jewels) *and* the most OCR-damaged section (both substantive
   `source_gap` flags). Flag the damage loudly; do not paper over it.

---

## What the recon actually says

201 findings, 199 `high` confidence / 2 `medium`. Distribution (counted, not
eyeballed):

| `kind` | count | of which `sc≥4` |
| --- | --- | --- |
| `workflow_gotcha` | 70 | 28 |
| `schema_element` | 65 | 48 |
| `hard_constraint` | 61 | **47 (77%)** |
| `source_gap` | 3 | 2 |
| `version_sensitive` | 2 | 0 |
| `cross_reference` | **0** | — |

By relevance: `sc5` → **34**, `sc4` → 91, `sc3` → 60, `sc2` → 16. So **125 of 201
(62%) are `sc≥4`.** This is a dense, high-signal corpus, not a sparse one — the
recon brief's "weight toward hard_constraint and schema_element" landed.

Five signals drive every architecture call below:

**1 — Density is lumpy.** Findings per chapter (26 chapters touched):

| chapter | findings | `sc≥4` | | chapter | findings | `sc≥4` |
| --- | --- | --- | --- | --- | --- | --- |
| 23 Instruments & Effects | 20 | 15 | | 3 Live Concepts | 10 | 8 |
| 17 Routing & I/O | 18 | 13 | | 6 Arrangement View | 10 | 2 |
| 16 Launching Clips | 16 | 15 | | 24 Racks | 9 | 5 |
| 18 Mixing | 14 | 9 | | 9 Audio/Tempo/Warp | 8 | 6 |
| 7 Session View | 13 | 8 | | 19 Recording | 7 | 5 |
| 26 Clip Envelopes | 12 | 9 | | …then a long tail | 1–5 each | — |
| 5 Files & Sets | 12 | 3 | | (11, 27, 30, 32, 40 ⇒ **1 each**) | | |
| 25 Automation | 11 | 9 | | | | |
| 8 Clip View | 11 | 5 | | | | |

A flat per-chapter fan-out spends as much coordination on a 1-finding chapter as
on a 20-finding one. Cluster by density.

**2 — The crown jewels cluster by *concern*, not by chapter.** The 34 `sc5`
findings don't spread evenly across the manual — they pile into ~6 functional
themes that cut across chapter boundaries, and those themes are exactly what a
Code session writing `.als` XML or driving AbletonOSC needs:

- **Track types & what they can hold** — `3.7`, `3.8`, `3.11`, `18.3`, `18.4`,
  `40.4.1`, `23.2`, `23.3`, `7.2`. *(includes `3.8.3` — the audio-vs-MIDI rule
  that cost* Pression Archivée *seven tracks.)*
- **Session ⇄ Arrangement exclusivity** — `3.7.5`, `7.5.13`, `7.5.14`, `26.3.3`,
  `25.2.15`, `7.2.1`. *(the constraint that forced the scene-cue redesign.)*
- **Follow Actions** — `16.7.{1,6,7,9,10,24,25,27}` — 8 crown jewels in one
  section.
- **Tempo / warp / sync** — `9.1.4.5`, `9.1.4.8`, `36.2.1.8`.
- **Automation vs modulation envelopes** — `26.1`, `26.3.1`, `26.3.3`.
- **Routing & monitoring** — `17.1.3`, `17.1.4`, `17.4.2`.

This is the strongest signal in the data: the corpus earns its keep as **concept
hubs**, not as a pile of chapter transcriptions.

**3 — Zero `cross_reference` findings.** Codex catalogued facts, not the links
between them. Every wikilink in the corpus is synthesis I author. Plan for it
deliberately (see *Wikilinks*), and treat it as the highest-error-risk surface
for the audit.

**4 — `hard_constraint` skews high and scatters wide.** 61 constraints, 47 at
`sc≥4`, spread across 18+ chapters. A session debugging "why did my Arrangement
go silent" should not grep 26 files. This is the case for a dedicated, ranked
`Hard Constraints` file — answered *yes* below.

**5 — Follow Actions is simultaneously richest and most damaged.** 8 crown jewels
*and* both substantive `source_gap` flags (`16.7 :: 12` "Previous" entry
fragmented; `16.7 :: 14` "Next" entry truncated). The highest-value concept sits
on the shakiest source. This needs explicit handling, not silent best-effort.

---

## Pushback on the original sketch

The brief floated *(1) per-chapter fan-out → per-chapter `.md`, (2) coordinator
merge + index + README, (3) one file per chapter + index + README.* Two changes:

- **Per-chapter → density-balanced clusters + a concept layer.** Chapters are the
  manual's filing system, not the consumer's retrieval pattern. A fresh Code
  session asks *"can a return track hold a clip?"* or *"will launching this
  Session clip stop my Arrangement?"* — questions that span chapters. Keep chapter
  files as a faithful **substrate** (good for provenance and Codex's audit), but
  make the **concept hubs** and the **constraint digest** the front door.
- **Transcription-first → synthesis-first, and tiered.** The original plan's
  centre of gravity is "read HTML, emit chapter files." But the JSONL already
  *is* a structured corpus of the high-value facts. The synthesised layer is
  buildable now, cheaply, with no HTML; the HTML substrate is completeness
  insurance. Inverting the order means value ships first and cost is gated on a
  real ROI decision.

---

## Proposed shape

Three layers, lifted straight from the signals above.

### Layer A — Entries (the atomic findings, faithful to source)

Each recon finding becomes one addressable, uniformly-templated block. Home: one
file per chapter that has findings, named to mirror the locator so *"where does
`26.3` live?"* is trivially answerable. Uniformity matters more here than in human
docs — a machine reader and an auditor both depend on every entry looking the
same. Template:

```markdown
### Audio and MIDI tracks host only their own clip type

> Audio signals are recorded and played back using audio tracks, and MIDI
> signals are recorded and played back using MIDI tracks. The two track types
> have their own corresponding clip types. Audio clips cannot be added to MIDI
> tracks and vice versa.

- **Claim:** Audio and MIDI tracks have distinct clip types and cannot host the
  other track type's clips.
- **Source:** `3. Live Concepts :: 3.8 Audio and MIDI :: 3`
- **Kind:** `hard_constraint` · **SC-relevance:** 5/5 · **Confidence:** high
- **See also:** [[Track Types & Clip Hosting]] · [[Hard Constraints]]
```

Verbatim quote in a blockquote, **OCR artifacts preserved** (same discipline as
recon). Locator in inline code, exactly as Codex wrote it, so an audit is a string
match. `kind` / `sc_relevance` / `confidence` carried through verbatim. This is
the corpus's **single source of truth**; everything else links here.

> **Design call worth ratifying:** entries stay *source-pure* — claim, quote,
> locator, links, nothing else. SC-specific colour ("this is the bug that cost us
> seven tracks") lives in the concept hubs, clearly marked as interpretation, not
> mixed into the verbatim layer. That keeps Codex's audit a clean check of corpus
> against manual, with no editorial to wade through.

### Layer B — Hubs & the constraint digest (the front door)

- **`Hard Constraints.md` — yes, its own file.** All 61, ranked by `sc_relevance`
  then chapter. Each line is *summary + locator + wikilink to the entry + score*.
  My recommendation: it's a **digest that links**, not a second copy of the
  quotes — single source of truth stays in Layer A, the digest is a fast triage
  surface. (Trade-off flagged for Elias below: inline-quotes reads in one file but
  risks drift; link-only avoids drift but costs a hop.)
- **~6 concept hubs**, one per crown-jewel theme from signal #2:
  `Session vs Arrangement`, `Track Types & Clip Hosting`, `Follow Actions`,
  `Tempo, Warp & Sync`, `Automation vs Modulation`, `Routing & Monitoring`
  (a 7th, `Devices, Racks & Plug-ins`, is likely given chapter 23+24 density —
  final cut decided once Layer A exists). Each hub is a short synthesised
  narrative + a table of wikilinks into Layer A. **This is where the corpus beats
  raw search** — it's the editorial a semantic index can't produce.

### Layer C — `README.md` (orientation for incoming Claude)

The single most important file, because it tells a fresh session how to *use* the
rest: what the corpus is, its provenance (ABBYY HTML + Codex JSONL, no web), the
read order ("start at `Hard Constraints`, then the hub for your task"), the locator
scheme, the `kind`/`sc_relevance` taxonomy, where the OCR gaps are, and the
contract — *ground truth, quote-backed, cite the locator, don't invent.*

### Proposed vault layout

```
Live Knowledge/
  README.md                       ← Layer C — read me first
  Hard Constraints.md             ← Layer B — 61 constraints, ranked
  Concepts/
    Session vs Arrangement.md     ← Layer B — concept hubs
    Track Types & Clip Hosting.md
    Follow Actions.md             ← carries the OCR source-gap callouts
    Tempo, Warp & Sync.md
    Automation vs Modulation.md
    Routing & Monitoring.md
  Chapters/                       ← Layer A — faithful substrate (Tier 2)
    03 Live Concepts.md
    07 Session View.md
    …
    40 Accessibility.md
```

Folders/prefixes are a placeholder — **final filenames match the vault's existing
convention**, which I can't see from the container. Decided at build time against
the real `~/Desktop/Obsidian Vault/`.

### Wikilinks — hybrid, curated, glossary-seeded

Because the recon has *zero* cross-references, links are authored, and naive
"link every term everywhere" produces noise that's worse than nothing for a
machine reader. Plan:

1. A small **controlled vocabulary** (~40–60 Live terms: *Session View*, *scene*,
   *Follow Action*, *return track*, *Group Track*, *Warp Marker*, *clip envelope*,
   *modulation*, *tempo leader*, *Drum Rack*, *Simpler*, …), each a link target.
2. Every entry links to **its concept hub** and to **sibling entries in the same
   sub-section** — high-precision, low-noise.
3. Concept hubs are **hand-curated** (the high-value synthesis).
4. No bulk auto-linking of prose. Curated + glossary-seeded only.

### `source_gap` handling — flag, don't fabricate

Three flags. The chapter-title OCR (`17. Routing and 1/O`, `sc2`) is cosmetic —
note it once. The two that matter are both in Follow Actions (`sc4`). My
recommendation: **leave the gap, mark it loudly, do not backfill from memory or
web.** In `Follow Actions.md`, at the exact spot:

```markdown
> [!warning] Source gap — verify before relying on exact option text
> The ABBYY/OCR pass fragmented the Follow Action option list here. The
> **"Previous"** (`16.7 :: 12`) and **"Next"** (`16.7 :: 14`) entries are
> damaged in source. Behaviour is described from surrounding intact text; the
> *exact* option wording is unconfirmed. Confirm against Live's UI or a clean
> source before treating wording as ground truth.
```

The corpus's value depends on it being honest about what it doesn't reliably know.
A future session must never mistake a reconstructed list for verified fact, and
preserving Codex's flags keeps his audit meaningful. *Optional, Elias's call:* if
the exact wording matters, hand me **just the 16.7 PDF pages** at build time for a
targeted backfill — narrow, not a source-discipline breach.

### `version_sensitive` — too few for a file

Only 2 (`5.5.1.15` can't-overwrite-older-Sets; `7.2.1.14` pre-Live-11 scene-name
tempo conversion). Tag them, keep them in their chapter files, surface in the
relevant hub. No dedicated file.

---

## Build mechanics

### Tiering (the headline mechanic)

- **Tier 1 — synthesised layer, from the JSONL, no HTML.** `README.md`,
  `Hard Constraints.md`, the ~6 concept hubs. Buildable **now**; the JSONL has the
  quotes and locators. ~9 files. This is the part that prevents the next
  scene-cue-style wall.
- **Tier 2 — faithful chapter substrate, from the ABBYY HTML.** The Layer-A
  chapter files. Built **after** the HTML lands. This is the expensive, lower-
  marginal-value half.

Note: Tier 2 *can't* start now regardless — the HTML isn't uploaded. So "Tier 1
first" isn't just my preference, it's what's physically buildable.

### Subagents & chunking (for Tier 2)

**~8–10 fan-out subagents, not 26**, partitioned by *finding density* (each bundle
≈ 20–30 findings; dense chapters solo, the long tail pooled). The real reason for
fan-out here is **context isolation, not speed**: ABBYY HTML from a ~90 MB PDF is
large, and each subagent should burn *its* context window on raw HTML and hand back
only finished, templated `.md` — keeping the main thread's context clean for the
merge.

Phases:

0. **Design jig (me, main thread):** partition the 201 rows by chapter, map
   chapters → HTML files, freeze the entry template + glossary + hub list. So every
   subagent emits byte-identical structure.
1. **Fan-out (Tier 2):** each subagent owns a chapter-bundle → reads its HTML +
   its JSONL slice → emits chapter files, flags any `source_gap` it meets.
2. **Coordinate (me):** build Layer B + C from the finished entries, verify every
   wikilink resolves, verify all 201 locators are represented.
3. **Self-audit before Codex:** count in = count out (201), every hub claim traces
   to a locator (no invented facts), OCR callouts present. Then hand to Codex.

---

## Cost estimate

In my terms (subagents / allowance / wall-clock). HTML size is unseen, so Tier 2
is a range, tightened the moment the HTML lands.

| | subagents | tokens (rough) | wall-clock | allowance feel |
| --- | --- | --- | --- | --- |
| **Tier 1** (JSONL only) | 0–2 helpers; mostly main thread | ~150–300 K | this session, ~30–45 min | a small feature |
| **Tier 2** (HTML substrate) | ~8–10, 1–3 waves | **HTML-dominated**, ~1–3 M | a few hrs active, parallelised | a medium-large build |

The swing factor is entirely **how big the ABBYY HTML is** and how cleanly it's
chunked — that's the #1 unknown for cost (below). Tier 1's cost is predictable
because I already hold its only input.

---

## ROI sanity check

The honest question the brief asks: with an **Ableton Knowledge MCP doing semantic
search over the same corpus on Dispatch's side**, is a static `.md` corpus worth
building, or redundant?

**Split the answer by tier.**

- **Tier 1 is worth building almost regardless of the MCP.** Semantic search
  returns *relevant manual passages*; it does not return *"the 7 things that will
  silently break your scene-cue feature, ranked."* The ranked constraint digest,
  the six concept hubs, and the OCR-honesty callouts are **editorial synthesis** a
  query-time index doesn't produce. A raw search over the damaged HTML will cheerfully
  hand back the corrupted Follow Action text with no warning — the corpus won't.
  And it's auditable and stable, which the whole "Codex audits later" plan needs.
- **Tier 2's ROI hinges on one fact I don't have: do fresh Code sessions actually
  have the MCP?** The brief says it's *"on Dispatch's side, not yours."* If a
  cloud-spun Code session gets the synced vault but **not** the MCP, then the
  chapter substrate is that session's only retrieval channel and Tier 2 earns its
  cost. If every session has the MCP, Tier 2 is largely redundant with semantic
  search and I'd **defer or skip it**, keeping only Tier 1's synthesis. **This is
  the single most decision-relevant question for Elias.**

So: **build Tier 1; gate Tier 2 on the MCP answer.** That's the "the simpler thing
delivers most of the value" version the brief invited — and it happens to be the
only thing buildable before the HTML arrives anyway.

---

## Unknowns & decisions for Elias

Things that would change the architecture or that I can't resolve from the
container:

1. **MCP availability (the ROI hinge).** Do fresh Code sessions get the Ableton
   Knowledge MCP, or only the vault? Determines whether Tier 2 is worth its cost.
2. **Scope/tier.** Tier 1 now and reassess? Full corpus? Or is the MCP enough that
   we don't build at all? (My rec: Tier 1 now.)
3. **Output delivery.** I run without filesystem access to the vault, so even
   finished files can't be written there from here. Do I commit them to the repo /
   attach them for you to drop into `Live Knowledge/`, or is there a sync path
   back? (Affects nothing about the content; everything about handoff.)
4. **Vault filename convention.** Final names must match the existing vault
   (date-stamped canon, character packets, lore bible). I need to see
   `~/Desktop/Obsidian Vault/` at build time; the layout above is a placeholder.
5. **`Hard Constraints.md` duplication policy.** Link-only (no drift, one hop) —
   my recommendation — vs. inline verbatim quotes (one-file read, drift risk).
6. **Follow Actions OCR gap.** Accept + flag (recommended), or hand me the 16.7 PDF
   pages for a targeted backfill?
7. **Exact Live version to pin.** Manual is "Live 12"; the `version_sensitive`
   findings reference the Live 11 boundary. The README should pin the precise
   manual version — which one?

Nothing here says the corpus shouldn't exist. It says: **build the synthesis half
now, prove it against real use, and let the HTML-heavy half wait for one fact and
the upload.**

---

See also: [pipeline doctrine](pipeline-doctrine.md) ·
[architecture](architecture.md) · [README](../README.md)
