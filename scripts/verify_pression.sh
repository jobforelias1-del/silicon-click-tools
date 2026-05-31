#!/usr/bin/env bash
#
# Staged real-Live verification for "Pression Archivée".
#
# This is the one-command version of docs/testing-on-real-live.md, specialised to
# the Pression Archivée example specs. It runs everything that can be checked
# *without* Ableton first (tests + audit gate), and only then touches Live.
#
#   Phase A (headless): test suite + audit gate. No Live required.
#   Phase B (Live):     ping Ableton, then scaffold -> audit -> apply.
#
# Usage, from the repo root:
#
#   1. With Live CLOSED (or open, doesn't matter) -- proves the tool is sound:
#         bash scripts/verify_pression.sh --headless
#
#   2. With Live OPEN on a NEW, EMPTY set and AbletonOSC enabled -- the real run:
#         bash scripts/verify_pression.sh
#
# Notes baked in from pre-flight:
#   * Tests run via `python -m pytest` (bare `pytest` may resolve to a stale shim).
#   * The audit is run WITHOUT --strict on purpose: the arrangement is a sparse
#     grid (drums drop out in Break/Outro), which is 36 intentional warnings.
#     --strict would fail the gate on those by design-correct gaps.

set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 2

STRUCTURE="examples/pression_archivee.yml"
ARRANGEMENT="examples/pression_archivee.arrangement.yml"

HEADLESS_ONLY=0
[ "${1:-}" = "--headless" ] && HEADLESS_ONLY=1

hr() { printf '%s\n' "------------------------------------------------------------"; }
say() { printf '\n%s\n' "$*"; }

# ----------------------------------------------------------------------------- #
# Phase A -- headless gate (no Live)
# ----------------------------------------------------------------------------- #
say "PHASE A  headless gate (no Ableton required)"; hr

say "[A1] test suite (python -m pytest)"
if ! python -m pytest -q; then
  echo "NO-GO: test suite failed. Fix before touching Live."; exit 1
fi

say "[A2] audit gate  (expect: 0 error(s); ~36 'incomplete grid' warnings are fine)"
if ! sc-produce audit "$ARRANGEMENT" --structure "$STRUCTURE"; then
  echo "NO-GO: audit reported errors. Fix the arrangement/structure before applying."; exit 1
fi

echo; echo "PHASE A: GO  (tool is sound, specs are clean)"

if [ "$HEADLESS_ONLY" -eq 1 ]; then
  echo; echo "Headless run complete. Re-run WITHOUT --headless once Ableton Live is"
  echo "open on a NEW empty set with AbletonOSC enabled to do the real build."
  exit 0
fi

# ----------------------------------------------------------------------------- #
# Phase B -- Live
# ----------------------------------------------------------------------------- #
say "PHASE B  real Ableton Live"; hr

say "[B1] probing Ableton Live (AbletonOSC on 127.0.0.1:11000/11001)..."
if ! python - <<'PY'
import sys
try:
    from sc_produce import LiveSession
    with LiveSession() as s:
        if not s.bridge.ping():
            sys.exit(1)
        print("    connected. Live version:", s.bridge.get_live_version())
except Exception as exc:  # OSCTimeoutError or anything else == not reachable
    print("    no reply:", exc)
    sys.exit(1)
PY
then
  cat <<'EOF'

NO-GO (not an error -- Live just isn't reachable yet). To fix:
  1. Open Ableton Live on a NEW, EMPTY set (File -> New Live Set).
  2. Preferences -> Link/Tempo/MIDI -> Control Surface -> AbletonOSC.
  3. Re-run:  bash scripts/verify_pression.sh
EOF
  exit 1
fi

say "[B2] pipeline: audit -> scaffold -> apply"; hr
if ! sc-produce pipeline "$STRUCTURE" "$ARRANGEMENT"; then
  echo; echo "PIPELINE reported errors -- read the per-cell report above."; exit 1
fi

cat <<'EOF'

------------------------------------------------------------
PASS/FAIL CHECKLIST  -- verify by eye in Live's Session view:

  [ ] Tracks exist IN ORDER: D_kick D_clap D_rim D_hat D_openhat D_808
      K_piano K_bells P_pad L_lead  (MIDI), then A_server_hum A_vinyl_crackle
      A_field_paris (AUDIO), then returns R_REVERB R_DELAY R_DRIVE.
  [ ] Scenes named: Intro  Verse  Pre  Drop  Break  Outro.
  [ ] Tempo = 142 BPM, time signature 4/4.
  [ ] MIDI tracks (D_/K_/P_/L_) have clips; double-click one -> notes in piano roll.
  [ ] AUDIO tracks (A_*) have NO clips.  <-- the headline bug this tool prevents.
  [ ] MIDI tracks show a MIDI input slot; audio tracks do not.

If all boxes check: the tool is proven against real Live. Save the set.
If a track/scene is missing on first run but appears on re-run, raise the
settle delay:  sc-produce scaffold examples/pression_archivee.yml --settle 0.5
------------------------------------------------------------
EOF
