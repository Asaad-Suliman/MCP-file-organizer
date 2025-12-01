from pathlib import Path

def list_files(path="."):
    folder = Path(path)
    if not folder.exists():
        print("Folder not found:", folder)
        return

    for item in folder.iterdir():
        print(item)

list_files(".")
