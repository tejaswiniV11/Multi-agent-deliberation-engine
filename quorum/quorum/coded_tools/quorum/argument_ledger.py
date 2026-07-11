"""ArgumentLedger coded tool.

Demonstrates neuro-san's ``sly_data`` \u2014 a private key/value bag that travels
with a session but is NOT dumped into every LLM prompt. Each advisor agent
appends its position here; the Synthesizer reads the whole ledger back to draft
the verdict. This keeps the running transcript structured and lets us render a
clean "positions" panel in the UI.

Actions (``args["action"]``):
    * ``add``  \u2013 append an entry ``{"role": ..., "stance": ..., "point": ...}``
    * ``list`` \u2013 return every entry recorded so far
"""

from __future__ import annotations

from typing import Any, Dict, List

from coded_tools.quorum._base import QuorumTool

LEDGER_KEY = "quorum_ledger"


class ArgumentLedger(QuorumTool):
    tool_name = "argument_ledger"

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        action = (args.get("action") or "list").lower()
        ledger: List[Dict[str, str]] = sly_data.setdefault(LEDGER_KEY, [])

        if action == "add":
            entry = {
                "role": args.get("role", "unknown"),
                "stance": args.get("stance", "neutral"),
                "point": args.get("point", ""),
            }
            ledger.append(entry)
            return {"status": "recorded", "count": len(ledger), "entry": entry}

        # default: list
        return {"count": len(ledger), "entries": ledger}
