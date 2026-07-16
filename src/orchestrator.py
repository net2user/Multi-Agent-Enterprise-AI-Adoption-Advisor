"""
Orchestrator

Wires the Value, Risk, and Architecture agents together using LangGraph.
A single use case input flows through all three agents and comes out as
one combined assessment. Adoption, Portfolio Prioritization, and
Executive Summary agents plug into this same graph in later phases.
"""

import json
from typing import TypedDict, Optional

from langgraph.graph import StateGraph, END

from agents import evaluate_business_value
from risk_agent import evaluate_risk
from architecture_agent import evaluate_architecture


class AssessmentState(TypedDict):
    use_case_description: str
    portfolio_context: Optional[dict]
    value_result: Optional[dict]
    risk_result: Optional[dict]
    architecture_result: Optional[dict]


def run_value_node(state: AssessmentState) -> AssessmentState:
    result = evaluate_business_value(state["use_case_description"], state.get("portfolio_context"))
    state["value_result"] = result
    return state


def run_risk_node(state: AssessmentState) -> AssessmentState:
    result = evaluate_risk(state["use_case_description"], state.get("portfolio_context"))
    state["risk_result"] = result
    return state


def run_architecture_node(state: AssessmentState) -> AssessmentState:
    result = evaluate_architecture(state["use_case_description"], state.get("portfolio_context"))
    state["architecture_result"] = result
    return state


def build_graph():
    graph = StateGraph(AssessmentState)

    graph.add_node("value_agent", run_value_node)
    graph.add_node("risk_agent", run_risk_node)
    graph.add_node("architecture_agent", run_architecture_node)

    # Sequential for now (Day 3-4 scope). Phase 4 revisits this for
    # parallel fan-out once the Adoption and Portfolio agents are added.
    graph.set_entry_point("value_agent")
    graph.add_edge("value_agent", "risk_agent")
    graph.add_edge("risk_agent", "architecture_agent")
    graph.add_edge("architecture_agent", END)

    return graph.compile()


def run_assessment(use_case_description: str, portfolio_context: dict = None) -> dict:
    app = build_graph()
    initial_state: AssessmentState = {
        "use_case_description": use_case_description,
        "portfolio_context": portfolio_context,
        "value_result": None,
        "risk_result": None,
        "architecture_result": None,
    }
    final_state = app.invoke(initial_state)

    return {
        "value": final_state["value_result"],
        "risk": final_state["risk_result"],
        "architecture": final_state["architecture_result"],
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
    }

    combined = run_assessment(uc["description"], context)
    print(json.dumps(combined, indent=2))
