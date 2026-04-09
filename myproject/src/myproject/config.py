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
            cfg =  yaml.safe_load(f)

        # Validate required fields
        if not cfg.get("data_path"):
            raise ValueError("data_path is required in config")
        if not Path(cfg["data_path"]).exists():
            raise ValueError(f"data_path does not exist: {cfg['data_path']}")

        # Inject secret from environment
        api_key = os.getenv("MYPROJECT_API_KEY")
        if not api_key:
            raise EnvironmentError("MYPROJECT_API_KEY environment variable is not set")
        cfg["API_KEY"] = api_key

        return cfg