from pathlib import Path
from datetime import datetime
from send2trash import send2trash

# Local imports
from .step2_find_category import find_category
from .step1_categories import CATEGORIES
from .step2_detect_folder import detect_folder_type
from ..paths import unique_destination
from ..history import (
    save_history,
    pop_last_history,
    ACTION_MOVE_FILE,
    ACTION_MOVE_FOLDER,
    ACTION_MOVE_EMPTY_FILE,
    ACTION_MOVE_FOLDER_BULK,
)

# ---------------------------------------------------
# PATHS
# ---------------------------------------------------
LOG_FILE = "organizer.log"


# ---------------------------------------------------
# LOGGING
# ---------------------------------------------------
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


# ---------------------------------------------------
# MAIN ORGANIZER
# ---------------------------------------------------
def organize_folder(path="."):
    folder = Path(path)

    if not folder.exists():
        message = f"Error: Folder not found - {folder}"
        print(message)
        log(message)
        return {"status": "error", "message": message}

    moved_items = []

    for item in folder.iterdir():

        # -------------------------------------------------
        # 1) FILE HANDLING
        # -------------------------------------------------
        if item.is_file():

            name_lower = item.name.lower()
            ext = item.suffix.lower()

            # --------------------------------------------
            # A) System files → skip
            # --------------------------------------------
            if name_lower in ["desktop.ini", "thumbs.db"]:
                save_history({
                    "type": "system_file_skipped",
                    "file": item.name
                })
                continue

            # --------------------------------------------
            # B) EMPTY files → move to Empty_Files
            # --------------------------------------------
            if item.stat().st_size == 0:
                target_folder = folder / "Empty_Files"
                target_folder.mkdir(exist_ok=True)
                destination = unique_destination(target_folder / item.name)

                try:
                    item.rename(destination)
                    save_history({
                        "type": ACTION_MOVE_EMPTY_FILE,
                        "from": str(item),
                        "to": str(destination)
                    })
                    print(f"Moved EMPTY file: {item.name} → Empty_Files/")
                    log(f"Moved EMPTY file: {item.name} → Empty_Files/")
                    moved_items.append({
                        "type": "empty_file",
                        "name": item.name,
                        "category": "Empty_Files"
                    })
                except Exception as e:
                    print(f"Could not move empty file {item.name}: {e}")
                    log(f"Error moving empty file {item.name}: {e}")

                continue   # VERY IMPORTANT

            # --------------------------------------------
            # C) Installers / executables → skip
            # --------------------------------------------
            if ext in [".exe", ".msi", ".bat", ".cmd"]:
                save_history({
                    "type": "installer_skipped",
                    "file": item.name,
                    "reason": "Executable or installer detected."
                })
                continue

            # --------------------------------------------
            # D) Shortcuts → skip
            # --------------------------------------------
            if ext == ".lnk":
                save_history({
                    "type": "shortcut_skipped",
                    "file": item.name
                })
                continue

            # --------------------------------------------
            # E) Normal files → categorize
            # --------------------------------------------
            category = find_category(item.name)
            target_folder = folder / category
            target_folder.mkdir(exist_ok=True)

            destination = unique_destination(target_folder / item.name)

            try:
                item.rename(destination)

                save_history({
                    "type": ACTION_MOVE_FILE,
                    "from": str(item),
                    "to": str(destination),
                    "category": category
                })

                print(f"Moved file: {item.name} → {category}/")
                log(f"Moved file: {item.name} → {category}/")

                moved_items.append({
                    "type": "file",
                    "name": item.name,
                    "category": category
                })

            except Exception as e:
                log(f"Error moving file {item.name}: {e}")
                print(f"Could not move file {item.name}: {e}")

        # -------------------------------------------------
        # 2) FOLDER HANDLING
        # -------------------------------------------------
        elif item.is_dir():

            # Skip internal folders
            if item.name in {"Archive", "Duplicates", "Empty_Files"}:
                continue

            folder_type = detect_folder_type(item)

            # Application-like folders → skip
            if folder_type == "Applications_NEEDS_CONFIRMATION":
                save_history({
                    "type": "folder_skipped_requires_confirmation",
                    "folder": item.name
                })
                continue

            target_folder = folder / folder_type
            target_folder.mkdir(exist_ok=True)

            new_path = unique_destination(target_folder / item.name)

            try:
                item.rename(new_path)

                save_history({
                    "type": ACTION_MOVE_FOLDER,
                    "from": str(item),
                    "to": str(new_path),
                    "folder_type": folder_type
                })

                print(f"Moved folder: {item.name} → {folder_type}/")
                log(f"Moved folder: {item.name} → {folder_type}/")

                moved_items.append({
                    "type": "folder",
                    "name": item.name,
                    "category": folder_type
                })

            except Exception as e:
                log(f"Error moving folder {item.name}: {e}")
                print(f"Could not move folder {item.name}: {e}")

    return {"status": "ok", "moved": moved_items}


# ---------------------------------------------------
# UNDO FOR FOLDERS
# ---------------------------------------------------
def undo_last_folder_move():
    """Undo the most recent folder move."""
    entry = pop_last_history()

    if not entry:
        return {"status": "error", "message": "No history available."}

    if entry["type"] not in {ACTION_MOVE_FOLDER, ACTION_MOVE_FOLDER_BULK}:
        return {"status": "skipped", "reason": "Last history entry is not a folder move."}

    old_path = Path(entry["from"])
    new_path = Path(entry["to"])

    if new_path.exists():
        try:
            old_path = unique_destination(old_path)
            new_path.rename(old_path)
            return {
                "status": "ok",
                "action": "folder_move_undone",
                "folder": new_path.name,
                "restored_to": str(old_path)
            }
        except Exception as e:
            return {
                "status": "error",
                "folder": new_path.name,
                "message": str(e)
            }

    return {
        "status": "error",
        "message": f"Folder not found at undo location: {new_path}"
    }


# ---------------------------------------------------
# MAIN (standalone)
# ---------------------------------------------------
if __name__ == "__main__":
    result = organize_folder(".")
    print(result)
