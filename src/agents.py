"""
Enterprise AI Adoption Advisor - Agent Definitions
Business Value Agent

Each agent is a thin wrapper around an LLM call with a structured prompt
and a structured JSON output contract. Later agents (Risk, Architecture,
Adoption, Portfolio, Executive Summary) follow the same pattern and plug
into the same orchestrator interface.
"""

import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ.get("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

VALUE_AGENT_SYSTEM_PROMPT = """You are the Business Value Agent inside an Enterprise AI Adoption Advisor system.

Your job is to evaluate the expected business impact of a proposed AI use case for BFSI or Healthcare
organizations. You reason like a senior digital transformation advisor with deep operational experience,
not like a generic assistant. You are specific, you quantify where you can, and you do not inflate value
estimates to sound impressive.

You will be given:
1. A use case description (free text)
2. Optional portfolio context: cost, sector, domain, current process maturity

Return your evaluation as strict JSON with this exact schema, and nothing else:

{
  "value_score": <integer 0-100>,
  "value_tier": "<Low | Moderate | High | Transformational>",
  "estimated_annual_value_range_usd": "<string range, e.g. '1.2M - 1.8M'>",
  "value_drivers": ["<driver 1>", "<driver 2>", "<driver 3>"],
  "key_assumptions": ["<assumption 1>", "<assumption 2>"],
  "confidence": "<Low | Medium | High>",
  "rationale": "<2-3 sentence rationale in plain, consulting-grade language>"
}

Scoring guidance:
- 0-30: Low value, likely a point solution or process convenience only
- 31-55: Moderate value, meaningful efficiency gain in one function
- 56-80: High value, measurable impact on cost, revenue, or risk exposure at a business unit level
- 81-100: Transformational, impact spans multiple functions or changes a core operating model

Do not include markdown formatting, code fences, or any text outside the JSON object.
"""


def evaluate_business_value(use_case_description: str, portfolio_context: dict = None) -> dict:
    """
    Run the Business Value Agent against a single AI use case.

    Args:
        use_case_description: free text description of the proposed AI use case
        portfolio_context: optional dict with cost, sector, domain, maturity fields
                            pulled from data/use_case_portfolio.json

    Returns:
        dict matching the Value Agent JSON schema
    """
    user_content = f"Use case description:\n{use_case_description}"
    if portfolio_context:
        user_content += f"\n\nPortfolio context:\n{json.dumps(portfolio_context, indent=2)}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": VALUE_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    return json.loads(raw)


if __name__ == "__main__":
    # Quick manual test using UC-001 from the synthetic portfolio
    with open("data/use_case_portfolio.json") as f:
        portfolio = json.load(f)

    uc = portfolio["use_cases"][0]  # UC-001: procurement operations
    context = {
        "sector": uc["sector"],
        "domain": uc["domain"],
        "estimated_annual_cost_usd": uc["estimated_annual_cost_usd"],
        "current_process_maturity": uc["current_process_maturity"],
    }

    result = evaluate_business_value(uc["description"], context)
    print(json.dumps(result, indent=2))