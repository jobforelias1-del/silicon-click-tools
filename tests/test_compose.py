"""Tests for :mod:`sc_produce.compose` and :mod:`sc_produce.mistral`.

These cover the two halves of the ``compose`` command -- rendering the authoring
brief from a :class:`~sc_produce.models.StructureSpec`, and parsing a Mistral
reply back into a validated :class:`~sc_produce.models.ArrangementSpec` -- plus
the thin :class:`~sc_produce.mistral.MistralClient` HTTP wrapper.

No real network is used: :class:`MistralClient` posts through an injected fake
``session`` (a tiny object exposing ``.post``), so every success and error path
is exercised deterministically without the ``responses`` library.
"""

from __future__ import annotations

import argparse
import json

import pytest
import requests
import yaml

from sc_produce import compose, spec
from sc_produce.errors import ComposeError, MistralAPIError
from sc_produce.mistral import DEFAULT_MODEL, MistralClient
from sc_produce.models import ArrangementSpec, ClipSpec, NoteSpec, StructureSpec


# --------------------------------------------------------------------------- #
# Fakes for the Mistral HTTP seam
# --------------------------------------------------------------------------- #
class _FakeResponse:
    """A stand-in for :class:`requests.Response` returned by the fake session."""

    def __init__(
        self,
        payload: dict | None = None,
        *,
        raise_status: Exception | None = None,
        text: str = "",
    ) -> None:
        self._payload = payload if payload is not None else {}
        self._raise_status = raise_status
        self.text = text

    def raise_for_status(self) -> None:
        """Raise the configured error (mimicking a non-2xx status), if any."""
        if self._raise_status is not None:
            raise self._raise_status

    def json(self) -> dict:
        """Return the canned JSON payload."""
        return self._payload


class _FakeSession:
    """A fake ``requests.Session`` capturing the POST and returning a canned reply."""

    def __init__(
        self,
        response: _FakeResponse | None = None,
        *,
        post_error: Exception | None = None,
    ) -> None:
        self._response = response or _FakeResponse()
        self._post_error = post_error
        self.calls: list[dict] = []

    def post(self, url: str, *, json: dict, headers: dict, timeout: float) -> _FakeResponse:
        """Record the request and return the canned response (or raise)."""
        self.calls.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        if self._post_error is not None:
            raise self._post_error
        return self._response


def _payload(content: str) -> dict:
    """Build a realistic Mistral chat-completions JSON payload around ``content``."""
    return {
        "id": "cmpl-test",
        "object": "chat.completion",
        "model": DEFAULT_MODEL,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }


class _FakeClient:
    """A fake :class:`MistralClient` whose ``complete`` returns a canned reply."""

    def __init__(self, reply: str) -> None:
        self._reply = reply
        self.prompts: list[str] = []

    def complete(self, prompt: str, *, system: str | None = None) -> str:
        """Record the prompt and return the canned reply."""
        self.prompts.append(prompt)
        return self._reply


# --------------------------------------------------------------------------- #
# build_brief
# --------------------------------------------------------------------------- #
def test_build_brief_includes_structure_facts_and_output_instruction(
    structure: StructureSpec,
) -> None:
    """The full brief states the tempo/key/idiom, every MIDI track and scene, and YAML."""
    brief = compose.build_brief(structure)

    assert "142" in brief  # bpm
    assert "Am" in brief  # key
    assert "french_drill" in brief  # idiom
    assert "4/4" in brief  # time signature rendered as "n/d"
    for name in structure.midi_track_names():
        assert name in brief
    for scene in structure.scene_names():
        assert scene in brief
    # The exact, load-bearing output instruction.
    assert "```yaml" in brief
    # The middle-C convention is stated.
    assert "C3" in brief


def test_build_brief_full_mode_has_no_per_track_scope(structure: StructureSpec) -> None:
    """Without a chunk track the brief asks for the full arrangement."""
    brief = compose.build_brief(structure)

    assert "full arrangement" in brief.lower()
    # An audio track is listed (so Mistral is told what NOT to author).
    assert "A_server_hum" in brief


