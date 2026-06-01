"""Regression tests: commands fail gracefully when Live is unreachable.

The per-command unit tests monkeypatch ``connect`` to a working fake, so they do
not exercise the path where the OSC timeout surfaces *during* the operation (not
during ``connect``, which only binds a socket). These tests drive ``run()`` with a
transport that always times out and assert a clean exit code 1 -- never a leaked
traceback.
"""

from __future__ import annotations

import argparse

from _fakes import FailingTransport

from sc_produce import apply as apply_mod
from sc_produce import common
from sc_produce import pipeline as pipeline_mod
from sc_produce import scaffold as scaffold_mod
from sc_produce.live_session import LiveSession
from sc_produce.spec import dump_arrangement, dump_structure


def _failing_connect(_args) -> LiveSession:
    return LiveSession(transport=FailingTransport())


def _conn_args() -> dict:
    return dict(
        host="127.0.0.1",
        send_port=11000,
        receive_port=11001,
        timeout=5.0,
        middle_c_octave=3,
        json=False,
    )


def test_scaffold_run_handles_timeout(monkeypatch, tmp_path, structure):
    path = tmp_path / "s.yml"
    path.write_text(dump_structure(structure), encoding="utf-8")
    monkeypatch.setattr(common, "connect", _failing_connect)
    args = argparse.Namespace(structure=str(path), dry_run=False, settle=0.0, **_conn_args())
    assert scaffold_mod.run(args) == 1


def test_apply_run_handles_timeout(monkeypatch, tmp_path, structure, arrangement):
    s = tmp_path / "s.yml"
    a = tmp_path / "a.yml"
    s.write_text(dump_structure(structure), encoding="utf-8")
    a.write_text(dump_arrangement(arrangement), encoding="utf-8")
    monkeypatch.setattr(common, "connect", _failing_connect)
    args = argparse.Namespace(
        arrangement=str(a), structure=str(s), dry_run=False, launcher=None, **_conn_args()
    )
    assert apply_mod.run(args) == 1


def test_pipeline_run_handles_timeout(monkeypatch, tmp_path, structure, arrangement):
    s = tmp_path / "s.yml"
    a = tmp_path / "a.yml"
    s.write_text(dump_structure(structure), encoding="utf-8")
    a.write_text(dump_arrangement(arrangement), encoding="utf-8")
    monkeypatch.setattr(common, "connect", _failing_connect)
    args = argparse.Namespace(
        structure=str(s),
        arrangement=str(a),
        launcher=None,
        dry_run=False,
        strict=False,
        force=True,  # skip the audit gate so we reach the connect/operation path
        **_conn_args(),
    )
    assert pipeline_mod.run(args) == 1
