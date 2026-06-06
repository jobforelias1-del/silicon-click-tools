"""The ``compose`` command: brief generation and Mistral response capture.

``compose`` sits between :mod:`sc_produce.scaffold` (which builds the Live
skeleton) and :mod:`sc_produce.audit`/:mod:`sc_produce.apply` (which check and
write the authored notes). It has two complementary jobs:

* **Author a brief.** Render a high-quality, copy-paste-friendly creative brief
  from a :class:`~sc_produce.models.StructureSpec` -- one prompt that tells
  Mistral exactly what to write and in what YAML schema. For large arrangements
  the brief can be *chunked* one MIDI track at a time (the proven shape: a single
  track authored across every scene), which keeps each generation focused.
* **Ingest a response.** Parse the fenced YAML (or JSON) block Mistral returns --
  in either the full-arrangement or the per-track schema -- into a validated
  :class:`~sc_produce.models.ArrangementSpec`, optionally merging it into an
  arrangement already in progress.

Two run modes wrap those jobs. *Paste* mode (the default) just prints the brief
for the producer to hand to Mistral by hand, then ``--capture-response`` reads
the reply back. *API* mode (``--api``) calls Mistral directly via
:class:`~sc_produce.mistral.MistralClient` and produces the arrangement in one
step. Either way the resulting arrangement is the same shape the rest of the
pipeline consumes.

Every parse/validation problem is funnelled into
:class:`~sc_produce.errors.ComposeError` (with API failures arriving as the
:class:`~sc_produce.errors.MistralAPIError` subclass) so the CLI prints one
readable message instead of a traceback.
"""

from __future__ import annotations

import argparse
import importlib.resources
import os
import re
import sys
from typing import Any

import jinja2
import yaml

from . import common, spec
from .errors import ComposeError, MistralAPIError, SpecError
from .mistral import DEFAULT_MODEL, MistralClient
from .models import ArrangementSpec, ClipSpec, StructureSpec

#: The subcommand name, as it appears on the ``sc-produce`` CLI.
NAME = "compose"

#: One-line help shown in the ``sc-produce`` subcommand listing.
HELP = "Generate the Mistral authoring brief, or ingest its response into an arrangement"

#: The package-data path of the Jinja2 brief template. Loaded via
#: ``files('sc_produce').joinpath('templates', ...)`` so the ``templates``
#: directory needs no ``__init__.py`` to be importable as a resource.
_TEMPLATE_NAME = "mistral_brief_template.md"

#: The note-octave convention restated in every brief: C3 is middle C (MIDI 60),
#: matching Ableton Live's default display.
_MIDDLE_C_NOTE = "C3 = middle C (MIDI note 60)"


def _load_template_text() -> str:
    """Read the raw brief template from package data.

    Returns:
        The template source as text.
    """
    resource = importlib.resources.files("sc_produce").joinpath("templates", _TEMPLATE_NAME)
    return resource.read_text(encoding="utf-8")


def _render(context: dict[str, Any]) -> str:
    """Render the brief template with ``context``.

    Args:
        context: The Jinja2 variables the template expects (title, bpm, key,
            idiom, time_signature, tracks, midi_track_names, scenes,
            chunk_track, middle_c).

    Returns:
        The rendered brief text.
    """
    env = jinja2.Environment(
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        autoescape=False,
    )
    template = env.from_string(_load_template_text())
    return template.render(**context)


def _track_context(structure: StructureSpec) -> list[dict[str, Any]]:
    """Return a plain-dict view of the structure's regular tracks for the brief."""
    return [
        {"name": t.name, "type": t.type.value, "instrument": t.instrument} for t in structure.tracks
    ]


def build_brief(structure: StructureSpec, *, chunk_track: str | None = None) -> str:
    """Render the authoring brief for ``structure``.

    Args:
        structure: The Live skeleton to brief Mistral against.
        chunk_track: When given, scope the brief to a single MIDI track (authored
            across every scene) and request only that track's schema. When
            ``None``, brief the full arrangement.

    Returns:
        The rendered brief, ready to hand to Mistral.
    """
    num, den = structure.time_signature
    context: dict[str, Any] = {
        "title": structure.title,
        "bpm": structure.bpm,
        "key": structure.key,
        "idiom": structure.idiom,
        "time_signature": f"{num}/{den}",
        "tracks": _track_context(structure),
        "midi_track_names": structure.midi_track_names(),
        "scenes": list(structure.scenes),
        "chunk_track": chunk_track,
        "middle_c": _MIDDLE_C_NOTE,
    }
    return _render(context)


