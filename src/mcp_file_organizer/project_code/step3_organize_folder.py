from pathlib import Path
from .step1_categories import CATEGORIES
from .step2_find_category import find_category

def organize_folder(path="."):
    folder = Path(path)

    if not folder.exists():
        print("Folder not found:", folder)
        return

    for item in folder.iterdir():
        if item.is_file():
            category = find_category(item.name)

            target_folder = folder / category
            target_folder.mkdir(exist_ok=True)

            destination = target_folder / item.name

            try:
                item.rename(destination)
                print(f"Moved: {item.name} → {category}/")
            except Exception as e:
                print(f"Could not move {item.name}: {e}")

# Test on the current folder
organize_folder(".")
