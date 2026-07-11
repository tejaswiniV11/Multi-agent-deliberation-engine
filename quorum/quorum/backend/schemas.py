"""Pydantic models describing the API's request and event payloads."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DeliberateRequest(BaseModel):
    """A decision to put before the Quorum council."""

    decision: str = Field(..., min_length=3, description="The decision or dilemma.")
    context: Optional[str] = Field(
        None, description="Optional extra context, constraints, or goals."
    )
    weights: Optional[Dict[str, int]] = Field(
        None, description="Optional criteria weights (e.g. {Impact: 5, Cost: 3})."
    )


class DeliberationEvent(BaseModel):
    """A single streamed event (one per SSE `data:` line).

    ``kind`` drives how the frontend renders it:
      * ``status``  \u2013 lifecycle marker (started / finished)
      * ``turn``    \u2013 an advisor spoke (has role + text)
      * ``tool``    \u2013 a coded tool ran (has role + payload)
      * ``verdict`` \u2013 the final decision matrix result
      * ``error``   \u2013 something went wrong (has text)
    """

    kind: str
    role: Optional[str] = None
    text: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str
    mode: str
    agent_network: str
    llm_model: str
    llm_key_configured: bool
    neuro_san_target: str
