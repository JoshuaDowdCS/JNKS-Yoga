"""LLM integration for yoga coaching. All Gemini."""

import base64
import json
import os
import httpx

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
ANALYSIS_MODEL = "gemini-2.5-flash"                     # video analysis
DISTILL_MODEL = "gemini-2.5-flash"                     # distillation (fast/cheap)
TTS_MODEL = "gemini-2.5-flash-preview-tts"     # low-latency text-to-speech


async def _call_gemini(prompt, model=DISTILL_MODEL, max_tokens=500):
    """Call Gemini and return the text response."""
    if not GEMINI_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{GEMINI_BASE}/{model}:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"Gemini ({model}) error: {e}")
    return None


async def distill_to_structured(clip_advices, batch_report):
    """Distill per-clip video advice into structured JSON scores + coaching."""

    prompt = f"""You are an encouraging yoga instructor. A practitioner just performed yoga poses across {len(clip_advices)} video clips.

Here is what a video analysis AI observed for each clip:
{chr(10).join(f"Clip {i+1}: {a}" for i, a in enumerate(clip_advices) if a)}

Return a JSON object. Be brief and direct — no fluff.

Rules:
- Score 0-100. Grade vs intermediate practitioners. Decent form = 75-85. Below 60 only if truly poor.
- "coaching": ONE sentence max. Say what to fix and how. No preamble.
- Each "tip": ONE sentence max. Direct and actionable.
- Labels: 90+ = Excellent, 75-89 = Good, 60-74 = Needs Work, <60 = Poor.

Return ONLY valid JSON, no markdown:
{{
  "overallScore": <0-100>,
  "overallLabel": "<Excellent|Good|Needs Work|Poor>",
  "coaching": "<one direct sentence>",
  "categories": [
    {{"name": "Alignment", "score": <0-100>, "label": "<label>", "tip": "<one sentence>"}},
    {{"name": "Balance", "score": <0-100>, "label": "<label>", "tip": "<one sentence>"}},
    {{"name": "Flexibility", "score": <0-100>, "label": "<label>", "tip": "<one sentence>"}},
    {{"name": "Form", "score": <0-100>, "label": "<label>", "tip": "<one sentence>"}}
  ]
}}"""

    result = await _call_gemini(prompt, max_tokens=2000)
    if result:
        try:
            # Strip markdown fences if present
            text = result.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()
            parsed = json.loads(text)
            # Validate required fields
            if "overallScore" in parsed and "categories" in parsed and "coaching" in parsed:
                return parsed
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Gemini JSON parse error: {e}, raw: {result[:200]}")
    return None


async def analyze_pose_video(video_path):
    """Send a single video clip to Gemini for visual yoga coaching."""
    if not GEMINI_API_KEY or not video_path or not os.path.exists(video_path):
        return None

    parts = [
        {"text": """You are an expert yoga instructor watching a practitioner perform yoga poses.

Watch the video. Give exactly 2 sentences of coaching advice based on what you SEE.
Be specific — reference actual body positioning, alignment, balance, or engagement you observe. Be direct."""},
    ]

    with open(video_path, "rb") as f:
        video_b64 = base64.b64encode(f.read()).decode("utf-8")
    parts.append({"inline_data": {"mime_type": "video/mp4", "data": video_b64}})

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{GEMINI_BASE}/{ANALYSIS_MODEL}:generateContent?key={GEMINI_API_KEY}",
                json={
                    "contents": [{"parts": parts}],
                    "generationConfig": {"maxOutputTokens": 500, "temperature": 0.7},
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
            else:
                print(f"Gemini video error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"Gemini video error: {e}")
    return None


def _fallback_advice(batch_report):
    """Generate advice without LLM based on worst category."""
    categories = batch_report.get("categories", [])
    if not categories:
        return "Keep practicing and focus on mindful alignment."
    worst = min(categories, key=lambda c: c["score"])
    return f"{worst['tip']} Focus on your {worst['name'].lower()} — it's the area with the most room for improvement."


async def text_to_speech(text):
    """Convert text to speech using Gemini TTS. Returns base64-encoded WAV audio."""
    if not GEMINI_API_KEY or not text:
        return None
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{GEMINI_BASE}/{TTS_MODEL}:generateContent",
                headers={
                    "x-goog-api-key": GEMINI_API_KEY,
                    "Content-Type": "application/json",
                },
                json={
                    "contents": [{"parts": [{"text": f"Say in a calm, encouraging tone: {text}"}]}],
                    "generationConfig": {
                        "responseModalities": ["AUDIO"],
                        "speechConfig": {
                            "voiceConfig": {
                                "prebuiltVoiceConfig": {
                                    "voiceName": "Kore"
                                }
                            }
                        },
                    },
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                audio_b64 = data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
                return audio_b64
    except Exception as e:
        print(f"TTS error: {e}")
    return None
