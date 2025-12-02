from pathlib import Path
from .step1_categories import CATEGORIES


def detect_folder_type(folder_path):
    """
    Inspect a folder and determine what category it belongs to
    based on its content.
    """

    folder = Path(folder_path)
    counts = {cat: 0 for cat in CATEGORIES}
    file_count = 0

    # -------------------------------------------------
    # Detect folder type by scanning its contents
    # -------------------------------------------------
    for item in folder.rglob("*"):
        if item.is_file():
            file_count += 1
            ext = item.suffix.lower()

            # Installers → skip whole folder
            if ext in {".exe", ".msi", ".bat", ".cmd"}:
                return "Applications_NEEDS_CONFIRMATION"

            # Shortcuts
            if ext == ".lnk":
                return "Applications_NEEDS_CONFIRMATION"

            # Normal files: count types
            for category, extensions in CATEGORIES.items():
                if ext in extensions:
                    counts[category] += 1

    # -------------------------------------------------
    # If no files → consider it "Other"
    # -------------------------------------------------
    if file_count == 0:
        return "Other"

    # -------------------------------------------------
    # Compute dominant category
    # -------------------------------------------------
    dominant_category = max(counts, key=counts.get)

    if counts[dominant_category] == 0:
        return "Other"

    return dominant_category
