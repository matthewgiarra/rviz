import platform
import subprocess
import os
import json
import webbrowser
from html import escape

# Detect operating system
is_windows = platform.system() == "Windows"
is_mac = platform.system() == "Darwin"

# Default config file name
config_file = "config.json"

# Function to load config from JSON
def load_config():
    default_config = {
        "repo_dir": os.getcwd(),
        "output_file": "repo_view.html"
    }
    if not os.path.exists(config_file):
        print(f"Config file '{config_file}' not found. Using defaults: {default_config}")
        return default_config
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        return {**default_config, **config}
    except json.JSONDecodeError as e:
        print(f"Error parsing '{config_file}': {e}. Using defaults: {default_config}")
        return default_config
    except Exception as e:
        print(f"Error loading '{config_file}': {e}. Using defaults: {default_config}")
        return default_config

# Load configuration
config = load_config()
repo_dir = config["repo_dir"]
output_file = os.path.join(repo_dir, config["output_file"])

# Change to repo directory
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
commit_history = run_cmd(["git", "log", "--pretty=format:%h|%an|%ad|%s", "--date=short"])
status_data = run_cmd(["git", "status", "--porcelain"])

# Build file tree and collect directory descriptions
file_tree = {}
readme_files = []
dir_descriptions = {}
for line in tree_data:
    parts = line.split()
    if len(parts) >= 4:
        path = parts[3]
        dirs = path.split("/")
        current = file_tree
        for d in dirs[:-1]:
            current = current.setdefault(d, {})
        current[dirs[-1]] = None
        if dirs[-1].lower() == "readme.md":
            readme_files.append(path)
        elif dirs[-1] == "contents.json":
            dir_path = "/".join(dirs[:-1])
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    dir_descriptions[dir_path] = data.get("description", "No description provided")
            except (json.JSONDecodeError, FileNotFoundError):
                dir_descriptions[dir_path] = "Invalid or missing contents.json"

# Convert READMEs to HTML using Pandoc
readme_html = {}
for readme in readme_files:
    temp_html = f"temp_{readme.replace('/', '_')}.html"
    pandoc_cmd = ["pandoc", "-f", "markdown", "-t", "html", readme, "-o", temp_html]
    run_cmd(pandoc_cmd)
    try:
        with open(temp_html, "r", encoding="utf-8") as f:
            readme_html[readme] = f.read()
        os.remove(temp_html)
    except FileNotFoundError:
        readme_html[readme] = f"<p>Could not render {readme}</p>"

# Generate HTML content with improved styling
html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Repository Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        h1 {
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        h2 {
            color: #34495e;
            margin-top: 30px;
            cursor: pointer;
            display: flex;
            align-items: center;
        }
        h2::before {
            content: '▶';
            display: inline-block;
            margin-right: 8px;
            transform: rotate(0deg);
            transition: transform 0.3s ease;
        }
        h2.expanded::before {
            transform: rotate(90deg);
        }
        .tree {
            margin: 20px 0;
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .tree.collapsed {
            display: none;
        }
        .tree ul {
            padding-left: 20px;
            list-style: none;
        }
        .tree li {
            position: relative;
            margin: 10px 0;
        }
        .tree .dir {
            cursor: pointer;
            display: flex;
            align-items: center;
            padding: 8px;
            background-color: #ecf0f1;
            border-radius: 5px;
            transition: background-color 0.3s;
        }
        .tree .dir:hover {
            background-color: #dfe6e9;
        }
        .tree .dir::before {
            content: '▶';
            display: inline-block;
            margin-right: 8px;
            transition: transform 0.3s ease;
        }
        .tree .expanded > .dir::before {
            transform: rotate(90deg);
        }
        .tree .collapsed > ul {
            display: none;
        }
        .tree .description {
            font-style: italic;
            color: #7f8c8d;
            margin-left: 15px;
            font-size: 0.9em;
        }
        .commit-list, .uncommitted, .readme-section {
            background-color: #fff;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin: 20px 0;
        }
        .commit-list.collapsed, .uncommitted.collapsed {
            display: none;
        }
        .commit {
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }
        .uncommitted {
            color: #c0392b;
        }
        .readme-section h3 {
            color: #2980b9;
            margin-top: 0;
        }
    </style>
</head>
<body>
    <h1>Repository Viewer</h1>

    <h2>File Hierarchy</h2>
    <div class="tree collapsed">
"""

# Recursive function to build tree HTML with descriptions
def build_tree_html(tree, current_path=""):
    html = "<ul>"
    for name, subtree in sorted(tree.items()):
        full_path = f"{current_path}/{name}" if current_path else name
        is_dir = bool(subtree)
        description = dir_descriptions.get(full_path, "") if is_dir else ""
        html += "<li>"
        if is_dir:
            html += f'<span class="dir">{escape(name)}'
            if description:
                html += f'<span class="description">{escape(description)}</span>'
            html += "</span>"
            html += build_tree_html(subtree, full_path)
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
        hash, author, date, message = commit.split("|", 3)
        html += f'<div class="commit">{date}: {escape(message)} ({escape(author)}) - {hash}</div>'
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

    <h2>README Files</h2>
"""
for readme, content in readme_html.items():
    html += f'<div class="readme-section"><h3>{escape(readme)}</h3>{content}</div>'
html += """
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
    </script>
</body>
</html>
"""

# Write and open the HTML file
with open(output_file, "w", encoding="utf-8") as f:
    f.write(html)

webbrowser.open(f"file://{os.path.abspath(output_file)}")