def test_build_brief_chunk_track_scopes_to_one_track(structure: StructureSpec) -> None:
    """A chunk brief names its track and uses the per-track scope wording."""
    brief = compose.build_brief(structure, chunk_track="D_kick")

    assert "D_kick" in brief
    # The per-track scope instruction is present (and the full-arrangement one isn't).
    assert "Author **only** the track" in brief
    assert "full arrangement" not in brief.lower()
    # The per-track schema header references the track.
    assert "track: D_kick" in brief


# --------------------------------------------------------------------------- #
# build_chunked_briefs
# --------------------------------------------------------------------------- #
def test_build_chunked_briefs_one_per_midi_track(structure: StructureSpec) -> None:
    """One brief is produced per MIDI track (audio tracks are excluded)."""
    briefs = compose.build_chunked_briefs(structure)

    names = [name for name, _ in briefs]
    assert names == structure.midi_track_names()
    assert "A_server_hum" not in names  # audio track never authored


def test_build_chunked_briefs_each_brief_names_its_track(structure: StructureSpec) -> None:
    """Each chunk brief names its own track and carries the per-track wording."""
    for name, brief in compose.build_chunked_briefs(structure):
        assert name in brief
        # The chunk-specific scope instruction names the single track.
        assert f"Author **only** the track `{name}`" in brief
        assert f"track: {name}" in brief  # the per-track schema header


# --------------------------------------------------------------------------- #
# parse_response
# --------------------------------------------------------------------------- #
def test_parse_response_full_shape() -> None:
    """A fenced yaml block in the full schema yields the right cells."""
    text = (
        "Here is the arrangement:\n"
        "```yaml\n"
        "scenes:\n"
        "  Intro:\n"
        "    D_kick:\n"
        "      length: 4.0\n"
        "      notes:\n"
        '        - {pitch: "C3", start: 0.0, duration: 0.5, velocity: 100}\n'
        "```\n"
        "thanks!\n"
    )

    arr = compose.parse_response(text)

    cell = arr.cell("Intro", "D_kick")
    assert cell is not None
    assert cell.length == 4.0
    assert len(cell.notes) == 1
    assert cell.notes[0].pitch == "C3"
    assert cell.notes[0].velocity == 100


def test_parse_response_per_track_shape() -> None:
    """A per-track block (``track`` + ``clips``) places the cell under scene/track."""
    text = (
        "```yaml\n"
        "track: D_kick\n"
        "clips:\n"
        "  Intro:\n"
        "    notes:\n"
        "      - {pitch: 36, start: 0.0, duration: 0.25, velocity: 110}\n"
        "```\n"
    )

    arr = compose.parse_response(text)

    cell = arr.cell("Intro", "D_kick")
    assert cell is not None
    assert cell.notes[0].pitch == 36
    assert list(arr.scenes["Intro"].keys()) == ["D_kick"]


def test_parse_response_per_track_accepts_scenes_key() -> None:
    """The per-track schema also accepts ``scenes`` as the per-scene container."""
    text = (
        "```yaml\n"
        "track: K_piano\n"
        "scenes:\n"
        "  Verse:\n"
        '      notes: [{pitch: "A2", start: 0.0, duration: 1.0, velocity: 70}]\n'
        "```\n"
    )

    arr = compose.parse_response(text)

    cell = arr.cell("Verse", "K_piano")
    assert cell is not None
    assert cell.notes[0].pitch == "A2"


def test_parse_response_json_block() -> None:
    """A fenced json block parses (YAML is a JSON superset)."""
    body = {
        "scenes": {
            "Intro": {"K_piano": {"notes": [{"pitch": "A2", "start": 0.0, "duration": 2.0}]}}
        }
    }
    text = "```json\n" + json.dumps(body) + "\n```\n"

    arr = compose.parse_response(text)

    cell = arr.cell("Intro", "K_piano")
    assert cell is not None
    assert cell.notes[0].pitch == "A2"


def test_parse_response_bare_block_without_language_tag() -> None:
    """An untagged fenced block is used when no labelled block is present."""
    text = "```\n" "track: D_clap\n" "clips:\n" "  Drop:\n" "    notes: []\n" "```\n"

    arr = compose.parse_response(text)

    cell = arr.cell("Drop", "D_clap")
    assert cell is not None
    assert cell.notes == []


