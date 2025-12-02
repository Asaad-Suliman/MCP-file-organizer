# -----------------------------
# IMPORT LIBRARIES
# -----------------------------

from mcp.server.fastmcp import FastMCP
from pathlib import Path
from datetime import datetime
import os
import json
import hashlib

from .project_code.organizer import organize_folder
from send2trash import send2trash


# -----------------------------
# MCP SERVER
# -----------------------------
mcp = FastMCP("file-organizer")


# -----------------------------
# BASE PATHS
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE = BASE_DIR / "workspace"
HISTORY_FILE = WORKSPACE / "_history.json"
REDO_FILE = WORKSPACE / "_redo.json"
RULES_FILE = WORKSPACE / "rules.json"
PROTECTED_EXTENSIONS = {".py", ".ipynb", ".md", ".docx", ".txt", ".json"}
APP_EXTENSIONS = [".exe", ".msi", ".bat", ".cmd"]
APP_KEYWORDS = ["setup", "installer", "install", "app", "program", "bin", "windows", "driver"]


# -----------------------------
# RULES
# -----------------------------
def load_rules():
    if RULES_FILE.exists():
        try:
            with open(RULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_rules(rules):
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=4)


# -----------------------------
# TOOLS
# -----------------------------
@mcp.tool()
def ping():
    return {"status": "ok", "message": "Server is running."}


@mcp.tool()
def list_files():
    """Return a list of files in the workspace folder."""
    if not WORKSPACE.exists():
        return {"status": "error", "message": "Workspace folder not found."}

    files = [
        item.name
        for item in WORKSPACE.iterdir()
        if item.is_file()
    ]

    return {"status": "ok", "files": files}


@mcp.tool()
def organize_workspace():
    """Organize all files inside the workspace folder."""
    result = organize_folder(WORKSPACE)
    return result


