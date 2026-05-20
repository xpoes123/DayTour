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

Output ONLY a JSON object with these fields:
{
  "start_loc": string,       // city, address, or landmark
  "radius_m": integer,       // 500-20000
  "stop_count": integer,     // 2-10
  "transit_mode": "walking" | "driving" | "bicycling" | "transit"
}

If a field is not specified, pick a reasonable default.
"""


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
    return json.loads(text)


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