def test_parse_response_no_code_block_and_no_keys_raises() -> None:
    """Plain prose with no fenced block and no schema key is a ComposeError."""
    with pytest.raises(ComposeError):
        compose.parse_response("Sorry, I cannot help with that right now.")


def test_parse_response_mapping_without_known_keys_raises() -> None:
    """A YAML mapping with neither ``track`` nor ``scenes`` is a ComposeError."""
    with pytest.raises(ComposeError):
        compose.parse_response("```yaml\nfoo: 1\nbar: 2\n```\n")


def test_parse_response_bad_velocity_breaks_validation() -> None:
    """A non-numeric velocity fails model validation and surfaces as ComposeError."""
    text = (
        "```yaml\n"
        "scenes:\n"
        "  Intro:\n"
        "    D_kick:\n"
        "      notes:\n"
        '        - {pitch: "C3", start: 0.0, duration: 0.5, velocity: "loud"}\n'
        "```\n"
    )
    with pytest.raises(ComposeError):
        compose.parse_response(text)


def test_parse_response_invalid_yaml_raises() -> None:
    """A block that is not valid YAML is a ComposeError, not a raw YAMLError."""
    with pytest.raises(ComposeError):
        compose.parse_response("```yaml\n: : : not valid : :\n  - [\n```\n")


# --------------------------------------------------------------------------- #
# capture_response
# --------------------------------------------------------------------------- #
def test_capture_response_merges_into_base() -> None:
    """Capturing merges new cells while preserving the base's existing cells."""
    base = ArrangementSpec(
        scenes={
            "Intro": {
                "K_piano": ClipSpec(notes=[NoteSpec(pitch="A2", start=0.0, duration=2.0)]),
            }
        }
    )
    text = (
        "```yaml\n"
        "track: D_kick\n"
        "clips:\n"
        "  Intro:\n"
        "    notes: [{pitch: 36, start: 0.0, duration: 0.25, velocity: 110}]\n"
        "```\n"
    )

    merged = compose.capture_response(text, base=base)

    # Existing cell preserved.
    assert merged.cell("Intro", "K_piano") is not None
    # New cell added alongside it.
    assert merged.cell("Intro", "D_kick") is not None
    assert sorted(merged.scenes["Intro"].keys()) == ["D_kick", "K_piano"]


def test_capture_response_without_base_starts_empty() -> None:
    """With no base, capture returns just the parsed arrangement."""
    text = "```yaml\ntrack: D_kick\nclips:\n  Intro:\n    notes: []\n```\n"

    arr = compose.capture_response(text)

    assert arr.scene_names() == ["Intro"]
    assert arr.cell("Intro", "D_kick") is not None


# --------------------------------------------------------------------------- #
# MistralClient.complete
# --------------------------------------------------------------------------- #
def test_complete_returns_message_content() -> None:
    """A well-formed reply yields the assistant message content."""
    session = _FakeSession(_FakeResponse(_payload("hello from mistral")))
    client = MistralClient("sk-test", session=session)

    out = client.complete("write something", system="you are helpful")

    assert out == "hello from mistral"
    # The request carried the model, both messages, the bearer header and timeout.
    call = session.calls[0]
    assert call["json"]["model"] == DEFAULT_MODEL
    roles = [m["role"] for m in call["json"]["messages"]]
    assert roles == ["system", "user"]
    assert call["headers"]["Authorization"] == "Bearer sk-test"
    assert call["headers"]["Content-Type"] == "application/json"


def test_complete_without_system_sends_only_user_message() -> None:
    """Omitting ``system`` posts a single user message."""
    session = _FakeSession(_FakeResponse(_payload("ok")))
    client = MistralClient("sk-test", session=session)

    client.complete("just a prompt")

    roles = [m["role"] for m in session.calls[0]["json"]["messages"]]
    assert roles == ["user"]


