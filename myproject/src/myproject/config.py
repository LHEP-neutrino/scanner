from pathlib import Path
import os
import yaml


class Config:
    def __init__(self, path: str | None = None):
        """
        Load configuration from YAML.

        Priority:
        1. Explicit path argument
        2. MYPROJECT_CONFIG environment variable
        3. ./config.yaml (project root)
        """
        if path:
            self.path = Path(path)
        elif os.getenv("MYPROJECT_CONFIG"):
            self.path = Path(os.getenv("MYPROJECT_CONFIG"))
        else:
            self.path = Path.cwd() / "config.yaml"

    def parse_yaml(self) -> dict:
        if not self.path.exists():
            raise FileNotFoundError(f"Config file not found: {self.path}")

        with self.path.open("r") as f:
            return yaml.safe_load(f) or {}
