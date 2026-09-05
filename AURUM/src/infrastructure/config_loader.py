from pathlib import Path
from typing import Any
import os
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"


class ConfigError(Exception):
    pass


def load_config(environment: str | None = None) -> dict[str, Any]:
    env = environment or os.getenv("AURUM_ENV", "dev")
    config_path = CONFIG_DIR / f"{env}.yaml"

    if not config_path.exists():
        raise ConfigError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ConfigError(f"Invalid config format: {config_path}")

    return config


def get_config_value(config: dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    current = config

    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]

    return current


if __name__ == "__main__":
    config = load_config()
    print("CONFIG LOADED")
    print(f"Project: {get_config_value(config, 'project.name')}")
    print(f"Environment: {get_config_value(config, 'project.environment')}")
    print(f"Tickers: {get_config_value(config, 'market_data.tickers')}")
    print(f"Database enabled: {get_config_value(config, 'database.enabled')}")
