# Quorum — a multi-agent deliberation engine..

> Put a hard decision before a council of AI advisors. They argue it from
> multiple lenses; a Synthesizer weighs them with a transparent decision matrix
> and returns a verdict with a confidence figure.

Built on **neuro-san** for the Cognizant Neuro® AI Multi-Agent Accelerator
Hackathon by **Team AutoMinds**.

- `registries/quorum.hocon` — the neuro-san agent network (the graded core)
- `coded_tools/quorum/` — four deterministic coded tools
- `backend/` — FastAPI service + middleware that streams the debate
- `frontend/` — the deliberation-chamber web UI
- `architecture.md`, `summary.md` — design docs

---

## Quick start (demo mode — no API key)

Demo mode runs the full council choreography offline, calling the **real** coded
tools. Perfect for trying it and recording the video.

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # defaults to BACKEND_MODE=demo
python main.py
```

Open the URL printed in the terminal, usually **http://127.0.0.1:8001**. If that port is busy, Quorum automatically moves to the next free port and prints it.

---

## Live mode (real neuro-san + LLM)

This is what showcases neuro-san end-to-end. It needs the network running inside
a neuro-san-studio checkout and one LLM key.

1. **Install the agent network into neuro-san-studio**
   - Copy `registries/quorum.hocon` into the studio's `registries/` folder and
     add `"quorum.hocon": true,` to its `manifest.hocon`.
   - Copy `coded_tools/quorum/` into the studio's `coded_tools/` folder.

2. **Set your key** (Mistral is the hackathon default):
   ```bash
   export MISTRAL_API_KEY=...        # or OPENAI_API_KEY / ANTHROPIC_API_KEY
   ```
   Make sure `model_name` in `quorum.hocon` matches your provider.

3. **Start the neuro-san server** from the studio (default gRPC port `30011`).
   See the studio's `integration_quickstart.md` for the exact run command.

4. **Point Quorum at it and switch modes** in `.env`:
   ```
   BACKEND_MODE=live
   NEURO_SAN_SERVER_HOST=localhost
   NEURO_SAN_SERVER_PORT=30011
   MISTRAL_API_KEY=...
   ```
   Then `python main.py`.

> You can also drive the network purely from neuro-san-studio's own client — the
> HOCON + coded tools are self-contained. Quorum's UI is the novel wrapper on top.

---

## Features

### Multi-agent deliberation
Seven specialised agents (Moderator, Advocate, Skeptic, Researcher, Domain
Analyst, Ethicist, Synthesizer) argue from distinct lenses with tool-backed
analysis.

### Evidence-grounded research
The Researcher agent calls the **WebSearch** coded tool to find evidence before
the Domain Analyst gives its assessment. In demo mode, results are
contextually-matched synthetic data; in live mode, the tool can be extended to
use a real search API.

### Custom criteria weights
Before convening the council, expand the **"Tune criteria weights"** panel to
adjust how much Impact, Cost, Risk, and Reversibility matter. The sliders
directly influence the DecisionMatrix scoring.

### Deterministic coded tools
Four coded tools (`DecisionMatrix`, `BiasCheck`, `ArgumentLedger`, `WebSearch`)
run real Python — the verdict is computed, not guessed.

---

## ⚠️ Three spots to reconcile against your cloned repo

I built to standard neuro-san conventions, but pin these against the **hackathon
branch** you cloned (open any working sample network to compare):

1. **Coded-tool base import** — `coded_tools/quorum/_base.py`: the line
   `from neuro_san.interfaces.coded_tool import CodedTool`.
2. **Manifest** — `registries/manifest.hocon`: if the studio already ships one,
   add your line to it instead of replacing it.
3. **HOCON field shapes** — `registries/quorum.hocon`: confirm the coded-tool
   `class` path format, the top-agent instruction style, and the `llm_config`
   model key. Each is flagged inline with `VERIFY-AGAINST-REPO`.

Everything else (the agent design, the tools, the app) is version-independent.

---

## Hackathon demo path

For judging, start in demo mode first. It runs offline, uses the real coded
tools, and cannot fail because an external LLM service is slow.

1. Run `python main.py`.
2. Open the printed URL.
3. Use a decision with constraints, for example:
   `Should we launch the AI triage pilot next month?`
4. Add context:
   `Budget is tight, patient safety matters, rollback is possible, and speed matters.`
5. Optionally tune the criteria weights before convening.
6. Point out the proof points:
   - agents debate from different lenses,
   - Researcher provides evidence via WebSearch coded tool,
   - BiasCheck and DecisionMatrix are deterministic coded tools,
   - the final verdict includes confidence, ranking, bias flags, and the advisor ledger,
   - criteria weights are user-controllable.

Then switch to live mode only after the neuro-san server and API key are ready.

---

## Environment variables

See `.env.example` — every variable is documented there. The only value you must
supply for live mode is **one** LLM key (`MISTRAL_API_KEY`, `OPENAI_API_KEY`, or
`ANTHROPIC_API_KEY`). Demo mode needs no key at all.

---

## Repo layout

```
quorum/
├── main.py                     # entry point (python main.py)
├── requirements.txt
├── .env.example
├── architecture.md             # required deliverable
├── summary.md                  # required deliverable
├── registries/
│   ├── manifest.hocon
│   └── quorum.hocon            # the neuro-san agent network
├── coded_tools/quorum/
│   ├── _base.py
│   ├── decision_matrix.py
│   ├── bias_check.py
│   ├── argument_ledger.py
│   └── web_search.py           # NEW: evidence retrieval for Researcher
├── backend/
│   ├── app.py  config.py  middleware.py  neuro_san_client.py  schemas.py
└── frontend/
    ├── index.html  styles.css  app.js
```

---

## 5-minute demo video outline

1. **10s** — the problem: decisions fail when one voice dominates.
2. **30s** — show `quorum.hocon`: the Moderator delegating to advisors, the
   Researcher under DomainAnalyst, and the four coded tools. Say the words
   "AAOSA delegation, agents-as-tools, coded tools, sly_data."
3. **2m** — live run: type a decision, tune the criteria weights, narrate the
   seats lighting up, the Researcher's WebSearch results, the Skeptic's BiasCheck
   chip, and the Synthesizer's DecisionMatrix verdict + gauge.
4. **1m** — open one coded tool to show the verdict is computed, not guessed.
5. **20s** — why it's novel: adversarial-collaborative agents + evidence research
   + a code-computed verdict = auditable decision intelligence.

---

## Bonus: Cursor power-prompt (to extend the project)

Paste this into Cursor to keep building in the same style:

> You are working on **Quorum**, a neuro-san multi-agent deliberation app.
> Architecture: a HOCON agent network (`registries/quorum.hocon`) with a
> Moderator front-man delegating to Advocate/Skeptic/DomainAnalyst/Ethicist and a
> Synthesizer, plus a Researcher sub-agent under DomainAnalyst with WebSearch.
> Four Python coded tools in `coded_tools/quorum/`
> (DecisionMatrix, BiasCheck, ArgumentLedger, WebSearch). A FastAPI backend
> (`backend/`) streams the deliberation over SSE to a zero-build frontend
> (`frontend/`) with a deliberation-chamber UI and criteria weight sliders.
> There is a `live` mode (real neuro-san) and an offline `demo` mode that calls
> the real coded tools.
>
> Follow these rules: keep coded tools deterministic, pure-Python, and importable
> by both neuro-san and the demo backend; keep the SSE event shape
> `{kind, role, text, payload}` stable; match the existing frontend palette
> (dark chamber + per-agent jewel accents); add type hints and docstrings; never
> add browser localStorage.
