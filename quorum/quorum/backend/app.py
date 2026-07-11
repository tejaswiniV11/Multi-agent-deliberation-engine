"""Quorum backend application.

Exposes:
  GET  /                       -> the deliberation-chamber UI
  GET  /api/health             -> config + readiness snapshot
  POST /api/deliberate/stream  -> Server-Sent Events stream of the debate

The SSE stream is the interesting part: each council turn, tool call, and the
final verdict arrive as their own event, so the browser can reveal the debate
live rather than waiting for one big blob of text.
"""

from __future__ import annotations

import json
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from backend.config import settings
from backend.middleware import RequestContextMiddleware
from backend.neuro_san_client import deliberate
from backend.schemas import DeliberateRequest, HealthResponse

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger("quorum")

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")

app = FastAPI(title="Quorum", description="Multi-agent deliberation engine", version="1.0.0")

# --- middleware stack (order matters: CORS outermost, then our context) ---
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        mode=settings.backend_mode,
        agent_network=settings.agent_network,
        llm_model=settings.llm_model,
        llm_key_configured=settings.has_llm_key,
        neuro_san_target=f"{settings.neuro_san_host}:{settings.neuro_san_port}",
    )


@app.post("/api/deliberate/stream")
async def deliberate_stream(req: DeliberateRequest) -> StreamingResponse:
    """Stream the council's deliberation as Server-Sent Events."""

    async def event_source():
        try:
            async for evt in deliberate(req.decision, req.context, req.weights):
                yield f"data: {json.dumps(evt)}\n\n"
        except Exception as exc:  # noqa: BLE001
            logger.exception("deliberation failed")
            err = {"kind": "error", "text": f"Deliberation failed: {exc}"}
            yield f"data: {json.dumps(err)}\n\n"

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- frontend (mounted last so /api/* wins) ---
@app.get("/")
async def index() -> FileResponse:
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


app.mount("/", StaticFiles(directory=FRONTEND_DIR), name="static")
