"""Gemini-only scoring for yoga pose analysis.

Produces the final AnalysisResponse-compatible dict for the upload endpoint.
"""

from datetime import datetime, timezone

from pipeline.gemini_vision import (
    extract_coach_summary,
    extract_gemini_scores,
    extract_section_feedback,
)

WEIGHTS = {
    "Alignment": 0.3,
    "Balance": 0.25,
    "Flexibility": 0.25,
    "Form": 0.2,
}

TIPS = {
    "Alignment": {
        "high": "Excellent alignment — your spine and joints are well-stacked throughout.",
        "mid": "Your alignment is close — focus on keeping your spine neutral and joints stacked.",
        "low": "Focus on spine neutrality and stacking your joints properly in each pose.",
    },
    "Balance": {
        "high": "Great stability — you're grounded and steady throughout your practice.",
        "mid": "Work on grounding through your feet and engaging your core for better stability.",
        "low": "Focus on grounding through your feet and engaging your core for stability.",
    },
    "Flexibility": {
        "high": "Impressive range of motion — you're moving with ease and openness.",
        "mid": "Your flexibility is developing — keep working on gradual depth without forcing.",
        "low": "Focus on gentle, consistent stretching to increase your range of motion over time.",
    },
    "Form": {
        "high": "Beautiful form — your poses are clean, symmetrical, and well-engaged.",
        "mid": "Good form overall — pay attention to symmetry and full muscle engagement.",
        "low": "Focus on the fundamentals of each pose — proper engagement and symmetry.",
    },
}


def _get_label(score: int | float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Needs Work"
    return "Poor"


def _get_tip(category: str, score: int) -> str:
    tips = TIPS.get(category, TIPS["Alignment"])
    if score >= 80:
        return tips["high"]
    if score >= 60:
        return tips["mid"]
    return tips["low"]


def build_analysis_result(
    final_text: str,
    clip_results: list[dict],
    input_type: str,
) -> dict:
    """Build the final analysis result dict from Gemini output.

    Uses 100% Gemini vision scores for all categories.
    """
    gemini_scores = extract_gemini_scores(final_text)
    coach_summary = extract_coach_summary(final_text)

    # Gemini-based scores (default 70 if not parsed)
    alignment_score = gemini_scores.get("alignment_score", 70)
    balance_score = gemini_scores.get("balance_score", 70)
    flexibility_score = gemini_scores.get("flexibility_score", 70)
    form_score = gemini_scores.get("form_score", 70)

    # Extract per-category feedback from the final Gemini text
    alignment_fb = extract_section_feedback(final_text, "Alignment")
    balance_fb = extract_section_feedback(final_text, "Balance")
    flexibility_fb = extract_section_feedback(final_text, "Flexibility")
    form_fb = extract_section_feedback(final_text, "Form")

    categories = [
        {
            "name": "Alignment",
            "score": alignment_score,
            "label": _get_label(alignment_score),
            "tip": _get_tip("Alignment", alignment_score),
            "feedback": alignment_fb,
        },
        {
            "name": "Balance",
            "score": balance_score,
            "label": _get_label(balance_score),
            "tip": _get_tip("Balance", balance_score),
            "feedback": balance_fb,
        },
        {
            "name": "Flexibility",
            "score": flexibility_score,
            "label": _get_label(flexibility_score),
            "tip": _get_tip("Flexibility", flexibility_score),
            "feedback": flexibility_fb,
        },
        {
            "name": "Form",
            "score": form_score,
            "label": _get_label(form_score),
            "tip": _get_tip("Form", form_score),
            "feedback": form_fb,
        },
    ]

    overall = round(sum(c["score"] * WEIGHTS[c["name"]] for c in categories))

    clips_out = [
        {
            "clip_index": r["clip_index"],
            "time_range": r["time_range"],
            "feedback": r["feedback"],
        }
        for r in clip_results
    ]

    return {
        "overallScore": overall,
        "overallLabel": _get_label(overall),
        "categories": categories,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "inputType": input_type,
        "coachSummary": coach_summary or None,
        "clips": clips_out,
    }
