"""
Enterprise AI Adoption Advisor - Streamlit Frontend

Two tabs. Single Use Case wraps the four agent pipeline plus Executive
Summary for one use case at a time. Portfolio View runs the full
synthetic portfolio through all four agents, then ranks every use case
with the Portfolio Prioritization agent, the piece that was built and
tested standalone but never wired into the live interface until now.
"""

import json
import streamlit as st

from orchestrator import run_single_use_case_assessment, run_full_portfolio_assessment
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


def sequence_color(seq: str) -> str:
    mapping = {
        "Quick Win": "🟢", "Strategic Bet": "🟡", "Long Term Play": "🟠", "Reconsider": "🔴",
    }
    return mapping.get(seq, "⚪")


st.title("Enterprise AI Adoption Advisor")
st.caption("Multi agent evaluation for BFSI and Healthcare AI use cases, built by Vikas Sharma, Senior AI and Digital Transformation Advisor")

portfolio = load_portfolio()

tab_single, tab_portfolio = st.tabs(["Single Use Case", "Portfolio View"])

with tab_single:
    portfolio_titles = ["Write my own use case"] + [f"{uc['id']}: {uc['title']}" for uc in portfolio]

    selected = st.selectbox("Choose a sample use case, or write your own", portfolio_titles, key="single_select")

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

    run_button = st.button("Run assessment", type="primary", key="single_run")

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

        headline_safe = summary["executive_headline"].replace("$", "\\$")
        briefing_safe = summary["briefing_paragraph"].replace("$", "\\$")

        st.markdown(f"**{headline_safe}**")
        st.write(briefing_safe)

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
            value_range_parts = v["estimated_annual_value_range_usd"].split(" - ")
            value_range_display = " to ".join(
                p.strip() if p.strip().startswith("$") else "$" + p.strip()
                for p in value_range_parts
            )
            st.caption(tier_color(v["value_tier"]) + " " + value_range_display.replace("$", "\\$"))

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

with tab_portfolio:
    st.markdown("Runs all eight synthetic use cases through Value, Risk, Architecture, and Adoption, then ranks them with the Portfolio Prioritization agent. This takes longer than a single assessment since it makes roughly forty LLM calls in sequence.")

    portfolio_run = st.button("Run full portfolio assessment", type="primary", key="portfolio_run")

    if portfolio_run:
        progress_text = st.empty()
        progress_text.info(f"Assessing {len(portfolio)} use cases across four agents each, then ranking the portfolio, this may take a few minutes...")

        with st.spinner("Running full portfolio assessment..."):
            result = run_full_portfolio_assessment(portfolio)

        progress_text.empty()
        st.success("Portfolio assessment complete.")

        ranked = result["ranked_portfolio"]["ranked_portfolio"]

        st.divider()
        st.header("Ranked Portfolio")

        for entry in ranked:
            seq = entry["recommended_sequence"]
            with st.container():
                cols = st.columns([0.6, 3, 1.2, 1.5, 4])
                cols[0].markdown(f"**#{entry['rank']}**")
                cols[1].markdown(f"**{entry['use_case_title']}**  \n`{entry['use_case_id']}`")
                cols[2].markdown(f"**{entry['composite_score']}**/100")
                cols[3].markdown(f"{sequence_color(seq)} {seq}")
                cols[4].markdown(entry["one_line_justification"])
            st.divider()

        st.subheader("Portfolio Level Observations")
        for obs in result["ranked_portfolio"]["portfolio_level_observations"]:
            st.write(f"- {obs}")

        st.divider()
        st.subheader("Per Use Case Detail")
        for uc_id, assessment in result["per_use_case_assessments"].items():
            title = next(u["title"] for u in portfolio if u["id"] == uc_id)
            with st.expander(f"{uc_id}: {title}"):
                v, r, a, ad = assessment["value"], assessment["risk"], assessment["architecture"], assessment["adoption"]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Value", f"{v['value_score']}/100", v["value_tier"])
                c2.metric("Risk", f"{r['risk_score']}/100", r["risk_tier"])
                c3.metric("Complexity", f"{a['complexity_score']}/100", a["complexity_tier"])
                c4.metric("Adoption", f"{ad['adoption_score']}/100", ad["adoption_tier"])

st.divider()
st.caption("Source code: github.com/net2user/Multi-Agent-Enterprise-AI-Adoption-Advisor")
