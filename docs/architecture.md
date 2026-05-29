# Architecture

How `sc-produce` is put together: the two-spec model, the data model, the live
session and transport constraint, and how the five commands compose.

For *why* it is built this way, read the [pipeline doctrine](pipeline-doctrine.md).
For *how to use it*, read [usage](usage.md).

---

## Two specs, kept separate

A Silicon Click project is described by **two** YAML documents, deliberately split:

<a id="two-specs"></a>

| Spec | What it describes | Produced/edited by | Consumed by |
| --- | --- | --- | --- |
| **Structure spec** | The Live *skeleton*: `bpm`, `key`, `idiom`, `time_signature`; tracks with their correct MIDI/audio type; return tracks; sends; scene names | Designed up front | `scaffold`, `compose`, and the `--structure` side of `audit`/`apply`/`pipeline` |
| **Arrangement spec** | The authored *content*: a `scene -> track -> clip{notes}` grid | Authored by Mistral, captured via `compose` | `audit`, `apply`, `pipeline` |

**Why split them?** The skeleton is designed once and is stable; the notes are
authored later and iterated on. Keeping them apart means an arrangement can be
**re-audited and re-applied against a stable structure** as many times as needed,
without redesigning the set each pass.

### The scene/track grid and clip slots

The arrangement is a grid. Each **cell** is a `(scene, track)` pair holding one
clip's notes. The clip-slot index of a cell is **not stored** on the arrangement —
it is *derived*: a scene's clip-slot index is its position in
`StructureSpec.scenes` (i.e. session-view rows). That single source of truth keeps
the grid unambiguous and lets the same arrangement map cleanly onto the skeleton
`scaffold` built.

```
                track "D_kick"   track "K_piano"   track "A_server_hum"
scene 0 "Intro"   clip slot 0      clip slot 0       (audio — no MIDI)
scene 1 "Verse"   clip slot 1      clip slot 1
scene 2 "Drop"    clip slot 2      clip slot 2
```

---

## The data model

