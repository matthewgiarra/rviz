import platform
import subprocess

is_windows = platform.system() == "Windows"

def run_cmd(cmd_list):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(cmd_list, shell=is_windows, capture_output=True, text=True, check=True)
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Command '{' '.join(cmd_list)}' failed: {e}")
        return []
    except Exception as e:
        print(f"Error running '{' '.join(cmd_list)}': {e}")
        return []

def gather_git_data(repo_dir):
    """Gather Git data for the repository."""
    tree_data = run_cmd(["git", "ls-tree", "-r", "HEAD"])
    commit_history = run_cmd(["git", "log", "--pretty=format:%h|%an|%ae|%ad|%cn|%ce|%cd|%s", "--date=iso"])
    status_data = run_cmd(["git", "status", "--porcelain"])

    commit_details = {}
    for commit in commit_history:
        try:
            hash_short, author_name, author_email, author_date, committer_name, committer_email, commit_date, message = commit.split("|", 7)
            full_hash = run_cmd(["git", "rev-parse", hash_short])[0] if run_cmd(["git", "rev-parse", hash_short]) else hash_short
            stat_lines = run_cmd(["git", "show", hash_short, "--stat", "--oneline"])
            files_changed = run_cmd(["git", "show", hash_short, "--name-status", "--oneline"])
            
            changes = {"added": [], "modified": [], "deleted": []}
            for line in files_changed[1:]:
                if line:
                    status, file = line.split(maxsplit=1)
                    if status.startswith("A"):
                        changes["added"].append(file)
                    elif status.startswith("M"):
                        changes["modified"].append(file)
                    elif status.startswith("D"):
                        changes["deleted"].append(file)
            
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

    return tree_data, commit_history, status_data, commit_details