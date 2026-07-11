"""WebSearch coded tool.

Provides grounded evidence for the Researcher agent. In standalone / demo mode
it returns contextually-relevant **synthetic** results derived from keyword
analysis of the query — no network calls, no API key. When a real search
backend is wired up (e.g. Tavily, Serper, SerpAPI), swap the ``_search``
implementation without changing the interface.

Input (``args``)::

    {"query": "AI triage pilot patient safety"}

Output::

    {
      "results": [
          {"title": "...", "snippet": "...", "url": "https://..."},
          ...
      ],
      "summary": "Found 3 results relevant to AI triage pilot."
    }
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

from coded_tools.quorum._base import QuorumTool

# ---------------------------------------------------------------------------
#  Synthetic result bank — keyed by topic keywords so the demo returns
#  contextually plausible results rather than identical boilerplate.
# ---------------------------------------------------------------------------
_TOPIC_RESULTS: Dict[str, List[Dict[str, str]]] = {
    "ai": [
        {
            "title": "McKinsey: The state of AI in 2024 — adoption and impact",
            "snippet": "65% of organisations now regularly use generative AI, "
                       "nearly double the share from ten months ago. Early "
                       "adopters report measurable revenue gains.",
            "url": "https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai",
        },
        {
            "title": "IEEE Spectrum: When AI goes wrong — lessons from deployment failures",
            "snippet": "Rushed AI rollouts share common failure patterns: "
                       "inadequate testing on edge cases, brittle data pipelines, "
                       "and over-reliance on accuracy metrics that hide fairness gaps.",
            "url": "https://spectrum.ieee.org/ai-failures",
        },
    ],
    "healthcare": [
        {
            "title": "WHO guideline on AI for health — 2024 update",
            "snippet": "AI health tools must satisfy six guiding principles: "
                       "transparency, safety, human autonomy, equity, "
                       "sustainability, and accountability.",
            "url": "https://www.who.int/publications/i/item/9789240029200",
        },
        {
            "title": "JAMA: AI-assisted triage in emergency departments — a systematic review",
            "snippet": "Across 14 studies, AI triage systems reduced median "
                       "wait-to-treatment by 18% while maintaining ≥94% "
                       "sensitivity for high-acuity cases.",
            "url": "https://jamanetwork.com/journals/jama/fullarticle/ai-triage-review",
        },
    ],
    "cost": [
        {
            "title": "Harvard Business Review: The hidden costs of technology adoption",
            "snippet": "Organisations consistently under-estimate integration, "
                       "training, and change-management costs by 40-60%. "
                       "A phased rollout reduces budget overruns significantly.",
            "url": "https://hbr.org/2024/03/hidden-costs-tech-adoption",
        },
    ],
    "migration": [
        {
            "title": "Martin Fowler: Monolith to microservices — patterns and pitfalls",
            "snippet": "Start with the Strangler Fig pattern: incrementally "
                       "extract services while keeping the monolith running. "
                       "Big-bang rewrites fail 70% of the time.",
            "url": "https://martinfowler.com/articles/break-monolith-into-microservices.html",
        },
        {
            "title": "InfoQ: Lessons from 200 microservice migrations",
            "snippet": "The top predictor of success is team autonomy, not "
                       "tooling. Companies that reorganised teams around services "
                       "before migrating code were 3× more likely to succeed.",
            "url": "https://www.infoq.com/articles/microservice-migration-lessons",
        },
    ],
    "ethics": [
        {
            "title": "Stanford HAI: Ethical considerations for workplace AI",
            "snippet": "Workplace AI should be opt-in where possible, "
                       "transparent about what data it uses, and subject to "
                       "regular third-party audits.",
            "url": "https://hai.stanford.edu/policy/ethical-workplace-ai",
        },
    ],
    "work": [
        {
            "title": "4 Day Week Global: Results from the world's largest trial",
            "snippet": "92% of participating companies continued the four-day "
                       "week after the trial. Revenue stayed flat or increased; "
                       "burnout dropped 71%.",
            "url": "https://www.4dayweek.com/research",
        },
        {
            "title": "Gallup: Employee engagement and schedule flexibility",
            "snippet": "Flexible scheduling is now the #1 factor in job "
                       "satisfaction, ahead of pay for knowledge workers.",
            "url": "https://www.gallup.com/workplace/flexible-scheduling-engagement",
        },
    ],
    "startup": [
        {
            "title": "a]6z: When to raise — signals that funding timing matters",
            "snippet": "Raising too early dilutes founders; raising too late "
                       "risks missing the market window. The sweet spot is when "
                       "unit economics are proven but growth is capital-constrained.",
            "url": "https://a16z.com/when-to-raise",
        },
    ],
    "default": [
        {
            "title": "Harvard Business Review: How to make better decisions",
            "snippet": "Structured decision processes outperform intuition by "
                       "up to 25%. The key elements are: multiple perspectives, "
                       "explicit criteria, and a transparent weighting method.",
            "url": "https://hbr.org/2023/11/how-to-make-better-decisions",
        },
        {
            "title": "Decision Science: The value of adversarial deliberation",
            "snippet": "Teams that assign a formal devil's advocate produce "
                       "decisions rated 18% higher in quality by independent "
                       "reviewers, primarily by surfacing hidden risks.",
            "url": "https://doi.org/10.1016/j.jdm.2024.01.004",
        },
    ],
}

# Mapping from keyword to topic key for matching.
_KEYWORD_MAP: Dict[str, str] = {
    "ai": "ai", "artificial intelligence": "ai", "machine learning": "ai",
    "ml": "ai", "llm": "ai", "model": "ai", "automat": "ai",
    "health": "healthcare", "patient": "healthcare", "medical": "healthcare",
    "hospital": "healthcare", "triage": "healthcare", "clinical": "healthcare",
    "cost": "cost", "budget": "cost", "expensive": "cost", "price": "cost",
    "invest": "cost", "funding": "startup", "venture": "startup",
    "startup": "startup", "bootstrap": "startup",
    "migrat": "migration", "microservice": "migration", "monolith": "migration",
    "ethic": "ethics", "fairness": "ethics", "bias": "ethics", "privacy": "ethics",
    "work week": "work", "four-day": "work", "remote": "work",
    "schedule": "work", "employee": "work",
}


class WebSearch(QuorumTool):
    """Deterministic web-search stand-in for the Researcher agent."""

    tool_name = "web_search"

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Dict[str, Any]:
        query: str = (args.get("query") or "").strip()
        if not query:
            return {"results": [], "summary": "No query provided."}

        results = self._search(query)
        summary = (
            f"Found {len(results)} result(s) relevant to: {query[:80]}"
            if results
            else "No relevant results found."
        )
        return {"results": results, "summary": summary}

    # ------------------------------------------------------------------
    #  Private helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _search(query: str) -> List[Dict[str, str]]:
        """Match query keywords to the synthetic result bank."""
        lowered = query.lower()
        matched_topics: set[str] = set()

        for keyword, topic in _KEYWORD_MAP.items():
            if keyword in lowered:
                matched_topics.add(topic)

        # Collect results from matched topics (de-dup by URL).
        seen_urls: set[str] = set()
        results: List[Dict[str, str]] = []
        for topic in matched_topics:
            for item in _TOPIC_RESULTS.get(topic, []):
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    results.append(item)

        # Always include at least the default results if nothing matched.
        if not results:
            results = list(_TOPIC_RESULTS["default"])

        # Cap at 4 results for readability.
        return results[:4]
