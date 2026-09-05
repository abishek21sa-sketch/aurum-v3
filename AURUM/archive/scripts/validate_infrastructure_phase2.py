import requests
from pathlib import Path

from src.core.config import settings
from src.services.redis_client import check_redis_connection
from src.infrastructure.pipeline_runtime import PIPELINE_RUN_LOG
from src.infrastructure.storage_paths import DATA_DIR, RESULTS_DIR


API_BASE_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"


def check_file_exists(path: Path, label: str) -> dict:
    return {
        "check": label,
        "status": "pass" if path.exists() else "fail",
        "path": str(path),
    }


def check_api_endpoint(path: str, label: str, headers: dict | None = None) -> dict:
    try:
        response = requests.get(
            f"{API_BASE_URL}{path}",
            headers=headers or {},
            timeout=10,
        )

        return {
            "check": label,
            "status": "pass" if response.status_code == 200 else "fail",
            "status_code": response.status_code,
            "latency_ms": response.headers.get("X-AURUM-Latency-ms"),
        }

    except Exception as error:
        return {
            "check": label,
            "status": "fail",
            "error": str(error),
        }


def main():
    print("\nAURUM INFRASTRUCTURE PHASE 2 VALIDATION")
    print("=" * 70)

    checks = []

    checks.append(check_file_exists(Path("requirements.txt"), "requirements.txt exists"))
    checks.append(check_file_exists(Path("Dockerfile.api"), "API Dockerfile exists"))
    checks.append(check_file_exists(Path("Dockerfile.dashboard"), "Dashboard Dockerfile exists"))
    checks.append(check_file_exists(Path("docker-compose.yml"), "Docker Compose exists"))
    checks.append(check_file_exists(Path(".dockerignore"), ".dockerignore exists"))

    checks.append(check_file_exists(DATA_DIR, "data directory exists"))
    checks.append(check_file_exists(RESULTS_DIR, "results directory exists"))
    checks.append(check_file_exists(PIPELINE_RUN_LOG, "pipeline runtime log exists"))

    redis_status = check_redis_connection()
    checks.append(
        {
            "check": "redis connection",
            "status": "pass" if redis_status["status"] == "healthy" else "fail",
            "details": redis_status,
        }
    )

    checks.append(check_api_endpoint("/api/v1/health", "basic health endpoint"))
    checks.append(check_api_endpoint("/api/v1/health/redis", "redis health endpoint"))
    checks.append(check_api_endpoint("/api/v1/decision/snapshot", "decision snapshot endpoint"))
    checks.append(check_api_endpoint("/api/v1/pipeline/status", "pipeline status endpoint"))

    protected_headers = {
        "x-api-key": settings.API_KEY,
    }

    checks.append(
        check_api_endpoint(
            "/api/v1/health/full",
            "protected full health endpoint",
            headers=protected_headers,
        )
    )

    passed = 0
    failed = 0

    for item in checks:
        mark = "PASS" if item["status"] == "pass" else "FAIL"

        if mark == "PASS":
            passed += 1
        else:
            failed += 1

        print(f"[{mark}] {item['check']}")

        if "status_code" in item:
            print(f"       status_code: {item['status_code']}")

        if "latency_ms" in item:
            print(f"       latency_ms: {item['latency_ms']}")

        if "path" in item:
            print(f"       path: {item['path']}")

        if "error" in item:
            print(f"       error: {item['error']}")

    print("\nSUMMARY")
    print("-" * 70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\nINFRASTRUCTURE PHASE 2 STATUS: COMPLETE")
    else:
        print("\nINFRASTRUCTURE PHASE 2 STATUS: NEEDS ATTENTION")


if __name__ == "__main__":
    main()