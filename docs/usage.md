# Usage

Example-driven reference for the five `sc-produce` commands. Every command line
below assumes the package is installed (`pip install -e ".[dev]"`) and — for the
commands that touch Live — that AbletonOSC is enabled in a running Ableton Live
set (see [testing on real Live](testing-on-real-live.md)).

For *why* the pipeline is shaped this way read the
[pipeline doctrine](pipeline-doctrine.md); for *how it fits together* read the
[architecture](architecture.md).

The examples use the two specs that ship in [`examples/`](../examples):

- `examples/pression_archivee.yml` — the structure spec (the Live skeleton).
- `examples/pression_archivee.arrangement.yml` — the arrangement spec (the
  authored notes).

---

## Conventions shared by every command

**Connection flags** (on the commands that talk to Live — `scaffold`, `apply`,
`pipeline`):

| Flag | Default | Meaning |
| --- | --- | --- |
| `--host` | `127.0.0.1` | AbletonOSC host |
| `--send-port` | `11000` | UDP port AbletonOSC listens on |
| `--receive-port` | `11001` | UDP port AbletonOSC replies to |
| `--timeout` | `5.0` | Seconds to wait for an OSC reply before `OSCTimeoutError` |
| `--middle-c-octave` | `3` | Octave for middle C in note names (3 = Ableton, 4 = strict SPN) |

**`--json`** is available on `scaffold`, `audit`, `apply` and `pipeline` and emits
the [`Report`](../sc_produce/report.py) as machine-readable JSON instead of text:

```json
{
  "title": "Audit",
  "passed": true,
  "summary": { "ok": 24, "warnings": 0, "errors": 0 },
  "findings": [
    { "severity": "ok", "message": "...", "scene": "Drop", "track": "D_kick", "index": null }
  ]
}
```

**Exit codes.** A command exits non-zero when its report has any error-severity
findings (or, under `--strict`, any warnings), or when a spec fails to load.

**Report glyphs** in text output: `✓` ok · `•` info · `!` warning · `✗` error.
Each line is `glyph [scene/track note N] message`, followed by a one-line
`N ok, N warning(s), N error(s)` summary.

---

## `scaffold` — build the Live skeleton

Materialise the structure spec into the open Live set: create each track **with
its correct MIDI/audio type** (the headline fix), create return tracks, create and
name scenes, set tempo and time signature, and configure sends.

```bash
sc-produce scaffold examples/pression_archivee.yml
```

`scaffold` is **idempotent**: it skips tracks and scenes that already exist by
name, and *flags* (does not silently fix) a track that exists with the wrong type.

| Flag | Default | Meaning |
| --- | --- | --- |
| `--dry-run` | off | Report what *would* be created/renamed; touch nothing |
| `--settle SECONDS` | `0.2` | Pause after the fire-and-forget creates before reading names back to verify |
| `--json` | off | JSON report |
| connection flags | see above | `--host` / `--send-port` / `--receive-port` / `--timeout` / `--middle-c-octave` |

Representative output against a blank set:

```text
== Scaffold ==
✓ Tempo set to 142.0 BPM
✓ Time signature set to 4/4
✓ [D_kick] created midi track
✓ [D_clap] created midi track
...
✓ [A_server_hum] created audio track
✓ [R_REVERB] created return track
✓ [R_DELAY] created return track
✓ [R_DRIVE] created return track
✓ [Intro] created scene
✓ [Verse] created scene
...
✓ [K_piano] send to R_REVERB set to 0.10
✓ [K_bells] send to R_DELAY set to 0.18
...
13 ok, 0 warning(s), 0 error(s)
```

Re-running is safe:

```text
== Scaffold ==
• [D_kick] track already exists (midi) — skipped
• [Intro] scene already exists — skipped
...
```

A type clash is flagged, not auto-corrected:

```text
✗ [K_piano] exists as an audio track but the spec says midi — fix it in Live or rename
```

