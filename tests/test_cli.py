"""Tests for the CLI wiring and dispatch."""

from __future__ import annotations

import pytest

import sc_produce.scaffold as scaffold_mod
from sc_produce.cli import build_parser, main
from sc_produce.spec import dump_arrangement, dump_structure


def test_build_parser_registers_all_commands():
    parser = build_parser()
    # Drill into the subparsers action to read the registered command names.
    choices = {}
    for action in parser._actions:
        if hasattr(action, "choices") and action.choices:
            choices = action.choices
    assert set(choices) == {"scaffold", "compose", "audit", "apply", "pipeline"}


def test_version_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert "sc-produce" in capsys.readouterr().out


def test_no_command_errors():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2


def test_dispatch_invokes_selected_handler(monkeypatch, tmp_path):
    called = {}

    def fake_run(args):
        called["structure"] = args.structure
        return 7

    monkeypatch.setattr(scaffold_mod, "run", fake_run)
    code = main(["scaffold", "some_structure.yml"])
    assert code == 7
    assert called["structure"] == "some_structure.yml"


def test_audit_end_to_end_clean(tmp_path, structure, arrangement, capsys):
    # The fixture arrangement only authors MIDI tracks; pad missing cells so the
    # only findings are completeness warnings (not errors) -> exit 0.
    structure_path = tmp_path / "s.yml"
    arr_path = tmp_path / "a.yml"
    structure_path.write_text(dump_structure(structure), encoding="utf-8")
    arr_path.write_text(dump_arrangement(arrangement), encoding="utf-8")
    code = main(["audit", str(arr_path), "--structure", str(structure_path)])
    assert code == 0
    assert "Audit" in capsys.readouterr().out


def test_audit_end_to_end_detects_errors(tmp_path, structure, capsys):
    # An arrangement that writes MIDI onto an audio track must fail (exit 1).
    bad = (
        "scenes:\n"
        "  Intro:\n"
        "    A_server_hum:\n"
        "      notes:\n"
        "        - {pitch: C1, start: 0.0, duration: 0.25, velocity: 200}\n"
    )
    structure_path = tmp_path / "s.yml"
    arr_path = tmp_path / "a.yml"
    structure_path.write_text(dump_structure(structure), encoding="utf-8")
    arr_path.write_text(bad, encoding="utf-8")
    code = main(["audit", str(arr_path), "--structure", str(structure_path)])
    assert code == 1
