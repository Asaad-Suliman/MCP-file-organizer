from pathlib import Path
from datetime import datetime
import json
from send2trash import send2trash

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


# ------------------------------------------
# Organizer Logic
# ------------------------------------------
from project_code.step2_find_category import find_category
from project_code.step1_categories import CATEGORIES

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

    moved_files = []

    for item in folder.iterdir():
        if item.is_file():

            category = find_category(item.name)
            target_folder = folder / category
            target_folder.mkdir(exist_ok=True)

            destination = target_folder / item.name

            try:
                item.rename(destination)

                # 🔥 Add history
                save_history({
                    "type": "move",
                    "from": str(item),
                    "to": str(destination)
                })

                message = f"Moved: {item.name} → {category}/"
                print(message)
                log(message)
                moved_files.append({"file": item.name, "category": category})

            except Exception as e:
                message = f"Could not move {item.name}: {e}"
                print(message)
                log(message)

    return {"status": "ok", "moved": moved_files}


if __name__ == "__main__":
    result = organize_folder(".")
    print(result)