def build_chunked_briefs(structure: StructureSpec) -> list[tuple[str, str]]:
    """Render one per-track brief for each MIDI track in ``structure``.

    This is the proven shape for big arrangements: rather than asking Mistral for
    the whole grid at once, ask it for one track across all scenes at a time and
    merge the replies. Audio tracks are skipped (they are never authored).

    Args:
        structure: The Live skeleton to brief against.

    Returns:
        A list of ``(track_name, brief)`` pairs, one per MIDI track, in order.
    """
    return [
        (name, build_brief(structure, chunk_track=name)) for name in structure.midi_track_names()
    ]


#: Matches a fenced code block, capturing an optional language tag and the body.
_FENCE_RE = re.compile(
    r"```[ \t]*(?P<lang>[A-Za-z0-9_+-]*)[ \t]*\r?\n(?P<body>.*?)```",
    re.DOTALL,
)


def _extract_block(text: str) -> str:
    """Return the most likely YAML/JSON payload from a Mistral reply.

    Prefers a fenced block explicitly tagged ``yaml``/``yml``/``json``; failing
    that, the first fenced block of any kind; failing that, the whole text (so a
    bare-YAML reply with no fences still parses).

    Args:
        text: The raw assistant reply.

    Returns:
        The extracted code-block body (or the whole input when unfenced).
    """
    blocks = [(m.group("lang").lower(), m.group("body")) for m in _FENCE_RE.finditer(text)]
    if not blocks:
        return text
    for lang, body in blocks:
        if lang in {"yaml", "yml", "json"}:
            return body
    return blocks[0][1]


def _clip_from_mapping(raw: Any, *, scene: str, track: str) -> ClipSpec:
    """Validate one cell mapping (``{notes, length?}``) into a :class:`ClipSpec`.

    Args:
        raw: The raw cell mapping from the parsed YAML/JSON.
        scene: The scene name (for error messages).
        track: The track name (for error messages).

    Returns:
        The validated clip.

    Raises:
        ComposeError: If the cell is not a mapping or fails model validation.
    """
    if not isinstance(raw, dict):
        raise ComposeError(
            f"cell {scene!r}/{track!r} must be a mapping with 'notes', got {type(raw).__name__}"
        )
    try:
        return ClipSpec.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError (and any odd input)
        raise ComposeError(f"invalid clip at {scene!r}/{track!r}: {exc}") from exc


def _parse_per_track(data: dict[str, Any]) -> ArrangementSpec:
    """Build an arrangement from the per-track schema (``track`` + ``clips``).

    Args:
        data: The parsed mapping; must carry a string ``track`` and a mapping of
            ``scene -> {notes, length?}`` under ``clips`` (or ``scenes``).

    Returns:
        An arrangement holding ``scenes[scene][track]`` for each authored scene.

    Raises:
        ComposeError: If ``track`` is not a string, the per-scene container is not
            a mapping, or any cell fails validation.
    """
    track = data.get("track")
    if not isinstance(track, str):
        raise ComposeError("per-track response: 'track' must be a string track name")

    clips = data.get("clips", data.get("scenes"))
    if not isinstance(clips, dict):
        raise ComposeError("per-track response: expected a mapping under 'clips' or 'scenes'")

    scenes: dict[str, dict[str, ClipSpec]] = {}
    for scene_name, raw in clips.items():
        clip = _clip_from_mapping(raw, scene=str(scene_name), track=track)
        scenes[str(scene_name)] = {track: clip}
    return ArrangementSpec(title=data.get("title"), scenes=scenes)


