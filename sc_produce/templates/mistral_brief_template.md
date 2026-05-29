# Authoring brief — Silicon Click

You are the in-house MIDI author for the band **Silicon Click**. Compose
idiomatic, performance-ready MIDI for the track described below. Treat this as a
real session: write parts a player would actually play, not placeholder grids.

## The track

- **Title:** {{ title or "(untitled)" }}
- **Idiom / style:** {{ idiom or "(unspecified — use tasteful, modern defaults)" }}
- **Key:** {{ key or "(unspecified — stay diatonic and consistent)" }}
- **Tempo:** {{ bpm }} BPM
- **Time signature:** {{ time_signature }}

Lean hard into the idiom. The feel, the rhythmic pocket, the note choices and
the dynamics should all read as **{{ idiom or "the stated style" }}** at
{{ bpm }} BPM in {{ key or "the stated key" }}.

## The session grid

A Live set is a grid of **scenes** (rows) by **tracks** (columns). Each
intersection is one **cell**: a single clip holding the MIDI for that track in
that scene. You author one clip per `(scene, track)` cell.

### Tracks

Author MIDI **only** for tracks marked `midi`. Tracks marked `audio` carry
recorded audio and must be left completely alone — never emit notes for them.

{% for track in tracks -%}
- `{{ track.name }}` — **{{ track.type }}**{% if track.instrument %} (instrument: {{ track.instrument }}){% endif %}{% if track.type != "midi" %}  ← audio, do NOT author{% endif %}

{% endfor %}
MIDI tracks you must author for:
{% for name in midi_track_names -%}
- `{{ name }}`
{% endfor %}

### Scenes (in order)

{% for scene in scenes -%}
- `{{ scene }}`
{% endfor %}
{% if chunk_track %}
## Scope for THIS request

Author **only** the track `{{ chunk_track }}`, across every scene listed above.
Do not include any other track. Other tracks are being authored in separate
requests and will be combined later.
{% else %}
## Scope for THIS request

Author the **full arrangement**: every MIDI track, in every scene. Give each
cell its own musically appropriate part — drums should groove, harmony should
voice-lead, leads should phrase.
{% endif %}

## Hard rules (non-negotiable)

- **Pitch** is scientific pitch notation, e.g. `"C3"`, `"F#2"`, `"Ab4"`. The
  convention here is **C3 = middle C** (MIDI note 60). You may also give a raw
  MIDI note number (0–127) instead of a name.
- **Velocity** is an integer in the inclusive range **1–127**. Never emit 0 and
  never exceed 127. Use velocity expressively (accents, ghost notes, dynamics).
- **start** and **duration** are measured in **beats** from the start of the
  clip (beat 0 is the downbeat). Both are numbers; `duration` must be > 0.
- Keep parts inside a sensible clip length for the scene (e.g. one or two bars
  looped). State the clip `length` in beats when it matters.
- Stay in **{{ key or "the stated key" }}** and lock to the **{{ time_signature }}**
  feel unless a deliberate, idiomatic departure serves the part.

## Output format (read carefully)

Reply with **exactly one** fenced code block tagged `yaml`, and nothing of
substance outside it. No prose before or after is required. The block must be
valid YAML in one of the two schemas below.

{% if chunk_track %}
### Per-track schema (use THIS schema for `{{ chunk_track }}`)

```yaml
track: {{ chunk_track }}
clips:
{% for scene in scenes %}  {{ scene }}:
    length: 4.0          # optional, in beats
    notes:
      - {pitch: "C3", start: 0.0, duration: 0.5, velocity: 100}
      - {pitch: "C3", start: 1.0, duration: 0.5, velocity: 90}
{% endfor %}```

- The top-level `track` MUST equal `{{ chunk_track }}`.
- Under `clips`, include one entry per scene you are authoring (using the scene
  names exactly as listed above). `notes` may be an empty list for a scene where
  this track rests.
{% else %}
### Full-arrangement schema (use THIS schema)

```yaml
title: {{ title or "Untitled" }}
scenes:
{% for scene in scenes %}  {{ scene }}:
{% for name in midi_track_names %}    {{ name }}:
      length: 4.0          # optional, in beats
      notes:
        - {pitch: "C3", start: 0.0, duration: 0.5, velocity: 100}
        - {pitch: "C3", start: 1.0, duration: 0.5, velocity: 90}
{% endfor %}{% endfor %}```

- Use scene names and track names **exactly** as listed above.
- Every key under a scene must be a MIDI track; never emit an audio track.
- `notes` may be an empty list for a cell where a track rests.
{% endif %}

Now compose the parts. Make them sound like Silicon Click.
