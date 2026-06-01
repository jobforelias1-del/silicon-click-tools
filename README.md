# silicon-click-tools

**The Silicon Click music-production pipeline as a CLI.** `sc-produce` turns a
multi-agent workflow that used to run by hand — Mistral authors the MIDI, Claude
audits it, a bridge writes it into Ableton Live — into one tool with five
subcommands. Every future track starts from a *tool*, not a copied-and-mutated
script: a single source-controlled pair of YAML specs becomes a real Ableton set.

It exists because of two bugs that bit the first manual run (the track *Pression
Archivée*): seven tracks were built as **audio** while Mistral had authored
**MIDI** for them (audio tracks silently cannot hold MIDI), and the authored output
carried **value violations** (velocities above 127) and **YAML syntax errors**.
`sc-produce` makes both classes of bug impossible to ship silently. The full story
is in the [pipeline doctrine](docs/pipeline-doctrine.md).

---

## Install

```bash
pip install -e ".[dev]"        # runtime + dev tooling (pytest, ruff, black)
# or just the runtime:
pip install -e .
```

Requires Python 3.10+. `sc-produce` depends on
[`ableton-bridge`](https://github.com/jobforelias1-del/ableton-bridge-v2) (a git
dependency, installed automatically by the commands above), plus `pydantic`,
`PyYAML`, `requests` and `Jinja2`.

To actually drive Ableton Live you also need **AbletonOSC** installed *into Live*:

