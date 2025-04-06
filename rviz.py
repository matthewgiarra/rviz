import platform
import subprocess
import os
import json
import webbrowser
import argparse
from html import escape
from datetime import datetime

# Detect operating system
is_windows = platform.system() == "Windows"
is_mac = platform.system() == "Darwin"

# Default config file name in the script's directory
default_config_file = "rviz.json"

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Generate a repository viewer HTML page.")
parser.add_argument("-t", "--title", help="Specify the repository title (use single quotes, e.g., 'My Title', if double quotes cause shell issues)")
parser.add_argument("-d", "--dir", help="Specify the repository directory (overrides config 'repo_dir')")
parser.add_argument("-o", "--output", help="Specify the output HTML file name (overrides config 'output_file')")
parser.add_argument("-f", "--file", "-c", "--config", help="Specify the path to config file (overrides rviz.json/rviz.config in repo_dir and default rviz.json)")
args = parser.parse_args()

# Function to load config from JSON
def load_config(config_path):
    default_config = {
        "repo_dir": os.getcwd(),
        "output_file": "rviz.html"
    }
    if not os.path.exists(config_path):
        print(f"Config file '{config_path}' not found. Using defaults: {default_config}")
        return default_config
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        return {**default_config, **config}
    except json.JSONDecodeError as e:
        print(f"Error parsing '{config_path}': {e}. Using defaults: {default_config}")
        return default_config
    except Exception as e:
        print(f"Error loading '{config_path}': {e}. Using defaults: {default_config}")
        return default_config

# Determine initial repo_dir for rviz config check
initial_repo_dir = args.dir or os.getcwd()
rviz_json_path = os.path.join(initial_repo_dir, "rviz.json")
rviz_config_path = os.path.join(initial_repo_dir, "rviz.config")

# Determine which config file to use
if args.file:
    config_file = args.file
elif os.path.exists(rviz_config_path):
    config_file = rviz_config_path
    if os.path.exists(rviz_json_path):
        print(f"Warning: Both 'rviz.json' and 'rviz.config' found in '{initial_repo_dir}'. Prioritizing 'rviz.config'.")
elif os.path.exists(rviz_json_path):
    config_file = rviz_json_path
else:
    config_file = default_config_file

# Load configuration from chosen file
config = load_config(config_file)

# Set repo_dir once, respecting precedence: command-line > config > default
repo_dir = args.dir or config["repo_dir"]
output_file = os.path.join(repo_dir, args.output or config["output_file"])

# Determine repository title
repo_name = os.path.basename(repo_dir)
repo_title = args.title or config.get("title", repo_name)

# Get current date and time
creation_time = datetime.now().strftime("%B %d, %Y %I:%M:%S %p")

# Change to repo directory (only once)
try:
    os.chdir(repo_dir)
except Exception as e:
    print(f"Error: Cannot access repository directory '{repo_dir}': {e}")
    exit(1)

# Function to run Git or Pandoc commands
def run_cmd(cmd_list):
    try:
        result = subprocess.run(cmd_list, shell=is_windows, capture_output=True, text=True, check=True)
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Command '{' '.join(cmd_list)}' failed: {e}")
        return []
    except Exception as e:
        print(f"Error running '{' '.join(cmd_list)}': {e}")
        return []

# Gather Git data
tree_data = run_cmd(["git", "ls-tree", "-r", "HEAD"])
commit_history = run_cmd(["git", "log", "--pretty=format:%h|%an|%ae|%ad|%cn|%ce|%cd|%s", "--date=iso"])  # Updated format
status_data = run_cmd(["git", "status", "--porcelain"])

# Fetch detailed commit info
commit_details = {}
for commit in commit_history:
    try:
        hash_short, author_name, author_email, author_date, committer_name, committer_email, commit_date, message = commit.split("|", 7)
        # Get full hash and change stats
        full_hash = run_cmd(["git", "rev-parse", hash_short])[0] if run_cmd(["git", "rev-parse", hash_short]) else hash_short
        stat_lines = run_cmd(["git", "show", hash_short, "--stat", "--oneline"])
        files_changed = run_cmd(["git", "show", hash_short, "--name-status", "--oneline"])
        
        # Parse file changes
        changes = {"added": [], "modified": [], "deleted": []}
        for line in files_changed[1:]:  # Skip first line (commit message)
            if line:
                status, file = line.split(maxsplit=1)
                if status.startswith("A"):
                    changes["added"].append(file)
                elif status.startswith("M"):
                    changes["modified"].append(file)
                elif status.startswith("D"):
                    changes["deleted"].append(file)
        
        # Parse stats (e.g., "2 files changed, 10 insertions(+), 5 deletions(-)")
        stats = ""
        for line in stat_lines:
            if "files changed" in line or "file changed" in line:
                stats = line.split(hash_short)[-1].strip()
                break
        
        commit_details[hash_short] = {
            "full_hash": full_hash,
            "author": f"{author_name} <{author_email}>",
            "committer": f"{committer_name} <{committer_email}>",
            "author_date": author_date,
            "commit_date": commit_date,
            "message": message,
            "changes": changes,
            "stats": stats
        }
    except ValueError:
        continue

