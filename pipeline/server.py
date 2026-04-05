"""FastAPI server for yoga pose analysis.

Accepts video uploads or webcam recordings and sends them to Gemini
for AI-powered yoga form analysis.
"""

import asyncio
import base64
import json
import os
import tempfile
import time

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pipeline.llm import distill_to_structured, text_to_speech, _fallback_advice
from pipeline.voice import create_live_session, send_audio, receive_audio
from pipeline.video import convert_video, split_video
from pipeline.gemini_vision import analyze_clip_with_gemini
from pipeline.scoring import build_analysis_result

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _process_single_clip(idx: int, clip: str, max_clip_sec: int) -> dict:
    """Process a single clip: send inline to Gemini for analysis."""
    print(f"  Clip {idx}: sending to Gemini...")
    t0 = time.time()
    feedback = analyze_clip_with_gemini(clip)
    print(f"  Clip {idx}: done in {time.time() - t0:.1f}s")

    start_sec = idx * max_clip_sec
    end_sec = start_sec + max_clip_sec
    return {
        "clip_index": idx,
        "clip_path": clip,
        "time_range": f"{start_sec:.1f}s-{end_sec:.1f}s",
        "feedback": feedback,
    }


async def _analyze_video(tmp_path: str, input_type: str) -> dict:
    """Common analysis pipeline for both upload and webcam paths.

    Two stages:
    1. Per-clip Gemini analysis (parallel)
    2. Distill into structured scores + coaching (single call)
    """
    print(f"Converting video...")
    video_path = convert_video(tmp_path)
    print(f"Splitting into clips...")
    clips = split_video(video_path)
    max_clip_sec = 5
    print(f"Processing {len(clips)} clips in parallel...")

    # Stage 1: Process all clips in parallel threads
    clip_futures = [
        asyncio.to_thread(_process_single_clip, idx, clip, max_clip_sec)
        for idx, clip in enumerate(clips)
    ]
    clip_results: list[dict] = list(await asyncio.gather(*clip_futures))
    clip_results.sort(key=lambda r: r["clip_index"])

    # Stage 2: Distill clip feedbacks into structured result
    clip_feedbacks = [r["feedback"] for r in clip_results if r["feedback"]]
    print(f"Distilling {len(clip_feedbacks)} clip feedbacks into structured result...")

    result = None
    if clip_feedbacks:
        try:
            result = await asyncio.wait_for(
                distill_to_structured(clip_feedbacks, {}), timeout=30
            )
        except Exception as e:
            print(f"Gemini distill failed: {e}")

    if result and "overallScore" in result and "categories" in result:
        # Use distilled result directly
        result.setdefault("timestamp", time.strftime("%Y-%m-%dT%H:%M:%SZ"))
        result.setdefault("inputType", input_type)
        result.setdefault("clips", [
            {"clip_index": r["clip_index"], "time_range": r["time_range"], "feedback": r["feedback"]}
            for r in clip_results
        ])
        if "coaching" not in result:
            result["coaching"] = _fallback_advice(result)
        print(f"Score: {result['overallScore']} — {result.get('coaching', '')[:80]}")
    else:
        # Fallback: build from raw clip text
        print("Distill failed, using fallback scoring...")
        combined_text = "\n\n".join(clip_feedbacks)
        result = build_analysis_result(combined_text, clip_results, input_type)
        result["coaching"] = _fallback_advice(result)

    global _latest_report
    _latest_report = result

    return result


@app.post("/api/analyze")
async def analyze_upload(
    video: UploadFile = File(...),
    input_type: str = Query(default="upload"),
):
    """Upload a video file for yoga pose analysis."""
    suffix = os.path.splitext(video.filename or "video.mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await video.read())
        tmp_path = tmp.name

    try:
        return await _analyze_video(tmp_path, input_type)
    except FileNotFoundError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"error": str(e)})
    except ValueError as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=400, content={"error": str(e)})
    except Exception as e:
        from fastapi.responses import JSONResponse
        print(f"Analysis error: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.websocket("/ws/analyze")
async def ws_analyze(ws: WebSocket):
    """Receive video recording from webcam, process when complete."""
    await ws.accept()

    chunks: list[bytes] = []

    try:
        while True:
            data = await ws.receive()

            if "bytes" in data:
                chunks.append(data["bytes"])
                await ws.send_json({"type": "status", "chunks_received": len(chunks)})

            elif "text" in data:
                msg = json.loads(data["text"])
                if msg.get("type") == "stop" and chunks:
                    await ws.send_json({"type": "status", "message": "Analyzing your yoga form..."})

                    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                        for chunk in chunks:
                            tmp.write(chunk)
                        tmp_path = tmp.name

                    try:
                        result = await _analyze_video(tmp_path, "webcam")
                        await ws.send_json({"type": "analysis_complete", "result": result})
                    except Exception as e:
                        await ws.send_json({"type": "error", "message": str(e)})
                    finally:
                        if os.path.exists(tmp_path):
                            os.unlink(tmp_path)

                    chunks.clear()

                elif msg.get("type") == "reset":
                    chunks.clear()

    except WebSocketDisconnect:
        pass


# Store latest report for voice coach context
_latest_report = {}


@app.websocket("/ws/voice")
async def ws_voice(ws: WebSocket):
    await ws.accept()
    gemini_ws = await create_live_session(_latest_report)
    if not gemini_ws:
        await ws.send_json({"type": "error", "message": "Voice coach unavailable"})
        await ws.close()
        return
    await ws.send_json({"type": "ready"})

    async def forward_responses():
        try:
            while True:
                chunks = await receive_audio(gemini_ws)
                if chunks:
                    for chunk in chunks:
                        await ws.send_json({"type": "audio", "data": chunk})
                await asyncio.sleep(0.05)
        except Exception:
            pass

    response_task = asyncio.create_task(forward_responses())
    try:
        while True:
            data = await ws.receive()
            if "bytes" in data:
                pcm_b64 = base64.b64encode(data["bytes"]).decode("utf-8")
                await send_audio(gemini_ws, pcm_b64)
            elif "text" in data:
                msg = json.loads(data["text"])
                if msg.get("type") == "end":
                    break
    except WebSocketDisconnect:
        pass
    finally:
        response_task.cancel()
        await gemini_ws.close()


@app.get("/api/health")
async def health():
    return {"status": "ok"}


# Serve Next.js static export pages
_out_dir = os.path.join(os.path.dirname(__file__), "..", "out")
if os.path.isdir(_out_dir):
    from fastapi.responses import FileResponse

    @app.get("/analyze")
    async def serve_analyze():
        return FileResponse(os.path.join(_out_dir, "analyze.html"))

    @app.get("/results")
    async def serve_results():
        return FileResponse(os.path.join(_out_dir, "results.html"))

    app.mount("/", StaticFiles(directory=_out_dir, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
