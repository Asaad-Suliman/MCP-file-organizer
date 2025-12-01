from pathlib import Path
from datetime import datetime

from .step1_categories import CATEGORIES
from .step2_find_category import find_category


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
        return

    for item in folder.iterdir():
        if item.is_file():
            category = find_category(item.name)
            target_folder = folder / category
            target_folder.mkdir(exist_ok=True)

            destination = target_folder / item.name

            try:
                item.rename(destination)
                message = f"Moved: {item.name} → {category}/"
                print(message)
                log(message)
            except Exception as e:
                message = f"Could not move {item.name}: {e}"
                print(message)
                log(message)

# Test
organize_folder(".")
