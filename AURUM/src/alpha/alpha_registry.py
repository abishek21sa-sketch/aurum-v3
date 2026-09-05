from pathlib import Path
import json


REGISTRY_PATH = Path("results/alpha/alpha_registry.json")


class AlphaRegistry:
    def load(self) -> dict:
        if not REGISTRY_PATH.exists():
            return {"alphas": []}

        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def list_alpha_ids(self) -> list[str]:
        registry = self.load()
        return [alpha["alpha_id"] for alpha in registry.get("alphas", [])]

    def get_alpha(self, alpha_id: str) -> dict | None:
        registry = self.load()

        for alpha in registry.get("alphas", []):
            if alpha["alpha_id"] == alpha_id:
                return alpha

        return None