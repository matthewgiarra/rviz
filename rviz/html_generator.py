import os
import json
from html import escape
from datetime import datetime
from .utils import run_cmd
import pdb

def build_file_tree(tree_data, verbose=False):
    """Build file tree and collect Markdown files and descriptions."""
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
    return file_tree, md_files, dir_descriptions, root_readme

def convert_markdown(repo_dir, md_files, root_readme, verbose=False):
    """Convert Markdown files to HTML."""
    for md_path, html_file in md_files.items():
        html_path = os.path.join(repo_dir, html_file)
        run_cmd(["pandoc", "-f", "markdown", "-t", "html", md_path, "-o", html_path, "--standalone"], verbose=verbose)
    
    readme_content = ""
    if root_readme:
        temp_html = "temp_root_readme.html"
        run_cmd(["pandoc", "-f", "markdown", "-t", "html", root_readme, "-o", temp_html], verbose=verbose)
        try:
            with open(temp_html, "r", encoding="utf-8") as f:
                readme_content = f.read()
            os.remove(temp_html)
        except FileNotFoundError:
            readme_content = "<p>Could not render README.md</p>"
    return readme_content

def generate_tree_html(tree, md_files, dir_descriptions, current_path=""):
    """Generate HTML for file tree."""
    with open(os.path.join(os.path.dirname(__file__), "templates/file_tree.html"), "r", encoding="utf-8") as f:
        template = f.read()
    
    dirs = sorted([(name, subtree) for name, subtree in tree.items() if bool(subtree)], key=lambda x: x[0])
    files = sorted([(name, None) for name, subtree in tree.items() if not bool(subtree)], key=lambda x: x[0])
    
    dir_html = ""
    for name, subtree in dirs:
        full_path = f"{current_path}/{name}" if current_path else name
        description = dir_descriptions.get(full_path, "")
        dir_html += f'<li><span class="dir">{escape(name)}'
        if description:
            dir_html += f'<span class="description">{escape(description)}</span>'
        dir_html += "</span>" + generate_tree_html(subtree, md_files, dir_descriptions, full_path) + "</li>"
    
    file_html = ""
    for name, _ in files:
        full_path = f"{current_path}/{name}" if current_path else name
        file_html += "<li>"
        if name.lower().endswith(".md"):
            html_file = md_files.get(full_path, "")
            if html_file:
                file_html += f'<a href="{html_file}" target="_blank" class="md-link">{escape(name)}</a>'
            else:
                file_html += escape(name)
        else:
            file_html += escape(name)
        file_html += "</li>"
    
    return template.format(dirs=dir_html, files=file_html)

def generate_commit_html(commit_history, commit_details):
    """Generate HTML for commit history."""
    with open(os.path.join(os.path.dirname(__file__), "templates/commit_entry.html"), "r", encoding="utf-8") as f:
        template = f.read()
    
    commit_html = ""
    for commit in commit_history:
        try:
            hash_short, author_name, author_email, author_date, committer_name, committer_email, commit_date, message = commit.split("|", 7)
            details = commit_details.get(hash_short, {})
            commit_line = f"{author_date.split()[0]}: {escape(message)} ({escape(author_name)}) - {hash_short}"
            details_html = (
                f'<p><strong>Full Hash:</strong> {escape(details.get("full_hash", hash_short))}</p>'
                f'<p><strong>Author:</strong> {escape(details.get("author", author_name))}</p>'
                f'<p><strong>Authored:</strong> {escape(details.get("author_date", author_date))}</p>'
                f'<p><strong>Committer:</strong> {escape(details.get("committer", committer_name))}</p>'
                f'<p><strong>Committed:</strong> {escape(details.get("commit_date", commit_date))}</p>'
                f'<p><strong>Stats:</strong> {escape(details.get("stats", "No stats available"))}</p>'
                '<p><strong>Files Changed:</strong></p><ul>'
            )
            for file in details.get("changes", {}).get("added", []):
                details_html += f'<li>Added: {escape(file)}</li>'
            for file in details.get("changes", {}).get("modified", []):
                details_html += f'<li>Modified: {escape(file)}</li>'
            for file in details.get("changes", {}).get("deleted", []):
                details_html += f'<li>Deleted: {escape(file)}</li>'
            details_html += '</ul>'
            commit_html += template.format(hash=hash_short, commit_line=commit_line, details=details_html)
        except ValueError:
            commit_html += f'<div class="commit">{escape(commit)}</div>'
    return commit_html

def load_theme(theme_name):
    """Load the theme JSON file."""
    theme_path = os.path.join(os.path.dirname(__file__), "themes", f"{theme_name}.css")
    if not os.path.exists(theme_path):
        raise FileNotFoundError(f"Theme '{theme_name}' not found in the themes directory.")
    with open(theme_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_html(repo_dir, repo_title, tree_data, commit_history, status_data, commit_details, theme="light", verbose=False):
    """Generate the full HTML page."""
    
    # Load the CSS theme
    themeData = load_theme(theme)

    # Load the HTML template        
    with open(os.path.join(os.path.dirname(__file__), "templates/main.html"), "r", encoding="utf-8") as f:
        template = f.read()
    
    creation_time = datetime.now().strftime("%B %d, %Y %I:%M:%S %p")
    file_tree, md_files, dir_descriptions, root_readme = build_file_tree(tree_data)
    readme_content = convert_markdown(repo_dir, md_files, root_readme, verbose=verbose)
    tree_html = generate_tree_html(file_tree, md_files, dir_descriptions)
    commit_html = generate_commit_html(commit_history, commit_details)
    status_html = "".join(f'<div>{escape(line)}</div>' for line in status_data)
    # pdb.set_trace()
    return template.format(
        style_template=themeData,
        title=escape(repo_title),
        timestamp=creation_time,
        readme_content=readme_content if root_readme else "",
        tree_html=tree_html,
        commit_html=commit_html,
        status_html=status_html
    )