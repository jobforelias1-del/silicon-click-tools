"""Generate a self-contained launcher script.

When ``apply``/``pipeline`` are run somewhere Live is not reachable (CI, a remote
box, this container), they can instead emit a standalone Python script that the
producer runs **locally**, against their open Live set. The script embeds the
(already audited) structure and arrangement inline as validated dict literals, so
it is a single portable file that depends only on ``sc_produce`` and
``ableton_bridge`` -- no spec files need to travel with it.
"""

from __future__ import annotations

import datetime as _dt
import pprint
from pathlib import Path

from .models import ArrangementSpec, StructureSpec

_HEADER = '''#!/usr/bin/env python3
"""Auto-generated Silicon Click launcher{title_suffix}.

Generated {timestamp}.

Run this against a *running* Ableton Live session with AbletonOSC enabled as the
active Control Surface:

    python {filename}

Depends only on `sc_produce` and `ableton_bridge` (both pip-installable). It will
{actions}.
"""

from sc_produce.live_session import LiveSession
from sc_produce.spec import load_arrangement_data, load_structure_data

MIDDLE_C_OCTAVE = {middle_c_octave}

STRUCTURE_DATA = {structure_data}

ARRANGEMENT_DATA = {arrangement_data}
'''

_MAIN = '''

def main() -> int:
    """Materialise the embedded project in the running Live set."""
    structure = load_structure_data(STRUCTURE_DATA)
    arrangement = (
        load_arrangement_data(ARRANGEMENT_DATA) if ARRANGEMENT_DATA is not None else None
    )
    with LiveSession(middle_c_octave=MIDDLE_C_OCTAVE) as session:
        if not session.bridge.ping():
            print("Ableton Live is not reachable (is AbletonOSC enabled?)")
            return 1
{body}
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def _format_data(data: object) -> str:
    """Pretty-print a dict literal, preserving key order."""
    return pprint.pformat(data, indent=4, width=96, sort_dicts=False)


def generate_launcher(
    structure: StructureSpec,
    arrangement: ArrangementSpec | None = None,
    *,
    do_scaffold: bool = True,
    do_apply: bool = True,
    middle_c_octave: int = 3,
    filename: str = "launcher.py",
) -> str:
    """Render a self-contained launcher script as a string.

    Args:
        structure: The structure spec to embed and scaffold.
        arrangement: The arrangement spec to embed and apply, if any.
        do_scaffold: Whether the launcher should scaffold the structure.
        do_apply: Whether the launcher should apply the arrangement.
        middle_c_octave: Octave convention baked into the launcher.
        filename: The intended filename, used only in the docstring.

    Returns:
        The launcher source code.
    """
    apply_enabled = do_apply and arrangement is not None
    actions: list[str] = []
    if do_scaffold:
        actions.append("scaffold the track/scene/send skeleton")
    if apply_enabled:
        actions.append("apply the MIDI arrangement cell by cell")
    action_text = " and ".join(actions) if actions else "connect and verify reachability"

    structure_data = _format_data(
        structure.model_dump(mode="json", by_alias=True, exclude_none=True)
    )
    if arrangement is not None:
        arrangement_data = _format_data(
            arrangement.model_dump(mode="json", by_alias=True, exclude_none=True)
        )
    else:
        arrangement_data = "None"

    title_suffix = f" for {structure.title!r}" if structure.title else ""
    header = _HEADER.format(
        title_suffix=title_suffix,
        timestamp=_dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        filename=filename,
        actions=action_text,
        middle_c_octave=middle_c_octave,
        structure_data=structure_data,
        arrangement_data=arrangement_data,
    )

    body_lines: list[str] = []
    if do_scaffold:
        body_lines.append("        from sc_produce.scaffold import scaffold_project")
        body_lines.append("        scaffold_report = scaffold_project(structure, session)")
        body_lines.append("        print(scaffold_report.render())")
    if apply_enabled:
        body_lines.append("        from sc_produce.apply import apply_project")
        body_lines.append("        apply_report = apply_project(structure, arrangement, session)")
        body_lines.append("        print(apply_report.render(show_ok=False))")
    if not body_lines:
        body_lines.append('        print("Connected; nothing to do.")')
    body = "\n".join(body_lines)

    return header + _MAIN.format(body=body)


def write_launcher(path: str | Path, source: str) -> None:
    """Write launcher source to ``path`` and mark it executable.

    Args:
        path: Destination path.
        source: The launcher source code.
    """
    p = Path(path)
    p.write_text(source, encoding="utf-8")
    try:
        p.chmod(0o755)
    except OSError:  # pragma: no cover - non-POSIX filesystems
        pass
