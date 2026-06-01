#!/usr/bin/env python3
"""Build the Tier 1 SC Live Knowledge Corpus from Codex's recon JSONL.

Tier 1 = the *synthesised* layer (ranked constraint digest + concept hubs +
README), generated entirely from the recon findings. No HTML, no web. The
per-chapter faithful substrate (Tier 2) is a separate, later build from the
ABBYY HTML.

Why a generator instead of hand-written Markdown: the verbatim quotes must stay
byte-for-byte faithful to Codex's recon (OCR artifacts intact) so his later
audit is a clean string-level triangulation. The *prose* (hub intros, the
read-me) is authored here; the *entries* are rendered from the data. Because
both the constraint digest and the hubs are generated from one source, the
quote duplication between them cannot drift.

Run:  python3 build_corpus.py        # reads the JSONL next to this file,
                                      # writes ../  (the "Live Knowledge" folder)
"""
from __future__ import annotations
import json, pathlib, sys, collections

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "live12_manual_recon_findings.jsonl"
OUT = HERE.parent                      # the "Live Knowledge" folder
CONCEPTS = OUT / "Concepts"

LIVE_VERSION = "Live 12"

# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
def load():
    rows = []
    for line in SRC.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows

ROWS = load()
BY_LOC = {r["locator"]: r for r in ROWS}

# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------
KIND_LABEL = {
    "hard_constraint": "hard constraint",
    "schema_element": "schema element",
    "workflow_gotcha": "workflow gotcha",
    "version_sensitive": "version sensitive",
    "source_gap": "source gap",
}

def entry(loc: str, *, seealso: list[str] | None = None) -> str:
    """Render one finding as a uniform, source-pure block."""
    r = BY_LOC[loc]
    lines = [f"### {r['summary']}", ""]
    lines.append(f"> {r['verbatim_quote']}")
    lines.append("")
    meta = (
        f"`{r['locator']}` &nbsp;·&nbsp; **{KIND_LABEL[r['kind']]}** "
        f"&nbsp;·&nbsp; SC-relevance {r['sc_relevance']}/5 "
        f"&nbsp;·&nbsp; confidence: {r['confidence']}"
    )
    lines.append(meta)
    if seealso:
        lines.append("")
        lines.append("See also: " + " · ".join(f"[[{s}]]" for s in seealso))
    lines.append("")
    return "\n".join(lines)

def render_entries(locs: list[str], seealso_map: dict[str, list[str]] | None = None) -> str:
    seealso_map = seealso_map or {}
    return "\n".join(entry(l, seealso=seealso_map.get(l)) for l in locs)

