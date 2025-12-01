from pathlib import Path

def safe_read(path):
    p = Path(path)

    try:
        content = p.read_text()
        print("File content loaded:")
        print(content)
    except FileNotFoundError:
        print("Error: File not found.")
    except PermissionError:
        print("Error: Permission denied.")
    except Exception as e:
        print("Unexpected error:", e)

# Test it
safe_read("hello.txt")        # likely missing → FileNotFoundError
safe_read("step5_error_handling.py")  # should work
