import subprocess
import sys
import os
from pathlib import Path

def generate_completion(cli_module, output_path):
    result = subprocess.run(
        [sys.executable, "-m", cli_module, "--show-completion=bash"],
        capture_output=True,
        text=True,
        check=True
    )
    os.makedirs(Path(output_path).parent, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(result.stdout)

def main():
    if os.geteuid() == 0:
        bash_dir = "/etc/bash_completion.d"
    else:
        bash_dir = str(Path.home() / ".local" / "share" / "bash-completion" / "completions")

    generate_completion("myproject.cli:cli", f"{bash_dir}/myproject")
    generate_completion("myproject.admin_cli:cli", f"{bash_dir}/myproject-admin")

if __name__ == "__main__":
    main()
