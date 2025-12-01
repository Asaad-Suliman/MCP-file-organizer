from pathlib import Path

def create_folder(path):
    folder = Path(path)

    try:
        folder.mkdir(exist_ok=True)
        print(f"Folder ready: {folder}")
    except Exception as e:
        print("Error creating folder:", e)

# Test it
create_folder("Videos")
create_folder("Images")
create_folder("Documents")
