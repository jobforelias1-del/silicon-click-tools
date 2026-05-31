# ableton-bridge onboarding — push to GitHub + both-repo Code session

> Phase 1 of the scene-follow-actions mission is blocked until `ableton-bridge`
> is on GitHub **and** a Claude Code session is authorized for both repos. This
> file is the exact runbook. Hand the commands to Elias; the access step is his.

## Why this is needed

The bridge currently lives only at `~/Projects/ableton-bridge` on Elias's Mac.
The Code session that does Phase 1 (a) can't see it — the container only cloned
`silicon-click-tools` — and (b) is GitHub-scoped to `silicon-click-tools` *only*,
so it cannot open a PR against a bridge repo even once one exists. Both facts have
to change before Phase 1 can produce its deliverable (a PR on the bridge).

## Step 1 — Elias: push the bridge to GitHub

Run from the Mac, in the bridge working copy. These commands assume the repo
`jobforelias1-del/ableton-bridge` has been **created empty** on GitHub first
(no README/license, so the first push isn't a non-fast-forward).

```bash
cd ~/Projects/ableton-bridge

# If it's not a git repo yet:
git init
git add -A
git commit -m "Initial import of ableton-bridge v2"

# If it IS already a git repo, skip init/add/commit above and just continue.

# Point it at the new GitHub repo and push the default branch:
git branch -M main
git remote add origin https://github.com/jobforelias1-del/ableton-bridge.git
git push -u origin main
```

If `git remote add` errors with "remote origin already exists" (the local repo
had a remote), replace it instead:

```bash
git remote set-url origin https://github.com/jobforelias1-del/ableton-bridge.git
git push -u origin main
```

Verify: <https://github.com/jobforelias1-del/ableton-bridge> shows the source,
including `KNOWN_LIMITATIONS.md` and the AbletonOSC commit pin referenced by
silicon-click-tools' docs.

## Step 2 — Elias: authorize a both-repo Code session

The current session's GitHub tools are restricted to `silicon-click-tools`. Phase 1
needs a session whose repo scope includes **both** `silicon-click-tools` and the
new `ableton-bridge`. Start a fresh Claude Code session (web or app) with both
repos selected/granted, OR add `ableton-bridge` to this environment's authorized
repositories, then re-open. Confirm by checking that the new session can
`list_branches` on `jobforelias1-del/ableton-bridge` without a scope-denied error.

> Note: this present session cannot widen its own scope — repo authorization is
> set when the environment/session is created. So Phase 1's bridge work runs in
> the new both-repo session, not here.

## Step 3 — Phase 1 begins (in the both-repo session)

Only once Steps 1–2 are done:

1. Clone/read the bridge; locate the OSC-send + AbletonOSC address surface.
2. **Source-read + introspect first** — do NOT write follow-action methods from
   LOM memory. Confirm against a running Live session:
   - whether the LOM exposes a **scene-level loop/repeat count** (if yes, the
     `repeat_count` model gets even simpler — see decisions doc);
   - the exact AbletonOSC addresses/property names for Follow Action Time,
     Follow Action A/B, Chance A/B, Jump Target A/B, per-scene enable, and the
     global Enable Follow Actions toggle.
   (The 2026-05-27 `save_song()` failure is the standing reason for this rule.)
3. Implement the setter methods + a 3-scene smoke test (INTRO 16-beat → Next;
   CHORUS 32-beat → Play-Again-once-then-Next; OUTRO 16-beat → Stop) that
   verifies playback flows correctly.
4. Open a **draft PR** on `jobforelias1-del/ableton-bridge`.
