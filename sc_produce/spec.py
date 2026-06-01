"""Loading, dumping and merging of structure and arrangement specs.

All YAML and validation failures are wrapped in :class:`~sc_produce.errors.SpecError`
so the CLI presents one readable message instead of a raw traceback. This is the
single choke point for turning a flawed document into a "syntax error", which is
one of the failure classes the auditor reports on.
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from .errors import SpecError
from .models import ArrangementSpec, StructureSpec


def _read_yaml(path: str | Path) -> dict[str, Any]:
    """Read a YAML file into a mapping.

    Args:
        path: Path to the YAML document.

    Returns:
        The parsed mapping.

    Raises:
        SpecError: If the file is missing, unreadable, not valid YAML, or does not
            contain a top-level mapping.
    """
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise SpecError(f"Could not read spec file {p}: {exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise SpecError(f"Invalid YAML in {p}: {exc}") from exc
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise SpecError(f"Spec file {p} must contain a YAML mapping at the top level")
    return data


def _format_validation_error(label: str, exc: ValidationError) -> str:
    """Render a pydantic validation error as a compact, multi-line message."""
    lines = [f"{label} failed validation:"]
    for err in exc.errors():
        loc = ".".join(str(part) for part in err["loc"]) or "<root>"
        lines.append(f"  - {loc}: {err['msg']}")
    return "\n".join(lines)


def load_structure_data(data: dict[str, Any]) -> StructureSpec:
    """Validate a mapping into a :class:`StructureSpec`.

    Args:
        data: The raw mapping (e.g. from YAML).

    Returns:
        The validated structure spec.

    Raises:
        SpecError: If validation fails.
    """
    try:
        return StructureSpec.model_validate(data)
    except ValidationError as exc:
        raise SpecError(_format_validation_error("Structure spec", exc)) from exc


def load_arrangement_data(data: dict[str, Any]) -> ArrangementSpec:
    """Validate a mapping into an :class:`ArrangementSpec`.

    Args:
        data: The raw mapping (e.g. from YAML).

    Returns:
        The validated arrangement spec.

    Raises:
        SpecError: If validation fails.
    """
    try:
        return ArrangementSpec.model_validate(data)
    except ValidationError as exc:
        raise SpecError(_format_validation_error("Arrangement spec", exc)) from exc


def load_structure(path: str | Path) -> StructureSpec:
    """Load and validate a structure spec from a YAML file.

    Args:
        path: Path to the structure YAML.

    Returns:
        The validated structure spec.

    Raises:
        SpecError: If the file cannot be read or fails validation.
    """
    return load_structure_data(_read_yaml(path))


def load_arrangement(path: str | Path) -> ArrangementSpec:
    """Load and validate an arrangement spec from a YAML file.

    Args:
        path: Path to the arrangement YAML.

    Returns:
        The validated arrangement spec.

    Raises:
        SpecError: If the file cannot be read or fails validation.
    """
    return load_arrangement_data(_read_yaml(path))


def dump_structure(spec: StructureSpec) -> str:
    """Serialise a :class:`StructureSpec` to YAML text (aliases, no nulls)."""
    data = spec.model_dump(mode="json", by_alias=True, exclude_none=True)
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def dump_arrangement(spec: ArrangementSpec) -> str:
    """Serialise an :class:`ArrangementSpec` to YAML text (aliases, no nulls)."""
    data = spec.model_dump(mode="json", by_alias=True, exclude_none=True)
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def save_arrangement(spec: ArrangementSpec, path: str | Path) -> None:
    """Write an arrangement spec to ``path`` as YAML.

    Args:
        spec: The arrangement to write.
        path: Destination path.

    Raises:
        SpecError: If the file cannot be written.
    """
    try:
        Path(path).write_text(dump_arrangement(spec), encoding="utf-8")
    except OSError as exc:
        raise SpecError(f"Could not write arrangement to {path}: {exc}") from exc


def merge_arrangement(base: ArrangementSpec, addition: ArrangementSpec) -> ArrangementSpec:
    """Deep-merge ``addition`` into ``base``, returning a new arrangement.

    Cells (``scene -> track``) present in ``addition`` replace those in ``base``;
    everything else is preserved. Neither argument is mutated. This is how a
    captured Mistral response (often one track at a time) accumulates into a
    complete arrangement.

    Args:
        base: The arrangement to merge into.
        addition: The newly captured/authored cells.

    Returns:
        A new merged :class:`ArrangementSpec`.
    """
    merged_scenes = copy.deepcopy(base.scenes)
    for scene_name, tracks in addition.scenes.items():
        merged_scenes.setdefault(scene_name, {})
        for track_name, clip in tracks.items():
            merged_scenes[scene_name][track_name] = copy.deepcopy(clip)
    return ArrangementSpec(title=addition.title or base.title, scenes=merged_scenes)
