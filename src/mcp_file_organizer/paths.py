from pathlib import Path

from .workspace_config import get_workspace


def resolve_in_workspace(name: str) -> Path:
    """
    Resolve `name` against the current workspace, rejecting anything that
    escapes it via ".." components or an absolute path.
    """
    workspace = get_workspace().resolve()
    candidate = (workspace / name).resolve()

    if not candidate.is_relative_to(workspace):
        raise ValueError(f"Path escapes workspace: {name}")

    return candidate


def unique_destination(path: Path) -> Path:
    """
    Return `path` if nothing exists there yet, otherwise the first
    "name(1).ext", "name(2).ext", ... variant that is free.
    """
    if not path.exists():
        return path

    base = path.stem
    ext = path.suffix
    parent = path.parent
    counter = 1

    while True:
        candidate = parent / f"{base}({counter}){ext}"
        if not candidate.exists():
            return candidate
        counter += 1
