import os
import json
import argparse
from datetime import datetime

def load_config(args):
    """Load and process configuration with precedence."""
    parser = argparse.ArgumentParser(description="Generate a repository viewer HTML page.")
    parser.add_argument("-t", "--title", help="Specify the repository title")
    parser.add_argument("-d", "--dir", help="Specify the repository directory")
    parser.add_argument("-o", "--output", help="Specify the output HTML file name")
    parser.add_argument("-f", "--file", "-c", "--config", help="Specify the path to config file")
    args = parser.parse_args(args)

    default_config_file = "rviz.json"
    default_config = {
        "repo_dir": os.getcwd(),
        "output_file": "rviz.html"
    }

    initial_repo_dir = args.dir or os.getcwd()
    rviz_json_path = os.path.join(initial_repo_dir, "rviz.json")
    rviz_config_path = os.path.join(initial_repo_dir, "rviz.config")

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

    repo_dir = args.dir or config["repo_dir"]
    output_file = os.path.join(repo_dir, args.output or config["output_file"])
    repo_name = os.path.basename(repo_dir)
    repo_title = args.title or config.get("title", repo_name)

    try:
        os.chdir(repo_dir)
    except Exception as e:
        print(f"Error: Cannot access repository directory '{repo_dir}': {e}")
        exit(1)

    return repo_dir, output_file, repo_title, False  # file_details_enabled not used here