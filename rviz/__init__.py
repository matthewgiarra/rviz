import webbrowser
import os
import subprocess
import platform
from .config import load_config
from .git_parser import gather_git_data
from .html_generator import generate_html

def run(argv=None, **kwargs):
    """Main entry point for rviz."""
    # Pass argv and kwargs to load_config for processing
    config = load_config(argv=argv, **kwargs)
    repo_dir = config.get("repo_dir")
    output_file = config.get("output_file")
    repo_title = config.get("repo_title")
    verbose = config.get("verbose")
    theme = config.get("theme")

    # Gather git data
    if verbose: print("Gathering git data...")
    tree_data, commit_history, status_data, commit_details = gather_git_data(repo_dir, verbose=verbose)

    # Generate HTML
    if verbose: print("Generating HTML...")
    html = generate_html(repo_dir, repo_title, tree_data, commit_history, status_data, commit_details, verbose=verbose, theme=theme)

    # Write HTML to file
    if verbose: print("Writing %s" % output_file)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    # Open the generated file in a web browser
    if verbose: print("Opening %s in a web browser..." % output_file)
    webbrowser.open(f"file://{os.path.abspath(output_file)}")