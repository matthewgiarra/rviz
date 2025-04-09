import platform
import subprocess
import os
from .utils import run_cmd

def gather_git_data(repo_dir, verbose=False):
    """Gather Git data for the repository."""
    
    if verbose:
        print("Moving to %s..." % repo_dir)
    try:
        os.chdir(repo_dir)
    except Exception as e:
        print(f"Error: Cannot access repository directory '{repo_dir}': {e}")
        exit(1)
    
    if verbose: print("Running git commands in %s:" % repo_dir)
    tree_data = run_cmd(["git", "ls-tree", "-r", "HEAD"], verbose=verbose)
    commit_history = run_cmd(["git", "log", "--pretty=format:%h|%an|%ae|%ad|%cn|%ce|%cd|%s", "--date=iso"], verbose=verbose)
    status_data = run_cmd(["git", "status", "--porcelain"], verbose=verbose)

    # Number of commits
    num_commits = len(commit_history)
    if verbose: print("Found %d commits in git history" % num_commits)
   
    # Parse each commit
    commit_details = {}
    for i, commit in enumerate(commit_history):
        try:
            hash_short, author_name, author_email, author_date, committer_name, committer_email, commit_date, message = commit.split("|", 7)
            if verbose: print("Gathering git data for commit %s (%d of %d)" % (hash_short, i+1, num_commits))
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