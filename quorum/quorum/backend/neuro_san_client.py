"""Bridge between the FastAPI backend and the Quorum agent network.

Two modes (chosen by ``BACKEND_MODE`` in .env):

  * ``live`` - talk to a running neuro-san server. The LLM-backed agents do the
    real work; we forward their streamed messages to the browser.

  * ``demo`` - no LLM, no network. A deterministic, decision-aware script walks
    the same council choreography and calls the REAL coded tools
    (DecisionMatrix / BiasCheck / ArgumentLedger / WebSearch). This makes the UI
    fully demoable on a laptop with zero keys, and proves the tools work.

Both modes yield the same event dicts, so the API and frontend never branch.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from backend.config import settings
from coded_tools.quorum import ArgumentLedger, BiasCheck, DecisionMatrix, WebSearch

logger = logging.getLogger("quorum.neuro_san")

# Visual identity for each council seat, mirrored in the frontend palette.
ROLES = ["Moderator", "Advocate", "Skeptic", "Researcher", "DomainAnalyst", "Ethicist", "Synthesizer"]

# Small pause between streamed events so the UI reveals the debate turn by turn.
STREAM_DELAY = 0.45


def _event(kind: str, role: str | None = None, text: str | None = None,
           payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {"kind": kind, "role": role, "text": text, "payload": payload}


# =============================================================================
#  Public entry point
# =============================================================================
async def deliberate(decision: str, context: str | None = None,
                     weights: Optional[Dict[str, int]] = None,
                     ) -> AsyncGenerator[Dict[str, Any], None]:
    """Yield deliberation events for a decision, using the configured mode."""
    question = decision.strip()
    if context:
        question = f"{question}\n\nContext: {context.strip()}"

    if settings.backend_mode == "live":
        async for evt in _deliberate_live(question):
            yield evt
    else:
        async for evt in _deliberate_demo(question, user_weights=weights):
            yield evt


# =============================================================================
#  LIVE mode  -  forward a real neuro-san session
# =============================================================================
async def _deliberate_live(question: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream from a running neuro-san server.

    VERIFY-AGAINST-REPO (live client)
    ---------------------------------
    neuro-san exposes a streaming chat API. The exact client class/method can
    differ slightly between releases, so this path is wrapped defensively: any
    import/connection problem becomes a clean 'error' event instead of a crash,
    and you can fall back to demo mode by setting BACKEND_MODE=demo.

    The reference call shape (neuro-san Python client) is:

        from neuro_san.client.agent_session_factory import AgentSessionFactory
        session = AgentSessionFactory().create_session(
            agent_name=settings.agent_network,
            hostname=settings.neuro_san_host,
            port=settings.neuro_san_port,
        )
        for message in session.streaming_chat({"user_input": question}):
            ...  # forward message.text

    Confirm the factory path + streaming method against your cloned repo's
    `integration_quickstart.md`, then map each streamed chunk to an _event(...).
    """
    yield _event("status", text="Connecting to neuro-san server...")
    try:
        # Imported lazily so demo mode never needs neuro-san installed.
        from neuro_san.client.agent_session_factory import AgentSessionFactory  # type: ignore

        factory = AgentSessionFactory()
        session = factory.create_session(
            agent_name=settings.agent_network,
            hostname=settings.neuro_san_host,
            port=settings.neuro_san_port,
        )

        yield _event("status", text="Council convened. Deliberating...")

        # streaming_chat is a (possibly sync) generator of message objects.
        chat_stream = session.streaming_chat({"user_input": question})
        for message in chat_stream:
            role = getattr(message, "origin", None) or getattr(message, "agent", None)
            text = getattr(message, "text", None) or str(message)
            if text and text.strip():
                yield _event("turn", role=str(role or "Moderator"), text=text)
                await asyncio.sleep(0)  # cooperative yield

        yield _event("status", text="finished")

    except Exception as exc:  # noqa: BLE001
        logger.exception("live mode failed")
        yield _event(
            "error",
            text=(
                f"Could not reach neuro-san in live mode ({exc}). "
                "Check the server is running and BACKEND_MODE/host/port, "
                "or set BACKEND_MODE=demo to run the offline choreography."
            ),
        )


