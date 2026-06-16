"""Tests for scaffold/scripts/task_runner.py."""

import importlib.util
import json
from pathlib import Path

import pytest


def load_task_runner():
    spec = importlib.util.spec_from_file_location(
        "task_runner",
        Path(__file__).parent.parent / "scaffold" / "scripts" / "task_runner.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


tr = load_task_runner()


def make_prd(tmp_path: Path, stories: list[dict]) -> Path:
    data = {"project": {"name": "test", "version": "0.1.0", "branch": "main"}, "stories": stories}
    p = tmp_path / "prd.json"
    p.write_text(json.dumps(data))
    return p


def story(
    id: str, priority: int = 1, passes: bool = False, blocked: bool = False, optional: bool = False
) -> dict:
    return {
        "id": id,
        "title": f"Task {id}",
        "priority": priority,
        "optional": optional,
        "passes": passes,
        "blocked": blocked,
        "blocked_reason": "",
        "acceptance": "",
        "notes": "",
    }


# --- next ---

def test_next_returns_highest_priority(tmp_path, monkeypatch, capsys):
    prd = make_prd(tmp_path, [story("T-001", priority=2), story("T-002", priority=1)])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    tr.cmd_next([])
    out = json.loads(capsys.readouterr().out)
    assert out["id"] == "T-002"


def test_next_skips_blocked(tmp_path, monkeypatch, capsys):
    prd = make_prd(tmp_path, [
        story("T-001", priority=1, blocked=True),
        story("T-002", priority=2),
    ])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    tr.cmd_next([])
    out = json.loads(capsys.readouterr().out)
    assert out["id"] == "T-002"


def test_next_skips_optional_for_next(tmp_path, monkeypatch, capsys):
    prd = make_prd(tmp_path, [
        story("T-OPT", priority=1, optional=True),
        story("T-001", priority=2),
    ])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    tr.cmd_next([])
    out = json.loads(capsys.readouterr().out)
    assert out["id"] == "T-001"


def test_next_done_when_all_required_pass(tmp_path, monkeypatch, capsys):
    prd = make_prd(tmp_path, [
        story("T-001", passes=True),
        story("T-OPT", optional=True),
    ])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    tr.cmd_next([])
    out = json.loads(capsys.readouterr().out)
    assert out == {"done": True}


def test_next_not_done_when_blocked_remains(tmp_path, monkeypatch, capsys):
    prd = make_prd(tmp_path, [story("T-001", blocked=True)])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    tr.cmd_next([])
    out = json.loads(capsys.readouterr().out)
    assert out.get("done") is False


# --- complete ---

def test_complete_sets_passes(tmp_path, monkeypatch, capsys):
    prd = make_prd(tmp_path, [story("T-001")])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    tr.cmd_complete(["T-001"])
    capsys.readouterr()
    data = json.loads(prd.read_text())
    assert data["stories"][0]["passes"] is True


def test_complete_idempotent(tmp_path, monkeypatch, capsys):
    prd = make_prd(tmp_path, [story("T-001", passes=True)])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    tr.cmd_complete(["T-001"])
    capsys.readouterr()
    data = json.loads(prd.read_text())
    assert data["stories"][0]["passes"] is True


def test_complete_unknown_id_exits(tmp_path, monkeypatch):
    prd = make_prd(tmp_path, [story("T-001")])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    with pytest.raises(SystemExit):
        tr.cmd_complete(["UNKNOWN"])


# --- block ---

def test_block_writes_reason(tmp_path, monkeypatch, capsys):
    prd = make_prd(tmp_path, [story("T-001")])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    tr.cmd_block(["T-001", "some error"])
    capsys.readouterr()
    data = json.loads(prd.read_text())
    assert data["stories"][0]["blocked"] is True
    assert data["stories"][0]["blocked_reason"] == "some error"


def test_block_unknown_id_exits(tmp_path, monkeypatch):
    prd = make_prd(tmp_path, [story("T-001")])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    with pytest.raises(SystemExit):
        tr.cmd_block(["UNKNOWN", "reason"])


# --- status ---

def test_status_runs(tmp_path, monkeypatch, capsys):
    prd = make_prd(tmp_path, [story("T-001"), story("T-002", priority=2)])
    monkeypatch.setenv("RALPH_PRD", str(prd))
    tr.cmd_status([])
    out = capsys.readouterr().out
    assert "T-001" in out
    assert "T-002" in out


# --- missing prd.json ---

def test_missing_prd_exits(tmp_path, monkeypatch):
    monkeypatch.setenv("RALPH_PRD", str(tmp_path / "nonexistent.json"))
    with pytest.raises(SystemExit):
        tr.cmd_next([])