def test_complete_network_error_raises_mistral_api_error() -> None:
    """A ``requests.RequestException`` from ``post`` becomes a MistralAPIError."""
    session = _FakeSession(post_error=requests.RequestException("connection reset"))
    client = MistralClient("sk-test", session=session)

    with pytest.raises(MistralAPIError):
        client.complete("anything")


def test_complete_http_error_includes_response_text() -> None:
    """A non-2xx status raises MistralAPIError carrying the response body."""
    response = _FakeResponse(raise_status=requests.HTTPError("401 Unauthorized"), text="bad key")
    session = _FakeSession(response)
    client = MistralClient("sk-test", session=session)

    with pytest.raises(MistralAPIError) as excinfo:
        client.complete("anything")
    assert "bad key" in str(excinfo.value)


def test_complete_malformed_json_raises_mistral_api_error() -> None:
    """A reply missing ``choices`` raises the 'unexpected shape' MistralAPIError."""
    session = _FakeSession(_FakeResponse({"unexpected": True}))
    client = MistralClient("sk-test", session=session)

    with pytest.raises(MistralAPIError) as excinfo:
        client.complete("anything")
    assert "unexpected Mistral response shape" in str(excinfo.value)


# --------------------------------------------------------------------------- #
# MistralClient.from_env
# --------------------------------------------------------------------------- #
def test_from_env_without_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A missing ``MISTRAL_API_KEY`` is a MistralAPIError."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    with pytest.raises(MistralAPIError):
        MistralClient.from_env()


def test_from_env_with_key_returns_client(monkeypatch: pytest.MonkeyPatch) -> None:
    """With the env var set, ``from_env`` builds a client carrying the key/model."""
    monkeypatch.setenv("MISTRAL_API_KEY", "sk-live-xyz")

    client = MistralClient.from_env(model="mistral-medium")

    assert isinstance(client, MistralClient)
    assert client.api_key == "sk-live-xyz"
    assert client.model == "mistral-medium"


# --------------------------------------------------------------------------- #
# run(): CLI entry point
# --------------------------------------------------------------------------- #
def _args(structure_path, **overrides) -> argparse.Namespace:
    """Build a parsed-args namespace for ``compose.run`` via its own parser."""
    parser = argparse.ArgumentParser()
    compose.configure_parser(parser)
    ns = parser.parse_args([str(structure_path)])
    for key, value in overrides.items():
        setattr(ns, key, value)
    return ns


@pytest.fixture
def structure_file(tmp_path, structure: StructureSpec):
    """Write the ``structure`` fixture to a temp YAML file and return its path."""
    path = tmp_path / "structure.yaml"
    path.write_text(spec.dump_structure(structure), encoding="utf-8")
    return path


def test_run_paste_mode_prints_brief(structure_file, capsys) -> None:
    """Paste mode (the default) prints the brief to stdout and returns 0."""
    code = compose.run(_args(structure_file))

    assert code == 0
    out = capsys.readouterr().out
    assert "```yaml" in out
    assert "142" in out  # bpm appears in the printed brief


def test_run_paste_chunked_mode_emits_per_track_headers(structure_file, capsys) -> None:
    """Chunked paste mode prints one section per MIDI track, with headers."""
    code = compose.run(_args(structure_file, chunked=True))

    assert code == 0
    out = capsys.readouterr().out
    for name in ("D_kick", "D_clap", "K_piano"):
        assert f"===== TRACK: {name} =====" in out


def test_run_capture_mode_writes_arrangement(structure_file, tmp_path) -> None:
    """Capture mode reads a saved reply and writes a loadable arrangement to ``-o``."""
    response = tmp_path / "reply.txt"
    response.write_text(
        "```yaml\n"
        "scenes:\n"
        "  Intro:\n"
        "    D_kick:\n"
        "      notes: [{pitch: 36, start: 0.0, duration: 0.25, velocity: 110}]\n"
        "```\n",
        encoding="utf-8",
    )
    out = tmp_path / "arrangement.yaml"

    code = compose.run(
        _args(structure_file, capture_response=str(response), arrangement_out=str(out))
    )

    assert code == 0
    arr = spec.load_arrangement(out)  # round-trips through the loader
    assert arr.cell("Intro", "D_kick") is not None