# =============================================================================
#  DEMO mode  -  offline, deterministic, uses the real coded tools
# =============================================================================
def _derive_options(question: str) -> List[str]:
    """Pull explicit 'A vs B' options if present, else default to proceed/hold."""
    lowered = question.lower()
    for sep in (" vs ", " versus ", " or "):
        if sep in lowered:
            head = question.split("?")[0]
            if sep in head.lower():
                left, right = head.lower().split(sep, 1)
                left = left.split()[-3:]
                right = right.split()[:3]
                return [" ".join(left).strip().title() or "Option A",
                        " ".join(right).strip().title() or "Option B"]
    return ["Proceed", "Hold"]


def _demo_scores(question: str, opt_a: str, opt_b: str,
                 user_weights: Optional[Dict[str, int]] = None,
                 ) -> tuple[Dict[str, int], Dict[str, Dict[str, int]]]:
    """Create an explainable offline scorecard from the user's language."""
    text = question.lower()
    weights = {"Impact": 5, "Cost": 3, "Risk": 4, "Reversibility": 2}
    proceed = {"Impact": 8, "Cost": 5, "Risk": 6, "Reversibility": 6}
    hold = {"Impact": 4, "Cost": 8, "Risk": 5, "Reversibility": 8}

    if any(word in text for word in ("urgent", "deadline", "competitor", "first-mover", "launch")):
        proceed["Impact"] += 1
        hold["Impact"] -= 1
    if any(word in text for word in ("budget", "cash", "burn", "expensive", "cost")):
        weights["Cost"] = 5
        proceed["Cost"] -= 1
    if any(word in text for word in ("safety", "legal", "compliance", "privacy", "security", "risk")):
        weights["Risk"] = 5
        proceed["Risk"] -= 1
    if any(word in text for word in ("pilot", "trial", "reversible", "rollback", "experiment")):
        proceed["Reversibility"] += 2
        proceed["Risk"] += 1
    if any(word in text for word in ("customers", "users", "patients", "employees", "students")):
        weights["Impact"] = 5

    # Apply user-supplied weights if provided (override defaults).
    if user_weights:
        for criterion in weights:
            if criterion in user_weights:
                weights[criterion] = max(1, min(5, int(user_weights[criterion])))

    def clamp(scorecard: Dict[str, int]) -> Dict[str, int]:
        return {key: max(0, min(10, value)) for key, value in scorecard.items()}

    return weights, {opt_a: clamp(proceed), opt_b: clamp(hold)}


