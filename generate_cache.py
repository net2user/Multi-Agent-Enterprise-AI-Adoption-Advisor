"""
Cache Generator

Run this once, locally, to generate genuine cached results for all
eight synthetic use cases plus the portfolio ranking, saved to
data/cached_assessments.json. app.py reads this file directly for any
preset use case or the default Portfolio View, no live API calls
needed for those paths going forward. "Write my own use case" and the
optional "Run live portfolio assessment anyway" button in Portfolio
View still call the API live, on purpose.

This script deliberately reuses each use case's individual agent
scores to build the portfolio ranking input, rather than re-running
all five agents a second time through run_full_portfolio_assessment,
cutting total token cost roughly in half compared to running both
separately.

Cost estimate: eight use cases at roughly seven calls each (five agents,
one executive summary, one roadmap), plus one final portfolio ranking
call, using your account's own recent average of about 872 tokens per
call, this totals approximately 49,000 tokens. Check your Groq usage
page first and run this when the day's usage is low.
"""

import json
import time

from orchestrator import run_single_use_case_assessment
from executive_summary_agent import generate_executive_summary
from implementation_roadmap_agent import generate_implementation_roadmap
from portfolio_agent import prioritize_portfolio

with open("data/use_case_portfolio.json") as f:
    portfolio = json.load(f)["use_cases"]

single_use_case_cache = {}
per_use_case_assessments = {}
scored_for_ranking = []

for uc in portfolio:
    print(f"Running {uc['id']}: {uc['title']}...")

    context = {
        "sector": uc["sector"],
        "domain": uc["domain"],
        "estimated_annual_cost_usd": uc.get("estimated_annual_cost_usd"),
        "current_process_maturity": uc.get("current_process_maturity"),
        "data_sensitivity": uc.get("data_sensitivity"),
        "regulatory_exposure": uc.get("regulatory_exposure"),
        "integration_points": uc.get("integration_points"),
        "vendor": uc.get("vendor"),
        "stakeholders": uc.get("stakeholders"),
    }

    assessment = run_single_use_case_assessment(uc["description"], context)

    summary = generate_executive_summary(
        uc["description"],
        assessment["value"],
        assessment["risk"],
        assessment["architecture"],
        assessment["adoption"],
        assessment.get("data_readiness"),
    )

    roadmap = generate_implementation_roadmap(
        uc["description"],
        assessment["value"],
        assessment["risk"],
        assessment["architecture"],
        assessment["adoption"],
        assessment.get("data_readiness"),
    )

    single_use_case_cache[uc["id"]] = {
        "assessment": assessment,
        "summary": summary,
        "roadmap": roadmap,
    }
    per_use_case_assessments[uc["id"]] = assessment

    scored_for_ranking.append({
        "use_case_id": uc["id"],
        "title": uc["title"],
        "value_score": assessment["value"]["value_score"],
        "risk_score": assessment["risk"]["risk_score"],
        "complexity_score": assessment["architecture"]["complexity_score"],
        "adoption_score": assessment["adoption"]["adoption_score"],
    })

    print("  Done. Pausing briefly before the next use case...")
    time.sleep(3)

print("Running portfolio ranking using scores already collected above...")
ranked_portfolio = prioritize_portfolio(scored_for_ranking)

output = {
    "single_use_case": single_use_case_cache,
    "portfolio_view": {
        "ranked_portfolio": ranked_portfolio,
        "per_use_case_assessments": per_use_case_assessments,
    },
}

with open("data/cached_assessments.json", "w") as f:
    json.dump(output, f, indent=2)

print("\nDone. Saved to data/cached_assessments.json")
print(f"Cached {len(single_use_case_cache)} use cases plus one portfolio ranking.")