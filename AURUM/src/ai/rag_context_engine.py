from pathlib import Path
import json
import re


CONTEXT_PATH = Path("results/ai/aurum_context_snapshot.json")


KEYWORD_GROUPS = {
    "regime": ["regime", "transition", "market state", "probability"],
    "risk": ["risk", "drawdown", "stress", "cvar", "tail", "volatility", "shock"],
    "allocation": ["allocation", "weights", "portfolio", "optimizer", "optimization"],
    "scenario": ["scenario", "shock", "crash", "gap", "rates", "rally"],
    "executive": ["executive", "summary", "strategy", "decision", "recommendation"],
    "technical": ["technical", "variance", "covariance", "sharpe", "efficient frontier"],
    "hedging": ["hedge", "hedging", "overlay", "tlt", "spy"],
}


def load_context():
    if not CONTEXT_PATH.exists():
        raise FileNotFoundError(
            "Context snapshot not found. Run: python -m src.ai.context_loader"
        )

    with CONTEXT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def infer_query_topics(query: str):
    query_norm = normalize_text(query)
    matched_topics = []

    for topic, keywords in KEYWORD_GROUPS.items():
        if any(keyword in query_norm for keyword in keywords):
            matched_topics.append(topic)

    return matched_topics or ["general"]


def score_document(query: str, path: str, content: str):
    query_terms = normalize_text(query).split()
    content_norm = normalize_text(content)
    path_norm = normalize_text(path)

    score = 0

    for term in query_terms:
        if term in content_norm:
            score += 2
        if term in path_norm:
            score += 3

    topics = infer_query_topics(query)

    for topic in topics:
        for keyword in KEYWORD_GROUPS.get(topic, []):
            if keyword in content_norm:
                score += 1
            if keyword in path_norm:
                score += 2

    return score


def build_document_index(context: dict):
    docs = []

    for path, content in context.get("text_reports", {}).items():
        docs.append(
            {
                "path": path,
                "type": "text",
                "content": content,
            }
        )

    for path, content in context.get("csv_reports", {}).items():
        docs.append(
            {
                "path": path,
                "type": "csv",
                "content": content,
            }
        )

    for path, content in context.get("json_reports", {}).items():
        docs.append(
            {
                "path": path,
                "type": "json",
                "content": json.dumps(content, indent=2),
            }
        )

    return docs


def retrieve_relevant_context(query: str, top_k: int = 5):
    context = load_context()
    docs = build_document_index(context)

    scored_docs = []

    for doc in docs:
        score = score_document(query, doc["path"], doc["content"])

        if score > 0:
            scored_docs.append(
                {
                    "score": score,
                    "path": doc["path"],
                    "type": doc["type"],
                    "content": doc["content"],
                }
            )

    scored_docs = sorted(scored_docs, key=lambda x: x["score"], reverse=True)

    return scored_docs[:top_k]


def format_retrieved_context(results):
    lines = []
    lines.append("AURUM RETRIEVED CONTEXT")
    lines.append("=" * 70)

    if not results:
        lines.append("No relevant context found.")
        return "\n".join(lines)

    for i, item in enumerate(results, start=1):
        preview = item["content"][:1200]

        lines.append("")
        lines.append(f"[{i}] {item['path']}")
        lines.append(f"Type: {item['type']}")
        lines.append(f"Score: {item['score']}")
        lines.append("-" * 70)
        lines.append(preview)

    return "\n".join(lines)


if __name__ == "__main__":
    test_queries = [
        "Why did the portfolio allocation change?",
        "What happens during an equity gap down scenario?",
        "Give me an executive summary of current portfolio risk.",
        "Explain the technical optimization logic.",
    ]

    for query in test_queries:
        print("\n" + "#" * 90)
        print(f"QUERY: {query}")
        print("#" * 90)

        results = retrieve_relevant_context(query, top_k=5)
        print(format_retrieved_context(results))