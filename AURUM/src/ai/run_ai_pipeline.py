from src.ai.router import AIRouter, save_router_output


def run_ai_pipeline():
    router = AIRouter()

    tasks = {
        "market_signal": "Analyze market signal report",
        "executive": "Generate executive portfolio analysis",
        "technical": "Generate technical portfolio analysis",
        "structured": "Generate structured portfolio analysis"
    }

    for name, task in tasks.items():
        result = router.route(task)

        output_path = f"results/reports/router_{name}_output.txt"

        if isinstance(result, dict):
            output_path = f"results/reports/router_{name}_output.json"

        save_router_output(result, output_path)

        print(f"Saved {name} output to: {output_path}")


if __name__ == "__main__":
    run_ai_pipeline()
