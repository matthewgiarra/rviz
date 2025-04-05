# rviz - Repository Visualization Tool

rviz is a Python script that generates an HTML visualization of a Git repository's structure, commit history, and uncommitted changes. It supports rendering Markdown files as clickable links and embeds the root-level `README.md` in an expandable section.

[Example output](https://htmlpreview.github.io/?https://raw.githubusercontent.com/matthewgiarra/rviz/main/example.html)

# Features

- **Expandable Sections**: View the root `README.md`, file hierarchy, commit history, and uncommitted changes in collapsible sections with spinning triangle indicators.
- **File Hierarchy**: Displays a tree of the repository's files and directories, with clickable Markdown (`.md`) files opening in new tabs as rendered HTML.
- **Commit History**: Lists commits in the format `<date>: <message> (<author>) - <hash>`.
- **Uncommitted Changes**: Shows `git status --porcelain` output in red.
- **Customizable Title**: Set via command-line, config file, or defaults to the repository name.
- **Markdown Rendering**: All `.md` files in the hierarchy are converted to HTML and linked; the root `README.md` is embedded directly.

# Usage

Run `rviz.py` (or `rviz_fallback.py` for environments without Pandoc):

```
python3 rviz.py [options]
```

# Command-Line Options

- `-t, --title <title>`: Set the repository title (use single quotes, e.g., `'My Title'`, if double quotes cause shell issues).
- `-d, --dir <path>`: Specify the target repository directory (overrides config `repo_dir`).
- `-o, --output <filename>`: Specify the output HTML file name (overrides config `output_file`).
- `-f, --file, -c, --config <path>`: Specify a custom config file path (overrides `rviz.json`/`rviz.config` in target dir and default `rviz.json`).

# Config File Precedence

rviz supports configuration via JSON files, with the following precedence:
1. Command-line `-f`/`-c` specified file.
2. `rviz.config` in the target repository’s root (if both exist, prioritizes over `rviz.json` with a warning).
3. `rviz.json` in the target repository’s root.
4. `rviz.json` in the script’s directory (e.g., `rviz/rviz.json`).

Example `rviz.json` or `rviz.config`:
```
{
    "repo_dir": "/path/to/repo",
    "output_file": "rviz.html",
    "title": "My Repository"
}
```

# Config Fields

- `repo_dir`: Target repository path (default: current working directory).
- `output_file`: Output HTML file name (default: `rviz.html`).
- `title`: Repository title (default: basename of `repo_dir`).

Command-line options (`-d`, `-o`, `-t`) override these fields.

# Directory Descriptions

If a `contents.json` file exists in a directory, its `description` field is displayed in italics next to the directory name in the file hierarchy:
```
{
    "description": "This is a subdirectory"
}
```

# Requirements

- **rviz.py**: Requires Git and Pandoc installed.
- **rviz_fallback.py**: Requires only Git (falls back to plain text for Markdown files).

# Installation

1. Clone the repository:
   ```
   git clone <repo-url>
   cd repo_viewer
   ```
2. Ensure dependencies are installed:
   - Git: `git --version`
   - Pandoc (for `rviz.py`): `pandoc --version`

# Example

To visualize a repo at `/path/to/repo` with a custom title and output file:
```
python3 rviz.py -d /path/to/repo -t 'My Project' -o output.html
```

The output file (e.g., `/path/to/repo/output.html`) will open in your default browser.

# Notes

- Use single quotes for command-line args with spaces or special characters (e.g., `-t 'My Title!'`).
- If both `rviz.json` and `rviz.config` exist in the target dir, a warning is printed, and `rviz.config` is used.