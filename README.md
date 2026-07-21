# Enterprise AI Adoption Advisor

A multi agent system that evaluates proposed AI use cases for BFSI and Healthcare organizations across business value, risk and governance, technical architecture, organizational adoption readiness, and portfolio priority, then produces a board level executive briefing.

Built by Vikas Sharma, Senior AI and Digital Transformation Advisor.

Live app: https://multi-agent-enterprise-ai-adoption-advisor-ixmdm7zxqmqrhxgkzna.streamlit.app
Source: github.com/net2user/Multi-Agent-Enterprise-AI-Adoption-Advisor

## Status

Complete and working end to end. Five agents, an orchestrator, and a Streamlit dashboard are built, tested, and confirmed against use cases spanning BFSI and Healthcare. This is not a proof of concept, it runs.

## Problem statement

Organizations across BFSI and Healthcare now have more AI use case ideas than they have capacity to evaluate. The gap is not idea generation, it is disciplined assessment. Most organizations lack a repeatable way to compare a fraud detection use case against a clinical documentation use case on equal footing, across value, risk, feasibility, and organizational readiness, and to turn that comparison into a defensible roadmap a board can act on.

This system addresses that gap directly. Feed it a single use case description, or a portfolio of them, and it returns a structured assessment covering the dimensions that actually determine whether an AI initiative succeeds after approval, not just whether it sounds promising in a slide.

## Business context

The assessment logic here reflects patterns seen across twenty five years of enterprise AI and digital transformation advisory work in BFSI, Healthcare, Telecom, and Public Sector settings. The agents are calibrated with a synthetic but realistic portfolio of eight BFSI and Healthcare use cases, covering procurement, KYC, claims fraud, clinical documentation, prior authorization, and lending, so the scoring reflects real regulatory and operational texture rather than generic assumptions.

## Architecture

![System architecture diagram](docs/architecture_diagram.png)

A single use case input flows through an orchestrator built on LangGraph. The orchestrator routes the input sequentially through four specialist agents, Value, Risk and Governance, Architecture, and Adoption, each producing an independent structured assessment. Once all four complete, their outputs feed into the Executive Summary agent, which synthesizes them into one board level recommendation. The Portfolio Prioritization agent runs separately, ranking multiple already scored use cases against each other rather than evaluating any single one from scratch.

All five agents run on Groq's Llama 3.3 70B model rather than OpenAI, a deliberate choice made during the build to keep the project genuinely free to run and test, with no billing dependency for anyone cloning the repository to try it themselves.

## Agent design

Each agent is a focused LLM call with a strict JSON output schema, not a general purpose chatbot wrapped in a persona. This keeps outputs composable, so the orchestrator and the Streamlit dashboard can render structured scores rather than parsing free text.

Value agent evaluates expected business impact, returning a value score, tier, estimated annual value range, and the specific drivers behind the number.

Risk and Governance agent evaluates compliance, security, privacy, and operational risk, returning a risk score, a breakdown across those four categories, and required mitigations.

Architecture agent evaluates integration complexity and technical feasibility, returning a complexity score, integration challenges, a recommended architecture pattern, and a build versus buy recommendation.

Adoption agent evaluates organizational readiness, the dimension most AI post mortems point to when a technically sound project fails anyway, returning an adoption score, readiness factors across leadership sponsorship, process disruption, workforce impact, and incentive alignment, plus concrete change management actions.

Portfolio Prioritization agent takes the four scores above across multiple use cases and reasons about sequencing, not re-scoring, labeling each use case a Quick Win, Strategic Bet, Long Term Play, or Reconsider.

Executive Summary agent reads all four completed assessments for a single use case and writes the board level call, a clear Fund, Fund with Conditions, Delay, or Do Not Fund recommendation, a one sentence headline, a short briefing paragraph, and the key tension a board member actually needs to weigh.

## Data flow

Input is a plain text use case description, optionally paired with portfolio context pulled from the synthetic dataset, sector, domain, estimated cost, data sensitivity, regulatory exposure, and current process maturity. Each agent receives the same description and context, reasons independently, and returns its own structured JSON. The orchestrator collects Value, Risk, Architecture, and Adoption results, then passes all four into the Executive Summary agent for synthesis.

## Prompt design

Every agent prompt follows the same structure, a role definition that anchors the agent as a senior domain specialist rather than a generic assistant, an explicit input contract, a strict output JSON schema with no markdown or commentary allowed outside it, and numeric scoring bands with concrete criteria for each band, so scores are reproducible rather than arbitrary.

## Evaluation framework

The system was tested against three use cases spanning two sectors before being called complete, UC-001, indirect spend procurement in BFSI, UC-002, automated KYC document verification in BFSI, and UC-004, ambient clinical documentation in Healthcare.

Results confirmed the agents differentiate correctly rather than returning similar scores regardless of input. UC-002 scored substantially higher on risk than UC-001, 70 versus 42, consistent with its High data sensitivity and direct AML and KYC regulatory exposure against UC-001's Medium sensitivity internal procurement data. UC-004 scored highest of all three on both risk and complexity, 85 and 85, consistent with a use case touching live clinical conversations, HIPAA exposure, and EHR integration, territory meaningfully different from either BFSI use case. In each case, the Executive Summary agent's briefing paragraph correctly named the specific regulatory and operational concerns relevant to that use case rather than generic language, and correctly identified different stakeholder groups affected, procurement and finance for UC-001, compliance and operations for UC-002, clinical staff for UC-004.

This cross domain differentiation, rather than any single score in isolation, is the strongest evidence the system reasons about each use case on its own terms.

## Sample inputs and outputs

See the samples folder. UC-001, an indirect spend procurement use case, is used as the running example throughout this repository and was the first use case every agent was individually tested against during the build. sample_input_UC-001.json shows the raw input, sample_output_UC-001.json shows the Value agent output alone, and sample_output_UC-001_combined.json shows Value, Risk, and Architecture together as an early orchestrator run produced them, before the Adoption and Executive Summary agents were added.

## Lessons learned

Groq's Llama 3.3 70B, run through an OpenAI compatible endpoint, proved a reliable and genuinely free substitute for OpenAI's API during development, worth knowing for anyone building a portfolio project without a billing budget, since OpenAI's API requires a funded account with no meaningful free tier at the time of this build.

The Adoption agent surfaced a pattern worth naming explicitly, high value and technically feasible use cases do not automatically score well on adoption readiness, UC-004's strong value and architecture scores came with only Medium adoption confidence, driven specifically by clinical workforce concerns rather than anything technical. This is precisely the kind of tension a single technical evaluation would miss, and precisely why the system evaluates adoption as an independent dimension rather than folding it into risk.

## Deployment guide

Clone the repository, create a virtual environment, install the packages listed in requirements.txt, set a GROQ_API_KEY environment variable, either exported directly or through a local .env file, then run `python src/orchestrator.py` from the project root to see a combined four agent assessment for the sample procurement use case, or run `streamlit run src/app.py` for the full interactive dashboard.

## Source code

All agent logic lives in src. agents.py holds the Value agent, risk_agent.py holds the Risk and Governance agent, architecture_agent.py holds the Architecture agent, adoption_agent.py holds the Change Management and Adoption agent, portfolio_agent.py holds the Portfolio Prioritization agent, executive_summary_agent.py holds the Executive Summary agent, orchestrator.py wires the first four together using LangGraph, and app.py is the Streamlit frontend. data holds the synthetic BFSI and Healthcare use case portfolio. samples holds real input and output pairs for demonstration.
