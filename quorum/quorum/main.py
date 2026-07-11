#!/usr/bin/env python3
"""Quorum \u2014 single entry point.

Launches the FastAPI backend (which also serves the frontend). Run:

    python main.py

Then open the URL printed in the terminal.

Modes are controlled by BACKEND_MODE in your .env file:
    demo  (default)  fully offline; great for building the UI and the demo video
    live             connects to a running neuro-san server (real LLM agents)

See README.md for how to start the neuro-san server for live mode.
"""

from __future__ import annotations

import socket

from backend.config import settings


def _port_is_available(host: str, port: int) -> bool:
    bind_host = "" if host in {"0.0.0.0", "::"} else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((bind_host, port))
        except OSError:
            return False
    return True


def _resolve_port(host: str, preferred_port: int) -> int:
    port = preferred_port
    while not _port_is_available(host, port):
        port += 1
    return port


def main() -> None:
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        if exc.name == "uvicorn":
            print("Missing dependency: uvicorn")
            print("Run: python -m pip install -r requirements.txt")
            raise SystemExit(1) from exc
        raise

    app_port = _resolve_port(settings.app_host, settings.app_port)
    print("=" * 64)
    print("  QUORUM  \u2014  multi-agent deliberation engine")
    print(f"  mode        : {settings.backend_mode}")
    print(f"  agent net   : {settings.agent_network}")
    print(f"  llm model   : {settings.llm_model}")
    print(f"  llm key set : {settings.has_llm_key}")
    if app_port != settings.app_port:
        print(f"  port        : {settings.app_port} busy, using {app_port}")
    print(f"  listening   : http://{settings.app_host}:{app_port}")
    print("=" * 64)
    uvicorn.run(
        "backend.app:app",
        host=settings.app_host,
        port=app_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
