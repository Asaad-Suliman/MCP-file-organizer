from mcp.server.fastmcp import FastMCP
from pathlib import Path
from .organizer import organize_folder

mcp = FastMCP("file-organizer")

WORKSPACE = Path("workspace")

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
    
    result = organize_folder("workspace")
    return result


if __name__ == "__main__":
    mcp.run()
