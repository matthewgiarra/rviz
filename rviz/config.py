import os
import json
import argparse
from datetime import datetime

def load_config(argv=None, **kwargs):
    """Load and process configuration with precedence."""
    # Parse command-line arguments if argv is provided
    parser = argparse.ArgumentParser(description="Generate a repository viewer HTML page.")
    parser.add_argument("-t", "--title", help="Specify the repository title")
    parser.add_argument("-d", "--dir", help="Specify the repository directory")
    parser.add_argument("-o", "--output", help="Specify the output HTML file name")
    parser.add_argument("-f", "--file", "-c", "--config", help="Specify the path to config file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--theme", help="Specify the theme (e.g., 'dark' or 'light')")  # Added theme argument

    args = parser.parse_args(argv or [])
    
    # Merge parsed arguments with kwargs
    config_args = vars(args)
    config_args.update(kwargs)

    default_config_file = "rviz.json"
    default_config = {
        "repo_dir": os.getcwd(),
        "output_file": "rviz.html",
        "theme": "light"  # Default theme
    }

    initial_repo_dir = config_args.get("dir") or os.getcwd()
    rviz_json_path = os.path.join(initial_repo_dir, "rviz.json")
    rviz_config_path = os.path.join(initial_repo_dir, "rviz.config")

    if config_args.get("file"):
        config_file = config_args["file"]
    elif os.path.exists(rviz_config_path):
        config_file = rviz_config_path
        if os.path.exists(rviz_json_path):
            print(f"Warning: Both 'rviz.json' and 'rviz.config' found in '{initial_repo_dir}'. Prioritizing 'rviz.config'.")
    elif os.path.exists(rviz_json_path):
        config_file = rviz_json_path
    else:
        config_file = default_config_file

    if not os.path.exists(config_file):
        print(f"Config file '{config_file}' not found. Using defaults: {default_config}")
        config = default_config
    else:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = {**default_config, **json.load(f)}
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading '{config_file}': {e}. Using defaults: {default_config}")
            config = default_config

    repo_dir = config_args.get("dir") or config["repo_dir"]
    output_file = os.path.join(repo_dir, config_args.get("output") or config["output_file"])
    repo_name = os.path.basename(repo_dir)
    repo_title = config_args.get("title") or config.get("title", repo_name)
    verbose = config_args.get("verbose")
    theme = config_args.get("theme") or config.get("theme", "light")  # Get theme from arguments or config

    return {
        "repo_dir": repo_dir,
        "output_file": output_file,
        "repo_title": repo_title,
        "verbose": verbose,
        "theme": theme  # Include theme in the returned configuration
    }