# ---------------------------------------------------------------------------
# Concept hubs.  Each: title, authored intro, ordered locator list, see-also.
# Locators are validated against the JSONL below — a typo aborts the build.
# A finding may appear in more than one hub when it is genuinely central to
# both; that duplication is generated, so it cannot drift.
# ---------------------------------------------------------------------------
HUBS: dict[str, dict] = {
    "Track Types & Clip Hosting": {
        "intro": """\
*What kind of track can hold what.* This is the model that, mis-set, cost the
first SC track (*Pression Archivée*) seven tracks of silent drums: AbletonOSC
accepts MIDI note-writes onto an audio track and drops them on the floor, no
error. The structure spec declares track type once and `scaffold` builds it
correctly — but a session reasoning about *where a clip or device can live*
needs the rules below.

The short version: **audio clips and MIDI clips are not interchangeable**, the
device a track will accept depends on its type, and several track kinds (Group,
Return, Main) cannot hold clips at all.""",
        "locs": [
            "3. Live Concepts :: 3.8 Audio and MIDI :: 3",
            "3. Live Concepts :: 3.11 Devices :: 3",
            "3. Live Concepts :: 3.7 Tracks :: 3",
            "7. Session View :: 7.2 Tracks and Scenes :: 1",
            "23. Working with Instruments and Effects :: 23.2 Using Devices :: 36",
            "23. Working with Instruments and Effects :: 23.2 Using Devices :: 34",
            "23. Working with Instruments and Effects :: 23.3 Using Plug-Ins :: 4",
            "18. Mixing :: 18.3 Group Tracks :: 2",
            "18. Mixing :: 18.4 Return Tracks and the Main track :: 1",
            "18. Mixing :: 18.4 Return Tracks and the Main track :: 12",
            "40. Accessibility and Keyboard Navigation :: 40.4.1 Navigate Menu :: 10",
            "37. Computer Audio Resources and Strategies :: 37.1.4 Track Freeze :: 1",
        ],
        "seealso": ["Devices, Racks & Plug-ins", "Routing & Monitoring", "Hard Constraints"],
    },
    "Session vs Arrangement": {
        "intro": """\
*The exclusivity model SC keeps rediscovering.* Per track, Session and
Arrangement playback are **mutually exclusive** — launching a Session clip
stops that track's Arrangement playback, and it does not resume until **Back to
Arrangement** is pressed. This is the constraint that forced the scene-cue
redesign. The same split shows up in clip properties (launch controls exist
only for Session clips) and in envelopes (Arrangement clips carry only
modulation; automation lives on the track lane).

If a feature wires up scene cues, follow actions, or per-track playback state,
read this before assuming Session and Arrangement coexist on a track.""",
        "locs": [
            "3. Live Concepts :: 3.7 Tracks :: 5",
            "7. Session View :: 7.5 Recording Sessions into the Arrangement :: 13",
            "7. Session View :: 7.5 Recording Sessions into the Arrangement :: 14",
            "7. Session View :: 7.5 Recording Sessions into the Arrangement :: 12",
            "7. Session View :: 7.5 Recording Sessions into the Arrangement :: 19",
            "8. Clip View :: 8.3 Extended Clip Properties :: 3",
            "26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 3",
            "25. Automation and Editing Envelopes :: 25.2 Recording Automation in Session View :: 15",
            "25. Automation and Editing Envelopes :: 25.1 Recording Automation in Arrangement View :: 4",
            "19. Recording New Clips :: 19.2 Arming (Record-Enabling) Tracks :: 2",
        ],
        "seealso": ["Automation vs Modulation", "Follow Actions", "Hard Constraints"],
    },
    "Follow Actions": {
        "intro": """\
*The richest single concept in the recon (8 of the 34 top-relevance findings)
and also the most OCR-damaged section.* Follow Actions are central to SC's
scene/clip-cue work and to `.als` injection, so this hub is high-priority — but
see the **source-gap callout** below: the exact wording of two options
(*Previous*, *Next*) is damaged in the ABBYY/OCR source and is pending a
targeted PDF backfill. Behaviour described from the intact surrounding text is
reliable; the *exact option labels* for those two are not yet confirmed.

Mental model: a **group** is successive non-empty clip slots in one track; each
clip can carry **two** actions (A/B) with **Chance** weights; timing is the
**Follow Action Time** (or clip end, in Linked mode); Follow Actions bypass
**global** quantization but obey **clip** quantization; and scene Follow Actions
take precedence over clip ones once triggered.""",
        "locs": [
            "16. Launching Clips :: 16.7 Follow Actions :: 1",
            "16. Launching Clips :: 16.7 Follow Actions :: 6",
            "16. Launching Clips :: 16.7 Follow Actions :: 7",
            "16. Launching Clips :: 16.7 Follow Actions :: 9",
            "16. Launching Clips :: 16.7 Follow Actions :: 10",
            "16. Launching Clips :: 16.7 Follow Actions :: 20",
            "16. Launching Clips :: 16.7 Follow Actions :: 21",
            "16. Launching Clips :: 16.7 Follow Actions :: 24",
            "16. Launching Clips :: 16.7 Follow Actions :: 25",
            "16. Launching Clips :: 16.7 Follow Actions :: 27",
            "16. Launching Clips :: 16.7.6 Creating Nonrepetitive Structures :: 1",
            "16. Launching Clips :: 16.7.4 Adding Variations in Sync :: 2",
            "16. Launching Clips :: 16.7.2 Creating Cycles :: 1",
            "16. Launching Clips :: 16.3 Legato Mode :: 7",
        ],
        "seealso": ["Session vs Arrangement", "Tempo, Warp & Sync", "Hard Constraints"],
        "gap_callout": """\
> [!warning] Source gap — verify exact option wording before relying on it
> The ABBYY/OCR pass fragmented the Follow Action **option list** in section
> 16.7. Two entries are damaged in source:
>
> - **"Previous"** — `16. Launching Clips :: 16.7 Follow Actions :: 12` —
>   recon captured only `|* Previous-^] triggers`.
> - **"Next"** — `16. Launching Clips :: 16.7 Follow Actions :: 14` —
>   recon captured only `rs the next clip down` (the start of the entry is
>   dropped).
>
> The *behaviour* of these actions is described by surrounding intact text, but
> the **exact labels/wording are unconfirmed**. A targeted backfill from the
> 16.7 PDF pages is pending (Elias to supply). Until then: do not treat the
> precise option text as ground truth — confirm against Live's UI.
""",
    },
    "Tempo, Warp & Sync": {
        "intro": """\
*What determines the clock, and when warping is allowed.* Among multiple tempo
**leaders** only one wins (the bottom-most currently-playing clip); leaders
override the **Tempo Follower**; and **Tempo Follower and External Sync are
mutually exclusive** for receiving sync. Scene Tempo / Scene Time Signature
change the project on scene launch. On the audio side: unwarped clips cannot
loop, and Warp must be on before Loop is reachable.

Relevant to SC whenever a feature touches the transport, scene-level tempo
changes, or clip warp state via `.als` or AbletonOSC.""",
        "locs": [
            "9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 5",
            "9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 8",
            "9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 6",
            "9. Audio Clips, Tempo, and Warping :: 9.1.4 Clip Tempo Followers and Leaders :: 9",
            "36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.2.1 Setting Up Tempo Follower :: 8",
            "36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.2.1 Setting Up Tempo Follower :: 7",
            "36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.1.2 Using Link :: 8",
            "36. Synchronizing with Link, Tempo Follower, and MIDI :: 36.3 Synchronizing via MIDI :: 3",
            "7. Session View :: 7.2.1 Editing Scene Tempo and Time Signature Values :: 1",
            "7. Session View :: 7.2.1 Editing Scene Tempo and Time Signature Values :: 14",
            "8. Clip View :: 8.2.1 Clip and Loop Region Settings :: 7",
            "8. Clip View :: 8.9 Looping Clips :: 1",
            "9. Audio Clips, Tempo, and Warping :: 9.2.2 Importing Samples :: 2",
            "9. Audio Clips, Tempo, and Warping :: 9.2.3 Warp Markers :: 16",
            "25. Automation and Editing Envelopes :: 25.5.8 Editing the Tempo Automation :: 2",
            "6. Arrangement View :: 6.5 Time Signature Changes :: 1",
        ],
        "seealso": ["Routing & Monitoring", "Automation vs Modulation", "Hard Constraints"],
    },
    "Automation vs Modulation": {
        "intro": """\
*Who owns a parameter's value right now.* The load-bearing distinction:
**automation envelopes define the absolute value** of a control; **modulation
envelopes only influence** that value (relative). Both can act on one
parameter; automation is red, modulation is blue. Session clips can hold both;
**Arrangement clips hold only modulation** (automation lives on the track
lane). Manual moves override automation until re-enabled (or until a Session
clip with automation relaunches). Session-View automation becomes track-based
automation when copied/recorded into the Arrangement.

Critical for any feature that writes or reasons about envelopes/automation via
`.als` — confusing the two yields parameters that look automated but behave
unexpectedly.""",
        "locs": [
            "26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 1",
            "26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 3",
            "26. Clip Envelopes :: 26.3 Mixer and Device Clip Envelopes :: 5",
            "26. Clip Envelopes :: 26. Clip Envelopes :: 1",
            "26. Clip Envelopes :: 26.1 The Clip Envelope Editor :: 3",
            "26. Clip Envelopes :: 26.1 The Clip Envelope Editor :: 6",
            "26. Clip Envelopes :: 26.5 Unlinking Clip Envelopes From Clips :: 1",
            "26. Clip Envelopes :: 26.5.5 Warping Linked Envelopes :: 1",
            "26. Clip Envelopes :: 26.4 MIDI Controller Clip Envelopes :: 2",
            "26. Clip Envelopes :: 26.2.1 Clip Envelopes are Non-Destructive :: 1",
            "25. Automation and Editing Envelopes :: 25. Automation and Editing Envelopes :: 1",
            "25. Automation and Editing Envelopes :: 25.1 Recording Automation in Arrangement View :: 5",
            "25. Automation and Editing Envelopes :: 25.2 Recording Automation in Session View :: 15",
            "25. Automation and Editing Envelopes :: 25.2 Recording Automation in Session View :: 5",
            "25. Automation and Editing Envelopes :: 25.4 Overriding Automation :: 5",
            "25. Automation and Editing Envelopes :: 25.5 Drawing and Editing Automation :: 7",
            "3. Live Concepts :: 3.18 Automation Envelopes :: 4",
        ],
        "seealso": ["Session vs Arrangement", "Devices, Racks & Plug-ins", "Hard Constraints"],
    },
    "Routing & Monitoring": {
        "intro": """\
*Where a signal can be tapped, and when input is heard vs. clips.* Monitoring
state matters for recording features: **Auto** turns input monitoring off while
a track plays clips; **In** passes input permanently and **suppresses clip
output**; a **Resampling** track's own output is excluded from its recording.
Internal routing exposes **Pre FX / Post FX / Post Mixer** taps (including per
Rack chain), and return-track sends are disabled by default to prevent
feedback.

Relevant whenever a feature sets track I/O, sends, monitoring, or internal
routing — especially recording/resampling flows.""",
        "locs": [
            "17. Routing and 1/O :: 17.1 Monitoring :: 3",
            "17. Routing and 1/O :: 17.1 Monitoring :: 4",
            "17. Routing and 1/O :: 17.1 Monitoring :: 1",
            "17. Routing and 1/O :: 17.1 Monitoring :: 8",
            "17. Routing and 1/O :: 17.4 Resampling :: 2",
            "17. Routing and 1/O :: 17.5.1 Internal Routing Points :: 5",
            "17. Routing and 1/O :: 17.5.1 Internal Routing Points :: 6",
            "17. Routing and 1/O :: 17.5.1 Internal Routing Points :: 9",
            "17. Routing and 1/O :: 17.2.1 Mono/Stereo Conversions :: 1",
            "17. Routing and 1/O :: 17.3.3 Connecting External Synthesizers :: 2",
            "17. Routing and 1/O :: 17.3.4 MIDI In/Out Indicators :: 8",
            "17. Routing and 1/O :: 17. Routing and 1/O :: 69",
            "18. Mixing :: 18.4 Return Tracks and the Main track :: 9",
            "18. Mixing :: 18.4 Return Tracks and the Main track :: 4",
            "23. Working with Instruments and Effects :: 23.2 Using Devices :: 31",
            "39. MIDI Fact Sheet :: 39.5 Tips for Achieving Optimal MIDI Performance :: 4",
        ],
        "seealso": ["Track Types & Clip Hosting", "Devices, Racks & Plug-ins", "Hard Constraints"],
    },
    "Devices, Racks & Plug-ins": {
        "intro": """\
*The densest chapters in the recon (Instruments & Effects + Racks).* Signal in a
device chain flows **left to right**; in a MIDI track, devices **before** an
instrument see MIDI and **after** it see audio. Plug-in parameters must be
**published** (Configure Mode) to be addressable in Live's panel — relevant to
automating plug-in params via `.als`. Racks add Macros, Zones, and Drum-Rack
chains (Receive/Play/Choke, up to six return chains, and a 128-chain ceiling
that gates Slice-to-MIDI).

Read this for device-chain ordering, plug-in parameter exposure, and Rack
structure.""",
        "locs": [
            "23. Working with Instruments and Effects :: 23.2 Using Devices :: 36",
            "23. Working with Instruments and Effects :: 23.2 Using Devices :: 34",
            "23. Working with Instruments and Effects :: 23.3 Using Plug-Ins :: 4",
            "23. Working with Instruments and Effects :: 23.3.1 Plug-Ins in the Device View :: 17",
            "23. Working with Instruments and Effects :: 23.3.1 Plug-Ins in the Device View :: 19",
            "23. Working with Instruments and Effects :: 23.3.1 Plug-Ins in the Device View :: 21",
            "23. Working with Instruments and Effects :: 23.3.1 Plug-Ins in the Device View :: 23",
            "23. Working with Instruments and Effects :: 23.3 Using Plug-Ins :: 28",
            "24. Instrument, Drum and Effect Racks :: 24. Instrument, Drum and Effect Racks :: 2",
            "24. Instrument, Drum and Effect Racks :: 24.1.2 Macro Controls :: 3",
            "24. Instrument, Drum and Effect Racks :: 24.5 Zones :: 1",
            "24. Instrument, Drum and Effect Racks :: 24.6 Drum Racks :: 4",
            "24. Instrument, Drum and Effect Racks :: 24.6 Drum Racks :: 5",
            "24. Instrument, Drum and Effect Racks :: 24.6 Drum Racks :: 6",
            "24. Instrument, Drum and Effect Racks :: 24.6 Drum Racks :: 7",
            "13. Converting Audio to MIDI :: 13.1 Slice to New MIDI Track :: 3",
            "23. Working with Instruments and Effects :: 23.2 Using Devices :: 30",
        ],
        "seealso": ["Track Types & Clip Hosting", "Routing & Monitoring", "Automation vs Modulation", "Hard Constraints"],
    },
}

