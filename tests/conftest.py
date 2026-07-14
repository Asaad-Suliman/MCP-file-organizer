from pathlib import Path

import pytest

from mcp_file_organizer import workspace_config
from mcp_file_organizer.core import organizer as core_organizer


@pytest.fixture
def isolated_env(tmp_path, monkeypatch) -> Path:
    """
    Point WORKSPACE and all server state (history/redo/organizer log) at
    tmp_path for the duration of a test, so nothing touches the real
    ~/mcp-file-organizer-workspace or ~/.mcp-file-organizer.

    WORKSPACE has a real setter (set_workspace_path) so we use it.
    STATE_DIR/HISTORY_FILE have no public setter, and organizer.LOG_FILE is
    bound once at import time — those three are only reachable via
    monkeypatch.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    state_dir = tmp_path / "state"
    state_dir.mkdir()

    monkeypatch.setattr(workspace_config, "STATE_DIR", state_dir)
    monkeypatch.setattr(workspace_config, "HISTORY_FILE", state_dir / "history.json")
    monkeypatch.setattr(core_organizer, "LOG_FILE", state_dir / "organizer.log")

    workspace_config.set_workspace_path(str(workspace))

    return workspace
