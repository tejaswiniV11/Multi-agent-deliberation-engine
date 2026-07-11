# Project Summary — Quorum

**Team:** AutoMinds (2 members)
**Built with:** neuro-san (Cognizant Neuro® AI Multi-Agent Accelerator)

---

## The problem

Important decisions fail in a predictable way: one perspective dominates. A team
migrates to microservices because the loudest engineer is excited; a company
takes funding because the upside felt obvious and no one costed the downside.
Humans know the fix — get advocates, skeptics, domain experts, and an ethical
check into one room and force a structured trade-off — but that "room" is
expensive to convene and rarely happens for day-to-day calls.

## What Quorum does

Quorum is a **multi-agent deliberation engine**. You give it a decision in plain
language — *"Should we adopt a four-day work week?"* — and a council of
specialised AI agents deliberates it in front of you:

- an **Advocate** makes the strongest good-faith case *for*,
- a **Skeptic** makes the case *against* and runs the debate through a
  cognitive-bias scanner,
- a **Researcher** gathers evidence from web searches to ground the analysis in
  facts,
- a **Domain Analyst** provides feasibility analysis using the Researcher's
  findings and proposes scoring criteria,
- an **Ethicist** surfaces human and long-horizon consequences,
- a **Moderator** chairs and delegates, and
- a **Synthesizer** weighs every position with a transparent decision matrix and
  returns a verdict **plus a confidence figure**.

You can **tune the criteria weights** (Impact, Cost, Risk, Reversibility) before
convening, so the council weights what matters most to you.

You watch the council seats light up as each advisor speaks, read the debate as
it streams, and end with an auditable recommendation — not a black-box answer.

## Why it's novel

Most agent demos are *pipelines* (fetch → summarise → reply) or single
assistants with tools. Quorum is **adversarial-collaborative**: agents are
deliberately given *opposing* mandates so the system explores a genuine range of
views before converging. The convergence itself is not left to an LLM's vibe —
it is handed to a deterministic `DecisionMatrix` coded tool, so the final score
and confidence are reproducible and explainable. Pairing an LLM debate with a
code-computed verdict is the core idea: **let the agents reason, let the code
decide the arithmetic.** The result is decision *intelligence* you could defend
in a review, applicable to any domain (engineering, business, policy, personal)
without changing a line of code.

## How it uses neuro-san

The reasoning layer is entirely a neuro-san agent network (`registries/quorum.hocon`):

- **Hierarchical AAOSA delegation** — a Moderator front-man decomposes the
  request and calls each advisor as a down-chain agent (agents-as-tools).
- **Four coded tools** — `DecisionMatrix` (weighted scoring + confidence),
  `BiasCheck` (rule-based bias scan), `ArgumentLedger` (shared state), and
  `WebSearch` (evidence retrieval for the Researcher).
- **`sly_data`** — the ledger persists positions across agent turns without
  bloating every prompt.
- **Tool chaining** — the Skeptic invokes `BiasCheck`; the DomainAnalyst's
  Researcher invokes `WebSearch`; the Synthesizer invokes `DecisionMatrix`
  mid-reasoning.

The network drops straight into neuro-san-studio. On top of it we built a
FastAPI backend (with real request-id / timing / logging middleware) that
streams the deliberation over Server-Sent Events, and a hand-crafted
"deliberation-chamber" web UI with custom criteria weight controls. A fully
offline **demo mode** runs the same choreography and the same real coded tools
with no API key, so the project is demonstrable on any laptop.

## Results

- End-to-end deliberation on arbitrary decisions, streamed live turn-by-turn.
- Reproducible, explainable verdicts: the confidence number comes from code, and
  the bias flags cite the exact triggering language.
- Evidence-grounded analysis: the Researcher provides research findings that
  inform the DomainAnalyst's assessment.
- User-controlled criteria weights give stakeholders agency over what matters.
- Clean separation of concerns — agent network, coded tools, backend, frontend —
  each independently testable.

## What's next

- Wire the WebSearch coded tool to a real search API (Tavily, Serper) for
  live-mode evidence grounding.
- Add user-defined criteria (not just weights) so the council adapts to any
  decision framework.
- Persist past deliberations so teams can revisit the reasoning behind a call.
- Add a "Contrarian" mode that deliberately maximises disagreement before
  synthesis.

Quorum is small on purpose: one sharp idea — *structured, multi-lens
deliberation with a code-computed verdict* — executed cleanly on neuro-san.
