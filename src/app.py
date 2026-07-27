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
from openai import RateLimitError, APIError

from orchestrator import run_single_use_case_assessment, run_full_portfolio_assessment
from executive_summary_agent import generate_executive_summary
from implementation_roadmap_agent import generate_implementation_roadmap

st.set_page_config(page_title="Enterprise AI Adoption Advisor", layout="wide")


@st.cache_data
def load_portfolio():
    with open("data/use_case_portfolio.json") as f:
        return json.load(f)["use_cases"]


@st.cache_data
def load_cached_assessments():
    try:
        with open("data/cached_assessments.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"single_use_case": {}, "portfolio_view": None}


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
cached_data = load_cached_assessments()

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
        selected_uc_id = None
    else:
        uc = next(u for u in portfolio if selected.startswith(u["id"]))
        use_case_description = uc["description"]
        selected_uc_id = uc["id"]
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
        cached_entry = cached_data["single_use_case"].get(selected_uc_id) if selected_uc_id else None

        if cached_entry:
            st.caption("⚡ Instant result from cached assessment, no live API call needed for preset use cases.")
            assessment = cached_entry["assessment"]
            summary = cached_entry["summary"]
            roadmap = cached_entry.get("roadmap")
            assessment_succeeded = True
        else:
            assessment_succeeded = False
            roadmap = None
            try:
                with st.spinner("Running Value, Risk, Architecture, Adoption, and Data Readiness agents..."):
                    assessment = run_single_use_case_assessment(use_case_description, portfolio_context)

                with st.spinner("Synthesizing executive briefing..."):
                    summary = generate_executive_summary(
                        use_case_description,
                        assessment["value"],
                        assessment["risk"],
                        assessment["architecture"],
                        assessment["adoption"],
                        assessment.get("data_readiness"),
                    )

                with st.spinner("Building implementation roadmap..."):
                    roadmap = generate_implementation_roadmap(
                        use_case_description,
                        assessment["value"],
                        assessment["risk"],
                        assessment["architecture"],
                        assessment["adoption"],
                        assessment.get("data_readiness"),
                    )
                assessment_succeeded = True
            except RateLimitError:
                st.error("We're experiencing high demand right now. Please wait a minute and try again.")
            except APIError:
                st.error("Something went wrong reaching the AI service. Please try again in a moment.")
            except Exception:
                st.error("Something unexpected happened while running this assessment. Please try again, and if it keeps happening, try a different use case description.")

        if assessment_succeeded:
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

            v, r, a, ad, dr = assessment["value"], assessment["risk"], assessment["architecture"], assessment["adoption"], assessment.get("data_readiness")
            c1, c2, c3, c4, c5 = st.columns(5)

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

            with c5:
                if dr:
                    st.metric("Data Readiness", f"{dr['readiness_score']}/100", dr["readiness_tier"])
                    st.caption(tier_color(dr["readiness_tier"]) + f" ~{dr['estimated_data_prep_weeks']} weeks prep")

            st.divider()

            if roadmap:
                st.header("Implementation Roadmap")
                st.caption(f"Estimated total timeline: ~{roadmap['estimated_total_timeline_months']} months, confidence: {roadmap['confidence']}")

                for phase in roadmap["roadmap_phases"]:
                    with st.expander(f"{phase['timeframe']}: {phase['focus']}"):
                        st.markdown("**Key milestones**")
                        for m in phase["key_milestones"]:
                            st.write(f"- {m}")
                        if phase.get("dependencies"):
                            st.markdown("**Dependencies**")
                            for d in phase["dependencies"]:
                                st.write(f"- {d}")

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**Critical path dependencies**")
                    for cp in roadmap["critical_path_dependencies"]:
                        st.write(f"- {cp}")
                with col_b:
                    st.markdown("**Success metrics**")
                    for sm in roadmap["success_metrics"]:
                        st.write(f"- {sm}")

                st.caption(roadmap["rationale"])
                st.divider()
            else:
                st.caption("Implementation roadmap not available for this cached result yet, this preset was cached before the Roadmap agent was added.")
                st.divider()

            with st.expander("Value agent detail"):
                st.json(v)
            with st.expander("Risk and Governance agent detail"):
                st.json(r)
            with st.expander("Architecture agent detail"):
                st.json(a)
            with st.expander("Adoption agent detail"):
                st.json(ad)
            if dr:
                with st.expander("Data Readiness agent detail"):
                    st.json(dr)

    elif run_button:
        st.warning("Enter a use case description first.")

with tab_portfolio:
    if cached_data.get("portfolio_view"):
        st.markdown("Showing the cached ranking across all eight synthetic use cases, no live API calls needed.")
        result = cached_data["portfolio_view"]
        portfolio_succeeded = True

        with st.expander("Prefer a fresh live run instead? (uses API quota, takes a few minutes)"):
            st.caption("This re-runs all eight use cases through five agents each, roughly forty LLM calls, and will consume a meaningful share of the daily API budget.")
            live_refresh = st.button("Run live portfolio assessment anyway", key="portfolio_live_refresh")
            if live_refresh:
                try:
                    with st.spinner("Running full live portfolio assessment..."):
                        result = run_full_portfolio_assessment(portfolio)
                except RateLimitError:
                    st.error("We're experiencing high demand right now. Please try again in a few minutes.")
                    portfolio_succeeded = False
                except APIError:
                    st.error("Something went wrong reaching the AI service partway through this run. Please try again in a moment.")
                    portfolio_succeeded = False
                except Exception:
                    st.error("Something unexpected happened during the portfolio assessment. Please try again.")
                    portfolio_succeeded = False
    else:
        st.markdown("Runs all eight synthetic use cases through Value, Risk, Architecture, Adoption, and Data Readiness, then ranks them with the Portfolio Prioritization agent. This takes longer than a single assessment since it makes roughly forty LLM calls in sequence.")

        portfolio_run = st.button("Run full portfolio assessment", type="primary", key="portfolio_run")

        portfolio_succeeded = False
        if portfolio_run:
            progress_text = st.empty()
            progress_text.info(f"Assessing {len(portfolio)} use cases across five agents each, then ranking the portfolio, this may take a few minutes...")

            try:
                with st.spinner("Running full portfolio assessment..."):
                    result = run_full_portfolio_assessment(portfolio)
                portfolio_succeeded = True
                progress_text.empty()
            except RateLimitError:
                progress_text.empty()
                st.error("We're experiencing high demand right now, this run makes many calls in sequence. Please wait a few minutes and try again.")
            except APIError:
                progress_text.empty()
                st.error("Something went wrong reaching the AI service partway through this run. Please try again in a moment.")
            except Exception:
                progress_text.empty()
                st.error("Something unexpected happened during the portfolio assessment. Please try again.")

    if portfolio_succeeded:
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
                dr = assessment.get("data_readiness")
                cols = st.columns(5) if dr else st.columns(4)
                cols[0].metric("Value", f"{v['value_score']}/100", v["value_tier"])
                cols[1].metric("Risk", f"{r['risk_score']}/100", r["risk_tier"])
                cols[2].metric("Complexity", f"{a['complexity_score']}/100", a["complexity_tier"])
                cols[3].metric("Adoption", f"{ad['adoption_score']}/100", ad["adoption_tier"])
                if dr:
                    cols[4].metric("Data Readiness", f"{dr['readiness_score']}/100", dr["readiness_tier"])

st.divider()
st.caption("Source code: github.com/net2user/Multi-Agent-Enterprise-AI-Adoption-Advisor")