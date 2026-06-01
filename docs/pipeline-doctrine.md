# Pipeline doctrine

> Why `silicon-click-tools` exists, who does what in the Silicon Click pipeline,
> and the two bugs that made a tool — not a script — non-negotiable.

This document is the *why*. For the *what* and *how*, see
[`architecture.md`](architecture.md), [`usage.md`](usage.md) and the
[README](../README.md).

---

## The multi-agent pipeline

Silicon Click ships music by routing work between agents. Until now, that routing
happened **by hand** — copy-pasting between chat windows and ad-hoc scripts. The
roles are:

| Agent / layer | Role | Output |
| --- | --- | --- |
| **Mistral** | Creative authoring | Writes the MIDI — the notes for each clip |
| **web Claude** | Audit | Reviews Mistral's output for correctness |
| **Dispatch** | Orchestration | Routes work between the agents and the set |
| **ableton-bridge v2** | Execution | Wraps [AbletonOSC](https://github.com/ideoforms/AbletonOSC) to write into a live Ableton set |

The shape is deliberate: a *creative* author (Mistral) is paired with a separate
*critical* auditor (Claude), because the failure modes of generative authoring are
exactly the ones a second pass catches cheaply. The bridge is the only component
that touches the DAW, and it is intentionally narrow (see
[the bridge README](https://github.com/jobforelias1-del/ableton-bridge-v2)).

`sc-produce` is the tool that makes this routing **repeatable**. Each stage of the
hand-run workflow becomes a subcommand:

```
        ┌─────────┐   compose    ┌──────────┐   capture    ┌──────────────┐
        │ structure│ ──────────▶ │ Mistral  │ ───────────▶ │ arrangement  │
        │  spec    │   (brief)    │ (author) │  (response)  │   spec       │
        └────┬─────┘              └──────────┘              └──────┬───────┘
             │                                                     │
             │ scaffold                                  audit ◀───┘
             │ (correct track types)                     (Claude / CI gate)
             ▼                                                     │
        ┌─────────────────────────── apply ◀──────────────────────┘
        │  Ableton Live  (via ableton-bridge v2 → AbletonOSC)
        └────────────────────────────────────────────────────────
```

---

## The first manual run: "Pression Archivée"

The first track produced through this pipeline by hand was **"Pression Archivée"**
— 142 BPM, A minor, a French-drill idiom. It surfaced two classes of bug that a
script would keep re-introducing and that a tool can eliminate by construction.

### Bug class 1 — audio tracks built for MIDI content (the headline bug)

**Seven tracks were created as AUDIO tracks, but Mistral had authored MIDI for
them.** An audio track silently cannot hold MIDI. Raw AbletonOSC accepts the note
writes and drops them on the floor — no error, no clip, no sound. The mismatch was
invisible until someone looked at an empty set and asked where the drums went.

The fix is structural: the *track type is declared once*, in the structure spec,
and `scaffold` creates each track with the **correct** type. `audit` then
cross-checks the authored arrangement against that structure and refuses any cell
that targets an audio track with MIDI. `apply` catches the same error per cell from
the bridge (`AudioTrackCannotHoldMidiError`) and reports it cleanly instead of
losing the notes. The bug cannot reach the set silently again.

### Bug class 2 — value violations and YAML syntax errors

The authored output also carried **value violations** — velocities above 127 (an
invalid MIDI value) — and **YAML syntax errors** that broke parsing outright.

The fix is a deliberate two-tier validation policy (see
[architecture](architecture.md#permissive-values-strict-structure)):

* **Values load permissively.** `NoteSpec.pitch` and `NoteSpec.velocity` are not
  range-checked at parse time, so a clip with `velocity: 150` still *loads*. That
  lets `audit` **report** the violation as a finding — with its scene, track and
  note index — instead of the parser crashing on the first bad note and hiding the
  rest.
* **Structure is strict.** Unknown keys and wrong types are rejected
  (`extra="forbid"`) and surface as "syntax errors" — the same class of bug that
  bit the team — but now with a precise, readable message rather than a traceback.

---

## The doctrine

The first run was a script. Scripts rot: the next track copies the last one's
`.py`, inherits its bugs, and diverges. The doctrine for everything after
"Pression Archivée" is:

1. **Start from a tool, not a script.** The next track, the next album, every
   future SC project starts from `sc-produce`. Behaviour that was learned the hard
   way (correct track types, value auditing, settle-and-verify writes) is encoded
   once and reused.
2. **Every track is a source-controlled pair of specs.** A
   [structure spec](architecture.md#two-specs) and an
   [arrangement spec](architecture.md#two-specs) — two YAML files — fully describe a
   project. They live in version control. The DAW set is a *materialisation* of
   those specs, not the source of truth.
3. **Author and auditor stay separate.** Mistral authors; Claude (and the `audit`
   command, and CI) audits. The arrangement can be re-audited and re-applied
   against a stable structure as many times as it takes.
4. **The bridge never silently fails.** Every operation either succeeds, is
   verified, or is reported. Audio-track-holds-MIDI and out-of-range values are
   caught before they reach the set; unacknowledged writes are settled and read
   back.

The result: a new track is `git init`, two specs, and `sc-produce pipeline`.

---

See also: [architecture](architecture.md) ·
[usage](usage.md) · [testing on real Live](testing-on-real-live.md) ·
[README](../README.md)
