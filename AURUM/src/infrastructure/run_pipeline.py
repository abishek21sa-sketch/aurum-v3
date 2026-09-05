import argparse

from src.infrastructure.config_loader import load_config, get_config_value
from src.infrastructure.pipeline_orchestrator import run_pipeline
from src.infrastructure.pipeline_registry import get_pipeline_steps, list_pipelines


def main() -> None:
    parser = argparse.ArgumentParser(description="Run registered AURUM pipelines.")
    parser.add_argument(
        "pipeline_name",
        choices=list_pipelines(),
        help="Name of the registered pipeline to run.",
    )
    parser.add_argument(
        "--environment",
        default=None,
        help="Optional config environment: dev, research, prod.",
    )
    parser.add_argument(
        "--no-fail-fast",
        action="store_true",
        help="Continue running remaining steps even if one step fails.",
    )

    args = parser.parse_args()

    config = load_config(args.environment)
    config_fail_fast = get_config_value(config, "pipeline.fail_fast", True)

    fail_fast = False if args.no_fail_fast else config_fail_fast

    steps = get_pipeline_steps(args.pipeline_name)

    run_pipeline(
        pipeline_name=args.pipeline_name,
        steps=steps,
        fail_fast=fail_fast,
    )


if __name__ == "__main__":
    main()
