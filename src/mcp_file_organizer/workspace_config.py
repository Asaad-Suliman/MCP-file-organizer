from pathlib import Path

# Default: a stable, user-owned folder — not inside the installed package,
# which resolves inside the uv cache when installed via uvx and disappears
# on reinstall.
WORKSPACE = Path.home() / "mcp-file-organizer-workspace"
WORKSPACE.mkdir(parents=True, exist_ok=True)

# Server state (history/redo/rules) lives outside any folder the server
# scans, so organize/archive/dedup tools never touch it as if it were user
# data — and it stays valid even after set_workspace_path() changes the
# active workspace.
STATE_DIR = Path.home() / ".mcp-file-organizer"
STATE_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = STATE_DIR / "history.json"


def get_workspace() -> Path:
    """Return the current workspace path."""
    return WORKSPACE


def get_state_dir() -> Path:
    """Return the directory holding the server's own state files."""
    return STATE_DIR


def get_history_file() -> Path:
    """Return the history file path."""
    return HISTORY_FILE


def set_workspace_path(path: str):
    """
    Update WORKSPACE.

    - path: any folder path (e.g. "F:\\Laptop\\Desktop")
    """
    global WORKSPACE

    new_path = Path(path).expanduser().resolve()

    # Make sure it exists and is a directory
    if not new_path.exists():
        raise FileNotFoundError(f"Workspace path does not exist: {new_path}")
    if not new_path.is_dir():
        raise NotADirectoryError(f"Workspace path is not a directory: {new_path}")

    WORKSPACE = new_path

    return WORKSPACE
