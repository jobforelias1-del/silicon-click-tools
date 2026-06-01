# SC Live Knowledge — read me first

This folder is durable, queryable Ableton **Live 12** knowledge for future
Claude Code sessions working the Silicon Click pipeline. You (a fresh session)
are the primary audience; Elias reads it as a side benefit. Treat it as **ground
truth** — but ground truth that *cites its source* and *flags where the source
is damaged*.

## What this is (and isn't), yet

This is **Tier 1**: the synthesised layer, built from Codex's 201-finding recon
of the Live 12 manual. It contains the rules and concepts that actually bite a
build — ranked, grouped, and quote-backed. It is **not** the full manual.

- **Built:** [[Hard Constraints]] + 7 concept hubs (below).
- **Deferred (Tier 2):** a faithful per-chapter substrate from the ABBYY HTML.
  Not built yet — the HTML wasn't available at Tier 1 time. Fresh sessions get
  this vault but **not** the Ableton Knowledge MCP, so when Tier 2 lands it will
  be the only full-text channel; until then, Tier 1 is the channel.

## How to read it

1. Start at **[[Hard Constraints]]** — the 61 things that break silently.
2. Then open the **concept hub** for your task:

- [[Track Types & Clip Hosting]] — 12 findings
- [[Session vs Arrangement]] — 10 findings
- [[Follow Actions]] — 14 findings
- [[Tempo, Warp & Sync]] — 16 findings
- [[Automation vs Modulation]] — 17 findings
- [[Routing & Monitoring]] — 16 findings
- [[Devices, Racks & Plug-ins]] — 17 findings

Each finding is rendered uniformly:

- a **heading** = the claim (Codex's one-line summary),
- a **blockquote** = the *verbatim* manual text (OCR artifacts left intact — do
  not "correct" them; they are the audit anchor),
- a **metadata line** = `locator` · kind · SC-relevance /5 · confidence,
- `[[wikilinks]]` to related hubs.

## The taxonomy (Codex's `kind` field)

- **hard_constraint** — a rule Live enforces; violating it fails, silently or
  loudly. Most dangerous; all 61 are in [[Hard Constraints]].
- **schema_element** — a structural fact (what a control/section *is*). Maps to
  `.als` elements and AbletonOSC surfaces.
- **workflow_gotcha** — behaviour that surprises if you don't expect it.
- **version_sensitive** — depends on the Live version (only 2 in the corpus;
  tagged in place, not given a file).
- **source_gap** — the OCR/source is damaged here. **Verify before relying.**

`sc_relevance` (1–5) is Codex's score of how much this matters to Silicon Click.
The corpus is sorted and structured around it.

## The contract for a session using this

1. **Quote-backed or it didn't happen.** If you state a Live rule from this
   corpus, it has a `locator` and a verbatim quote. Cite the locator.
2. **Don't invent.** Nothing here was written from model memory of Ableton; it
   all traces to the recon. Keep it that way — if it's not in the corpus and not
   in the source, say so rather than guessing.
3. **Respect the gaps.** Where a `source_gap` callout appears (notably the
   *Previous*/*Next* options in [[Follow Actions]]), do **not** treat the exact
   wording as confirmed.

## Provenance & reproducibility

- Manual version: **Live 12**. The exact point release is not yet pinned —
  Elias to confirm; the two `version_sensitive` findings reference the Live 11
  boundary.
- Source of record: `_source/live12_manual_recon_findings.jsonl` (Codex's recon;
  201 findings, 199 `high` / 2 `medium` confidence). Distribution:
  61 hard_constraint, 65 schema_element,
  70 workflow_gotcha, 2 version_sensitive,
  3 source_gap, 0 cross_reference.
- This Tier 1 layer was **generated** from that JSONL by
  `_source/build_corpus.py` — re-run it to rebuild. The verbatim quotes are
  rendered from the data, not retyped, so Codex's later audit is a clean
  string-level check. All cross-links are authored synthesis (the recon has zero
  `cross_reference` findings).
- **No web, no PDF** were consulted building this. Same source discipline as the
  recon, so the audit stays a real triangulation.

## Staging note

This was staged inside the `silicon-click-tools` repo (the build runs in a cloud
container with no access to the vault). To install: copy this `Live Knowledge/`
folder into `~/Desktop/Obsidian Vault/`. Adjust filenames if they should match a
vault convention. `_source/` is provenance — optional to keep in the vault.
