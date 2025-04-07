import webbrowser
import os
from .config import load_config
from .git_utils import run_cmd, gather_git_data
from .html_generator import generate_html

def run(args):
    """Main entry point for rviz."""
    config = load_config(args)
    repo_dir, output_file, repo_title, file_details_enabled = config
    tree_data, commit_history, status_data, commit_details = gather_git_data(repo_dir)
    html = generate_html(repo_dir, repo_title, tree_data, commit_history, status_data, commit_details)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    webbrowser.open(f"file://{os.path.abspath(output_file)}")