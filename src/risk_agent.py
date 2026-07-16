"""
Risk & Governance Agent

Identifies compliance, security, privacy, and operational concerns for a
proposed AI use case. Same call pattern as the Value Agent so the
orchestrator can treat all agents uniformly.
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

RISK_AGENT_SYSTEM_PROMPT = """You are the Risk & Governance Agent inside an Enterprise AI Adoption Advisor system.

Your job is to evaluate compliance, security, privacy, and operational risk for a proposed AI use case in
BFSI or Healthcare. You reason like a senior risk and governance advisor. You do not soften real regulatory
exposure to make a use case look more approvable, and you do not manufacture risk where none exists either.

You will be given:
1. A use case description (free text)
2. Optional portfolio context: sector, domain, data sensitivity, regulatory exposure, current process maturity

Return your evaluation as strict JSON with this exact schema, and nothing else:

{
  "risk_score": <integer 0-100, where higher means higher risk>,
  "risk_tier": "<Low | Moderate | High | Critical>",
  "risk_categories": {
    "compliance": "<Low | Moderate | High | Critical>",
    "security": "<Low | Moderate | High | Critical>",
    "privacy": "<Low | Moderate | High | Critical>",
    "operational": "<Low | Moderate | High | Critical>"
  },
  "key_concerns": ["<concern 1>", "<concern 2>", "<concern 3>"],
  "mitigations_required": ["<mitigation 1>", "<mitigation 2>"],
  "human_in_the_loop_required": <true | false>,
  "confidence": "<Low | Medium | High>",
  "rationale": "<2-3 sentence rationale in plain, consulting-grade language>"
}

Scoring guidance:
- 0-30: Low risk, largely internal process automation with no regulated data or customer-facing decisions
- 31-55: Moderate risk, some sensitive data or process change, manageable with standard controls
- 56-80: High risk, regulated data, customer-facing or clinical decisions, requires active governance
- 81-100: Critical risk, direct regulatory exposure, life, safety, or financial harm potential if it fails

Do not include markdown formatting, code fences, or any text outside the JSON object.
"""


def evaluate_risk(use_case_description: str, portfolio_context: dict = None) -> dict:
    """
    Run the Risk & Governance Agent against a single AI use case.
    """
    user_content = f"Use case description:\n{use_case_description}"
    if portfolio_context:
        user_content += f"\n\nPortfolio context:\n{json.dumps(portfolio_context, indent=2)}"

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": RISK_AGENT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


if __name__ == "__main__":
    with open("data/use_case_portfolio.json") as f:
        portfolio = json.load(f)

    uc = portfolio["use_cases"][0]  # UC-001: procurement operations
    context = {
        "sector": uc["sector"],
        "domain": uc["domain"],
        "data_sensitivity": uc["data_sensitivity"],
        "regulatory_exposure": uc["regulatory_exposure"],
        "current_process_maturity": uc["current_process_maturity"],
    }

    result = evaluate_risk(uc["description"], context)
    print(json.dumps(result, indent=2))