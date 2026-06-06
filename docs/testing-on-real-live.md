# Testing on a real Ableton Live

The `sc_produce` test suite runs entirely against a **mock OSC transport**, so it
needs no Ableton Live (`pytest --cov=sc_produce`). This document is the other half:
a practical checklist for testing `sc-produce` against a **real, running Ableton
Live** — the steps that accompany the v0.1.0 release.

Budget ~15 minutes. You need Ableton Live (10+) and a checkout of this package
installed (`pip install -e ".[dev]"`).

---

## 0. Prerequisites

- [ ] Ableton Live installed and licensed.
- [ ] `silicon-click-tools` installed (`pip install -e ".[dev]"`), which pulls in
      the `ableton-bridge` dependency.
- [ ] A loopback connection (you will run `sc-produce` on the **same machine** as
      Live; defaults target `127.0.0.1`).

---

## 1. Install AbletonOSC

AbletonOSC is the Live Remote Script that exposes Live's Object Model over OSC.

- [ ] Download AbletonOSC from <https://github.com/ideoforms/AbletonOSC>.
- [ ] Copy the `AbletonOSC` folder into Live's **Remote Scripts** directory:
  - **macOS:** `~/Music/Ableton/User Library/Remote Scripts/`
  - **Windows:** `\Users\<you>\Documents\Ableton\User Library\Remote Scripts\`
- [ ] Restart Ableton Live so it discovers the script.

> AbletonOSC adds and renames endpoints over time. This release was verified
> against the AbletonOSC commit recorded in the bridge's
> [`KNOWN_LIMITATIONS.md`](https://github.com/jobforelias1-del/ableton-bridge-v2/blob/main/KNOWN_LIMITATIONS.md).
> If you run a very different build and creates misbehave, pin AbletonOSC to that
> commit.

---

## 2. Enable it as the active Control Surface

- [ ] In Live: **Preferences → Link / Tempo / MIDI** (older Live: **Link/MIDI**).
- [ ] Under **Control Surface**, pick **AbletonOSC** in a free slot.
- [ ] Leave Input/Output as *None* (AbletonOSC uses UDP, not a MIDI port).

It is **active** when selected here — there is no separate on switch. If
AbletonOSC is installed but not selected in this menu, every `sc-produce` command
that talks to Live will time out.

---

## 3. Confirm the ports

AbletonOSC uses two fixed UDP ports on loopback:

| Port | Direction | `sc-produce` flag |
| --- | --- | --- |
| **11000** | Live **listens** (you send to it) | `--send-port` (default 11000) |
| **11001** | Live **replies** (you receive on it) | `--receive-port` (default 11001) |

- [ ] Leave the defaults unless you have changed AbletonOSC's configuration.
- [ ] Make sure nothing else is bound to **11001** — only one AbletonOSC client may
      exist per Live instance (the reply port is fixed and exclusive). Close other
      OSC clients / a second `sc-produce` run.

A quick reachability check from a Python REPL:

```python
from sc_produce import LiveSession
with LiveSession() as s:
    print(s.bridge.ping())            # True if Live + AbletonOSC are live
    print(s.bridge.get_live_version())
```

`ping()` returning `True` (and a version tuple) means you are connected. A
`OSCTimeoutError` means you are not — see [troubleshooting](#troubleshooting).

---

## 4. Scaffold the skeleton

Open a **new, empty** Live set (File → New Live Set), then build the structure:

```bash
sc-produce scaffold examples/pression_archivee.yml
```

**What success looks like:**

- The report ends with errors `0` and a row of `✓` lines.
- In Live's Session view you now have, in order: the MIDI tracks (`D_kick`,
  `D_clap`, … `L_lead`), the audio tracks (`A_server_hum`, `A_vinyl_crackle`,
  `A_field_paris`), three return tracks (`R_REVERB`, `R_DELAY`, `R_DRIVE`), and six
  named scenes (`Intro`, `Verse`, `Pre`, `Drop`, `Break`, `Outro`).
- Tempo reads **142 BPM**; the time signature is **4/4**.
- The MIDI tracks have a MIDI input slot; the audio tracks do not — **this is the
  bug class this tool exists to prevent.**

Re-run it — every track and scene should now be reported as *already exists,
skipped* (`scaffold` is idempotent).

> If creates appear to **race** (a track or scene missing on first run, present on
> re-run), your machine needs more time to apply the fire-and-forget writes. Raise
> the settle delay: `sc-produce scaffold examples/pression_archivee.yml --settle 0.5`.

**Dry run first** if you want to see the plan without changing the set:

```bash
sc-produce scaffold examples/pression_archivee.yml --dry-run
```

---

## 5. Audit the arrangement

Before writing notes, confirm the arrangement is clean against the skeleton (this
needs no Live — but do it here so the apply step is trustworthy):

```bash
sc-produce audit examples/pression_archivee.arrangement.yml \
    --structure examples/pression_archivee.yml
