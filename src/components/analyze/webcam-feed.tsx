"use client";

import { useRef, useState, useEffect, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { BorderBeam } from "@/components/ui/border-beam";
import { useAccentColor } from "@/components/accent-color-provider";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

interface WebcamFeedProps {
  onReady: (ready: boolean) => void;
  onBatchComplete?: (result: Record<string, unknown>) => void;
}

export function WebcamFeed({ onReady, onBatchComplete }: WebcamFeedProps) {
  const { accent } = useAccentColor();
  const videoRef = useRef<HTMLVideoElement>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const startCamera = useCallback(async () => {
    try {
      setError(null);
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 1920 }, height: { ideal: 1080 } },
        audio: false,
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      onReady(true);
    } catch {
      setError("Could not access camera. Please allow camera permissions.");
      onReady(false);
    }
  }, [onReady]);

  const startRecording = useCallback(() => {
    if (!stream) return;

    chunksRef.current = [];
    const mimeType = ["video/webm;codecs=vp9", "video/webm;codecs=vp8", "video/webm", "video/mp4"].find(
      (t) => MediaRecorder.isTypeSupported(t)
    );

    const recorder = new MediaRecorder(stream, {
      mimeType: mimeType || undefined,
      videoBitsPerSecond: 4_000_000,
    });

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.start(1000); // Collect data every second
    recorderRef.current = recorder;
    setIsRecording(true);
  }, [stream]);

  const stopRecording = useCallback(async () => {
    if (!recorderRef.current || recorderRef.current.state !== "recording") return;

    setIsRecording(false);
    setIsAnalyzing(true);

    // Stop recording and wait for final data
    const recorder = recorderRef.current;
    await new Promise<void>((resolve) => {
      recorder.onstop = () => resolve();
      recorder.stop();
    });

    // Submit the recorded video to the API
    const blob = new Blob(chunksRef.current, { type: recorder.mimeType || "video/webm" });
    const formData = new FormData();
    formData.append("video", blob, "recording.webm");

    try {
      const res = await fetch(`${API_URL}/api/analyze?input_type=webcam`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Analysis failed");
      }

      const result = await res.json();
      onBatchComplete?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed. Is the backend running?");
    } finally {
      setIsAnalyzing(false);
    }
  }, [onBatchComplete]);

  // Ensure video element always has the stream
  useEffect(() => {
    if (stream && videoRef.current && !videoRef.current.srcObject) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);

  // Cleanup
  useEffect(() => {
    return () => {
      if (recorderRef.current && recorderRef.current.state === "recording") {
        recorderRef.current.stop();
      }
      if (stream) stream.getTracks().forEach((track) => track.stop());
    };
  }, [stream]);

  return (
    <div className="space-y-4">
      <div className="relative w-full aspect-[9/16] max-w-sm mx-auto overflow-hidden rounded-2xl border border-border/50 bg-muted/20">
        {stream ? (
          <>
            <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-contain" />
            <div className="absolute top-4 left-4 flex items-center gap-2 rounded-full bg-black/60 px-3 py-1.5 text-xs font-medium text-white backdrop-blur-sm">
              <span className={`h-2 w-2 rounded-full ${isRecording ? "bg-red-500" : isAnalyzing ? "bg-yellow-500" : "bg-emerald-500"} animate-pulse`} />
              {isRecording ? "Recording" : isAnalyzing ? "Analyzing..." : "Camera Ready"}
            </div>
            <BorderBeam
              size={120}
              duration={8}
              colorFrom={accent.hex}
              colorTo={accent.hexDark}
              borderWidth={2}
            />
          </>
        ) : (
          <div className="flex h-full flex-col items-center justify-center gap-4 p-8">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="48"
              height="48"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              className="text-muted-foreground/60"
            >
              <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z" />
              <circle cx="12" cy="13" r="3" />
            </svg>
            <p className="text-sm text-muted-foreground text-center">
              Click below to start your camera and record your yoga practice.
            </p>
            <Button onClick={startCamera} className="mt-2">
              Start Camera
            </Button>
          </div>
        )}
      </div>

      {stream && !isAnalyzing && (
        <div className="flex justify-center">
          {isRecording ? (
            <Button onClick={stopRecording} variant="destructive" size="lg">
              Stop Recording & Analyze
            </Button>
          ) : (
            <Button onClick={startRecording} size="lg">
              Start Recording
            </Button>
          )}
        </div>
      )}

      {isAnalyzing && (
        <p className="text-sm text-muted-foreground text-center animate-pulse">
          Analyzing your yoga form...
        </p>
      )}

      {error && (
        <p className="text-sm text-destructive text-center">{error}</p>
      )}
    </div>
  );
}
