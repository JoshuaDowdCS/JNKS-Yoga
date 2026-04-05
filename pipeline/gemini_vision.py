"""Gemini vision analysis — sends video clips inline for AI yoga coaching feedback.

Uses the Gemini REST API with inline base64 video for fast parallel analysis.
"""

import base64
import json
import mimetypes
import os
import re

import httpx

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

# Detailed coaching rubric for Gemini analysis
ANALYSIS_CATEGORIES = {
    "alignment": {
        "title": "Alignment",
        "items": [
            "Spine neutrality: straight spine without rounding or excessive arching",
            "Joint stacking: joints properly aligned (e.g. knee over ankle, shoulders over hips)",
            "Head and neck position: neutral cervical spine, gaze direction appropriate for the pose",
            "Pelvis alignment: level hips, proper tilt for the pose",
            "Limb alignment: arms and legs in correct planes and angles for the pose",
        ],
    },
    "balance": {
        "title": "Balance",
        "items": [
            "Stability: steadiness and control throughout the pose",
            "Weight distribution: even or intentional weight placement across base of support",
            "Grounding: firm connection through feet, hands, or other contact points",
            "Center of gravity: proper positioning relative to the base of support",
            "Recovery and adjustment: ability to maintain the pose without wobbling",
        ],
    },
    "flexibility": {
        "title": "Flexibility",
        "items": [
            "Range of motion: depth and openness achieved in the pose",
            "Joint mobility: freedom of movement in hips, shoulders, spine",
            "Muscle engagement vs forcing: active flexibility rather than passive collapse",
            "Progressive depth: appropriate level for the practitioner without strain",
            "Symmetry of flexibility: similar range on both sides of the body",
        ],
    },
    "form": {
        "title": "Form",
        "items": [
            "Overall pose quality: how closely the pose matches ideal form",
            "Symmetry: balanced engagement and positioning on both sides",
            "Breath integration: visible signs of controlled breathing and relaxation",
            "Transitions: smooth entry and exit from poses if visible",
            "Engagement: proper muscle activation and intentional positioning",
        ],
    },
}


def _build_category_rubric() -> str:
    lines: list[str] = []
    for category in ANALYSIS_CATEGORIES.values():
        lines.append(f'{category["title"]}:')
        for item in category["items"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).strip()


def analyze_clip_with_gemini(video_path: str) -> str:
    """Send a clip inline to Gemini and get yoga coaching feedback.

    Uses inline base64 video (no Files API upload/poll) for speed.
    Returns the raw text response from Gemini.
    """
    if not GEMINI_API_KEY:
        return ""

    mime_type = mimetypes.guess_type(video_path)[0] or "video/mp4"
    with open(video_path, "rb") as f:
        video_b64 = base64.b64encode(f.read()).decode("utf-8")

    rubric = _build_category_rubric()

    prompt = f"""Expert yoga instructor. Analyze the pose in this video.

For each category, give ONE bullet for what's good and ONE for what to fix:
{rubric}

End with scores as JSON:
```json
{{"alignment_score": <0-100>, "balance_score": <0-100>, "flexibility_score": <0-100>, "form_score": <0-100>}}
```
"""

    try:
        with httpx.Client(timeout=60) as client:
            resp = client.post(
                f"{GEMINI_BASE}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": mime_type, "data": video_b64}},
                    ]}],
                    "generationConfig": {"maxOutputTokens": 1500, "temperature": 0.7},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                print(f"Gemini clip error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"Gemini clip error: {e}")
    return ""


def extract_gemini_scores(text: str) -> dict[str, int]:
    """Extract JSON scores block from Gemini response text."""
    pattern = r"```json\s*(\{[^`]+\})\s*```"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return {}


def extract_coach_summary(text: str) -> str:
    """Extract the coach summary section from final analysis text."""
    match = re.search(
        r"Coach Summary:\s*\n(.*?)(?:\n\s*\n|\nScores:|\Z)",
        text,
        re.DOTALL,
    )
    if match:
        return match.group(1).strip()
    return ""


def extract_section_feedback(text: str, section_name: str) -> dict:
    """Extract strengths/issues/corrections for a named section.

    Returns {"strengths": [...], "issues": [...], "corrections": [...]}.
    """
    pattern = (
        rf"{re.escape(section_name)}:.*?"
        r"Strengths:\s*\n(.*?)"
        r"Issues:\s*\n(.*?)"
        r"Corrections:\s*\n(.*?)"
        r"(?=\n[A-Z]|\Z)"
    )
    match = re.search(pattern, text, re.DOTALL)
    if not match:
        return {"strengths": [], "issues": [], "corrections": []}

    def parse_bullets(block: str) -> list[str]:
        lines = []
        for line in block.strip().split("\n"):
            line = line.strip().lstrip("- ").strip()
            if line and not line.endswith(":"):
                lines.append(line)
        return lines

    return {
        "strengths": parse_bullets(match.group(1)),
        "issues": parse_bullets(match.group(2)),
        "corrections": parse_bullets(match.group(3)),
    }