> **Why `--settle`?** AbletonOSC writes are fire-and-forget (no acknowledgement),
> so `scaffold` computes target indices arithmetically, waits `--settle` seconds,
> then reads the names back to verify. If creates seem to race on a slow machine,
> raise it (e.g. `--settle 0.5`). See the
> [architecture note](architecture.md#writes-are-fire-and-forget).

---

## `compose` — brief Mistral, capture the result

`compose` reads a **structure** spec and produces the creative-authoring brief for
Mistral, then (separately) ingests Mistral's reply into an arrangement spec. It
never touches Live.

### Default: print a copy-paste brief (`--paste`)

```bash
sc-produce compose examples/pression_archivee.yml
```

Prints a ready-to-paste prompt: the track's title/idiom/key/tempo/time signature,
the full track list (audio tracks explicitly marked *do not author*), the scene
order, the hard rules (velocity 1–127, pitch as `"C3"` with C3 = middle C, beats
for `start`/`duration`), and the exact YAML output schema the auditor expects.

### Per-track briefs for big arrangements (`--chunked`)

```bash
sc-produce compose examples/pression_archivee.yml --chunked
```

Emits **one brief per MIDI track**, each scoped to that single track across *all*
scenes ("per-track-across-all-scenes" — the proven shape for large arrangements).
Author each track in its own Mistral turn; each reply is captured and merged (see
below).

### Call Mistral directly (`--api`)

```bash
export MISTRAL_API_KEY=sk-...
sc-produce compose examples/pression_archivee.yml --api -o arrangement.yml
```

POSTs the brief to Mistral and captures the response into `arrangement.yml`.
Requires `MISTRAL_API_KEY`; failures surface as a single readable error. Works
with `--chunked` to author and accumulate track by track.

### Capture a saved reply (the paste → capture loop)

The hand loop: run `--paste`, paste into Mistral, save its reply (the fenced
`yaml` block, or the whole message — the parser extracts the block), then ingest:

```bash
# 1. Generate the brief and copy it into Mistral.
sc-produce compose examples/pression_archivee.yml > brief.txt

# 2. Save Mistral's reply to a file, e.g. mistral_reply.txt, then capture it:
sc-produce compose examples/pression_archivee.yml \
    --capture-response mistral_reply.txt \
    -o arrangement.yml
```

For `--chunked`, capture each per-track reply and **merge** it into the
accumulating arrangement with `--base`:

```bash
# First track creates the file:
sc-produce compose examples/pression_archivee.yml \
    --capture-response reply_D_kick.txt -o arrangement.yml

# Each subsequent track merges into it (cells in the new reply win; the rest is kept):
sc-produce compose examples/pression_archivee.yml \
    --capture-response reply_D_clap.txt --base arrangement.yml -o arrangement.yml
```

Capture accepts **both** authored schemas: the full-arrangement
`title:` / `scenes:` document, and the per-track `track:` / `clips:` document
(which is folded into the right column of the grid).

Then audit the result:

```bash
sc-produce audit arrangement.yml --structure examples/pression_archivee.yml
```

| Flag | Meaning |
| --- | --- |
| `--paste` | Print a copy-paste brief (default) |
| `--api` | POST the brief to Mistral (needs `MISTRAL_API_KEY`) |
| `--chunked` | One brief per MIDI track (per-track-across-all-scenes) |
| `--capture-response <file>` | Ingest a saved Mistral reply instead of generating a brief |
| `--base <arrangement.yml>` | Merge the captured reply into this existing arrangement |
| `-o <arrangement.yml>` | Write the captured/validated arrangement here |

---

## `audit` — check Mistral's output

The Claude/CI gate as a command. Loads an arrangement (and optionally the
structure) and produces a `Report`:

```bash
sc-produce audit arrangement.yml --structure examples/pression_archivee.yml
```

What it checks:

- **Schema completeness** — every scene, every MIDI track has a cell (missing
  cells are flagged).
- **Value violations** — velocity > 127, invalid pitch, bad `start`/`duration`
  (these *load* permissively so the audit can report them rather than crash).
- **With `--structure`** — the **audio-vs-MIDI track-type mismatch** (a cell that
  targets an `audio` track), plus **unknown tracks/scenes** not present in the
  structure.

| Flag | Meaning |
| --- | --- |
| `--structure <structure.yml>` | Cross-check against the skeleton (type mismatch, unknown track/scene) |
| `-o <arrangement.yml>` | Write the validated arrangement out |
| `--strict` | Fail on warnings, not just errors |
| `--json` | JSON report |

Clean run:

```text
== Audit ==
✓ [Intro/D_kick] 8 notes, all values in range
✓ [Drop/D_808] 4 notes, all values in range
...
24 ok, 0 warning(s), 0 error(s)
```

A run that catches the two original bug classes:

```text
== Audit ==
✗ [Drop/D_kick note 3] velocity 150 is out of range (1-127)
✗ [Verse/A_server_hum] track is audio but has authored MIDI — audio tracks cannot hold MIDI
! [Pre/K_bells] no notes authored for this cell
✗ unknown track 'K_pianno' in scene 'Intro' (not in structure)
22 ok, 1 warning(s), 3 error(s)
```

A YAML/structure error (an unknown key, a wrong type) is reported as a load
("syntax") error before auditing begins:

```text
error: Arrangement spec failed validation:
  - scenes.Drop.D_kick.notes.0.velcoity: Extra inputs are not permitted
```

---

## `apply` — write the arrangement into Live

Routes each `(scene, track)` cell to its `(track, clip-slot)` pair — the clip slot
is the **scene's index in the structure** — then reconciles the clip to the desired
notes in the order **remove → modify → add**, reads the clip back, and logs
success/fail per cell.

```bash
sc-produce apply arrangement.yml --structure examples/pression_archivee.yml
```

| Flag | Meaning |
| --- | --- |
| `--structure <structure.yml>` | **Required** — supplies scene order (clip slots) and track types |
| `--dry-run` | Report the planned per-cell reconciliation without writing |
| `--launcher <path>` | Emit a self-contained script instead of applying (see below) |
| `--json` | JSON report |
| connection flags | `--host` / `--send-port` / `--receive-port` / `--timeout` / `--middle-c-octave` |

Representative output (OK lines are omitted by default in `apply` — only problems
and the summary are shown):

```text
== Apply ==
✗ [Verse/A_server_hum] audio track cannot hold MIDI — skipped (fix the track type)
48 ok, 0 warning(s), 1 error(s)
```

A cell that targets an audio track is caught cleanly per cell
(`AudioTrackCannotHoldMidiError` from the bridge) and reported — the notes are not
silently dropped, which is exactly the failure that started this project.

### The launcher flow

When Live is **not reachable** from where you run `apply` (CI, a remote box, this
container), emit a self-contained launcher instead of applying:

```bash
sc-produce apply arrangement.yml \
    --structure examples/pression_archivee.yml \
    --launcher run_pression.py
```

This writes `run_pression.py` with the **already-audited** structure and
arrangement embedded inline as validated dict literals — one portable file that
depends only on `sc_produce` and `ableton_bridge`, with no spec files to carry. The
producer runs it locally against their open set:

```bash
python run_pression.py
```

```text
Live version: (12, 0)
== Scaffold ==
...
== Apply ==
48 ok, 0 warning(s), 0 error(s)
```

If Live is unreachable when the launcher runs, it prints
`Ableton Live is not reachable (is AbletonOSC enabled?)` and exits non-zero.

---

## `pipeline` — audit → scaffold → apply, end to end

One command for the whole flow: **audit** (gates on errors), then **scaffold**
(correct types), then **apply** (or emit a launcher).

```bash
sc-produce pipeline examples/pression_archivee.yml arrangement.yml
```

| Flag | Meaning |
| --- | --- |
| `--strict` | Audit fails on warnings, not just errors |
| `--force` | Proceed to scaffold/apply even if the audit found errors |
| `--dry-run` | Run all stages without writing to Live |
| `--launcher <path>` | After auditing, emit a launcher instead of scaffolding/applying live |
| `--json` | JSON report |
| connection flags | `--host` / `--send-port` / `--receive-port` / `--timeout` / `--middle-c-octave` |

If the audit finds errors, `pipeline` stops before touching Live (unless
`--force`):

```text
== Audit ==
✗ [Drop/D_kick note 3] velocity 150 is out of range (1-127)
23 ok, 0 warning(s), 1 error(s)
error: audit found 1 error(s); not scaffolding or applying (use --force to override)
```

A clean run materialises the whole project:

```text
== Audit ==
24 ok, 0 warning(s), 0 error(s)
== Scaffold ==
13 ok, 0 warning(s), 0 error(s)
== Apply ==
48 ok, 0 warning(s), 0 error(s)
```

Emit a launcher for the whole pipeline (audit here, scaffold + apply locally):

```bash
sc-produce pipeline examples/pression_archivee.yml arrangement.yml \
    --launcher run_pression.py
```

---

See also: [doctrine](pipeline-doctrine.md) · [architecture](architecture.md) ·
[testing on real Live](testing-on-real-live.md) · [README](../README.md)