def _parse_full(data: dict[str, Any]) -> ArrangementSpec:
    """Build an arrangement from the full schema (``scenes -> track -> cell``).

    Delegates to :func:`sc_produce.spec.load_arrangement_data` so the whole grid
    is validated through the same path the rest of the pipeline uses.

    Args:
        data: The parsed mapping; must carry a ``scenes`` mapping.

    Returns:
        The validated arrangement.

    Raises:
        ComposeError: If ``scenes`` is not a mapping or validation fails.
    """
    scenes = data.get("scenes")
    if not isinstance(scenes, dict):
        raise ComposeError("full response: 'scenes' must be a mapping of scene -> track -> cell")
    payload: dict[str, Any] = {"scenes": scenes}
    if "title" in data:
        payload["title"] = data["title"]
    try:
        return spec.load_arrangement_data(payload)
    except SpecError as exc:
        raise ComposeError(f"invalid arrangement: {exc}") from exc


def parse_response(text: str) -> ArrangementSpec:
    """Parse a Mistral reply into a validated :class:`ArrangementSpec`.

    Extracts the fenced code block (preferring a ``yaml``/``yml``/``json`` tag),
    loads it as YAML -- which also accepts JSON -- and accepts either of the two
    documented schemas: the per-track shape (a ``track`` key plus per-scene clips)
    or the full shape (a ``scenes`` mapping).

    Args:
        text: The raw assistant reply.

    Returns:
        The parsed arrangement.

    Raises:
        ComposeError: If the block is not valid YAML/JSON, is not a mapping, or
            matches neither schema (no ``track`` and no ``scenes`` key), or if any
            cell fails model validation.
    """
    block = _extract_block(text)
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        raise ComposeError(f"response is not valid YAML/JSON: {exc}") from exc

    if not isinstance(data, dict):
        raise ComposeError("response must be a mapping (a YAML/JSON object)")

    if "track" in data:
        return _parse_per_track(data)
    if "scenes" in data:
        return _parse_full(data)
    raise ComposeError("response has neither a 'track' (per-track) nor a 'scenes' (full) key")


def capture_response(text: str, *, base: ArrangementSpec | None = None) -> ArrangementSpec:
    """Parse a reply and merge it into ``base`` (or a fresh arrangement).

    Args:
        text: The raw assistant reply.
        base: An arrangement to merge the parsed cells into; a new empty
            arrangement is used when omitted.

    Returns:
        The merged arrangement (newly parsed cells win over existing ones).

    Raises:
        ComposeError: If the reply cannot be parsed (see :func:`parse_response`).
    """
    return spec.merge_arrangement(base or ArrangementSpec(), parse_response(text))


# ---------------------------------------------------------------------------- #
# CLI wiring
# ---------------------------------------------------------------------------- #
def configure_parser(parser: argparse.ArgumentParser) -> None:
    """Configure the ``compose`` subcommand's argument parser.

    Args:
        parser: The subparser to populate.
    """
    parser.add_argument("structure", help="path to the structure spec YAML")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--paste",
        dest="paste",
        action="store_true",
        default=True,
        help="print the brief to paste into Mistral by hand (the default)",
    )
    mode.add_argument(
        "--api",
        dest="api",
        action="store_true",
        help="call the Mistral API directly (needs MISTRAL_API_KEY)",
    )

    parser.add_argument(
        "--chunked",
        action="store_true",
        help="produce one brief per MIDI track (proven shape for big arrangements)",
    )
    parser.add_argument(
        "--out",
        help="where to write the brief (paste mode) or the raw response (api mode); "
        "default: stdout. In chunked api mode, a directory receives one file per track.",
    )
    parser.add_argument(
        "--capture-response",
        dest="capture_response",
        help="ingest a saved Mistral response (file path) into an arrangement",
    )
    parser.add_argument(
        "--base",
        help="path to an existing arrangement to merge the captured response into",
    )
    parser.add_argument(
        "-o",
        "--arrangement-out",
        dest="arrangement_out",
        help="where to write the resulting arrangement YAML; default: stdout",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Mistral model to request in api mode (default {DEFAULT_MODEL})",
    )


def _emit_arrangement(arrangement: ArrangementSpec, args: argparse.Namespace) -> None:
    """Write the arrangement to ``-o`` if given, else print it as YAML.

    Args:
        arrangement: The arrangement to emit.
        args: Parsed args carrying ``arrangement_out``.

    Raises:
        SpecError: If writing the file fails.
    """
    if args.arrangement_out:
        spec.save_arrangement(arrangement, args.arrangement_out)
    else:
        print(spec.dump_arrangement(arrangement), end="")


