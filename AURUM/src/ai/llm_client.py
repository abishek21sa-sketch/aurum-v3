from openai import OpenAI
from dotenv import load_dotenv
import os
import json

from src.ai.prompts import (
    SYSTEM_PROMPT,
    build_market_prompt
)

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def parse_json_response(content: str):
    content = content.strip()

    if content.startswith("```json"):
        content = content.replace("```json", "", 1).strip()

    if content.startswith("```"):
        content = content.replace("```", "", 1).strip()

    if content.endswith("```"):
        content = content[:-3].strip()

    return json.loads(content)

def query_llm(user_query, context=""):
    prompt = build_market_prompt(
        user_query=user_query,
        context=context
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content


def query_llm_structured(user_query, context=""):

    structured_prompt = f"""
    {build_market_prompt(user_query, context)}

    Return your response ONLY as valid JSON.

    Required schema:

    {{
        "portfolio_style": "",
        "risk_profile": "",
        "top_risk_factors": [],
        "diversification_assessment": "",
        "key_strengths": [],
        "key_weaknesses": [],
        "summary": ""
    }}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": structured_prompt
            }
        ],
        temperature=0.1
    )

    content = response.choices[0].message.content

    return parse_json_response(content)


if __name__ == "__main__":

    sample_context = """
    Portfolio Return: 14.2%
    Portfolio Volatility: 9.1%
    Sharpe Ratio: 1.31

    Top Assets:
    SPY: 32%
    TLT: 29%
    GLD: 11%
    """

    structured_output = query_llm_structured(
        user_query="Analyze this portfolio.",
        context=sample_context
    )

    print("\nSTRUCTURED AI OUTPUT")
    print("=" * 60)
    print(json.dumps(structured_output, indent=4))