# Build file tree and collect directory descriptions and Markdown files
file_tree = {}
md_files = {}
dir_descriptions = {}
root_readme = None
for line in tree_data:
    parts = line.split()
    if len(parts) >= 4:
        path = parts[3]
        dirs = path.split("/")
        current = file_tree
        for d in dirs[:-1]:
            current = current.setdefault(d, {})
        current[dirs[-1]] = None
        if dirs[-1].lower() == "readme.md" and len(dirs) == 1:
            root_readme = path
        elif dirs[-1].lower().endswith(".md"):
            md_files[path] = f"{path.replace('/', '_')}.html"
        elif dirs[-1] == "contents.json":
            dir_path = "/".join(dirs[:-1])
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    dir_descriptions[dir_path] = data.get("description", "No description provided")
            except (json.JSONDecodeError, FileNotFoundError):
                dir_descriptions[dir_path] = "Invalid or missing contents.json"

# Convert Markdown files to HTML
for md_path, html_file in md_files.items():
    html_path = os.path.join(repo_dir, html_file)
    run_cmd(["pandoc", "-f", "markdown", "-t", "html", md_path, "-o", html_path, "--standalone"])

# Convert root README.md to HTML if it exists
readme_content = ""
if root_readme:
    temp_html = "temp_root_readme.html"
    run_cmd(["pandoc", "-f", "markdown", "-t", "html", root_readme, "-o", temp_html])
    try:
        with open(temp_html, "r", encoding="utf-8") as f:
            readme_content = f.read()
        os.remove(temp_html)
    except FileNotFoundError:
        readme_content = "<p>Could not render README.md</p>"

