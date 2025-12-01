from pathlib import Path
from .step1_categories import CATEGORIES


SYSTEM_FILES = ["desktop.ini", "thumbs.db"]


def find_category(file_path):
    """Return the correct category for a file based on extension or name."""

    name = str(file_path).lower()
    ext = Path(file_path).suffix.lower()

    # --------------------------------------------------
    # 1) System files → ignore / leave them
    # --------------------------------------------------
    if name in SYSTEM_FILES:
        return "System"

    # --------------------------------------------------
    # 2) Windows shortcuts
    # --------------------------------------------------
    if ext == ".lnk":
        return "Applications_NEEDS_CONFIRMATION"

    # --------------------------------------------------
    # 3) Executables / installers
    # --------------------------------------------------
    if ext in [".exe", ".msi", ".bat", ".cmd"]:
        return "Applications_NEEDS_CONFIRMATION"

    # --------------------------------------------------
    # 4) Normal categories
    # --------------------------------------------------
    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category

    # --------------------------------------------------
    # 5) Unknown files → Other
    # --------------------------------------------------
    return "Other"
