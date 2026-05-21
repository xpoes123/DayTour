"""Claude API integration.

Two surfaces:
- `prompt_to_plan`: Haiku translates natural language to a PlanRequest.
- `summarize_itinerary`: Sonnet writes a short trip summary for a blog post.
"""

import json
import logging
from typing import Any

from anthropic import AsyncAnthropic

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_PROMPT_SYS = """You translate user requests for a day-trip itinerary into structured JSON.

Output ONLY a JSON object — no prose, no markdown fences, no leading or trailing text.
The JSON has exactly these fields:
{
  "start_loc": string,       // city, address, or landmark
  "radius_m": integer,       // 500-20000
  "stop_count": integer,     // 2-10
  "transit_mode": "walking" | "driving" | "bicycling" | "transit"
}

Defaults when unspecified: radius_m=4000, stop_count=5, transit_mode="walking".
Always return all four fields.
"""


def _extract_json_object(text: str) -> str:
    """Pull the first balanced {...} block out of the model's response.

    Claude usually obeys 'JSON only' but occasionally wraps in ```json fences
    or adds a one-line preamble. This recovers from both without changing the
    happy path.
    """
    text = text.strip()
    # Strip a leading code fence (```json or ```).
    if text.startswith("```"):
        first_nl = text.find("\n")
        if first_nl != -1:
            text = text[first_nl + 1 :]
        if text.endswith("```"):
            text = text[: -3]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return text
    return text[start : end + 1]


def _client() -> AsyncAnthropic:
    return AsyncAnthropic(api_key=get_settings().anthropic_api_key)


async def prompt_to_plan(prompt: str) -> dict[str, Any]:
    msg = await _client().messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        system=_PROMPT_SYS,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text")
    payload = _extract_json_object(text)
    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        logger.warning("prompt_to_plan: model returned non-JSON: %s", text[:300])
        raise ValueError(f"Could not parse Claude response as JSON: {e}") from e


_DESC_SYS = """You write one-sentence "why visit" blurbs for places on a day trip.

You'll be given a JSON list of {"name": "...", "context": "..."}.
Return JSON: a list of strings, same length and order. Each string is one
specific, vivid sentence (~15-25 words). No marketing fluff, no superlatives,
no "this iconic landmark" cliches. Lead with what's actually distinctive
about the place. If you don't recognize a place, write something that's
true of places of that kind in that context.

Output ONLY the JSON array, no prose."""


async def describe_places(items: list[dict[str, str]]) -> list[str]:
    """Generate a one-sentence blurb per place. Returns same length as items."""
    if not items:
        return []
    msg = await _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400 + 60 * len(items),
        system=_DESC_SYS,
        messages=[{"role": "user", "content": json.dumps(items, ensure_ascii=False)}],
    )
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
            # Trim to expected length defensively.
            return [parsed[i] if i < len(parsed) else "" for i in range(len(items))]
    except (ValueError, json.JSONDecodeError):
        logger.warning("describe_places: model returned non-JSON: %s", text[:200])
    return [""] * len(items)


async def summarize_itinerary(
    stop_names: list[str], start_loc: str, transit_mode: str
) -> str:
    msg = await _client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=(
            "You write short, vivid one-paragraph previews of day trips. "
            "Address the reader directly ('you'll'). Be specific about what makes "
            "each place feel like part of the same day. Avoid generic tourist-brochure "
            "phrasing. Skip greetings, headings, or lists — just the paragraph. "
            "Aim for 3-5 sentences, ~60-90 words."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Trip starts at: {start_loc}\n"
                    f"Travel mode: {transit_mode}\n"
                    f"Stops in order: {', '.join(stop_names)}\n"
                    f"Write the preview paragraph."
                ),
            }
        ],
    )
    return "".join(b.text for b in msg.content if b.type == "text").strip()
