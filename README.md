
# Repository Viewer

This project provides a Python script (`repo_viz.py`) to generate a browser-based, read-only view of a Git repository. It displays the repository's file hierarchy, commit history, uncommitted changes, and renders Markdown README files as HTML. The script is cross-platform (Windows and macOS), configurable via a JSON file, and includes a fallback version (`repo_viz_fallback.py`) for environments where subprocess execution is restricted.

## Features
- **File Hierarchy**: Collapsible tree view of the repository structure.
- **Commit History**: List of commits with hash, author, date, and message.
- **Uncommitted Changes**: Highlights modified or untracked files in red.
- **README Rendering**: Converts `README.md` files to HTML using Pandoc.
- **Cross-Platform**: Works on Windows and macOS with automatic OS detection.
- **Configurable**: Uses a `config.json` file to set paths, making it redistributable.

## Files
- **`repo_viz.py`**: Main script using `subprocess.run()` for Git and Pandoc commands.
- **`repo_viz_fallback.py`**: Fallback script for environments without subprocess permissions.
- **`config.json`**: Configuration file specifying repository path and output file.

## Setup

### Directory Structure
Place the files in a working directory (e.g., `repo_viewer`):
```
repo_viewer/
├── repo_viz.py
├── repo_viz_fallback.py
├── config.json
└── [your Git repository]
```
- `repo_viz.py` and `repo_viz_fallback.py` go in the root directory.
- `config.json` goes in the same directory as the scripts (or adjust the script's `config_file` path).
- Your Git repository can be a subdirectory (e.g., `myrepo/`) or elsewhere, as specified in `config.json`.

### Prerequisites
- **macOS (Home Testing)**:
  - Install Python 3: `brew install python`
  - Install Git: `brew install git`
  - Install Pandoc: `brew install pandoc`
  - Install a browser (e.g., Chrome or Safari, typically pre-installed).
  - Full control assumed, so all commands should work.
- **Windows (Work Environment)**:
  - Ensure Python, Git Bash, Pandoc, and a browser (Firefox/Chrome) are installed.
  - Verify tools are in PATH or use full paths in commands if PATH-restricted.
  - Test `subprocess.run()`: `python -c "import subprocess; print(subprocess.run('git --version', shell=True, capture_output=True, text=True).stdout)"`

### Configuration
Create a `config.json` file in the same directory as the scripts. Customize it for your environment:

- **macOS Example**:
  ```json
  {
      "repo_dir": "/Users/yourname/projects/myrepo",
      "output_file": "repo_view.html"
  }
  ```
- **Windows Example**:
  ```json
  {
      "repo_dir": "C:\\Users\\yourname\\projects\\myrepo",
      "output_file": "repo_view.html"
  }
  ```
- **`repo_dir`**: Absolute path to your Git repository.
- **`output_file`**: Name of the HTML output file (created in `repo_dir`).

## Usage

### Normal Execution (Using `repo_viz.py`)
Run this when you want to view the repository state, assuming `subprocess.run()` is allowed.

1. Ensure `config.json` points to your Git repository.
2. Open a terminal:
   - macOS: Terminal
   - Windows: CMD, PowerShell, or Git Bash
3. Navigate to the script directory:
   - macOS: `cd /path/to/repo_viewer`
   - Windows: `cd C:\path\to\repo_viewer`
4. Run the script:
   - macOS: `python3 repo_viz.py`
   - Windows: `python repo_viz.py`
5. The script generates `repo_view.html` in `repo_dir` and opens it in your default browser.

### Fallback Execution (Using `repo_viz_fallback.py`)
Use this if `repo_viz.py` fails due to permission errors (e.g., `subprocess.run()` blocked).

1. Pre-generate Git data in your repository directory:
   - **Windows (Git Bash or CMD)**:
     ```bash
     cd C:\Users\yourname\projects\myrepo
     git ls-tree -r HEAD > tree.txt
     git log --pretty=format:"%h|%an|%ad|%s" --date=short > log.txt
     git status --porcelain > status.txt
     for %f in (*.md) do pandoc -f markdown -t html "%f" -o "%f.html"
     ```
   - **macOS (Terminal, for testing)**:
     ```bash
     cd /Users/yourname/projects/myrepo
     git ls-tree -r HEAD > tree.txt
     git log --pretty=format:"%h|%an|%ad|%s" --date=short > log.txt
     git status --porcelain > status.txt
     for f in *.md; do pandoc -f markdown -t html "$f" -o "$f.html"; done
     ```
2. Ensure `config.json` points to the repo directory containing these files.
3. Navigate to the script directory:
   - macOS: `cd /path/to/repo_viewer`
   - Windows: `cd C:\path\to\repo_viewer`
4. Run the fallback script:
   - macOS: `python3 repo_viz_fallback.py`
   - Windows: `python repo_viz_fallback.py`
5. The script generates `repo_view.html` and opens it in your browser.

## Testing
- **macOS (Home)**:
  - Run `python3 repo_viz.py` with a valid `config.json`. It should work seamlessly with full control.
- **Windows (Work)**:
  - Try `python repo_viz.py` first. If it fails due to permissions, use the fallback method with `repo_viz_fallback.py`.
- **Cloud Testing (e.g., Azure VM)**:
  - Provision a Windows VM (e.g., Azure Virtual Machine with Windows 10/11).
  - Install Python, Git, Pandoc, and Chrome.
  - Copy `repo_viz.py`, `repo_viz_fallback.py`, and `config.json` to the VM.
  - Test both scripts as described above.

## Cloud Provisioning (Optional)
To test in a Windows environment similar to work:
- **Microsoft Azure**:
  1. Sign up at `portal.azure.com` ($200 free credit for 30 days).
  2. Create a VM: "Windows 10 Pro" or "Windows Server 2022", size `B2s` (~$0.02/hour).
  3. RDP in, install Python, Git, Pandoc, and Chrome.
  4. Copy files and test as above.
- **AWS EC2** or **GCP Compute Engine**: Similar steps, but Azure is recommended for Windows.

## Notes
- **Redistributing**: Share `repo_viz.py` and `repo_viz_fallback.py`. Users provide their own `config.json` and install prerequisites.
- **Output**: `repo_view.html` shows the repo state in your browser.
- **Fallback Files**: `tree.txt`, `log.txt`, `status.txt`, and `.md.html` files are temporary and should be regenerated as needed.

## Troubleshooting
- If `repo_viz.py` fails on Windows, check permissions and switch to `repo_viz_fallback.py`.
- Ensure Git and Pandoc are in PATH or use full paths in commands if restricted.
- Contact the author for support if needed.