```

**Success:** a wall of `✓` and `0 error(s)`. If you deliberately break it — set a
velocity to `150`, or move a clip onto `A_server_hum` — the audit should report the
exact offending cell/note. That is the gate working.

---

## 6. Apply the arrangement

With the scaffolded set still open:

```bash
sc-produce apply examples/pression_archivee.arrangement.yml \
    --structure examples/pression_archivee.yml
```

**What success looks like:**

- The report ends with `0 error(s)` (OK lines are hidden by default in `apply`).
- Each MIDI track now has clips in the scene rows that the arrangement populates;
  double-clicking a clip shows the authored notes in the piano roll.
- The audio tracks (`A_*`) have **no** clips — by design.

Re-running `apply` is safe: it reconciles each clip to the desired notes
(**remove → modify → add**) and reads back, so a second run is effectively a no-op
on an already-correct set.

**Dry run** to preview the per-cell plan without writing:

```bash
sc-produce apply examples/pression_archivee.arrangement.yml \
    --structure examples/pression_archivee.yml --dry-run
```

### Or do it all at once

```bash
sc-produce pipeline examples/pression_archivee.yml \
    examples/pression_archivee.arrangement.yml
```

This audits (gating on errors), then scaffolds, then applies. Expect three report
blocks (`Audit`, `Scaffold`, `Apply`), each ending `0 error(s)`.

### Can't run next to Live? Emit a launcher

If your shell is **not** on the machine running Live, generate a self-contained
script and run it where Live is open:

```bash
# on the build box / CI / container:
sc-produce pipeline examples/pression_archivee.yml \
    examples/pression_archivee.arrangement.yml --launcher run_pression.py

# copy run_pression.py to the machine with Live open, then:
python run_pression.py
```

The launcher embeds the audited specs inline and depends only on `sc_produce` and
`ableton_bridge`.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `OSCTimeoutError` on the first call | Live is not running | Start Live and open a set |
| `OSCTimeoutError`, Live is running | AbletonOSC not selected as a Control Surface | Preferences → Link/Tempo/MIDI → set Control Surface to **AbletonOSC** |
| `OSCTimeoutError`, AbletonOSC enabled | Wrong ports, or another client holds 11001 | Confirm `--send-port 11000` / `--receive-port 11001`; close any other AbletonOSC client / second `sc-produce` run |
| Tracks/scenes missing on first run, present on re-run | Creates raced ahead of Live (writes are unacknowledged) | Raise `--settle` (e.g. `--settle 0.5`) |
| Notes land an octave too high/low | C3-vs-C4 octave mismatch | Live labels MIDI 60 as **C3** (default `--middle-c-octave 3`). For strict SPN use `--middle-c-octave 4`. Pick one and be consistent |
| Audio track reported as cannot hold MIDI during `apply` | A cell targets an `audio` track | Correct the track's `type` in the structure spec (the headline bug — this is the tool catching it) |
| `Spec ... failed validation` / "syntax error" | Unknown key or wrong type in a YAML spec | Fix the reported key/line; structure is strict (`extra="forbid"`) |
| Returns/sends look wrong on a pre-existing set | Returns aren't name-resolvable over OSC | `scaffold` only creates returns on a **blank** set; start from a new set or configure sends by index in Live |

For the underlying constraints (unacknowledged writes, atomic-as-possible modify,
single client per Live, octave convention), see the bridge's
[`KNOWN_LIMITATIONS.md`](https://github.com/jobforelias1-del/ableton-bridge-v2/blob/main/KNOWN_LIMITATIONS.md)
and the [architecture doc](architecture.md#known-limitations-v01).

---

See also: [doctrine](pipeline-doctrine.md) · [architecture](architecture.md) ·
[usage](usage.md) · [README](../README.md)