async def _deliberate_demo(question: str,
                           user_weights: Optional[Dict[str, int]] = None,
                           ) -> AsyncGenerator[Dict[str, Any], None]:
    ledger = ArgumentLedger()
    bias = BiasCheck()
    matrix = DecisionMatrix()
    search = WebSearch()
    sly: Dict[str, Any] = {}  # stands in for neuro-san sly_data

    options = _derive_options(question)
    opt_a, opt_b = options[0], options[1]

    yield _event("status", text="started")
    await asyncio.sleep(STREAM_DELAY)

    yield _event(
        "turn", role="Moderator",
        text=(f"The council will deliberate: \u201c{question}\u201d. "
              f"I frame the choice as {opt_a} versus {opt_b}, and will gather "
              f"positions from each advisor before requesting a weighted verdict."),
    )
    await asyncio.sleep(STREAM_DELAY)

    # --- Advocate ---
    adv_text = (
        f"There is a strong case to {opt_a.lower()}. The upside is real and the "
        f"cost of inaction compounds: momentum, learning, and first-mover "
        f"advantage all favour moving now. Objections are mostly solvable with "
        f"planning rather than reasons to stop. Advocate stance: for."
    )
    ledger.invoke({"action": "add", "role": "Advocate", "stance": "for", "point": adv_text}, sly)
    yield _event("turn", role="Advocate", text=adv_text)
    await asyncio.sleep(STREAM_DELAY)

    # --- Skeptic (+ real BiasCheck tool) ---
    skeptic_text = (
        f"Before we commit, note the failure modes. This obviously will not be "
        f"as smooth as promised, hidden costs surface late, and we may be acting "
        f"because we have already invested so much. Skeptic stance: against."
    )
    ledger.invoke({"action": "add", "role": "Skeptic", "stance": "against", "point": skeptic_text}, sly)
    yield _event("turn", role="Skeptic", text=skeptic_text)
    await asyncio.sleep(STREAM_DELAY * 0.6)
    bias_result = bias.invoke({"text": adv_text + " " + skeptic_text}, sly)
    yield _event("tool", role="Skeptic", text="BiasCheck", payload=bias_result)
    await asyncio.sleep(STREAM_DELAY)

    # --- Researcher (+ real WebSearch tool) ---
    search_query = question.split("?")[0].strip()[:80]
    search_result = search.invoke({"query": search_query}, sly)
    research_bullets = []
    for r in search_result.get("results", [])[:3]:
        research_bullets.append(f"• {r['title']}: {r['snippet']}")
    researcher_text = (
        f"I searched for evidence on this decision. Key findings:\n"
        + "\n".join(research_bullets) if research_bullets else
        "I searched for evidence but found no directly relevant results."
    )
    yield _event("turn", role="Researcher", text=researcher_text)
    await asyncio.sleep(STREAM_DELAY * 0.6)
    yield _event("tool", role="Researcher", text="WebSearch", payload=search_result)
    await asyncio.sleep(STREAM_DELAY)

    # --- Domain Analyst ---
    criteria = ["Impact", "Cost", "Risk", "Reversibility"]
    analyst_text = (
        f"On the facts: feasibility is moderate and depends on a few key "
        f"dependencies. The research findings support a measured approach. "
        f"I recommend scoring both options against {', '.join(criteria)}. "
        f"The decision is more reversible than it first appears, which lowers the "
        f"stakes of a wrong call. Analyst suggested criteria: {criteria}."
    )
    ledger.invoke({"action": "add", "role": "DomainAnalyst", "stance": "neutral", "point": analyst_text}, sly)
    yield _event("turn", role="DomainAnalyst", text=analyst_text)
    await asyncio.sleep(STREAM_DELAY)

    # --- Ethicist ---
    eth_text = (
        f"Consider who is affected and whether the change is consented to and "
        f"reversible. No red lines are crossed here, but transparency with those "
        f"impacted is a condition, not a nicety. Ethicist stance: cautious-support."
    )
    ledger.invoke({"action": "add", "role": "Ethicist", "stance": "cautious", "point": eth_text}, sly)
    yield _event("turn", role="Ethicist", text=eth_text)
    await asyncio.sleep(STREAM_DELAY)

    # --- Synthesizer (+ real DecisionMatrix tool) ---
    weights, scores = _demo_scores(question, opt_a, opt_b, user_weights)
    verdict = matrix.invoke(
        {"options": [opt_a, opt_b], "criteria": criteria, "weights": weights, "scores": scores},
        sly,
    )
    positions = ledger.invoke({"action": "list"}, sly)
    verdict["positions"] = positions["entries"]
    verdict["bias_flags"] = bias_result["flags"]

    syn_text = (
        f"Weighing every lens through the decision matrix, the recommendation is "
        f"\u201c{verdict['winner']}\u201d with a confidence of {verdict['confidence']:.0%}. "
        f"The decisive criterion is Impact; the guardrail is to keep the move "
        f"reversible and communicate with everyone affected."
    )
    yield _event("turn", role="Synthesizer", text=syn_text)
    await asyncio.sleep(STREAM_DELAY * 0.6)
    yield _event("verdict", role="Synthesizer", payload=verdict)
    await asyncio.sleep(STREAM_DELAY * 0.4)
    yield _event("status", text="finished")
