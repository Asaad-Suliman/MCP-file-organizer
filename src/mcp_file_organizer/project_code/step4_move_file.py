from pathlib import Path

def move_file(source, destination_folder):
    src = Path(source)
    dest_folder = Path(destination_folder)

    # Create target folder if missing
    dest_folder.mkdir(exist_ok=True)

    # Build full destination path
    dest = dest_folder / src.name

    try:
        src.rename(dest)
        print(f"Moved: {src} -> {dest}")
    except Exception as e:
        print("Error moving file:", e)

# Test (you can replace with any small file name you have)
move_file("hello_mcp.py", "TestFolder")
