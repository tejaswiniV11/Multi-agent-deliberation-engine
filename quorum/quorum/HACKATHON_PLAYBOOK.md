# Quorum Hackathon Playbook

## 90-second pitch

Quorum turns high-stakes decisions into an auditable multi-agent council. A
Moderator frames the choice, specialist advisors argue from different lenses,
a Researcher gathers evidence, coded tools check bias and compute the decision
matrix, and a Synthesizer returns a verdict with confidence instead of a vague
answer. Users can tune criteria weights before convening.

## What to show judges

1. Start with the UI and run demo mode.
2. Use a decision with real constraints:
   `Should we launch an AI support copilot to all customers next month?`
3. Add context:
   `Budget is tight, support backlog is rising, privacy risk matters, and we can pilot with 10% of users.`
4. Expand "Tune criteria weights" and adjust Risk to 5 (max) to show customisation.
5. Narrate the council seats as they light up.
6. Pause on the Researcher turn — point out the WebSearch coded tool chip.
7. Pause on the final verdict and point at:
   - weighted ranking,
   - confidence gauge,
   - bias flags,
   - advisor ledger.
8. Open `coded_tools/quorum/decision_matrix.py` and show that the verdict math is deterministic.
9. Open `coded_tools/quorum/web_search.py` and show the evidence retrieval tool.
10. Open `registries/quorum.hocon` and show the neuro-san agent network.

## Judge questions

**What is novel?**
It combines adversarial multi-agent debate with evidence-grounded research and
deterministic coded tools, so the final recommendation is explainable and
reproducible.

**Why not just ask one LLM?**
One LLM can collapse into a single framing. Quorum separates lenses, records
positions, gathers evidence, scans for bias, and computes the verdict with
transparent weights the user can tune.

**Can it run without keys?**
Yes. Demo mode is fully offline and uses the same coded tools. Live mode
connects to neuro-san and a real model when API keys are available.

**Where is neuro-san used?**
`registries/quorum.hocon` defines the multi-agent network, advisor tools, coded
tools (DecisionMatrix, BiasCheck, ArgumentLedger, WebSearch), and shared
`sly_data` ledger pattern.

**What are the four coded tools?**
1. `DecisionMatrix` — weighted scoring + confidence computation.
2. `BiasCheck` — rule-based cognitive bias detection.
3. `ArgumentLedger` — structured position tracking via sly_data.
4. `WebSearch` — evidence retrieval for the Researcher agent.

## Backup plan

If live mode has any API or network issue, keep `BACKEND_MODE=demo`. The demo is
designed for judging reliability and still demonstrates the architecture.
