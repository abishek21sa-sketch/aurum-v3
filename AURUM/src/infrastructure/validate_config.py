from typing import Any

from src.infrastructure.config_loader import load_config


REQUIRED_KEYS = [
    "project.name",
    "project.environment",
    "paths.data_dir",
    "paths.results_dir",
    "database.enabled",
    "database.host",
    "database.port",
    "database.name",
    "database.user",
    "redis.enabled",
    "redis.host",
    "redis.port",
    "redis.db",
    "market_data.tickers",
    "market_data.lookback_days",
    "pipeline.fail_fast",
    "pipeline.log_runtime",
    "pipeline.save_artifacts",
]


def get_nested_value(config: dict[str, Any], dotted_key: str) -> Any:
    current = config

    for part in dotted_key.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(dotted_key)
        current = current[part]

    return current


def validate_config(config: dict[str, Any]) -> list[str]:
    issues = []

    for key in REQUIRED_KEYS:
        try:
            value = get_nested_value(config, key)
        except KeyError:
            issues.append(f"Missing required config key: {key}")
            continue

        if value is None:
            issues.append(f"Config key cannot be None: {key}")

    tickers = get_nested_value(config, "market_data.tickers")
    if not isinstance(tickers, list) or len(tickers) == 0:
        issues.append("market_data.tickers must be a non-empty list")

    lookback_days = get_nested_value(config, "market_data.lookback_days")
    if not isinstance(lookback_days, int) or lookback_days <= 0:
        issues.append("market_data.lookback_days must be a positive integer")

    db_port = get_nested_value(config, "database.port")
    if not isinstance(db_port, int):
        issues.append("database.port must be an integer")

    redis_port = get_nested_value(config, "redis.port")
    if not isinstance(redis_port, int):
        issues.append("redis.port must be an integer")

    return issues


def validate_environment(environment: str) -> None:
    config = load_config(environment)
    issues = validate_config(config)

    if issues:
        print(f"CONFIG VALIDATION FAILED: {environment}")
        for issue in issues:
            print(f"- {issue}")
        raise SystemExit(1)

    print(f"CONFIG VALIDATION PASSED: {environment}")


if __name__ == "__main__":
    for env in ["dev", "research", "prod"]:
        validate_environment(env)
