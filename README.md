# JNKS Yoga

AI-powered yoga form analyzer. Record your practice via webcam or upload a video, and get instant feedback on your technique.

## How It Works

1. **Record** your practice using a webcam or upload a video file
2. **Analyze** your form with Gemini AI vision analysis
3. **Get feedback** with scores and tips to improve your practice

## Tech Stack

**Frontend**
- Next.js 16 (React 19) with TypeScript
- Tailwind CSS 4
- Framer Motion, GSAP, Anime.js (animations)
- shadcn/ui components

**AI Pipeline**
- Gemini vision API (video analysis and scoring)
- Gemini text generation (coaching advice)
- Gemini TTS (voice coaching)
- FastAPI + WebSocket backend

## Project Structure

```
src/
  app/             # Next.js pages (landing, analyze, results)
  components/
    analyze/       # Webcam feed, video upload, analyze button
    landing/       # Hero section, features, how-it-works
    results/       # Score display, breakdown, tips
    layout/        # Navbar, theme provider, animated background
    ui/            # Reusable UI components (buttons, cards, etc.)
  lib/             # Utilities
  types/           # TypeScript interfaces

pipeline/          # Python AI pipeline
  server.py        # FastAPI server with WebSocket support
  gemini_vision.py # Gemini video analysis
  scoring.py       # Score computation from Gemini results
  llm.py           # Gemini text generation for coaching
  voice.py         # Real-time voice coaching via Gemini Live
  video.py         # Video format conversion and splitting
```

## Getting Started

### Frontend

```bash
npm install
npm run dev
```

### Python Pipeline

```bash
pip install -r pipeline/requirements.txt
python -m pipeline.server
```

## Scoring Categories

- **Alignment** (30%) - Spine neutrality, joint stacking, head/neck/pelvis position
- **Balance** (25%) - Stability, weight distribution, grounding
- **Flexibility** (25%) - Range of motion, depth, joint mobility
- **Form** (20%) - Overall pose quality, symmetry, engagement

Each category is scored 0-100 and combined into an overall score with actionable tips targeting your weakest area.