# ---------------------------------------------------------------------------
# Validation: every referenced locator must exist; report coverage.
# ---------------------------------------------------------------------------
def validate():
    errs = []
    referenced = set()
    for name, h in HUBS.items():
        for loc in h["locs"]:
            referenced.add(loc)
            if loc not in BY_LOC:
                errs.append(f"  [{name}] unknown locator: {loc!r}")
    if errs:
        print("LOCATOR VALIDATION FAILED:", file=sys.stderr)
        print("\n".join(errs), file=sys.stderr)
        sys.exit(1)
    hc = [r for r in ROWS if r["kind"] == "hard_constraint"]
    assert len(ROWS) == 201, f"expected 201 findings, got {len(ROWS)}"
    assert len(hc) == 61, f"expected 61 hard_constraints, got {len(hc)}"
    return referenced, hc

# ---------------------------------------------------------------------------
# Which hub(s) reference a given locator — for cross-links in the digest.
# ---------------------------------------------------------------------------
def hubs_for(loc: str) -> list[str]:
    return [name for name, h in HUBS.items() if loc in h["locs"]]

# ---------------------------------------------------------------------------
# Hard Constraints digest
# ---------------------------------------------------------------------------
def build_hard_constraints(hc):
    parts = [
        "# Hard Constraints",
        "",
        "> The non-negotiable rules of Ableton Live, pulled from Codex's recon and",
        "> **ranked by SC-relevance**. These are the things that break a build",
        "> *silently* if you assume otherwise. Read this before designing any",
        f"> feature that touches Live. Source: {LIVE_VERSION}, via the recon JSONL in",
        "> `_source/`. Quotes are verbatim (OCR artifacts intact).",
        "",
        f"**{len(hc)} hard constraints.** Each links to the concept hub that explains it",
        "in context. See [[README]] for how to read the corpus.",
        "",
    ]
    by_sc = collections.defaultdict(list)
    for r in hc:
        by_sc[r["sc_relevance"]].append(r)
    headers = {
        5: "SC-relevance 5 — these bite hardest",
        4: "SC-relevance 4",
        3: "SC-relevance 3",
        2: "SC-relevance 2",
    }
    for sc in (5, 4, 3, 2):
        group = sorted(by_sc.get(sc, []), key=lambda r: r["locator"])
        if not group:
            continue
        parts.append(f"## {headers[sc]}")
        parts.append("")
        for r in group:
            links = hubs_for(r["locator"])
            seealso = " &nbsp;·&nbsp; " + " · ".join(f"[[{l}]]" for l in links) if links else ""
            parts.append(f"### {r['summary']}")
            parts.append("")
            parts.append(f"> {r['verbatim_quote']}")
            parts.append("")
            parts.append(f"`{r['locator']}`{seealso}")
            parts.append("")
    return "\n".join(parts)

