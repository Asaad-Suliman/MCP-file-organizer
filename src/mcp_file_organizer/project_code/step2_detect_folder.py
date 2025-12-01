from pathlib import Path


def detect_folder_type(folder_path):
    """
    Look inside a folder and guess what type it is:
    Images, Videos, Apps, Documents, Code, Other.
    """

    folder_path = Path(folder_path)
    files = list(folder_path.glob("*"))

    if not files:
        return "Empty_Folder"

    # Count file types
    exts = [f.suffix.lower() for f in files if f.is_file()]
    ext_set = set(exts)

    # Image folder
    if ext_set & {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"}:
        return "Images"

    # Video
    if ext_set & {".mp4", ".mov", ".mkv", ".avi"}:
        return "Videos"

    # Documents
    if ext_set & {".pdf", ".docx", ".txt", ".pptx", ".xlsx"}:
        return "Documents"

    # Installers/software
    if ext_set & {".exe", ".msi", ".lnk"}:
        return "Applications_NEEDS_CONFIRMATION"

    # Code / scripts
    if ext_set & {".py", ".js", ".html", ".css"}:
        return "Code"

    # Archives
    if ext_set & {".zip", ".rar", ".7z", ".tar"}:
        return "Archives"

    return "Other"
