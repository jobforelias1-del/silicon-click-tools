"""Tests for self-contained launcher generation."""

from __future__ import annotations

import os

from sc_produce.launcher import generate_launcher, write_launcher


def test_launcher_with_structure_and_arrangement_compiles(structure, arrangement):
    src = generate_launcher(structure, arrangement)
    compile(src, "launcher.py", "exec")  # must be valid Python
    assert "scaffold_project" in src
    assert "apply_project" in src
    # specs are embedded inline as dict literals
    assert "STRUCTURE_DATA = {" in src
    assert "ARRANGEMENT_DATA = {" in src
    assert "Pression Archivée" in src
    assert "MIDDLE_C_OCTAVE = 3" in src


def test_launcher_structure_only_disables_apply(structure):
    src = generate_launcher(structure)  # no arrangement
    compile(src, "launcher.py", "exec")
    assert "scaffold_project" in src
    assert "apply_project" not in src
    assert "ARRANGEMENT_DATA = None" in src


def test_launcher_apply_only(structure, arrangement):
    src = generate_launcher(structure, arrangement, do_scaffold=False, do_apply=True)
    compile(src, "launcher.py", "exec")
    assert "apply_project" in src
    assert "scaffold_project" not in src


def test_launcher_noop_body(structure):
    src = generate_launcher(structure, None, do_scaffold=False, do_apply=False)
    compile(src, "launcher.py", "exec")
    assert "nothing to do" in src


def test_launcher_honours_middle_c_octave(structure, arrangement):
    src = generate_launcher(structure, arrangement, middle_c_octave=4)
    assert "MIDDLE_C_OCTAVE = 4" in src


def test_write_launcher_creates_executable_file(tmp_path, structure, arrangement):
    path = tmp_path / "go.py"
    src = generate_launcher(structure, arrangement, filename="go.py")
    write_launcher(path, src)
    assert path.exists()
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
    # best-effort executable bit on POSIX
    assert os.access(path, os.X_OK)
