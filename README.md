# Enterprise AI Adoption Advisor

A multi agent system that evaluates proposed AI use cases for BFSI and Healthcare organizations across business value, risk and governance, technical architecture, organizational adoption readiness, and portfolio priority, then produces a board level executive briefing.

Built by Vikas Sharma, Senior AI and Digital Transformation Advisor.

## Status

This repository is under active build. Value, Risk and Governance, and Architecture agents are complete and wired into a working orchestrator. Adoption, Portfolio Prioritization, and Executive Summary agents are in progress. This README will expand as each phase lands.

## Problem statement

Organizations across BFSI and Healthcare now have more AI use case ideas than they have capacity to evaluate. The gap is not idea generation, it is disciplined assessment. Most organizations lack a repeatable way to compare a fraud detection use case against a clinical documentation use case on equal footing, across value, risk, feasibility, and organizational readiness, and to turn that comparison into a defensible roadmap a board can act on.

This system addresses that gap directly. Feed it a single use case description, or a portfolio of them, and it returns a structured assessment covering the dimensions that actually determine whether an AI initiative succeeds after approval, not just whether it sounds promising in a slide.

## Business context

The assessment logic here reflects patterns seen across twenty five years of enterprise AI and digital transformation advisory work in BFSI, Healthcare, Telecom, and Public Sector settings. The agents are calibrated with a synthetic but realistic portfolio of BFSI and Healthcare use cases, covering procurement, KYC, claims fraud, clinical documentation, prior authorization, and lending, so the scoring reflects real regulatory and operational texture rather than generic assumptions.

## Architecture

A single use case input flows through an orchestrator built on LangGraph. The orchestrator currently routes the input sequentially through the Value agent, the Risk and Governance agent, and the Architecture agent. The Adoption agent, Portfolio Prioritization agent, and Executive Summary agent are being added in the next build phase, after which the orchestrator will produce one combined assessment covering all five agents plus a board level briefing.

```
Use case input
      |
      v
 Orchestrator (LangGraph)
      |
      v
 Value agent -> Risk and Governance agent -> Architecture agent
      |
      v
 [in progress] Adoption agent -> Portfolio Prioritization agent
      |
      v
 [in progress] Executive Summary agent
      |
      v
 Output: value score, risk score, complexity score, adoption score,
 ranked portfolio position, executive briefing
```

## Agent design

Each agent is a focused LLM call with a strict JSON output schema, not a general purpose chatbot wrapped in a persona. This keeps outputs composable, so the orchestrator and the eventual Streamlit dashboard can render structured scores rather than parsing free text.

Value agent evaluates expected business impact, returning a value score, tier, estimated annual value range, and the specific drivers behind the number.

Risk and Governance agent evaluates compliance, security, privacy, and operational risk, returning a risk score, a breakdown across those four categories, and required mitigations.

Architecture agent evaluates integration complexity and technical feasibility, returning a complexity score, integration challenges, a recommended architecture pattern, and a build versus buy recommendation.

Each agent is scored independently, then read together, since a high value use case with high risk and high complexity tells a very different story than a high value use case that is low risk and quick to pilot.

## Data flow

Input is a plain text use case description, optionally paired with portfolio context pulled from the synthetic dataset, sector, domain, estimated cost, data sensitivity, regulatory exposure, and current process maturity. Each agent receives the same description and context, reasons independently, and returns its own structured JSON. The orchestrator collects these into one combined result per use case.

## Prompt design

Every agent prompt follows the same structure, a role definition that anchors the agent as a senior domain specialist rather than a generic assistant, an explicit input contract, a strict output JSON schema with no markdown or commentary allowed outside it, and numeric scoring bands with concrete criteria for each band, so scores are reproducible rather than arbitrary.

## Evaluation framework

In progress. This section will document how agent outputs are checked for consistency across repeated runs on the same input, and how scores compare against the anonymized real world benchmarks the scoring bands were calibrated against.

## Sample inputs and outputs

See the samples folder. UC 001, an indirect spend procurement use case, is used as the running example throughout this repository. sample_input_UC-001.json shows the raw input, sample_output_UC-001.json shows the Value agent output alone, and sample_output_UC-001_combined.json shows Value, Risk, and Architecture together as the orchestrator currently produces them.

## Lessons learned

In progress. Will be filled out once the full five agent system has run against the entire synthetic portfolio and real patterns in agent disagreement, false confidence, and scoring drift have been observed and documented.

## Deployment guide

Clone the repository, create a virtual environment, install the packages listed in requirements.txt, set an OPENAI_API_KEY environment variable, then run `python src/orchestrator.py` from the project root to see a combined assessment for the sample procurement use case. A Streamlit frontend is planned for the next build phase to make this runnable without a terminal.

## Source code

All agent logic lives in src. agents.py holds the Value agent, risk_agent.py holds the Risk and Governance agent, architecture_agent.py holds the Architecture agent, and orchestrator.py wires them together using LangGraph. data holds the synthetic BFSI and Healthcare use case portfolio. samples holds real input and output pairs for demonstration.
