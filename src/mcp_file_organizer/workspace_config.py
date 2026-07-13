from pathlib import Path

# Default: folder next to the installed package (for local testing)
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE = BASE_DIR / "workspace"
HISTORY_FILE = WORKSPACE / "_history.json"


def get_workspace() -> Path:
    """Return the current workspace path."""
    return WORKSPACE


def get_history_file() -> Path:
    """Return the current history file path."""
    return HISTORY_FILE


def set_workspace_path(path: str):
    """
    Update WORKSPACE and HISTORY_FILE dynamically.

    - path: any folder path (e.g. "F:\\Laptop\\Desktop")
    """
    global WORKSPACE, HISTORY_FILE

    new_path = Path(path).expanduser().resolve()

    # Make sure it exists and is a directory
    if not new_path.exists():
        raise FileNotFoundError(f"Workspace path does not exist: {new_path}")
    if not new_path.is_dir():
        raise NotADirectoryError(f"Workspace path is not a directory: {new_path}")

    WORKSPACE = new_path
    HISTORY_FILE = WORKSPACE / "_history.json"

    return WORKSPACE
