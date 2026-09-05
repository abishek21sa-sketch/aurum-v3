import os


def get_database_url() -> str:
    return os.getenv(
        "TIMESCALE_DATABASE_URL",
        os.getenv(
            "DATABASE_URL",
            "postgresql://aurum:aurum@127.0.0.1:5434/aurum",
        ),
    )