def _summarise(arrangement: ArrangementSpec) -> str:
    """Return a one-line ``N scene(s) / N cell(s)`` summary of an arrangement."""
    cells = sum(1 for _ in arrangement.iter_cells())
    return f"{len(arrangement.scenes)} scene(s) / {cells} cell(s)"


def _run_capture(args: argparse.Namespace) -> int:
    """Handle ``--capture-response``: ingest a saved reply into an arrangement.

    Args:
        args: Parsed args (``capture_response``, ``base``, ``arrangement_out``).

    Returns:
        ``0`` on success, ``1`` on a read/parse/validation failure.
    """
    try:
        with open(args.capture_response, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        return common.fail(f"could not read response file {args.capture_response}: {exc}")

    try:
        base = spec.load_arrangement(args.base) if args.base else None
        arrangement = capture_response(text, base=base)
        _emit_arrangement(arrangement, args)
    except (ComposeError, SpecError) as exc:
        return common.fail(str(exc))

    print(f"captured arrangement: {_summarise(arrangement)}", file=sys.stderr)
    return 0


def _run_api(args: argparse.Namespace) -> int:
    """Handle ``--api``: call Mistral directly and build the arrangement.

    In ``--chunked`` mode each MIDI track is briefed and authored separately and
    the replies are merged; if ``--out`` names an existing directory, each raw
    reply is also saved as ``<out>/<track>.txt``. Otherwise a single full brief is
    sent and (optionally) its raw reply written to ``--out``.

    Args:
        args: Parsed args (``model``, ``chunked``, ``out``, ``arrangement_out``).

    Returns:
        ``0`` on success, ``1`` on an API or parse/validation failure.
    """
    structure = spec.load_structure(args.structure)

    try:
        client = MistralClient.from_env(model=args.model)
    except MistralAPIError as exc:
        return common.fail(str(exc))

    try:
        if args.chunked:
            arrangement = ArrangementSpec()
            out_is_dir = bool(args.out) and os.path.isdir(args.out)
            for track_name, brief in build_chunked_briefs(structure):
                reply = client.complete(brief)
                if out_is_dir:
                    _write_text(os.path.join(args.out, f"{track_name}.txt"), reply)
                arrangement = capture_response(reply, base=arrangement)
        else:
            reply = client.complete(build_brief(structure))
            if args.out:
                _write_text(args.out, reply)
            arrangement = capture_response(reply)
        _emit_arrangement(arrangement, args)
    except MistralAPIError as exc:
        return common.fail(str(exc))
    except (ComposeError, SpecError) as exc:
        return common.fail(str(exc))

    print(f"composed arrangement: {_summarise(arrangement)}", file=sys.stderr)
    return 0


def _run_paste(args: argparse.Namespace) -> int:
    """Handle paste mode (the default): render the brief(s) for hand-pasting.

    Args:
        args: Parsed args (``chunked``, ``out``).

    Returns:
        ``0`` on success, ``1`` on a write failure.
    """
    structure = spec.load_structure(args.structure)

    if args.chunked:
        sections = [
            f"\n\n===== TRACK: {name} =====\n\n{brief}"
            for name, brief in build_chunked_briefs(structure)
        ]
        text = "".join(sections).lstrip("\n")
    else:
        text = build_brief(structure)

    if args.out:
        try:
            _write_text(args.out, text)
        except OSError as exc:
            return common.fail(f"could not write brief to {args.out}: {exc}")
    else:
        print(text)
    return 0


def _write_text(path: str, text: str) -> None:
    """Write ``text`` to ``path`` as UTF-8 (a thin, mockable wrapper)."""
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def run(args: argparse.Namespace) -> int:
    """Execute the ``compose`` subcommand.

    Loads the structure spec, then dispatches to capture, API or paste handling
    depending on the flags. Capture mode takes precedence (it ingests a reply);
    otherwise ``--api`` selects API mode and the default is paste mode.

    Args:
        args: Parsed CLI arguments (as configured by :func:`configure_parser`).

    Returns:
        ``0`` on success, ``1`` on any load/parse/API failure.
    """
    try:
        spec.load_structure(args.structure)
    except SpecError as exc:
        return common.fail(str(exc))

    if args.capture_response:
        return _run_capture(args)
    if getattr(args, "api", False):
        return _run_api(args)
    return _run_paste(args)
