<h1 align="center">📁 MCP File Organizer</h1>
<p align="center">A smart local file–organizing MCP server that works with Claude Desktop.</p>

<hr/>

<h2>📌 Overview</h2>
<p>
The <strong>MCP File Organizer</strong> lets Claude analyze and organize files on your local machine safely.  
Claude connects through the Model Context Protocol (MCP) and can:
</p>
<ul>
  <li>Sort files into categories (Images, Videos, Documents, Audio, Archives, Other)</li>
  <li>Detect folder types automatically</li>
  <li>Skip system files, installers, shortcuts, and app folders</li>
  <li>Move only safe files (never delete unless you request)</li>
  <li>Undo and redo moves using the built-in history system</li>
</ul>

<hr/>

<h2>✨ Features</h2>
<ul>
  <li>Smart file classification (PDF → Documents, JPG → Images, etc.)</li>
  <li>Smart folder detection (Videos folder, Images folder, Code folder, etc.)</li>
  <li>Fully safe: skips EXE, MSI, shortcuts, installers, and system files</li>
  <li>Undo last move and redo undone actions</li>
  <li>Complete move history in <code>_history.json</code></li>
  <li>Zero destructive actions unless you explicitly request delete</li>
</ul>

<hr/>

<h2>📦 Installation</h2>
<p>You need Python and uv installed.</p>

<pre>
pip install uv
</pre>

<p>You don’t download anything manually — Claude does it automatically.</p>

<hr/>

<h2>🧠 Add to Claude Desktop (Step-by-Step)</h2>

<h3>1. Open Claude Desktop</h3>

<h3>2. Go to Settings → Model Context Protocol (MCP)</h3>
<p>Top-right corner → Profile → <b>Settings</b> → <b>Model Context Protocol (MCP)</b> → Developer settings.</p>

<h3>3. Open <code>claude_desktop_config.json</code></h3>
<p>Click: <b>Open config file</b></p>

<h3>4. Insert this JSON:</h3>

<pre>
{
  "mcpServers": {
    "file-organizer": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/Asaad-Suliman/MCP-file-organizer.git",
        "mcp-file-organizer"
      ]
    }
  }
}
</pre>

<h3>5. Save the file</h3>

<p>Press <code>Ctrl + S</code> or <code>Cmd + S</code>.</p>

<h3>6. Restart Claude Desktop</h3>

<p>Claude will detect and run the File Organizer automatically.</p>

<h3>7. Test it</h3>

<pre>ping the file-organizer MCP server</pre>

<hr/>

<h2>🚀 Usage with Claude</h2>

<h3>Tell Claude to use your Desktop as the workspace:</h3>

<pre>
Claude, use this path as the workspace:
"YOUR_PATH_HERE"

(Example on Windows: "C:\\Users\\YourName\\Desktop")
(Example on macOS/Linux: "/Users/YourName/Desktop")

Analyze everything and propose a clean folder structure.
Ask for confirmation before organizing.
Do not delete anything unless I explicitly confirm.
</pre>

<h3>Examples of what Claude can do:</h3>
<ul>
  <li>Organize all files into correct categories</li>
  <li>Detect miscategorized folders</li>
  <li>Skip app installers and shortcuts safely</li>
  <li>Undo last move</li>
  <li>Redo last undone action</li>
</ul>

<hr/>

<h2>🛡 Safety Rules</h2>
<ul>
  <li>Installer files (EXE, MSI, BAT, CMD) are always skipped</li>
  <li>Shortcuts (<code>.lnk</code>) are skipped</li>
  <li>System files like <code>desktop.ini</code> are skipped</li>
  <li>Folders containing installers require confirmation</li>
  <li>No delete happens unless requested</li>
  <li>All moves logged in <code>_history.json</code></li>
</ul>

<hr/>

<h2>↩ Undo &amp; Redo</h2>

<h3>Undo last action:</h3>
<pre>undo_last_action</pre>

<h3>Redo last undone action:</h3>
<pre>redo_last_action</pre>

<p>These tools are exposed through MCP.</p>

<hr/>

<h2>🧩 Claude System Prompt (Recommended)</h2>

<pre>
You are connected to an MCP File Organizer server.

Your job:
- Organize files ONLY when the user asks.
- Always ask for confirmation before reorganizing a full folder.
- Never delete anything unless the user explicitly requests it.
- Skip system files, shortcuts, installers, and app folders.
- Use the provided MCP tools (list_files, organize_workspace, move_file, undo_last_action, redo_last_action).

If the user gives a folder path:
1. Treat it as the workspace.
2. Analyze it.
3. Propose a clean structure.
4. Wait for confirmation.
5. Organize safely.
</pre>

<hr/>

<h2>📁 Project Structure</h2>

<pre>
src/
  mcp_file_organizer/
    __init__.py
    __main__.py
    mcp_server.py
    project_code/
      step1_categories.py
      step2_find_category.py
      step2_detect_folder.py
      organizer.py
      utils/
workspace/
  (created automatically)
</pre>

<hr/>

<h2>🧪 Local Testing (Optional)</h2>

<p>You can run the server manually:</p>

<pre>
python -m mcp_file_organizer
</pre>

<hr/>

<h2>🤝 Contributing</h2>
<p>Feel free to open issues or PRs!</p>

<hr/>

<h2>📜 License</h2>
<p>MIT License</p>