# ---------------------------------------------------------------------------
# Concept hub files
# ---------------------------------------------------------------------------
def build_hub(name, h):
    parts = [f"# {name}", "", h["intro"], ""]
    if h.get("gap_callout"):
        parts.append(h["gap_callout"])
        parts.append("")
    parts.append("## Findings")
    parts.append("")
    parts.append(render_entries(h["locs"]))
    parts.append("## See also")
    parts.append("")
    parts.append(" · ".join(f"[[{s}]]" for s in h["seealso"]))
    parts.append("")
    return "\n".join(parts)

# ---------------------------------------------------------------------------
# README + index
# ---------------------------------------------------------------------------
def build_readme(hc, referenced):
    kinds = collections.Counter(r["kind"] for r in ROWS)
    hub_lines = "\n".join(
        f"- [[{name}]] — {len(h['locs'])} findings" for name, h in HUBS.items()
    )
    return f"""# SC Live Knowledge — read me first

This folder is durable, queryable Ableton **{LIVE_VERSION}** knowledge for future
Claude Code sessions working the Silicon Click pipeline. You (a fresh session)
are the primary audience; Elias reads it as a side benefit. Treat it as **ground
truth** — but ground truth that *cites its source* and *flags where the source
is damaged*.

## What this is (and isn't), yet

This is **Tier 1**: the synthesised layer, built from Codex's 201-finding recon
of the Live 12 manual. It contains the rules and concepts that actually bite a
build — ranked, grouped, and quote-backed. It is **not** the full manual.

- **Built:** [[Hard Constraints]] + {len(HUBS)} concept hubs (below).
- **Deferred (Tier 2):** a faithful per-chapter substrate from the ABBYY HTML.
  Not built yet — the HTML wasn't available at Tier 1 time. Fresh sessions get
  this vault but **not** the Ableton Knowledge MCP, so when Tier 2 lands it will
  be the only full-text channel; until then, Tier 1 is the channel.

## How to read it

1. Start at **[[Hard Constraints]]** — the {len(hc)} things that break silently.
2. Then open the **concept hub** for your task:

{hub_lines}

Each finding is rendered uniformly:

- a **heading** = the claim (Codex's one-line summary),
- a **blockquote** = the *verbatim* manual text (OCR artifacts left intact — do
  not "correct" them; they are the audit anchor),
- a **metadata line** = `locator` · kind · SC-relevance /5 · confidence,
- `[[wikilinks]]` to related hubs.

## The taxonomy (Codex's `kind` field)

- **hard_constraint** — a rule Live enforces; violating it fails, silently or
  loudly. Most dangerous; all {len(hc)} are in [[Hard Constraints]].
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
  {kinds['hard_constraint']} hard_constraint, {kinds['schema_element']} schema_element,
  {kinds['workflow_gotcha']} workflow_gotcha, {kinds['version_sensitive']} version_sensitive,
  {kinds['source_gap']} source_gap, 0 cross_reference.
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
"""

