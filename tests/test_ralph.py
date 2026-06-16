"""Tests for scaffold/scripts/ralph.py."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def load_ralph():
    spec = importlib.util.spec_from_file_location(
        "ralph",
        Path(__file__).parent.parent / "scaffold" / "scripts" / "ralph.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ralph = load_ralph()


BASE_CONFIG = {
    "agent_cmd": "echo hello",
    "test_cmd": "pytest -q",
    "lint_cmd": "ruff check .",
    "max_loops": 5,
    "max_retries_per_task": 3,
    "circuit_breaker": {"no_progress_threshold": 3, "same_error_threshold": 5},
    "prompt_file": ".ralph/PROMPT.md",
    "progress_file": "progress.txt",
    "prd_file": "prd.json",
}

HIGH_CB = {"no_progress_threshold": 100, "same_error_threshold": 100}


def make_config(tmp_path: Path, overrides: dict | None = None) -> Path:
    cfg = {**BASE_CONFIG, "progress_file": str(tmp_path / "progress.txt"), **(overrides or {})}
    p = tmp_path / ".ralphrc.json"
    p.write_text(json.dumps(cfg))
    (tmp_path / "progress.txt").write_text("")
    return p


# --- config loading ---

def test_load_config_missing_exits(tmp_path):
    with pytest.raises(SystemExit):
        ralph._load_config(tmp_path / "nonexistent.json")


def test_load_config_invalid_json_exits(tmp_path):
    bad = tmp_path / ".ralphrc.json"
    bad.write_text("{bad json")
    with pytest.raises(SystemExit):
        ralph._load_config(bad)


def test_load_config_valid(tmp_path):
    p = make_config(tmp_path)
    cfg = ralph._load_config(p)
    assert cfg["agent_cmd"] == "echo hello"
    assert cfg["max_loops"] == 5


# --- dry-run ---

def test_dry_run_does_not_call_agent(tmp_path):
    cfg_path = make_config(tmp_path)
    config = ralph._load_config(cfg_path)
    config["progress_file"] = str(tmp_path / "progress.txt")
    config["prd_file"] = str(tmp_path / "prd.json")

    with (
        patch.object(ralph, "_task_runner_next", return_value={"done": True}),
        patch("subprocess.run") as mock_run,
    ):
        with pytest.raises(SystemExit) as exc_info:
            ralph.run_loop(config, dry_run=True)
        assert exc_info.value.code == 0
        mock_run.assert_not_called()


def test_dry_run_exits_cleanly_when_done(tmp_path):
    cfg_path = make_config(tmp_path)
    config = ralph._load_config(cfg_path)
    config["progress_file"] = str(tmp_path / "progress.txt")

    with patch.object(ralph, "_task_runner_next", return_value={"done": True}):
        with pytest.raises(SystemExit) as exc_info:
            ralph.run_loop(config, dry_run=True)
        assert exc_info.value.code == 0


# --- loop exits on done ---

def test_loop_exits_when_done(tmp_path):
    cfg_path = make_config(tmp_path)
    config = ralph._load_config(cfg_path)
    config["progress_file"] = str(tmp_path / "progress.txt")

    with patch.object(ralph, "_task_runner_next", return_value={"done": True}):
        with pytest.raises(SystemExit) as exc_info:
            ralph.run_loop(config, dry_run=False)
        assert exc_info.value.code == 0


# --- circuit breaker: no progress ---

def test_circuit_breaker_no_progress(tmp_path):
    overrides = {"circuit_breaker": {"no_progress_threshold": 2, "same_error_threshold": 10}}
    cfg_path = make_config(tmp_path, overrides)
    config = ralph._load_config(cfg_path)
    config["progress_file"] = str(tmp_path / "progress.txt")

    task_response = {"id": "T-001", "title": "Do something"}
    agent_result = MagicMock()
    agent_result.returncode = 0
    agent_result.stderr = ""

    with (
        patch.object(ralph, "_task_runner_next", return_value=task_response),
        patch.object(ralph, "_git_changed_files", return_value=[]),
        patch("subprocess.run", return_value=agent_result),
    ):
        with pytest.raises(SystemExit) as exc_info:
            ralph.run_loop(config, dry_run=False)
        assert exc_info.value.code == 2


# --- circuit breaker: same error ---

def test_circuit_breaker_same_error(tmp_path):
    overrides = {"circuit_breaker": {"no_progress_threshold": 100, "same_error_threshold": 2}}
    cfg_path = make_config(tmp_path, overrides)
    config = ralph._load_config(cfg_path)
    config["progress_file"] = str(tmp_path / "progress.txt")

    task_response = {"id": "T-001", "title": "Do something"}
    agent_result = MagicMock()
    agent_result.returncode = 1
    agent_result.stderr = "same error every time"

    with (
        patch.object(ralph, "_task_runner_next", return_value=task_response),
        patch.object(ralph, "_git_changed_files", return_value=["file.py"]),
        patch("subprocess.run", return_value=agent_result),
    ):
        with pytest.raises(SystemExit) as exc_info:
            ralph.run_loop(config, dry_run=False)
        assert exc_info.value.code == 2


# --- progress.txt appended ---

def test_progress_appended_each_loop(tmp_path):
    overrides = {"max_loops": 2, "circuit_breaker": HIGH_CB}
    cfg_path = make_config(tmp_path, overrides)
    config = ralph._load_config(cfg_path)
    progress = tmp_path / "progress.txt"
    config["progress_file"] = str(progress)

    responses = [
        {"id": "T-001", "title": "Task 1"},
        {"id": "T-001", "title": "Task 1"},
        {"done": True},
    ]
    call_count = 0

    def fake_next(_prd_file):
        nonlocal call_count
        r = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return r

    agent_result = MagicMock()
    agent_result.returncode = 0
    agent_result.stderr = ""

    with (
        patch.object(ralph, "_task_runner_next", side_effect=fake_next),
        patch.object(ralph, "_git_changed_files", return_value=["file.py"]),
        patch("subprocess.run", return_value=agent_result),
        pytest.raises(SystemExit),
    ):
        ralph.run_loop(config, dry_run=False)

    content = progress.read_text()
    assert "T-001" in content
    assert "PASS" in content


# --- max_loops ---

def test_max_loops_exits_with_code_2(tmp_path):
    overrides = {"max_loops": 1, "circuit_breaker": HIGH_CB}
    cfg_path = make_config(tmp_path, overrides)
    config = ralph._load_config(cfg_path)
    config["progress_file"] = str(tmp_path / "progress.txt")

    agent_result = MagicMock()
    agent_result.returncode = 0
    agent_result.stderr = ""

    with (
        patch.object(ralph, "_task_runner_next", return_value={"id": "T-001", "title": "Task"}),
        patch.object(ralph, "_git_changed_files", return_value=["file.py"]),
        patch("subprocess.run", return_value=agent_result),
    ):
        with pytest.raises(SystemExit) as exc_info:
            ralph.run_loop(config, dry_run=False)
        assert exc_info.value.code == 2
