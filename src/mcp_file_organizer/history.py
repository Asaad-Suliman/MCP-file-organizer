import json
from pathlib import Path

from .workspace_config import get_history_file, get_state_dir

# ---------------------------------------------------------------------------
# Canonical action-type vocabulary. Every history entry's "type" field must
# be one of these — undo_last_action/redo_last_action only know how to
# handle exactly this set, consistently, in both directions.
# ---------------------------------------------------------------------------
ACTION_MOVE_FILE = "move_file"
ACTION_MOVE_FOLDER = "move_folder"
ACTION_MOVE_EMPTY_FILE = "move_empty_file"
ACTION_MOVE_FOLDER_BULK = "move_folder_bulk"
ACTION_MOVE_APP_FOLDER = "move_app_folder"
ACTION_SAFE_DELETE = "safe_delete"

# Every type above except safe_delete is recorded as a plain rename —
# {"from": ..., "to": ...} — so undoing/redoing any of them means reversing
# that rename the same way. safe_delete is deliberately excluded: send2trash
# never returns a handle to where a file landed in the trash, so restoring
# it isn't feasible here. The guarantee is "never claim undo works for
# something it can't do," so safe_delete entries are recorded for history
# but are not offered as undoable.
RESTORABLE_MOVE_TYPES = frozenset({
    ACTION_MOVE_FILE,
    ACTION_MOVE_FOLDER,
    ACTION_MOVE_EMPTY_FILE,
    ACTION_MOVE_FOLDER_BULK,
    ACTION_MOVE_APP_FOLDER,
})


def get_redo_file() -> Path:
    """Return the redo-stack file path."""
    return get_state_dir() / "redo.json"


def _read_json_list(path: Path) -> list:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _write_json_list(path: Path, entries: list) -> None:
    path.write_text(json.dumps(entries, indent=2))


def load_history() -> list:
    """Return the full history list."""
    return _read_json_list(get_history_file())


def overwrite_history(entries: list) -> None:
    """Replace the entire history list (used to remove specific entries)."""
    _write_json_list(get_history_file(), entries)


def save_history(entry: dict) -> None:
    """Append a new history entry."""
    history = load_history()
    history.append(entry)
    overwrite_history(history)


def peek_last_history():
    """Return the most recent history entry without removing it."""
    history = load_history()
    return history[-1] if history else None


def pop_last_history():
    """Remove and return the most recent history entry, or None if empty."""
    history = load_history()
    if not history:
        return None
    last = history.pop()
    overwrite_history(history)
    return last


def load_redo() -> list:
    """Return the full redo stack."""
    return _read_json_list(get_redo_file())


def overwrite_redo(entries: list) -> None:
    """Replace the entire redo stack."""
    _write_json_list(get_redo_file(), entries)


def push_redo(entry: dict) -> None:
    """Push an entry onto the redo stack."""
    redo = load_redo()
    redo.append(entry)
    overwrite_redo(redo)


def peek_redo():
    """Return the most recent redo entry without removing it."""
    redo = load_redo()
    return redo[-1] if redo else None


def pop_redo():
    """Remove and return the most recent redo entry, or None if empty."""
    redo = load_redo()
    if not redo:
        return None
    entry = redo.pop()
    overwrite_redo(redo)
    return entry
