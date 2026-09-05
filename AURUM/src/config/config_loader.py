# src/config/config_loader.py

from pathlib import Path
import os
import yaml


CONFIG_DIR = Path("config")


def deep_merge(base: dict, override: dict) -> dict:
    merged = base.copy()

    for key, value in override.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value

    return merged


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_config(environment: str | None = None) -> dict:
    env = environment or os.getenv("AURUM_ENV", "development")

    base_config = load_yaml(CONFIG_DIR / "base.yaml")
    env_config = load_yaml(CONFIG_DIR / f"{env}.yaml")

    config = deep_merge(base_config, env_config)
    config["environment"] = env

    return config


if __name__ == "__main__":
    loaded_config = load_config()
    print(loaded_config)