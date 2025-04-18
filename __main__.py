import sys
import subprocess
import rviz

def run_cmd(cmd_list, verbose=False):
    """Run a shell command and return its output."""
    try:
        if verbose: print(f"{' '.join(cmd_list)}")  # Print the command
        result = subprocess.run(cmd_list, shell=is_windows, capture_output=True, text=True, check=True)
        return result.stdout.strip().splitlines()
    except subprocess.CalledProcessError as e:
        print(f"Command '{' '.join(cmd_list)}' failed: {e}")
        return []
    except Exception as e:
        print(f"Error running '{' '.join(cmd_list)}': {e}")
        return []

if __name__ == "__main__":
    # Pass raw command-line arguments to rviz.run
    rviz.run(argv=sys.argv[1:])