def build_index(hc):
    hub_lines = "\n".join(
        f"- [[{name}]] — {h['intro'].splitlines()[0].strip('*')}"
        if False else f"- [[{name}]] ({len(h['locs'])} findings)"
        for name, h in HUBS.items()
    )
    return f"""# Live Knowledge — index

Map of content for the SC Live Knowledge corpus. New here? → [[README]].

## Fast lookup
- [[Hard Constraints]] — all {len(hc)} hard constraints, ranked by SC-relevance.

## Concept hubs
{hub_lines}

## Provenance
- `_source/live12_manual_recon_findings.jsonl` — Codex's recon (201 findings).
- `_source/build_corpus.py` — regenerates this Tier 1 layer from the JSONL.
"""

# ---------------------------------------------------------------------------
# Write everything
# ---------------------------------------------------------------------------
def main():
    referenced, hc = validate()
    CONCEPTS.mkdir(parents=True, exist_ok=True)

    (OUT / "README.md").write_text(build_readme(hc, referenced), encoding="utf-8")
    (OUT / "_Index.md").write_text(build_index(hc), encoding="utf-8")
    (OUT / "Hard Constraints.md").write_text(build_hard_constraints(hc), encoding="utf-8")
    for name, h in HUBS.items():
        (CONCEPTS / f"{name}.md").write_text(build_hub(name, h), encoding="utf-8")

    # Report
    print(f"findings: {len(ROWS)}   hard_constraints: {len(hc)}")
    print(f"hubs: {len(HUBS)}   referenced findings: {len(referenced)}")
    covered_hc = sum(1 for r in hc if hubs_for(r['locator']))
    print(f"hard_constraints linked from a hub: {covered_hc}/{len(hc)} "
          f"(all {len(hc)} are listed in Hard Constraints.md regardless)")
    print("wrote:")
    for p in sorted(OUT.rglob("*.md")):
        print("  ", p.relative_to(OUT))

if __name__ == "__main__":
    main()