1. Install [AbletonOSC](https://github.com/ideoforms/AbletonOSC) into Live's
   **Remote Scripts** folder and restart Live.
2. Enable it as the active **Control Surface**
   (Preferences → Link/Tempo/MIDI → Control Surface → **AbletonOSC**).
3. It speaks UDP on **11000** (Live listens) / **11001** (Live replies) on
   `127.0.0.1`.

Step-by-step instructions and a verification checklist are in
[docs/testing-on-real-live.md](docs/testing-on-real-live.md).

---

## Quickstart

The repo ships an example project in [`examples/`](examples): a structure spec
(`pression_archivee.yml`) and an arrangement spec
(`pression_archivee.arrangement.yml`).

```bash
# 1. Check the authored arrangement against the skeleton (needs no Live).
sc-produce audit examples/pression_archivee.arrangement.yml \
    --structure examples/pression_archivee.yml

# 2. With Ableton Live open (AbletonOSC enabled) on a NEW, empty set:
sc-produce scaffold examples/pression_archivee.yml          # build the skeleton
sc-produce apply   examples/pression_archivee.arrangement.yml \
    --structure examples/pression_archivee.yml              # write the MIDI

# ...or do all three at once:
sc-produce pipeline examples/pression_archivee.yml \
    examples/pression_archivee.arrangement.yml
```

Not on the machine running Live? Emit a self-contained launcher and run it there:

```bash
sc-produce pipeline examples/pression_archivee.yml \
    examples/pression_archivee.arrangement.yml --launcher run_pression.py
python run_pression.py        # on the machine with Live open
```

See [docs/usage.md](docs/usage.md) for example-driven walk-throughs of every
command, including the paste → capture Mistral loop.

---

## The two-spec model

A Silicon Click project is **two** YAML documents, kept deliberately separate:

- **Structure spec** — the Live *skeleton*: `bpm`, `key`, `idiom`,
  `time_signature`; tracks with their correct MIDI/audio **type**; return tracks;
  sends; scene names. This is what `scaffold` materialises.
- **Arrangement spec** — the authored *content*: a `scene → track → clip{notes}`
  grid. A cell's clip-slot index is the scene's index in the structure (session
  rows). This is what Mistral writes, `audit` checks, and `apply` writes into Live.

Splitting them mirrors the real workflow — the skeleton is designed once and is
stable; the notes are authored later — and lets an arrangement be **re-audited and
re-applied against a stable structure** as many times as needed. The pydantic
models live in [`sc_produce/models.py`](sc_produce/models.py); the data model is
diagrammed in [docs/architecture.md](docs/architecture.md#the-data-model).

Note values (pitch, velocity) **load permissively** so the auditor can *report*
violations instead of crashing; structural typos (unknown keys, wrong types) are
**rejected** and surface as "syntax errors".

---

## The five commands

| Command | What it does |
| --- | --- |
| `sc-produce scaffold <structure.yml>` | Build the skeleton in the open Live set — tracks with the **correct** type (the headline fix), returns, scenes, tempo/time-signature, sends. Idempotent. |
| `sc-produce compose <structure.yml>` | Generate the Mistral authoring brief (`--paste` to copy, `--api` to call Mistral, `--chunked` for one brief per track), and ingest the reply into an arrangement (`--capture-response`). |
| `sc-produce audit <arrangement.yml> [--structure <structure.yml>]` | Check Mistral's output: schema completeness, value violations, and (with `--structure`) the audio-vs-MIDI mismatch and unknown tracks/scenes. |
| `sc-produce apply <arrangement.yml> --structure <structure.yml>` | Route each `(scene, track)` cell to its `(track, clip-slot)` pair and reconcile notes (**remove → modify → add**), then read back per cell. |
| `sc-produce pipeline <structure.yml> <arrangement.yml>` | End to end: **audit** (gates on errors) → **scaffold** → **apply** (or `--launcher`). |

Common flags: `--dry-run`, `--json`, `--strict` (fail on warnings), and the
connection flags `--host` / `--send-port` / `--receive-port` / `--timeout` /
`--middle-c-octave`. `apply`/`pipeline` accept `--launcher <path>` to emit a
standalone script. Full flag tables and sample output are in
[docs/usage.md](docs/usage.md).

---

## The multi-agent doctrine, in brief

Silicon Click ships music by routing work between agents: **Mistral** authors
(writes the MIDI), **web Claude** audits the output, a **Dispatch** layer
orchestrates, and **ableton-bridge v2** (wrapping AbletonOSC) executes into Ableton
Live. Pairing a *creative* author with a separate *critical* auditor catches
generative failure modes cheaply, and the bridge is the only component that touches
the DAW. `sc-produce` makes that routing repeatable: each hand-run stage is a
subcommand, and every track becomes a source-controlled pair of specs.

Read the full story — the two bugs and the doctrine that followed — in
[docs/pipeline-doctrine.md](docs/pipeline-doctrine.md).

---

## Development & testing

```bash
pytest --cov=sc_produce       # tests run against a mock OSC transport — no Live needed
ruff check .
black --check .
```

The suite mocks the OSC transport, so it needs no running Ableton Live. To exercise
`sc-produce` against a real set, follow
[docs/testing-on-real-live.md](docs/testing-on-real-live.md).

---

## Known limitations (v0.1)

Honest constraints inherited from AbletonOSC and OSC/UDP (detail in the architecture
doc and the
[bridge's `KNOWN_LIMITATIONS.md`](https://github.com/jobforelias1-del/ableton-bridge-v2/blob/main/KNOWN_LIMITATIONS.md)):

- **Return tracks aren't name-resolvable over OSC.** AbletonOSC's track endpoints
  exclude returns, so `scaffold` creates return tracks only on a **blank set**
  (where their order, and thus send indices, is known).
- **Writes are unacknowledged → settle + verify.** Creates/sets get no reply (and
  no error), so `scaffold` waits `--settle` seconds and reads names back to confirm.
- **`modify` is atomic-as-possible, not transactional.** There is no in-place note
  edit; `apply`'s reconcile does remove-then-add in a single OSC bundle, but a lost
  datagram has no rollback.
- **Single client per Live instance** (the fixed 11001 reply port), and the
  **C3-vs-C4** octave convention (default `--middle-c-octave 3`, Ableton's
  labelling).

---

## Documentation

- [Pipeline doctrine](docs/pipeline-doctrine.md) — why this tool exists; the
  agents and the two bugs.
- [Architecture](docs/architecture.md) — the two-spec model, the data model, the
  single-socket `LiveSession`, how the commands compose.
- [Usage](docs/usage.md) — example-driven reference for all five commands.
- [Testing on a real Live](docs/testing-on-real-live.md) — the AbletonOSC setup
  and verification checklist.

---

## License

MIT.
