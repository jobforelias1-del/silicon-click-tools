# sandbox/

A parallel play space. **Nothing in here is load-bearing.**

The main repo (`sc_produce/`, `examples/`, the two-spec discipline, the audit
gate, the doctrine) is the *production* side — careful, source-controlled, every
track starting from a tool. This folder is the opposite of all that on purpose.

## The only rules (there are basically none)

- **Copy and mutate freely.** Grab any example, paste it here, twist it. The
  thing the production side warns against — copy-and-mutated scripts — is exactly
  what this folder is *for*.
- **No audit has to pass.** Break the schema. Put velocities at 200. Author MIDI
  onto an audio track. Whatever. The auditor is a tool you can *choose* to point
  at something here, not a gate you have to clear.
- **No tests cover this.** `tests/` doesn't look here, coverage doesn't count it.
- **Nothing here has to become a track.** Half-ideas are allowed to stay
  half-ideas. Delete things without ceremony.

## What's here to start

- `scratch.yml` / `scratch.arrangement.yml` — a tiny 3-track toy (kick, sub,
  keys) to immediately mess with. Much smaller than the `examples/` track so
  there's less to stare at. Change the key, the BPM, the idiom, throw notes
  around. See what happens.

## If you ever want to use the real tools on something here

You can — they don't care what folder a file lives in:

```bash
sc-produce audit sandbox/scratch.arrangement.yml --structure sandbox/scratch.yml
```

But you never have to. That's the whole point.
