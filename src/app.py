"""
Enterprise AI Adoption Advisor - Streamlit Frontend

Wraps the full agent pipeline, Value, Risk, Architecture, Adoption, and
Executive Summary, into a clickable dashboard. Takes a use case
description as input, optionally pre-filled from the synthetic portfolio,
and displays every agent's output plus the final board level briefing.
"""

import json
import streamlit as st

from orchestrator import run_single_use_case_assessment
from executive_summary_agent import generate_executive_summary

st.set_page_config(page_title="Enterprise AI Adoption Advisor", layout="wide")


@st.cache_data
def load_portfolio():
    with open("data/use_case_portfolio.json") as f:
        return json.load(f)["use_cases"]


def tier_color(tier: str) -> str:
    mapping = {
        "Low": "🟢", "Moderate": "🟡", "High": "🟠", "Critical": "🔴",
        "Transformational": "🟣", "Strong": "🟢", "Very High": "🔴",
    }
    return mapping.get(tier, "⚪")


st.title("Enterprise AI Adoption Advisor")
st.caption("Multi agent evaluation for BFSI and Healthcare AI use cases, built by Vikas Sharma, Senior AI and Digital Transformation Advisor")

portfolio = load_portfolio()
portfolio_titles = ["Write my own use case"] + [f"{uc['id']}: {uc['title']}" for uc in portfolio]

selected = st.selectbox("Choose a sample use case, or write your own", portfolio_titles)

if selected == "Write my own use case":
    use_case_description = st.text_area(
        "Describe the AI use case",
        placeholder="e.g. Deploy AI for procurement operations to review vendor contracts and flag pricing anomalies.",
        height=100,
    )
    portfolio_context = None
else:
    uc = next(u for u in portfolio if selected.startswith(u["id"]))
    use_case_description = uc["description"]
    portfolio_context = {
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
    st.text_area("Use case description", value=use_case_description, height=100, disabled=True)

run_button = st.button("Run assessment", type="primary")

if run_button and use_case_description.strip():
    with st.spinner("Running Value, Risk, Architecture, and Adoption agents..."):
        assessment = run_single_use_case_assessment(use_case_description, portfolio_context)

    with st.spinner("Synthesizing executive briefing..."):
        summary = generate_executive_summary(
            use_case_description,
            assessment["value"],
            assessment["risk"],
            assessment["architecture"],
            assessment["adoption"],
        )

    st.divider()
    st.header("Executive Briefing")

    rec = summary["overall_recommendation"]
    rec_color = {"Fund": "🟢", "Fund with Conditions": "🟡", "Delay": "🟠", "Do Not Fund": "🔴"}.get(rec, "⚪")
    st.subheader(f"{rec_color} {rec}")
st.markdown(f"**{summary['executive_headline']}**".replace("$", "\\$"))
st.write(summary["briefing_paragraph"].replace("$", "\\$"))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Top conditions for funding**")
        for c in summary["top_conditions_for_funding"]:
            st.write(f"- {c}")
    with col2:
        st.markdown("**Key tension**")
        st.write(summary["key_tension"])

    st.divider()
    st.header("Agent Scorecards")

    v, r, a, ad = assessment["value"], assessment["risk"], assessment["architecture"], assessment["adoption"]
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("Value", f"{v['value_score']}/100", v["value_tier"])
        st.caption(tier_color(v["value_tier"]) + " " + v["estimated_annual_value_range_usd"])

    with c2:
        st.metric("Risk", f"{r['risk_score']}/100", r["risk_tier"])
        st.caption(tier_color(r["risk_tier"]) + " Human in loop: " + str(r["human_in_the_loop_required"]))

    with c3:
        st.metric("Complexity", f"{a['complexity_score']}/100", a["complexity_tier"])
        st.caption(tier_color(a["complexity_tier"]) + f" ~{a['estimated_time_to_pilot_weeks']} weeks to pilot")

    with c4:
        st.metric("Adoption", f"{ad['adoption_score']}/100", ad["adoption_tier"])
        st.caption(tier_color(ad["adoption_tier"]) + " " + ad["confidence"] + " confidence")

    st.divider()

    with st.expander("Value agent detail"):
        st.json(v)
    with st.expander("Risk and Governance agent detail"):
        st.json(r)
    with st.expander("Architecture agent detail"):
        st.json(a)
    with st.expander("Adoption agent detail"):
        st.json(ad)

elif run_button:
    st.warning("Enter a use case description first.")

st.divider()
st.caption("Source code: github.com/net2user/Multi-Agent-Enterprise-AI-Adoption-Advisor")
