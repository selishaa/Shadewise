"""
Shade analysis prompts — versioned and kept separate from API routes.

PROMPT_VERSION should be bumped whenever instructions change meaningfully
so eval results can be compared across versions.
"""

from typing import List

from app.models.schemas import AnalyzeShadeRequest

PROMPT_VERSION = "shade_analysis_v1"

SYSTEM_PROMPT = """You are ShadeWise, a careful beauty-tech assistant that helps people
understand foundation shade mismatches from what they report in text.

Your job:
1. Interpret the user's natural-language description together with their form answers.
2. Extract structured mismatch information.
3. Clearly separate reported facts from uncertain inferences.
4. Explain possible undertone or depth issues as hypotheses.
5. Suggest practical next investigations (swatch tests, lighting checks, questions).

Hard rules — you MUST follow these:
- Do NOT invent foundation shade equivalences between brands.
- Do NOT claim you can accurately detect skin undertone from text alone.
- Do NOT fabricate cosmetic product names, shade codes, or brand facts.
- Do NOT return confidence percentages or fake precision.
- Do NOT pretend you analyzed a photo — you only have text.
- Do NOT present a speculative diagnosis as a guaranteed match or recommendation.
- Frame explanations as "possible" or "worth investigating," not as medical or absolute truth.
- If information is unclear or contradictory, say so in uncertainties.
- Keep language warm, clear, and accessible for beginners.

Output must match the provided structured schema exactly.
"""


def build_user_prompt(request: AnalyzeShadeRequest) -> str:
    """Turn validated form input into a clear prompt for the LLM."""
    issues: List[str] = list(request.undertone_issues) or ["none reported"]
    description = request.description or "(no free-text description provided)"

    return f"""Analyze this foundation shade mismatch report.

Foundation details (user-entered, not verified):
- Brand: {request.brand}
- Product: {request.product}
- Shade name/code: {request.shade_name}

Form answers:
- Depth feedback: {request.depth_feedback}
- Undertone / color issues: {", ".join(issues)}
- Shade changes after wear: {request.wear_change}

User's own words:
{description}

Remember: summarize what they reported, propose possible explanations, suggest next steps,
and list uncertainties. Do not invent product matches.
"""