@mcp.tool()
def move_file(filename: str, target_folder: str):
    """
    Move a single file inside the workspace to a target category folder.
    Example:
        move_file("photo.png", "Images")
    """

    source = WORKSPACE / filename
    destination_folder = WORKSPACE / target_folder
    destination_folder.mkdir(exist_ok=True)

    if not source.exists():
        return {"status": "error", "message": f"File not found: {filename}"}

    try:
        new_path = destination_folder / filename
        source.rename(new_path)

        #  Add history tracking
        save_history({
            "type": "move",
            "from": str(source),
            "to": str(new_path)
        })

        return {
            "status": "ok",
            "message": f"Moved {filename} to {target_folder}/"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def debug_cwd():
    """Return the current working directory the MCP server sees."""
    return {"cwd": os.getcwd()}


@mcp.tool()
def list_subfolder(folder: str):
    """
    List all files inside a subfolder of the workspace.
    Example:
        list_subfolder("Documents")
    """
    target = WORKSPACE / folder

    if not target.exists():
        return {"status": "error", "message": f"Folder not found: {folder}"}
    
    if not target.is_dir():
        return {"status": "error", "message": f"{folder} is not a folder."}

    files = [item.name for item in target.iterdir() if item.is_file()]

    return {"status": "ok", "folder": folder, "files": files}


@mcp.tool()
def safe_delete(filename: str):
    """
    Safely delete a file by sending it to the system Trash/Recycle Bin.
    Never deletes permanently.
    """

    file_path = WORKSPACE / filename

    # Check if file exists
    if not file_path.exists():
        return {"status": "error", "message": f"File not found: {filename}"}

    try:
        send2trash(str(file_path))

        # 🔥 Add history entry
        save_history({
            "type": "safe_delete",
            "file": str(file_path),
            "reason": "safe_delete_tool"
        })

        return {"status": "ok", "message": f"Moved {filename} to Trash."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete: {str(e)}"}


@mcp.tool()
def permanent_delete(filename: str, confirm: str):
    """
    Permanently delete a file from the workspace.
    Requires confirmation:
      - Normal files → confirm="yes, permanently delete"
      - Protected files → confirm="PERMANENTLY DELETE <filename>"
    """

    file_path = WORKSPACE / filename

    # Exists?
    if not file_path.exists():
        return {"status": "error", "message": f"File not found: {filename}"}

    # Determine if file is protected
    ext = file_path.suffix.lower()
    is_protected = ext in PROTECTED_EXTENSIONS

    # Protected files require exact confirmation phrase
    if is_protected:
        required_text = f"PERMANENTLY DELETE {filename}"
        if confirm != required_text:
            return {
                "status": "error",
                "message": (
                    f"Protected file. To delete, confirm exactly: "
                    f"'{required_text}'"
                )
            }

    # Normal files need basic confirmation
    else:
        if confirm.lower().strip() != "yes, permanently delete":
            return {
                "status": "error",
                "message": "Confirmation missing. Use: yes, permanently delete"
            }

    # Try deleting
    try:
        file_path.unlink()
        return {"status": "ok", "message": f"{filename} PERMANENTLY deleted."}
    except PermissionError:
        return {"status": "error", "message": "Permission denied."}
    except Exception as e:
        return {"status": "error", "message": f"Unexpected error: {str(e)}"}


@mcp.tool()
def set_workspace(path: str):
    """
    Change the working directory (workspace) the MCP server operates in.
    Only allows switching to existing folders.
    """

    global WORKSPACE

    new_path = Path(path).expanduser().resolve()

    # Check if path exists
    if not new_path.exists():
        return {
            "status": "error",
            "message": f"Path does not exist: {new_path}"
        }

    # Must be a folder
    if not new_path.is_dir():
        return {
            "status": "error",
            "message": f"Path is not a directory: {new_path}"
        }

    # Update workspace
    WORKSPACE = new_path

    return {
        "status": "ok",
        "message": f"Workspace changed to: {WORKSPACE}"
    }


def get_folder_size(path: Path) -> int:
    """Return total size of all files inside a folder."""
    total = 0
    for item in path.rglob("*"):
        if item.is_file():
            total += item.stat().st_size
    return total


@mcp.tool()
def report_folder_stats():
    """
    Return statistics about the current workspace:
    - total files
    - total size
    - per-folder breakdown
    """
    if not WORKSPACE.exists():
        return {"status": "error", "message": "Workspace does not exist."}

    stats = {
        "workspace": str(WORKSPACE),
        "total_files": 0,
        "total_size_bytes": 0,
        "folders": {}
    }

    # Loop through each folder inside WORKSPACE
    for item in WORKSPACE.iterdir():
        if item.is_dir():
            folder_name = item.name
            files = [f for f in item.iterdir() if f.is_file()]
            size = get_folder_size(item)

            stats["folders"][folder_name] = {
                "file_count": len(files),
                "total_size_bytes": size
            }

            stats["total_files"] += len(files)
            stats["total_size_bytes"] += size

    return {"status": "ok", "stats": stats}


@mcp.tool()
def search_files(keyword: str):
    """
    Search for files inside the workspace matching a keyword.
    Matches partial names, case-insensitive.
    """

    if not WORKSPACE.exists():
        return {"status": "error", "message": "Workspace does not exist."}

    keyword_lower = keyword.lower()

    results = []

    # Search only in the top-level workspace
    for item in WORKSPACE.iterdir():
        if item.is_file():
            if keyword_lower in item.name.lower():
                results.append(item.name)

    # ALSO search inside subfolders (Documents, Images, etc.)
    for folder in WORKSPACE.iterdir():
        if folder.is_dir():
            for file in folder.iterdir():
                if file.is_file():
                    if keyword_lower in file.name.lower():
                        results.append(f"{folder.name}/{file.name}")

    return {
        "status": "ok",
        "keyword": keyword,
        "matches": results
    }


@mcp.tool()
def add_rule(condition_type: str, value: str, action_type: str, target: str = None, priority: int = 50):
    """
    Add a rule with priority.
    Lower priority number = run earlier.
    """
    rules = load_rules()

    rule = {
        "condition": {
            "type": condition_type,
            "value": value
        },
        "action": {
            "type": action_type,
            "target": target
        },
        "priority": priority
    }

    rules.append(rule)
    save_rules(rules)

    return {"status": "ok", "rule_added": rule}


@mcp.tool()
def apply_rules():
    """
    Apply all saved rules to files in the workspace.
    Supports:
    - extension rules
    - contains-text rules
    - age-based rules (older than X days)
    - size rules
    - temp rules
    """
    rules = load_rules()
    rules = sorted(rules, key=lambda r: r.get("priority", 50))
    results = []

    # Loop through workspace (recursive)
    for item in WORKSPACE.rglob("*"):
        if item.is_file():
            filename = item.name.lower()

            for rule in rules:
                cond = rule["condition"]
                act = rule["action"]

                # -----------------------------------
                # 1) Condition type: extension match
                # -----------------------------------
                if cond["type"] == "extension":
                    if filename.endswith(cond["value"]):
                        target = WORKSPACE / act["target"]
                        target.mkdir(exist_ok=True)

                        new_path = target / item.name
                        try:
                            item.rename(new_path)

                            # 🔥 log move
                            save_history({
                                "type": "move",
                                "from": str(item),
                                "to": str(new_path),
                                "reason": "rule_extension"
                            })

                            results.append({
                                "file": item.name,
                                "action": "moved",
                                "rule": "extension",
                                "target": act["target"]
                            })
                            continue   

                        except Exception as e:
                            results.append({
                                "file": item.name,
                                "action": "error",
                                "message": str(e)
                            })

                # -----------------------------------
                # 2) Condition type: filename contains
                # -----------------------------------
                elif cond["type"] == "contains":
                    if cond["value"].lower() in filename:
                        target = WORKSPACE / act["target"]
                        target.mkdir(exist_ok=True)

                        new_path = target / item.name
                        try:
                            item.rename(new_path)

                            # 🔥 log move
                            save_history({
                                "type": "move",
                                "from": str(item),
                                "to": str(new_path),
                                "reason": "rule_contains"
                            })

                            results.append({
                                "file": item.name,
                                "action": "moved",
                                "rule": "contains",
                                "target": act["target"]
                            })
                            continue   

                        except Exception as e:
                            results.append({
                                "file": item.name,
                                "action": "error",
                                "message": str(e)
                            })

                # -----------------------------------
                # 3) Condition type: file age > X days
                # -----------------------------------
                elif cond["type"] == "age":
                    try:
                        days_limit = int(cond["value"])
                    except:
                        continue  # invalid rule value → skip

                    # File age in days
                    mtime = datetime.fromtimestamp(item.stat().st_mtime)
                    file_age_days = (datetime.now() - mtime).days

                    if file_age_days >= days_limit:

                        # Action = MOVE
                        if act["type"] == "move":
                            target = WORKSPACE / act["target"]
                            target.mkdir(exist_ok=True)

                            new_path = target / item.name
                            try:
                                item.rename(new_path)

                                # 🔥 log move
                                save_history({
                                    "type": "move",
                                    "from": str(item),
                                    "to": str(new_path),
                                    "reason": "rule_age_move",
                                    "days_old": file_age_days
                                })

                                results.append({
                                    "file": item.name,
                                    "action": "moved_due_to_age",
                                    "days_old": file_age_days,
                                    "rule": "age",
                                    "target": act["target"]
                                })
                                continue   

                            except Exception as e:
                                results.append({
                                    "file": item.name,
                                    "action": "error",
                                    "message": str(e)
                                })

                        # Action = SAFE DELETE
                        if act["type"] == "safe_delete":
                            try:
                                send2trash(str(item))

                                # 🔥 log safe_delete
                                save_history({
                                    "type": "safe_delete",
                                    "file": str(item),
                                    "reason": "rule_age_safe_delete",
                                    "days_old": file_age_days
                                })

                                results.append({
                                    "file": item.name,
                                    "action": "safe_deleted_due_to_age",
                                    "days_old": file_age_days,
                                    "rule": "age"
                                })
                                continue   

                            except Exception as e:
                                results.append({
                                    "file": item.name,
                                    "action": "error",
                                    "message": str(e)
                                })

                # -----------------------------------
                # 4) Condition type: file size > X
                # -----------------------------------
                elif cond["type"] == "size":

                    raw_value = cond["value"].upper()

                    if raw_value.endswith("KB"):
                        size_limit = int(raw_value[:-2]) * 1024
                    elif raw_value.endswith("MB"):
                        size_limit = int(raw_value[:-2]) * 1024 * 1024
                    elif raw_value.endswith("GB"):
                        size_limit = int(raw_value[:-2]) * 1024 * 1024 * 1024
                    else:
                        continue  # unsupported format

                    file_size = item.stat().st_size  # bytes

                    if file_size >= size_limit:

                        # ACTION: MOVE
                        if act["type"] == "move":
                            target = WORKSPACE / act["target"]
                            target.mkdir(exist_ok=True)
                            new_path = target / item.name

                            try:
                                item.rename(new_path)

                                # 🔥 log move
                                save_history({
                                    "type": "move",
                                    "from": str(item),
                                    "to": str(new_path),
                                    "reason": "rule_size_move",
                                    "size_bytes": file_size
                                })

                                results.append({
                                    "file": item.name,
                                    "action": "moved_due_to_size",
                                    "size_bytes": file_size,
                                    "rule_value": cond["value"],
                                    "target": act["target"]
                                })
                                continue   

                            except Exception as e:
                                results.append({
                                    "file": item.name,
                                    "action": "error",
                                    "message": str(e)
                                })

                        # ACTION: SAFE DELETE
                        if act["type"] == "safe_delete":
                            try:
                                send2trash(str(item))

                                # 🔥 log safe_delete
                                save_history({
                                    "type": "safe_delete",
                                    "file": str(item),
                                    "reason": "rule_size_safe_delete",
                                    "size_bytes": file_size
                                })

                                results.append({
                                    "file": item.name,
                                    "action": "safe_deleted_due_to_size",
                                    "size_bytes": file_size,
                                })
                                continue   

                            except Exception as e:
                                results.append({
                                    "file": item.name,
                                    "action": "error",
                                    "message": str(e)
                                })

                # -----------------------------------
                # 5) Condition type: temp / useless files
                # -----------------------------------
                elif cond["type"] == "temp":

                    TEMP_EXTENSIONS = [
                        ".tmp", ".temp", ".cache", ".log",
                        ".bak", ".old", ".swp"
                    ]

                    TEMP_FILENAMES = [
                        "thumbs.db", ".ds_store"
                    ]

                    is_temp = (
                        filename in TEMP_FILENAMES or
                        filename.endswith(tuple(TEMP_EXTENSIONS)) or
                        filename.startswith("~$")
                    )

                    if is_temp:

                        # ACTION: MOVE
                        if act["type"] == "move":
                            target = WORKSPACE / act["target"]
                            target.mkdir(exist_ok=True)

                            new_path = target / item.name
                            try:
                                item.rename(new_path)

                                # 🔥 log move
                                save_history({
                                    "type": "move",
                                    "from": str(item),
                                    "to": str(new_path),
                                    "reason": "rule_temp_move"
                                })

                                results.append({
                                    "file": item.name,
                                    "action": "moved_temp_file",
                                    "rule": "temp",
                                    "target": act["target"]
                                })
                                continue   

                            except Exception as e:
                                results.append({
                                    "file": item.name,
                                    "action": "error",
                                    "message": str(e)
                                })

                        # ACTION: SAFE DELETE
                        if act["type"] == "safe_delete":
                            try:
                                send2trash(str(item))

                                # 🔥 log safe_delete
                                save_history({
                                    "type": "safe_delete",
                                    "file": str(item),
                                    "reason": "rule_temp_safe_delete"
                                })

                                results.append({
                                    "file": item.name,
                                    "action": "temp_file_deleted",
                                    "rule": "temp"
                                })
                                continue   

                            except Exception as e:
                                results.append({
                                    "file": item.name,
                                    "action": "error",
                                    "message": str(e)
                                })

    return {"status": "ok", "results": results}


@mcp.tool()
def find_duplicates():
    """
    Scan the workspace and find duplicate files using SHA-256 hashing.
    Returns groups of duplicates.
    """
    if not WORKSPACE.exists():
        return {"status": "error", "message": "Workspace does not exist"}

    file_hashes = {}  # hash → list of files
    duplicates = {}

    for file in WORKSPACE.rglob("*"):
        if file.is_file():
            # Compute hash
            try:
                file_hash = hashlib.sha256(file.read_bytes()).hexdigest()
            except Exception as e:
                continue

            # If hash already exists → duplicate found
            if file_hash in file_hashes:
                file_hashes[file_hash].append(str(file))
            else:
                file_hashes[file_hash] = [str(file)]

    # Only keep groups with more than one file
    for h, group in file_hashes.items():
        if len(group) > 1:
            duplicates[h] = group

    return {
        "status": "ok",
        "duplicates": duplicates
    }


@mcp.tool()
def delete_duplicates():
    """
    Find and safely delete duplicate files.
    Always keeps one original copy.
    Deletes only duplicates using Trash (safe delete).
    """
    if not WORKSPACE.exists():
        return {"status": "error", "message": "Workspace does not exist"}

    file_hashes = {}  # hash → list of files
    deleted_files = []

    # Scan workspace
    for file in WORKSPACE.rglob("*"):
        if file.is_file():
            try:
                file_hash = hashlib.sha256(file.read_bytes()).hexdigest()
            except Exception:
                continue

            if file_hash in file_hashes:
                file_hashes[file_hash].append(file)
            else:
                file_hashes[file_hash] = [file]

    # Delete duplicates (keep first file)
    for h, group in file_hashes.items():
        if len(group) > 1:
            originals = group[1:]  # everything except the first file
            for dup in originals:
                try:
                    send2trash(str(dup))
                    deleted_files.append(str(dup))
                except Exception as e:
                    deleted_files.append(f"ERROR deleting {dup}: {e}")

    return {
        "status": "ok",
        "deleted": deleted_files
    }

@mcp.tool()
def move_duplicates():
    """
    Find duplicate files and MOVE them into workspace/Duplicates.
    Always keeps one original copy in its place.
    """
    if not WORKSPACE.exists():
        return {"status": "error", "message": "Workspace does not exist"}

    duplicates_folder = WORKSPACE / "Duplicates"
    duplicates_folder.mkdir(exist_ok=True)

    file_hashes = {}
    moved_files = []

    # Scan workspace
    for file in WORKSPACE.rglob("*"):
        if file.is_file():
            try:
                file_hash = hashlib.sha256(file.read_bytes()).hexdigest()
            except Exception:
                continue

            if file_hash in file_hashes:
                file_hashes[file_hash].append(file)
            else:
                file_hashes[file_hash] = [file]

    # Move duplicates (keep first)
    for h, group in file_hashes.items():
        if len(group) > 1:
            duplicates = group[1:]  # skip original (first file)
            for dup in duplicates:
                try:
                    target_path = duplicates_folder / dup.name
                    dup.rename(target_path)
                    moved_files.append(str(target_path))
                except Exception as e:
                    moved_files.append(f"ERROR moving {dup}: {e}")

    return {
        "status": "ok",
        "moved": moved_files
    }


@mcp.tool()
def folder_health_report():
    """
    Analyze the workspace and return a health summary.
    """

    total_files = 0
    total_folders = 0
    total_size = 0

    largest_file = None
    largest_size = 0

    oldest_file = None
    oldest_time = None

    newest_file = None
    newest_time = None

    categories = {}

    warnings = []

    for item in WORKSPACE.rglob("*"):
        if item.is_dir():
            total_folders += 1
            continue

        if item.is_file():
            total_files += 1

            size = item.stat().st_size
            total_size += size

            mtime = datetime.fromtimestamp(item.stat().st_mtime)

            # Largest file
            if size > largest_size:
                largest_size = size
                largest_file = item.name

            # Oldest file
            if oldest_time is None or mtime < oldest_time:
                oldest_time = mtime
                oldest_file = item.name

            # Newest file
            if newest_time is None or mtime > newest_time:
                newest_time = mtime
                newest_file = item.name

            # Category breakdown
            folder = item.parent.name
            categories[folder] = categories.get(folder, 0) + 1

    # Warnings
    if total_files > 500:
        warnings.append("Workspace contains more than 500 files — consider cleanup.")

    if largest_size > 1_000_000_000:  # > 1 GB
        warnings.append("Very large files detected (>1GB).")

    if oldest_time and (datetime.now() - oldest_time).days > 365:
        warnings.append("Files older than 1 year detected — consider archiving.")

    return {
        "status": "ok",
        "summary": {
            "total_files": total_files,
            "total_folders": total_folders,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "largest_file": largest_file,
            "largest_size_mb": round(largest_size / (1024 * 1024), 2),
            "oldest_file": str(oldest_file),
            "oldest_file_date": str(oldest_time) if oldest_time else None,
            "newest_file": str(newest_file),
            "newest_file_date": str(newest_time) if newest_time else None,
            "categories": categories,
            "warnings": warnings
        }
    }


@mcp.tool()
def archive_old_files(days: int = 30):
    """
    Move files older than X days into Archive/YYYY/Month folders.
    Example:
        archive_old_files(30)
    """

    now = datetime.now()
    archive_root = WORKSPACE / "Archive"
    archive_root.mkdir(exist_ok=True)

    moved = []
    skipped = []

    for item in WORKSPACE.rglob("*"):
        if not item.is_file():
            continue

        # Calculate file age
        mtime = datetime.fromtimestamp(item.stat().st_mtime)
        age_days = (now - mtime).days

        if age_days < days:
            skipped.append(item.name)
            continue

        # Build archive folders: Archive/YYYY/Month
        year = mtime.year
        month = mtime.strftime("%B")  # 'January', 'February', etc.

        target_folder = archive_root / str(year) / month
        target_folder.mkdir(parents=True, exist_ok=True)

        new_path = target_folder / item.name

        try:
            item.rename(new_path)
            moved.append({
                "file": item.name,
                "from": str(item.parent),
                "to": str(target_folder),
                "age_days": age_days
            })
        except Exception as e:
            moved.append({
                "file": item.name,
                "action": "error",
                "message": str(e)
            })

    return {
        "status": "ok",
        "days": days,
        "moved_files_count": len(moved),
        "moved_files": moved,
        "skipped_count": len(skipped)
    }


def file_hash(path, chunk_size=8192):
    """
    Calculate SHA-256 hash of a file.
    Used for accurate duplicate detection.
    """
    hash_obj = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


@mcp.tool()
def find_duplicates(mode: str = "hash"):
    """
    Detect duplicate files in the workspace.

    Modes:
    - "hash": accurate (content-based)
    - "quick": fast (name + size)
    """

    files = [f for f in WORKSPACE.rglob("*") if f.is_file()]

    duplicates = {}

    if mode == "quick":
        # QUICK MODE: filename + size
        seen = {}
        for file in files:
            key = (file.name, file.stat().st_size)
            if key in seen:
                duplicates.setdefault(key, []).append(str(file))
            else:
                seen[key] = file

        return {
            "status": "ok",
            "mode": "quick",
            "duplicates": duplicates
        }


    # HASH MODE: content-based (accurate)
    seen_hashes = {}

    for file in files:
        h = file_hash(file)
        if h in seen_hashes:
            duplicates.setdefault(h, []).append(str(file))
        else:
            seen_hashes[h] = file

    return {
        "status": "ok",
        "mode": "hash",
        "duplicates": duplicates
    }

@mcp.tool()
def summarize_workspace():
    """
    Generate a high-level summary of the entire workspace.
    Claude can turn this JSON into a natural-language report.
    """

    summary = {
        "total_files": 0,
        "total_folders": 0,
        "total_size_mb": 0,
        "categories": {},
        "largest_files": [],
        "oldest_files": [],
        "temp_files_count": 0,
        "duplicates_quick": 0,
        "warnings": []
    }

    files = [f for f in WORKSPACE.rglob("*") if f.is_file()]
    folders = [d for d in WORKSPACE.rglob("*") if d.is_dir()]

    summary["total_files"] = len(files)
    summary["total_folders"] = len(folders)

    # Track largest / oldest
    file_sizes = []
    file_dates = []

    TEMP_EXTENSIONS = [
        ".tmp", ".temp", ".cache", ".log",
        ".bak", ".old", ".swp"
    ]

    TEMP_FILENAMES = [
        "thumbs.db", ".ds_store"
    ]

    total_size = 0

    for file in files:
        size = file.stat().st_size
        mtime = datetime.fromtimestamp(file.stat().st_mtime)

        total_size += size
        file_sizes.append((file, size))
        file_dates.append((file, mtime))

        # Count temp files
        if (
            file.name.lower() in TEMP_FILENAMES or
            file.name.lower().endswith(tuple(TEMP_EXTENSIONS)) or
            file.name.startswith("~$")
        ):
            summary["temp_files_count"] += 1

        # Category breakdown
        folder = file.parent.name
        summary["categories"][folder] = summary["categories"].get(folder, 0) + 1

    # Convert to MB
    summary["total_size_mb"] = round(total_size / (1024 * 1024), 2)

    # Largest 5 files
    largest_sorted = sorted(file_sizes, key=lambda x: x[1], reverse=True)
    summary["largest_files"] = [
        {"file": str(f), "size_mb": round(s / (1024*1024), 2)}
        for f, s in largest_sorted[:5]
    ]

    # Oldest 5 files
    oldest_sorted = sorted(file_dates, key=lambda x: x[1])
    summary["oldest_files"] = [
        {"file": str(f), "date": str(d)}
        for f, d in oldest_sorted[:5]
    ]

    # Duplicates (quick mode)
    quick_dups = find_duplicates("quick")["duplicates"]
    summary["duplicates_quick"] = len(quick_dups)

    # Warnings
    if summary["total_files"] > 500:
        summary["warnings"].append("Large number of files — consider cleanup.")

    if summary["temp_files_count"] > 20:
        summary["warnings"].append("Many temporary files detected.")

    if int(summary["total_size_mb"]) > 5000:
        summary["warnings"].append("Workspace size exceeds 5GB.")

    return {
        "status": "ok",
        "workspace_summary": summary
    }


@mcp.tool()
def preview_rules():
    """
    Simulate rule application WITHOUT moving or deleting files.
    Shows what rule will match each file based on priority order.
    Useful for safety checks.
    """

    rules = load_rules()
    rules = sorted(rules, key=lambda r: r.get("priority", 50))

    preview = []

    for item in WORKSPACE.rglob("*"):
        if not item.is_file():
            continue

        filename = item.name.lower()

        for rule in rules:
            cond = rule["condition"]
            act = rule["action"]
            matched = False

            # 1) Extension rule
            if cond["type"] == "extension":
                if filename.endswith(cond["value"]):
                    preview.append({
                        "file": str(item),
                        "rule": "extension",
                        "action": act["type"],
                        "target": act.get("target")
                    })
                    matched = True

            # 2) Contains rule
            elif cond["type"] == "contains":
                if cond["value"].lower() in filename:
                    preview.append({
                        "file": str(item),
                        "rule": "contains",
                        "action": act["type"],
                        "target": act.get("target")
                    })
                    matched = True

            # 3) Age rule
            elif cond["type"] == "age":
                try:
                    limit = int(cond["value"])
                except:
                    continue

                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                age_days = (datetime.now() - mtime).days

                if age_days >= limit:
                    preview.append({
                        "file": str(item),
                        "rule": "age",
                        "action": act["type"],
                        "target": act.get("target"),
                        "age_days": age_days
                    })
                    matched = True

            # 4) Size rule
            elif cond["type"] == "size":
                raw = cond["value"].upper()

                if raw.endswith("KB"):
                    size_limit = int(raw[:-2]) * 1024
                elif raw.endswith("MB"):
                    size_limit = int(raw[:-2]) * 1024 * 1024
                elif raw.endswith("GB"):
                    size_limit = int(raw[:-2]) * 1024 * 1024 * 1024
                else:
                    continue

                file_size = item.stat().st_size

                if file_size >= size_limit:
                    preview.append({
                        "file": str(item),
                        "rule": "size",
                        "action": act["type"],
                        "target": act.get("target"),
                        "size_bytes": file_size
                    })
                    matched = True

            # 5) Temp rule
            elif cond["type"] == "temp":
                TEMP_EXTENSIONS = [
                    ".tmp", ".temp", ".cache", ".log",
                    ".bak", ".old", ".swp"
                ]

                TEMP_FILENAMES = [
                    "thumbs.db", ".ds_store"
                ]

                is_temp = (
                    filename in TEMP_FILENAMES or
                    filename.endswith(tuple(TEMP_EXTENSIONS)) or
                    filename.startswith("~$")
                )

                if is_temp:
                    preview.append({
                        "file": str(item),
                        "rule": "temp",
                        "action": act["type"],
                        "target": act.get("target")
                    })
                    matched = True

            if matched:
                break  # only show first matching rule (priority)
    
    return {"status": "ok", "preview": preview}


def save_history(entry):
    """Append a history entry to the history file."""
    history = []

    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text())
        except:
            history = []

    history.append(entry)
    HISTORY_FILE.write_text(json.dumps(history, indent=2))


def load_history():
    """Load the full history list."""
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except:
            return []
    return []


def pop_last_history():
    """Remove and return the last history entry."""
    history = load_history()
    if not history:
        return None

    last = history.pop()

    HISTORY_FILE.write_text(json.dumps(history, indent=2))
    return last


def load_redo():
    if REDO_FILE.exists():
        try:
            return json.loads(REDO_FILE.read_text())
        except:
            return []
    return []


def save_redo(redo_list):
    REDO_FILE.write_text(json.dumps(redo_list, indent=2))


@mcp.tool()
def undo_last_action():
    """
    Undo the most recent action (move or delete).
    Supports:
    - undo move
    - undo safe delete (moves file back)
    """
    last = pop_last_history()
    if not last:
        return {"status": "error", "message": "No actions to undo."}

    # Load redo list
    redo_list = load_redo()

    action_type = last["type"]

    # Reverse MOVE
    if action_type == "move":
        src = Path(last["from"])
        dst = Path(last["to"])

        # If the file exists in destination → move it back
        if dst.exists():
            dst.rename(src)

        # Save this undo into redo stack
        redo_list.append(last)
        save_redo(redo_list)

        return {
            "status": "ok",
            "message": f"Undo: moved {src.name} back.",
            "undone_action": last
        }

    return {
        "status": "error",
        "message": "Undo type not supported yet."
    }


@mcp.tool()
def redo_last_action():
    """
    Reapply the last undone action.
    Only works if undo_last_action() was used before.
    """
    redo_list = load_redo()

    if not redo_list:
        return {"status": "error", "message": "No redo actions available."}

    last_redo = redo_list.pop()  # take last undone action
    save_redo(redo_list)

    action_type = last_redo["type"]

    # Reapply MOVE
    if action_type == "move":
        src = Path(last_redo["from"])
        dst = Path(last_redo["to"])

        # If original file exists → move again
        if src.exists():
            src.rename(dst)

        # Also return it to history
        save_history(last_redo)

        return {
            "status": "ok",
            "message": f"Redo: action reapplied for {src.name}",
            "redone_action": last_redo
        }

    return {
        "status": "error",
        "message": "Redo type not supported yet."
    }


@mcp.tool()
def reset_workspace():
    """
    Move ALL files from ALL subfolders back into the main workspace folder.
    Does NOT delete any folder.
    Does NOT overwrite files (adds a number if name already exists).
    """

    if not WORKSPACE.exists():
        return {"status": "error", "message": "Workspace does not exist."}

    moved = []
    skipped = []

    for folder in WORKSPACE.iterdir():
        # skip files in root
        if folder.is_file():
            continue

        # skip special system/internal folders
        if folder.name in ["Archive", "Duplicates"]:
            skipped.append(f"Skipped special folder: {folder.name}")
            continue

        # move files inside subfolder
        if folder.is_dir():
            for file in folder.iterdir():
                if not file.is_file():
                    continue

                # final target in root
                target = WORKSPACE / file.name

                # if file with same name exists → rename
                if target.exists():
                    base = file.stem
                    ext = file.suffix
                    counter = 1

                    # generate unique name: filename(1).png, filename(2).png, etc.
                    while True:
                        new_name = f"{base}({counter}){ext}"
                        new_target = WORKSPACE / new_name
                        if not new_target.exists():
                            target = new_target
                            break
                        counter += 1

                try:
                    file.rename(target)
                    moved.append({
                        "file": file.name,
                        "from": str(folder),
                        "to": str(target)
                    })
                except Exception as e:
                    skipped.append({
                        "file": file.name,
                        "folder": folder.name,
                        "reason": str(e)
                    })

    return {
        "status": "ok",
        "moved_files_count": len(moved),
        "moved": moved,
        "skipped": skipped
    }


@mcp.tool()
def move_app_folder(folder_name: str, target_category: str, confirm: str):
    """
    Move an app/installer folder ONLY with explicit confirmation.
    Example:
        move_app_folder("Blender_4.0_Setup", "Applications", "YES")
    """

    if confirm.upper() != "YES":
        return {
            "status": "error",
            "message": "Confirmation missing. Use confirm='YES' to move app folders."
        }

    folder_path = WORKSPACE / folder_name

    if not folder_path.exists() or not folder_path.is_dir():
        return {"status": "error", "message": f"Folder not found: {folder_name}"}

    target_folder = WORKSPACE / target_category
    target_folder.mkdir(exist_ok=True)

    new_path = target_folder / folder_name

    try:
        folder_path.rename(new_path)

        save_history({
            "type": "move_app_folder",
            "from": str(folder_path),
            "to": str(new_path),
            "confirmed": True
        })

        return {
            "status": "ok",
            "message": f"Folder '{folder_name}' moved to {target_category}/ (confirmed)"
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


@mcp.tool()
def list_app_folders():
    """
    Scan the workspace for folders that contain installer/executable files.
    Returns a clean list so Claude can ask for confirmation.
    """

    if not WORKSPACE.exists():
        return {"status": "error", "message": "Workspace does not exist."}

    app_folders = []

    for folder in WORKSPACE.iterdir():
        if not folder.is_dir():
            continue

        folder_lower = folder.name.lower()

        # 1) Folder name looks like an app installer
        if any(keyword in folder_lower for keyword in APP_KEYWORDS):
            app_folders.append(str(folder))
            continue

        # 2) Folder contains exe/msi/bat/cmd inside it
        for file in folder.rglob("*"):
            if file.is_file() and file.suffix.lower() in APP_EXTENSIONS:
                app_folders.append(str(folder))
                break

    return {
        "status": "ok",
        "workspace": str(WORKSPACE),
        "detected_app_folders": sorted(set(app_folders))
    }

# -----------------------------
# START SERVER
# -----------------------------
def main():
    mcp.run()
