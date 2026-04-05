# JNKS Yoga

AI-powered yoga form analyzer. Record your practice via webcam or upload a video, and get instant feedback on your alignment, balance, flexibility, and form. Uses Gemini AI vision for analysis — no local ML models required.

## How It Works

1. **Record** your practice using a webcam (live analysis) or upload a video file
2. **Analyze** your form with Gemini AI vision (video sent to API)
3. **Score** across 4 categories with detailed per-section feedback
4. **Coach** with real-time voice coaching via Gemini Live

## Tech Stack

**Frontend**
- Next.js 16 (React 19) with TypeScript
- Tailwind CSS 4, shadcn/ui components
- Framer Motion, GSAP, Anime.js (animations)

**AI Pipeline**
- Gemini Pro (video analysis per clip)
- Gemini Flash (structured scoring, coaching distillation)
- Gemini TTS (text-to-speech coaching)
- Gemini Live (real-time voice coaching session)
- FastAPI + WebSocket backend

## Prerequisites

- **Node.js** 18+
- **Python** 3.8+
- **ngrok** (tunnels the backend so your phone can connect)
  ```bash
  brew install ngrok
  ngrok config add-authtoken YOUR_TOKEN
  ```

No GPU or local ML models needed — all analysis runs through the Gemini API.

## Getting Started

### 1. Clone and install

```bash
git clone <repo-url>
cd JNKS-Yoga
npm install
```

### 2. Set up the Python backend

```bash
# Option A: create fresh venv
python3 -m venv venv
source venv/bin/activate
pip install -r pipeline/requirements.txt

# Option B: reuse JNKS venv (if you have the JNKS repo)
ln -s ../JNKS/venv venv
```

### 3. Configure environment

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_gemini_api_key
```

### 4. Run

```bash
./start.sh
```

This will:
- Start an ngrok tunnel on **port 8001**
- Build the frontend with the ngrok URL baked in
- Start the FastAPI backend
- Print the URL to open on your phone

**Access:**
- Phone/remote: the ngrok URL printed by the script
- Local: `http://localhost:8001`

Press `Ctrl+C` to stop everything.

### Manual start (without ngrok)

```bash
source venv/bin/activate
npm run build
python3 -m pipeline.server
```

Then open `http://localhost:8001`.

## Project Structure

```
src/
  app/              # Next.js pages (landing, analyze, results)
  components/
    analyze/        # Webcam feed, video upload, analyze button
    landing/        # Hero, features, how-it-works sections
    results/        # Score display, breakdown, tips
    layout/         # Navbar, theme, animated background
    ui/             # Reusable UI components
  lib/              # Utilities, API helpers
  types/            # TypeScript interfaces

pipeline/           # Python AI pipeline
  server.py         # FastAPI server (REST + WebSocket)
  gemini_vision.py  # Gemini video analysis per clip
  scoring.py        # Score computation from Gemini results
  llm.py            # Gemini text generation, TTS
  voice.py          # Gemini Live real-time voice coaching
  video.py          # Video conversion and splitting (ffmpeg)
  storage.py        # Simple JSON storage

start.sh            # One-command startup (ngrok + build + backend)
```

## Scoring Categories

| Category | Weight | Description |
|----------|--------|-------------|
| **Alignment** | 30% | Spine neutrality, joint stacking, head/neck/pelvis position |
| **Balance** | 25% | Stability, weight distribution, grounding |
| **Flexibility** | 25% | Range of motion, depth, joint mobility |
| **Form** | 20% | Overall pose quality, symmetry, muscle engagement |

Each category is scored 0-100 using hybrid scoring: Gemini vision analysis blended with pose metrics. The coaching advice targets your weakest area with specific, actionable tips.

## Key Differences from JNKS (Basketball)

| | JNKS (Basketball) | JNKS Yoga |
|-|-------------------|-----------|
| **Port** | 8000 | 8001 |
| **Local ML** | MediaPipe + YOLOv8 | None (cloud-only) |
| **Python deps** | 10 packages (heavy) | 7 packages (lightweight) |
| **Analysis** | Pose comparison to pro references | Gemini vision scoring |
| **Voice coaching** | TTS playback | Real-time Gemini Live conversation |