def test_run_capture_mode_bad_response_returns_one(structure_file, tmp_path) -> None:
    """An unparseable captured reply makes capture mode fail with exit code 1."""
    response = tmp_path / "reply.txt"
    response.write_text("not a fenced block and no keys", encoding="utf-8")

    code = compose.run(_args(structure_file, capture_response=str(response)))

    assert code == 1


def test_run_api_mode_produces_arrangement(
    structure_file, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """API mode calls a (faked) client and writes the composed arrangement to ``-o``."""
    reply = (
        "```yaml\n"
        "scenes:\n"
        "  Intro:\n"
        "    D_kick:\n"
        "      notes: [{pitch: 36, start: 0.0, duration: 0.25, velocity: 110}]\n"
        "```\n"
    )
    fake = _FakeClient(reply)
    monkeypatch.setattr(MistralClient, "from_env", classmethod(lambda cls, **kw: fake))

    out = tmp_path / "arrangement.yaml"
    code = compose.run(_args(structure_file, api=True, arrangement_out=str(out)))

    assert code == 0
    assert fake.prompts  # the client was actually called
    arr = spec.load_arrangement(out)
    assert arr.cell("Intro", "D_kick") is not None


def test_run_api_chunked_mode_merges_each_track(
    structure_file, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Chunked API mode calls the client per track and merges every reply."""

    class _PerTrackClient:
        """Returns a per-track reply derived from the prompt's chunk track."""

        def __init__(self) -> None:
            self.prompts: list[str] = []

        def complete(self, prompt: str, *, system: str | None = None) -> str:
            self.prompts.append(prompt)
            # The chunk track is named in the prompt; pick the first MIDI name found.
            for name in ("D_kick", "D_clap", "K_piano"):
                if f"track: {name}" in prompt:
                    track = name
                    break
            else:  # pragma: no cover - defensive
                track = "D_kick"
            return "```yaml\n" f"track: {track}\n" "clips:\n" "  Intro:\n" "    notes: []\n" "```\n"

    fake = _PerTrackClient()
    monkeypatch.setattr(MistralClient, "from_env", classmethod(lambda cls, **kw: fake))

    out = tmp_path / "arrangement.yaml"
    code = compose.run(_args(structure_file, api=True, chunked=True, arrangement_out=str(out)))

    assert code == 0
    assert len(fake.prompts) == 3  # one per MIDI track
    arr = spec.load_arrangement(out)
    assert sorted(arr.scenes["Intro"].keys()) == ["D_clap", "D_kick", "K_piano"]


def test_run_api_mode_missing_key_returns_one(
    structure_file, monkeypatch: pytest.MonkeyPatch
) -> None:
    """API mode surfaces a missing key (MistralAPIError) as exit code 1."""
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)

    code = compose.run(_args(structure_file, api=True))

    assert code == 1


def test_run_bad_structure_returns_one(tmp_path) -> None:
    """A structure that fails to load makes ``run`` fail fast with exit code 1."""
    bad = tmp_path / "bad.yaml"
    bad.write_text("tracks: [name: oops, extra_unknown_key: 1]\n", encoding="utf-8")

    code = compose.run(_args(bad))

    assert code == 1


def test_run_paste_mode_writes_brief_to_out(structure_file, tmp_path) -> None:
    """Paste mode with ``--out`` writes the brief to a file instead of stdout."""
    out = tmp_path / "brief.md"

    code = compose.run(_args(structure_file, out=str(out)))

    assert code == 0
    written = out.read_text(encoding="utf-8")
    assert "```yaml" in written
    assert "142" in written


def test_run_capture_mode_merges_base_and_prints_to_stdout(
    structure_file, tmp_path, capsys
) -> None:
    """Capture mode merges a ``--base`` arrangement and prints to stdout sans ``-o``."""
    base = tmp_path / "base.yaml"
    base.write_text(
        spec.dump_arrangement(
            ArrangementSpec(
                scenes={
                    "Intro": {
                        "K_piano": ClipSpec(notes=[NoteSpec(pitch="A2", start=0.0, duration=2.0)])
                    }
                }
            )
        ),
        encoding="utf-8",
    )
    response = tmp_path / "reply.txt"
    response.write_text(
        "```yaml\ntrack: D_kick\nclips:\n  Intro:\n    notes: []\n```\n",
        encoding="utf-8",
    )

    code = compose.run(_args(structure_file, capture_response=str(response), base=str(base)))

    assert code == 0
    captured = capsys.readouterr()
    # The merged arrangement is printed as YAML to stdout (both cells present).
    merged = spec.load_arrangement_data(yaml.safe_load(captured.out))
    assert merged.cell("Intro", "K_piano") is not None
    assert merged.cell("Intro", "D_kick") is not None
    # The one-line summary goes to stderr.
    assert "captured arrangement" in captured.err


def test_run_api_single_mode_writes_raw_response_to_out(
    structure_file, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Single API mode writes the raw reply to ``--out`` and the arrangement to ``-o``."""
    reply = (
        "```yaml\nscenes:\n  Intro:\n    D_kick:\n"
        "      notes: [{pitch: 36, start: 0.0, duration: 0.25, velocity: 110}]\n```\n"
    )
    fake = _FakeClient(reply)
    monkeypatch.setattr(MistralClient, "from_env", classmethod(lambda cls, **kw: fake))

    raw = tmp_path / "raw.txt"
    out = tmp_path / "arrangement.yaml"
    code = compose.run(_args(structure_file, api=True, out=str(raw), arrangement_out=str(out)))

    assert code == 0
    assert raw.read_text(encoding="utf-8") == reply  # raw reply saved verbatim
    assert spec.load_arrangement(out).cell("Intro", "D_kick") is not None


def test_run_api_chunked_mode_writes_per_track_files_to_out_dir(
    structure_file, tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Chunked API mode writes one raw-reply file per track when ``--out`` is a dir."""

    def _reply_for(prompt: str) -> str:
        for name in ("D_kick", "D_clap", "K_piano"):
            if f"track: {name}" in prompt:
                return f"```yaml\ntrack: {name}\nclips:\n  Intro:\n    notes: []\n```\n"
        raise AssertionError("no known track in prompt")  # pragma: no cover

    class _Client:
        def complete(self, prompt: str, *, system: str | None = None) -> str:
            return _reply_for(prompt)

    monkeypatch.setattr(MistralClient, "from_env", classmethod(lambda cls, **kw: _Client()))

    out_dir = tmp_path / "replies"
    out_dir.mkdir()
    out = tmp_path / "arrangement.yaml"
    code = compose.run(
        _args(
            structure_file,
            api=True,
            chunked=True,
            out=str(out_dir),
            arrangement_out=str(out),
        )
    )

    assert code == 0
    # One raw-reply file per MIDI track landed in the output directory.
    assert {p.name for p in out_dir.iterdir()} == {"D_kick.txt", "D_clap.txt", "K_piano.txt"}
    assert sorted(spec.load_arrangement(out).scenes["Intro"].keys()) == [
        "D_clap",
        "D_kick",
        "K_piano",
    ]


# --------------------------------------------------------------------------- #
# CLI metadata / parser contract
# --------------------------------------------------------------------------- #
def test_cli_metadata_and_parser_defaults() -> None:
    """The module exposes the expected CLI name/help and parser defaults."""
    assert compose.NAME == "compose"
    assert compose.HELP == (
        "Generate the Mistral authoring brief, or ingest its response into an arrangement"
    )

    parser = argparse.ArgumentParser()
    compose.configure_parser(parser)
    ns = parser.parse_args(["some/path.yaml"])

    assert ns.structure == "some/path.yaml"
    assert ns.paste is True
    assert ns.api is False
    assert ns.chunked is False
    assert ns.model == DEFAULT_MODEL


def test_parser_api_and_paste_are_mutually_exclusive() -> None:
    """``--api`` and ``--paste`` cannot be combined."""
    parser = argparse.ArgumentParser()
    compose.configure_parser(parser)
    with pytest.raises(SystemExit):
        parser.parse_args(["s.yaml", "--api", "--paste"])
