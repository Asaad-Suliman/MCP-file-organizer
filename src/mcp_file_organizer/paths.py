from pathlib import Path


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
