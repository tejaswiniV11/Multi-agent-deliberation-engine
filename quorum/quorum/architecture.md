# Architecture — Quorum

Quorum turns a hard decision into a **structured, multi-perspective deliberation**.
A user poses a dilemma; a council of specialised agents argues it from multiple
distinct lenses; a Synthesizer weighs every position with a deterministic
decision matrix and returns a verdict with a calibrated confidence figure.

The entire "thinking" layer is a **neuro-san agent network** — that is where the
project's intelligence lives and how it earns the neuro-san-feature marks.

---

## 1. The agentic system (neuro-san)

The network is defined declaratively in [`registries/quorum.hocon`](registries/quorum.hocon)
and follows neuro-san's **AAOSA** pattern: a front-man agent that decomposes a
request and delegates to down-chain agents, treating each sub-agent as a callable
tool.

```
                          ┌──────────────┐
              user  ─────▶ │  MODERATOR   │  (front-man / entry agent)
                          └──────┬───────┘
        delegates (agents-as-tools) │ frames the decision, fans out
        ┌───────────────┬──────────┼───────────────┬────────────────┐
        ▼               ▼          ▼                ▼                ▼
   ┌─────────┐    ┌─────────┐ ┌──────────────┐ ┌──────────┐   ┌───────────────┐
   │Advocate │    │ Skeptic │ │ DomainAnalyst│ │ Ethicist │   │  SYNTHESIZER  │
   │  (for)  │    │(against)│ │  (facts)     │ │ (values) │   │  (verdict)    │
   └─────────┘    └────┬────┘ └──────┬───────┘ └──────────┘   └──────┬────────┘
                       │ calls       │ calls                          │ calls
                       ▼             ▼                                ▼
                 ┌───────────┐ ┌────────────┐              ┌──────────────────┐
                 │ BiasCheck │ │ Researcher │              │  DecisionMatrix  │ (coded tool)
                 └───────────┘ └─────┬──────┘              └──────────────────┘
                       ▲             │ calls                         ▲
                       │             ▼                               │
                       │       ┌───────────┐                         │
                       │       │ WebSearch │  (coded tool)           │
                       │       └───────────┘                         │
                       └──────────  ArgumentLedger (sly_data)  ──────┘
```

### neuro-san features used

| Feature | Where | Why it matters |
|---|---|---|
| **Hierarchical delegation (AAOSA)** | Moderator → advisors → Synthesizer | A real orchestration tree, not a single prompt. |
| **Agents-as-tools** | Advisors are `tools` of the Moderator | Each lens is independently promptable and reusable. |
| **Coded tools** | `DecisionMatrix`, `BiasCheck`, `ArgumentLedger`, `WebSearch` | Deterministic Python does the arithmetic and auditing the LLM shouldn't. |
| **`sly_data` shared state** | `ArgumentLedger` | Positions persist across turns without polluting every prompt. |
| **Tool chaining** | Skeptic→BiasCheck, DomainAnalyst→Researcher→WebSearch, Synthesizer→DecisionMatrix | Agents compose code tools mid-reasoning. |

### The coded tools ([`coded_tools/quorum/`](coded_tools/quorum))

- **`DecisionMatrix`** — weighted multi-criteria scoring. Given options, criteria,
  integer weights, and 0–10 scores, it returns a ranking, a winner, and a
  **confidence** derived from the normalised gap between the top two options. The
  Synthesizer *delegates the maths to code* rather than hallucinating a number.
- **`BiasCheck`** — an explainable, rule-based scan for cognitive-bias markers
  (anchoring, sunk-cost, overconfidence, groupthink, …). Fast, free, auditable.
- **`ArgumentLedger`** — reads/writes the council's positions into `sly_data` so
  the Synthesizer can review the whole debate and the UI can render a clean
  positions panel.
- **`WebSearch`** — keyword-aware evidence retrieval. Provides grounded research
  findings to the Researcher agent, who feeds evidence to the DomainAnalyst.
  In demo mode returns contextually-relevant synthetic results; in live mode can
  be extended to call a real search API.

---

## 2. The application layer (novel wrapper)

neuro-san is the brain; Quorum wraps it in a product.

```
 browser  ──HTTP/SSE──▶  FastAPI backend  ──▶  neuro-san network
 (frontend/)             (backend/)            (registries/ + coded_tools/)
```

**Backend — `backend/`** (FastAPI)
- `app.py` — routes: `/api/health`, `/api/deliberate/stream` (Server-Sent Events).
- `middleware.py` — hand-rolled middleware adding a request-id, server-timing
  header, and structured access logs to every request.
- `neuro_san_client.py` — the bridge. In `live` mode it streams a real neuro-san
  session; in `demo` mode it runs an offline choreography that **still calls the
  real coded tools**, so nothing in the demo is faked.
- `config.py` / `schemas.py` — env-driven settings and typed payloads. The API
  accepts optional `weights` for custom criteria weighting.

**Frontend — `frontend/`** (zero-build HTML/CSS/JS)
- A **deliberation-chamber** UI: seven council seats arranged in a semicircle that
  glow as each advisor speaks, a live colour-coded transcript, and an animated
  **confidence gauge** that fills from the DecisionMatrix result. The verdict
  panel renders the weighted ranking as bars and the bias flags as chips.
- **Custom criteria weights** — a collapsible "Tune criteria weights" panel with
  sliders for Impact, Cost, Risk, and Reversibility lets the user influence the
  decision matrix before convening the council.

**Streaming.** The backend emits one SSE event per council turn / tool call /
verdict, so the browser reveals the debate live — which is also what makes the
five-minute demo compelling.

---

## 3. Data & safety

No client or proprietary data is used. Deliberation inputs are the user's own
free-text questions; the sample prompts and all demo content are synthetic.
