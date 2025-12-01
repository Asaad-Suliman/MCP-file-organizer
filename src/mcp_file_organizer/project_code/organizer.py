from pathlib import Path
from datetime import datetime
import json
from send2trash import send2trash
from .step2_find_category import find_category
from .step1_categories import CATEGORIES
from .step2_detect_folder import detect_folder_type


BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE = BASE_DIR / "workspace"
HISTORY_FILE = WORKSPACE / "_history.json"

# ------------------------------------------
# History Helpers
# ------------------------------------------
def save_history(entry):
    history = []

    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text())
        except:
            history = []

    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


LOG_FILE = "organizer.log"

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")


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

            category = find_category(item.name)
            target_folder = folder / category
            target_folder.mkdir(exist_ok=True)

            destination = target_folder / item.name

            try:
                item.rename(destination)

                save_history({
                    "type": "move_file",
                    "from": str(item),
                    "to": str(destination),
                    "category": category
                })

                message = f"Moved file: {item.name} → {category}/"
                print(message)
                log(message)
                moved_items.append({"type": "file", "name": item.name, "category": category})

            except Exception as e:
                log(f"Error moving file {item.name}: {e}")
                print(f"Could not move file {item.name}: {e}")

        # -------------------------------------------------
        # 2) FOLDER HANDLING
        # -------------------------------------------------
        elif item.is_dir():

            # Skip internal folders
            if item.name in {"Archive", "Duplicates"}:
                continue

            folder_type = detect_folder_type(item)

            # If folder might be an app → skip
            if folder_type == "Applications_NEEDS_CONFIRMATION":
                save_history({
                    "type": "folder_skipped_requires_confirmation",
                    "folder": item.name
                })
                continue

            # Move the folder to its target category
            target_folder = folder / folder_type
            target_folder.mkdir(exist_ok=True)

            new_path = target_folder / item.name

            try:
                item.rename(new_path)

                save_history({
                    "type": "move_folder",
                    "from": str(item),
                    "to": str(new_path),
                    "folder_type": folder_type
                })

                print(f"Moved folder: {item.name} → {folder_type}/")
                log(f"Moved folder: {item.name} → {folder_type}/")
                moved_items.append({"type": "folder", "name": item.name, "category": folder_type})

            except Exception as e:
                log(f"Error moving folder {item.name}: {e}")
                print(f"Could not move folder {item.name}: {e}")

    # End loop
    return {"status": "ok", "moved": moved_items}


if __name__ == "__main__":
    result = organize_folder(".")
    print(result)
