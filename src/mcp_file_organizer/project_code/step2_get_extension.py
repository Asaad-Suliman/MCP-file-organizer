from pathlib import Path

def get_extension(file_path):
    p = Path(file_path)
    return p.suffix  # returns ".txt", ".jpg", ".mp4", etc.

# Test it
print(get_extension("hello_mcp.py"))
print(get_extension("photo.jpg"))
print(get_extension("video.mp4"))
