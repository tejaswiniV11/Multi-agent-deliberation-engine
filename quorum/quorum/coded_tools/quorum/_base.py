"""Compatibility shim for the neuro-san ``CodedTool`` base class.

neuro-san discovers a coded tool by the ``class`` field in the HOCON network
and expects it to implement the ``CodedTool`` interface (an ``invoke`` method,
and optionally ``async_invoke``). When neuro-san is installed we subclass the
real interface so the framework's type checks pass. When it is not installed
(e.g. running the offline demo backend on a fresh laptop) we fall back to a
tiny stand-in with the same shape so imports never explode.

VERIFY-AGAINST-REPO #1
----------------------
The import path below (``neuro_san.interfaces.coded_tool.CodedTool``) matches
the public neuro-san API. If the hackathon branch pins a different path,
update the single line inside the ``try`` block and nothing else changes.
"""

from __future__ import annotations

from typing import Any, Dict

try:  # pragma: no cover - depends on environment
    from neuro_san.interfaces.coded_tool import CodedTool as _CodedTool

    CODED_TOOL_AVAILABLE = True
except Exception:  # noqa: BLE001 - any import failure means "run standalone"
    CODED_TOOL_AVAILABLE = False

    class _CodedTool:  # type: ignore[no-redef]
        """Minimal stand-in matching the neuro-san CodedTool contract."""

        def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Any:
            raise NotImplementedError


class QuorumTool(_CodedTool):
    """Shared base for every Quorum coded tool.

    Sub-classes implement ``invoke(args, sly_data)`` and return a JSON-safe
    value (str / dict / list). neuro-san serialises whatever is returned back
    into the calling agent's context.
    """

    #: Human-friendly name used in logs and the demo backend.
    tool_name: str = "quorum_tool"

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Any:  # noqa: D401
        raise NotImplementedError
