"""
Orchestrator

Wires all five agents together using LangGraph: Value, Risk, Architecture,
Adoption, then Portfolio Prioritization runs separately across the full
scored portfolio once every use case has been through the first four.
Executive Summary agent plugs in next, on top of this combined output.
"""

import json
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from agents import evaluate_business_value
from risk_agent import evaluate_risk
from architecture_agent import evaluate_architecture
from adoption_agent import evaluate_adoption
from portfolio_agent import prioritize_portfolio


class AssessmentState(TypedDict):
    use_case_description: str
    portfolio_context: Optional[dict]
    value_result: Optional[dict]
    risk_result: Optional[dict]
    architecture_result: Optional[dict]
    adoption_result: Optional[dict]


def run_value_node(state: AssessmentState) -> AssessmentState:
    state["value_result"] = evaluate_business_value(state["use_case_description"], state.get("portfolio_context"))
    return state


def run_risk_node(state: AssessmentState) -> AssessmentState:
    state["risk_result"] = evaluate_risk(state["use_case_description"], state.get("portfolio_context"))
    return state


def run_architecture_node(state: AssessmentState) -> AssessmentState:
    state["architecture_result"] = evaluate_architecture(state["use_case_description"], state.get("portfolio_context"))
    return state


def run_adoption_node(state: AssessmentState) -> AssessmentState:
    state["adoption_result"] = evaluate_adoption(state["use_case_description"], state.get("portfolio_context"))
    return state


def build_graph():
    graph = StateGraph(AssessmentState)

    graph.add_node("value_agent", run_value_node)
    graph.add_node("risk_agent", run_risk_node)
    graph.add_node("architecture_agent", run_architecture_node)
    graph.add_node("adoption_agent", run_adoption_node)

    graph.set_entry_point("value_agent")
    graph.add_edge("value_agent", "risk_agent")
    graph.add_edge("risk_agent", "architecture_agent")
    graph.add_edge("architecture_agent", "adoption_agent")
    graph.add_edge("adoption_agent", END)

    return graph.compile()


def run_single_use_case_assessment(use_case_description: str, portfolio_context: dict = None) -> dict:
    """
    Runs Value, Risk, Architecture, and Adoption for one use case.
    """
    app = build_graph()
    initial_state: AssessmentState = {
        "use_case_description": use_case_description,
        "portfolio_context": portfolio_context,
        "value_result": None,
        "risk_result": None,
        "architecture_result": None,
        "adoption_result": None,
    }
    final_state = app.invoke(initial_state)

    return {
        "value": final_state["value_result"],
        "risk": final_state["risk_result"],
        "architecture": final_state["architecture_result"],
        "adoption": final_state["adoption_result"],
    }


def run_full_portfolio_assessment(use_cases: list) -> dict:
    """
    Runs the full four-agent assessment across every use case in the
    portfolio, then feeds the resulting scores into the Portfolio
    Prioritization Agent for a ranked view.
    """
    per_use_case_results = {}
    scored_for_ranking = []

    for uc in use_cases:
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
        per_use_case_results[uc["id"]] = assessment

        scored_for_ranking.append({
            "use_case_id": uc["id"],
            "title": uc["title"],
            "value_score": assessment["value"]["value_score"],
            "risk_score": assessment["risk"]["risk_score"],
            "complexity_score": assessment["architecture"]["complexity_score"],
            "adoption_score": assessment["adoption"]["adoption_score"],
        })

    ranked = prioritize_portfolio(scored_for_ranking)

    return {
        "per_use_case_assessments": per_use_case_results,
        "ranked_portfolio": ranked,
    }


if __name__ == "__main__":
    with open("data/use_case_portfolio.json") as f:
        portfolio = json.load(f)

    uc = portfolio["use_cases"][0]  # UC-001: procurement operations
    context = {
        "sector": uc["sector"],
        "domain": uc["domain"],
        "estimated_annual_cost_usd": uc["estimated_annual_cost_usd"],
        "current_process_maturity": uc["current_process_maturity"],
        "data_sensitivity": uc["data_sensitivity"],
        "regulatory_exposure": uc["regulatory_exposure"],
        "integration_points": uc["integration_points"],
        "vendor": uc["vendor"],
        "stakeholders": uc["stakeholders"],
    }

    combined = run_single_use_case_assessment(uc["description"], context)
    print(json.dumps(combined, indent=2))