# Generate main HTML content
html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{escape(repo_title)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
            margin-bottom: 5px;
        }}
        .timestamp {{
            font-size: 0.9em;
            color: #7f8c8d;
            margin-top: 0;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            cursor: pointer;
            display: flex;
            align-items: center;
        }}
        h2::before {{
            content: '▶';
            display: inline-block;
            margin-right: 8px;
            transform: rotate(0deg);
            transition: transform 0.3s ease;
        }}
        h2.expanded::before {{
            transform: rotate(90deg);
        }}
        .readme, .tree, .commit-list, .uncommitted {{
            margin: 20px 0;
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .readme.collapsed, .tree.collapsed, .commit-list.collapsed, .uncommitted.collapsed {{
            display: none;
        }}
        .tree ul {{
            padding-left: 20px;
            list-style: none;
        }}
        .tree li {{
            position: relative;
            margin: 10px 0;
        }}
        .tree .dir {{
            cursor: pointer;
            display: flex;
            align-items: center;
            padding: 8px;
            background-color: #ecf0f1;
            border-radius: 5px;
            transition: background-color 0.3s;
        }}
        .tree .dir:hover {{
            background-color: #dfe6e9;
        }}
        .tree .dir::before {{
            content: '▶';
            display: inline-block;
            margin-right: 8px;
            transition: transform 0.3s ease;
        }}
        .tree .expanded > .dir::before {{
            transform: rotate(90deg);
        }}
        .tree .collapsed > ul {{
            display: none;
        }}
        .tree .description {{
            font-style: italic;
            color: #7f8c8d;
            margin-left: 15px;
            font-size: 0.9em;
        }}
        .tree .md-link {{
            color: #2980b9;
            text-decoration: none;
        }}
        .tree .md-link:hover {{
            text-decoration: underline;
        }}
        .commit {{
            padding: 8px 0;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            display: flex;
            align-items: center;
        }}
        .commit::before {{
            content: '▶';
            display: inline-block;
            margin-right: 8px;
            transition: transform 0.3s ease;
        }}
        .commit.expanded::before {{
            transform: rotate(90deg);
        }}
        .commit-details {{
            margin: 10px 0 0 20px;
            padding: 10px;
            background-color: #f9f9f9;
            border-radius: 5px;
            display: none;
        }}
        .commit.expanded + .commit-details {{
            display: block;
        }}
        .commit-details ul {{
            padding-left: 20px;
            margin: 5px 0;
        }}
        .uncommitted {{
            color: #c0392b;
        }}
    </style>
</head>
<body>
    <h1>{escape(repo_title)}</h1>
    <p class="timestamp">Generated on {creation_time}</p>
"""

# Add README section if root README exists
if root_readme:
    html += """
    <h2>README</h2>
    <div class="readme collapsed">
"""
    html += readme_content
    html += """
    </div>
"""

html += """
    <h2>File Hierarchy</h2>
    <div class="tree collapsed">
"""

# Recursive function to build tree HTML with directories first, then files
def build_tree_html(tree, current_path=""):
    html = "<ul>"
    dirs = [(name, subtree) for name, subtree in tree.items() if bool(subtree)]
    files = [(name, None) for name, subtree in tree.items() if not bool(subtree)]
    
    dirs = sorted(dirs, key=lambda x: x[0])
    files = sorted(files, key=lambda x: x[0])
    
    for name, subtree in dirs:
        full_path = f"{current_path}/{name}" if current_path else name
        description = dir_descriptions.get(full_path, "")
        html += "<li>"
        html += f'<span class="dir">{escape(name)}'
        if description:
            html += f'<span class="description">{escape(description)}</span>'
        html += "</span>"
        html += build_tree_html(subtree, full_path)
        html += "</li>"
    
    for name, _ in files:
        full_path = f"{current_path}/{name}" if current_path else name
        html += "<li>"
        if name.lower().endswith(".md"):
            html_file = md_files.get(full_path, "")
            if html_file:
                html += f'<a href="{html_file}" target="_blank" class="md-link">{escape(name)}</a>'
            else:
                html += f"{escape(name)}"
        else:
            html += f"{escape(name)}"
        html += "</li>"
    
    html += "</ul>"
    return html

html += build_tree_html(file_tree)
html += """
    </div>

    <h2>Commit History</h2>
    <div class="commit-list collapsed">
"""
for commit in commit_history:
    try:
        hash_short, author_name, author_email, author_date, committer_name, committer_email, commit_date, message = commit.split("|", 7)
        details = commit_details.get(hash_short, {})
        html += f'<div class="commit">{author_date.split()[0]}: {escape(message)} ({escape(author_name)}) - {hash_short}</div>'
        html += '<div class="commit-details">'
        html += f'<p><strong>Full Hash:</strong> {escape(details.get("full_hash", hash_short))}</p>'
        html += f'<p><strong>Author:</strong> {escape(details.get("author", author_name))}</p>'
        html += f'<p><strong>Authored:</strong> {escape(details.get("author_date", author_date))}</p>'
        html += f'<p><strong>Committer:</strong> {escape(details.get("committer", committer_name))}</p>'
        html += f'<p><strong>Committed:</strong> {escape(details.get("commit_date", commit_date))}</p>'
        html += f'<p><strong>Stats:</strong> {escape(details.get("stats", "No stats available"))}</p>'
        html += '<p><strong>Files Changed:</strong></p>'
        html += '<ul>'
        for file in details.get("changes", {}).get("added", []):
            html += f'<li>Added: {escape(file)}</li>'
        for file in details.get("changes", {}).get("modified", []):
            html += f'<li>Modified: {escape(file)}</li>'
        for file in details.get("changes", {}).get("deleted", []):
            html += f'<li>Deleted: {escape(file)}</li>'
        html += '</ul>'
        html += '</div>'
    except ValueError:
        html += f'<div class="commit">{escape(commit)}</div>'
html += """
    </div>

    <h2>Uncommitted Changes</h2>
    <div class="uncommitted collapsed">
"""
for line in status_data:
    html += f'<div>{escape(line)}</div>'
html += """
    </div>

    <script>
        document.querySelectorAll('.tree .dir').forEach(dir => {
            dir.addEventListener('click', (e) => {
                const li = dir.parentElement;
                li.classList.toggle('expanded');
                li.classList.toggle('collapsed');
                e.stopPropagation();
            });
        });
        document.querySelectorAll('.tree li').forEach(li => {
            if (li.querySelector('ul')) {
                li.classList.add('collapsed');
            }
        });
        document.querySelectorAll('h2').forEach(h2 => {
            h2.addEventListener('click', () => {
                const section = h2.nextElementSibling;
                section.classList.toggle('collapsed');
                h2.classList.toggle('expanded');
            });
        });
        document.querySelectorAll('.commit').forEach(commit => {
            commit.addEventListener('click', (e) => {
                commit.classList.toggle('expanded');
                e.stopPropagation();
            });
        });
    </script>
</body>
</html>
"""

# Write and open the main HTML file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html)

webbrowser.open(f"file://{os.path.abspath(output_file)}")