from pathlib import Path
from .step1_categories import CATEGORIES

def find_category(file_path):
    ext = Path(file_path).suffix.lower()

    for category, extensions in CATEGORIES.items():
        if ext in extensions:
            return category

    return "Other"  # fallback if extension not recognized

# Tests
print(find_category("photo.jpg"))   # Images
print(find_category("video.mp4"))   # Videos
print(find_category("resume.pdf"))  # Documents
print(find_category("sound.mp3"))   # Audio
print(find_category("random.xyz"))  # Other
