"""Tests for spec loading, dumping and merging."""

from __future__ import annotations

import pytest

from sc_produce.errors import SpecError
from sc_produce.models import ArrangementSpec, ClipSpec, NoteSpec
from sc_produce.spec import (
    dump_arrangement,
    dump_structure,
    load_arrangement,
    load_arrangement_data,
    load_structure,
    load_structure_data,
    merge_arrangement,
    save_arrangement,
)


def test_structure_roundtrip(structure):
    text = dump_structure(structure)
    assert "from:" in text  # send alias is emitted, not from_
    reloaded = load_structure_data(__import__("yaml").safe_load(text))
    assert reloaded == structure


def test_arrangement_roundtrip(arrangement):
    text = dump_arrangement(arrangement)
    reloaded = load_arrangement_data(__import__("yaml").safe_load(text))
    assert reloaded == arrangement


def test_load_structure_from_file(tmp_path, structure):
    path = tmp_path / "s.yml"
    path.write_text(dump_structure(structure), encoding="utf-8")
    assert load_structure(path) == structure


def test_load_arrangement_from_file(tmp_path, arrangement):
    path = tmp_path / "a.yml"
    path.write_text(dump_arrangement(arrangement), encoding="utf-8")
    assert load_arrangement(path) == arrangement


def test_missing_file_raises_specerror():
    with pytest.raises(SpecError):
        load_structure("/nonexistent/definitely/missing.yml")


def test_invalid_yaml_raises_specerror(tmp_path):
    path = tmp_path / "bad.yml"
    path.write_text("scenes: [unclosed\n", encoding="utf-8")
    with pytest.raises(SpecError):
        load_arrangement(path)


def test_non_mapping_top_level_raises(tmp_path):
    path = tmp_path / "list.yml"
    path.write_text("- a\n- b\n", encoding="utf-8")
    with pytest.raises(SpecError):
        load_structure(path)


def test_empty_file_loads_defaults(tmp_path):
    path = tmp_path / "empty.yml"
    path.write_text("", encoding="utf-8")
    spec = load_structure(path)
    assert spec.bpm == 120.0
    assert spec.tracks == []


def test_validation_error_is_wrapped_and_readable():
    with pytest.raises(SpecError) as exc:
        load_structure_data({"tracks": [{"name": "x", "type": "banana"}]})
    assert "Structure spec failed validation" in str(exc.value)
    assert "tracks" in str(exc.value)


def test_save_arrangement(tmp_path, arrangement):
    path = tmp_path / "out.yml"
    save_arrangement(arrangement, path)
    assert load_arrangement(path) == arrangement


def test_save_arrangement_bad_path_raises(arrangement):
    with pytest.raises(SpecError):
        save_arrangement(arrangement, "/nonexistent/dir/out.yml")


def test_merge_arrangement_adds_and_overrides_without_mutation():
    base = ArrangementSpec(
        scenes={
            "Intro": {"D_kick": ClipSpec(notes=[NoteSpec(pitch="C1", start=0.0, duration=1.0)])},
        }
    )
    addition = ArrangementSpec(
        scenes={
            "Intro": {
                "K_piano": ClipSpec(notes=[NoteSpec(pitch="A2", start=0.0, duration=2.0)]),
                # overrides the base D_kick cell
                "D_kick": ClipSpec(notes=[NoteSpec(pitch="C1", start=2.0, duration=1.0)]),
            },
            "Verse": {"D_kick": ClipSpec(notes=[])},
        }
    )
    merged = merge_arrangement(base, addition)
    # base untouched
    assert base.cell("Intro", "K_piano") is None
    assert base.cell("Intro", "D_kick").notes[0].start == 0.0
    # merged has both, with override applied and new scene/cells added
    assert merged.cell("Intro", "K_piano") is not None
    assert merged.cell("Intro", "D_kick").notes[0].start == 2.0
    assert merged.cell("Verse", "D_kick") is not None


def test_merge_title_precedence():
    base = ArrangementSpec(title="Base")
    addition = ArrangementSpec(title="New")
    assert merge_arrangement(base, addition).title == "New"
    assert merge_arrangement(base, ArrangementSpec()).title == "Base"
