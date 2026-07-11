"""DecisionMatrix coded tool.

Turns a set of options, criteria, and weights into a transparent weighted
score, a ranking, and a normalised confidence figure. This is the numerical
backbone of the Synthesizer agent's final verdict: instead of the LLM
inventing a score, it delegates the arithmetic to deterministic code.

Input (``args``)::

    {
      "options":  ["Option A", "Option B"],
      "criteria": ["Impact", "Cost", "Risk", "Effort"],
      "weights":  {"Impact": 5, "Cost": 3, "Risk": 4, "Effort": 2},
      "scores":   {                       # 0..10 per option per criterion
          "Option A": {"Impact": 9, "Cost": 4, "Risk": 6, "Effort": 5},
          "Option B": {"Impact": 6, "Cost": 8, "Risk": 8, "Effort": 7}
      }
    }

Output::

    {
      "ranking": [{"option": ..., "weighted_score": ..., "pct": ...}, ...],
      "winner": "Option A",
      "confidence": 0.63,          # separation between #1 and #2
      "matrix": {...}              # echo, for UI rendering
    }
"""

from __future__ import annotations

from typing import Any, Dict, List

from coded_tools.quorum._base import QuorumTool


class DecisionMatrix(QuorumTool):
    tool_name = "decision_matrix"

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        options: List[str] = args.get("options") or []
        criteria: List[str] = args.get("criteria") or []
        weights: Dict[str, float] = args.get("weights") or {}
        scores: Dict[str, Dict[str, float]] = args.get("scores") or {}

        if not options or not criteria:
            return {"error": "DecisionMatrix requires non-empty 'options' and 'criteria'."}

        # Default any missing weight to 1 so the tool degrades gracefully.
        weight_total = sum(float(weights.get(c, 1)) for c in criteria) or 1.0

        ranking: List[Dict[str, Any]] = []
        max_possible = 10.0 * weight_total  # every criterion scored 10/10
        for option in options:
            option_scores = scores.get(option, {})
            weighted = sum(
                float(option_scores.get(c, 0)) * float(weights.get(c, 1)) for c in criteria
            )
            pct = round(100.0 * weighted / max_possible, 1) if max_possible else 0.0
            ranking.append(
                {"option": option, "weighted_score": round(weighted, 2), "pct": pct}
            )

        ranking.sort(key=lambda r: r["weighted_score"], reverse=True)

        # Confidence = normalised gap between the top two options (0..1).
        if len(ranking) >= 2 and ranking[0]["weighted_score"] > 0:
            gap = ranking[0]["weighted_score"] - ranking[1]["weighted_score"]
            confidence = round(min(1.0, gap / ranking[0]["weighted_score"]), 2)
        else:
            confidence = 1.0 if ranking else 0.0

        return {
            "ranking": ranking,
            "winner": ranking[0]["option"] if ranking else None,
            "confidence": confidence,
            "matrix": {
                "options": options,
                "criteria": criteria,
                "weights": weights,
                "scores": scores,
            },
        }
