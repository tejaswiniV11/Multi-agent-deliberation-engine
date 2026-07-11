"""BiasCheck coded tool.

A lightweight, explainable cognitive-bias scanner. The Skeptic agent runs the
council's collected arguments through it to surface reasoning traps (anchoring,
sunk-cost, confirmation, groupthink, etc.). This is intentionally rule-based
rather than another LLM call: it is fast, free, deterministic, and easy for a
judge to audit.
"""

from __future__ import annotations

from typing import Any, Dict, List

from coded_tools.quorum._base import QuorumTool

# Each bias is a name -> list of trigger phrases (lower-cased substring match).
BIAS_SIGNALS: Dict[str, List[str]] = {
    "Anchoring": ["first", "initial estimate", "starting point", "originally", "baseline of"],
    "Sunk cost": ["already invested", "come this far", "can't waste", "spent so much", "too late to"],
    "Confirmation": ["as expected", "obviously", "everyone knows", "clearly proves", "just confirms"],
    "Overconfidence": ["guaranteed", "definitely will", "no doubt", "certainly", "can't fail", "always works"],
    "Groupthink": ["we all agree", "consensus is", "nobody disagrees", "everyone is on board"],
    "Availability": ["recently saw", "just read", "last time", "reminds me of", "heard that"],
    "Optimism": ["best case", "should be fine", "worst that could happen", "smoothly", "no problem"],
    "Status quo": ["keep things as", "why change", "if it isn't broken", "the way we've always"],
}


class BiasCheck(QuorumTool):
    tool_name = "bias_check"

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        text: str = (args.get("text") or "").lower()
        if not text.strip():
            return {"flags": [], "summary": "No text supplied to scan."}

        flags: List[Dict[str, str]] = []
        for bias, signals in BIAS_SIGNALS.items():
            hit = next((s for s in signals if s in text), None)
            if hit:
                flags.append(
                    {
                        "bias": bias,
                        "trigger": hit,
                        "note": f"Language like \u201c{hit}\u201d can indicate {bias.lower()} bias.",
                    }
                )

        if flags:
            names = ", ".join(f["bias"] for f in flags)
            summary = f"{len(flags)} potential bias(es) detected: {names}."
        else:
            summary = "No obvious cognitive-bias markers detected in the arguments."

        return {"flags": flags, "summary": summary}