All specs are [pydantic](https://docs.pydantic.dev) v2 models in
[`sc_produce/models.py`](../sc_produce/models.py), re-exported from the package
root (`from sc_produce import StructureSpec, ArrangementSpec, ...`).

```
StructureSpec                      ArrangementSpec
├─ title, bpm, key, idiom          ├─ title
├─ time_signature: (num, den)      └─ scenes: { scene_name: { track_name: ClipSpec } }
├─ tracks:  [TrackSpec]                                            │
├─ returns: [TrackSpec]                                            └─ ClipSpec
├─ sends:   [SendSpec]                                                ├─ length: float | None
└─ scenes:  [str]                                                     └─ notes: [NoteSpec]
                                                                          ├─ pitch: int | str   (e.g. 60 or "C3")
TrackSpec                           SendSpec                            ├─ start, duration: float
├─ name: str                        ├─ from (alias of from_)            ├─ velocity: float  (nominally 0–127)
├─ type: TrackType                  ├─ to: str                          └─ mute: bool
├─ instrument: str | None           └─ level: float (0.0–1.0)
└─ color: int | None

TrackType = midi | audio | return
```

### Key model behaviours

* **`TrackType` is load-bearing.** It is the single declaration of whether a track
  can hold MIDI. This is the field that prevents the headline audio-vs-MIDI bug.
* **Sends address returns by name, resolved to an index.** AbletonOSC addresses
  sends by *index* (0 == first return track). `StructureSpec.send_index(name)`
  resolves a return-track name to its index using `returns` order (falling back to
  the order returns first appear as send destinations). See
  [Known limitations](#known-limitations).
* **Helper accessors.** `StructureSpec` offers `track(name)`, `is_midi(name)`,
  `is_audio(name)`, `midi_track_names()`, `audio_track_names()`,
  `scene_index(name)` and `send_index(name)`. `ArrangementSpec` offers
  `cell(scene, track)`, `iter_cells()` and `scene_names()`.

### Permissive values, strict structure

<a id="permissive-values-strict-structure"></a>

This is the deliberate validation policy that lets the auditor *report* instead of
crash:

* **Values are permissive.** `NoteSpec.pitch` and `NoteSpec.velocity` are **not**
  range-checked at parse time. A clip with `velocity: 150` still loads, so `audit`
  can report it as a finding (with location) rather than the parser dying on the
  first bad note and masking everything after it.
* **Structure is strict.** Every model sets `extra="forbid"`. Unknown keys and
  wrong types are rejected and surface as **"syntax errors"** — exactly the failure
  class from the first manual run, but now with a precise message.

Loading, dumping and merging live in [`sc_produce/spec.py`](../sc_produce/spec.py).
All YAML and validation failures are wrapped in `SpecError` (one readable message,
no traceback). `merge_arrangement()` deep-merges a freshly captured response into a
base arrangement, cell by cell — how a per-track Mistral response accumulates into a
complete grid.

---

## The live session and the single-socket constraint

`sc-produce` writes to Live through
[`ableton-bridge` v2](https://github.com/jobforelias1-del/ableton-bridge-v2), which
wraps AbletonOSC. The bridge covers **clips, notes, name resolution, sends and
device parameters** — but deliberately **not** creating or renaming tracks and
scenes. Scaffolding a new set needs exactly those operations.

### Why `LiveSession` exists

AbletonOSC replies to a **single fixed UDP response port (11001)**, so only **one
client socket** may exist per Live instance. We cannot open a second socket for the
creation calls. So [`LiveSession`](../sc_produce/live_session.py):

* creates **one** OSC transport, and
* **shares it** between the wrapped `AbletonBridge` (for everything it does well)
  and its own raw creation calls sent on the same socket.

The raw creation/naming calls `LiveSession` adds, read from the AbletonOSC source:

| `LiveSession` method | OSC address |
| --- | --- |
| `create_midi_track(index=-1)` | `/live/song/create_midi_track [index]` (`-1` appends) |
| `create_audio_track(index=-1)` | `/live/song/create_audio_track [index]` |
| `create_return_track()` | `/live/song/create_return_track` (no args; always appended) |
| `create_scene(index=-1)` | `/live/song/create_scene [index]` |
| `set_track_name(i, name)` | `/live/track/set/name [i, name]` |
| `set_scene_name(i, name)` | `/live/scene/set/name [i, name]` |
| `get_num_tracks()` / `get_num_scenes()` | `/live/song/get/num_{tracks,scenes}` → `(count,)` |

It is a context manager (closes the shared transport on exit) and exposes the
wrapped bridge as `session.bridge`.

### Writes are fire-and-forget

Like all AbletonOSC writes, the creation calls are **unacknowledged** — no success
reply and, critically, **no error reply**. So `LiveSession` callers compute target
indices arithmetically and then verify by reading names back. This is why
[`scaffold`](usage.md#scaffold) takes a `--settle SECONDS` delay (let Live apply the
creates) followed by a read-back verification pass. See
[Known limitations](#known-limitations).

---

## How the five commands compose

The CLI entry point is `sc_produce.cli:main` (the `sc-produce` console script).
Each subcommand is its own module; shared connection/output plumbing lives in
[`sc_produce/common.py`](../sc_produce/common.py) and the shared reporting layer in
[`sc_produce/report.py`](../sc_produce/report.py).

```
                       structure.yml          arrangement.yml
                            │                        │
   compose ◀───────────────┤                         │   (briefs Mistral; captures the response)
                            │                         │
   audit  ◀─────────────────┼─────────────────────────┤   (schema + values + type mismatch → Report)
                            │                         │
   scaffold ◀───────────────┤                         │   (build skeleton, correct track types)
                            │                         │
   apply  ◀─────────────────┴─────────────────────────┤   (route cells → (track, clip slot), reconcile notes)
                            │                         │
   pipeline = audit → scaffold → apply  (one command, end to end)
```

* **`compose`** reads a structure and emits the Mistral authoring brief (paste or
  API), then ingests the response into an arrangement spec.
* **`audit`** reads an arrangement (and optionally a structure) and produces a
  `Report` of findings: schema completeness, value violations, and — with a
  structure — the audio-vs-MIDI mismatch and unknown tracks/scenes.
* **`scaffold`** reads a structure and builds the skeleton in the open set with the
  **correct** track types; idempotent.
* **`apply`** reads both specs, routes each cell to its `(track, clip slot)` and
  reconciles each clip to the desired notes in the order **remove → modify → add**,
  then reads back and logs success/fail per cell.
* **`pipeline`** runs `audit` (gates on errors) → `scaffold` → `apply` in one shot.

### The reporting layer

Every inspecting/mutating command returns a [`Report`](../sc_produce/report.py): an
ordered list of `Finding`s, each with a `Severity`
(`ok`/`info`/`warning`/`error`) and an optional `scene`/`track`/`index` location.
Reports render to terminal text (with glyphs) or to JSON (`--json`), and know
whether they `passed` (no error-severity findings). `--strict` promotes warnings to
a failure.

### The launcher escape hatch

When Live is **not reachable** from where the command runs (CI, a remote box, this
container), `apply` and `pipeline` can emit a **self-contained Python launcher**
instead of writing to Live ([`--launcher <path>`](usage.md#the-launcher-flow)). The
launcher ([`sc_produce/launcher.py`](../sc_produce/launcher.py)) embeds the
already-audited structure and arrangement **inline** as validated dict literals, so
it is one portable file depending only on `sc_produce` and `ableton_bridge` — no
spec files need to travel with it. The producer runs it locally against their open
set; it pings, then scaffolds and/or applies.

---

## Known limitations (v0.1)

These are honest constraints inherited from AbletonOSC and OSC/UDP. See the
[bridge's `KNOWN_LIMITATIONS.md`](https://github.com/jobforelias1-del/ableton-bridge-v2/blob/main/KNOWN_LIMITATIONS.md)
for the underlying detail.

* **Return tracks are not name-resolvable over OSC.** AbletonOSC's track endpoints
  operate on `song.tracks`, which excludes returns, so there is no call mapping a
  return *name* to an index. `scaffold` therefore creates return tracks only on a
  **blank set** (where their order — and thus send indices — is known); against an
  existing set it will not reconcile returns by name.
* **Writes are unacknowledged → settle + verify.** Creates/sets get no reply.
  `scaffold` waits `--settle` seconds and reads names back to confirm.
* **`modify` is atomic-as-possible, not transactional.** There is no in-place note
  edit; `apply`'s reconcile does remove-then-add in a single OSC bundle (one
  datagram, in-order within the bundle), but a lost datagram has no rollback.
* **Single client per Live instance.** The fixed 11001 response port means only one
  `sc-produce`/bridge client can run against a given Live at a time.
* **Octave convention (C3 vs C4).** Pitch names default to `middle_c_octave=3`
  (MIDI 60 = C3, Ableton's labelling). Pass `--middle-c-octave 4` for strict SPN.
  Pick one and be consistent or you will be an octave off.

---

See also: [doctrine](pipeline-doctrine.md) · [usage](usage.md) ·
[testing on real Live](testing-on-real-live.md) · [README](../README.md)
