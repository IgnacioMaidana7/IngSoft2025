"use client";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { uploadPhoto } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function CameraCapture({ onUploaded }: { onUploaded?: (result: { id: string; url: string }) => void }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { token } = useAuth();

  const stopStream = useCallback(() => {
    stream?.getTracks().forEach((t) => t.stop());
  }, [stream]);

  useEffect(() => {
    let active = true;
    const init = async () => {
      try {
        const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
        if (!active) return;
        setStream(s);
        if (videoRef.current) {
          videoRef.current.srcObject = s;
          await videoRef.current.play().catch(() => undefined);
        }
      } catch {
        setError("No se pudo acceder a la cámara. Permisos denegados o no disponible.");
      }
    };
    init();
    return () => {
      active = false;
      stopStream();
    };
  }, [stopStream]);

  const capture = useCallback(async () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise<Blob | null>((resolve) => canvas.toBlob((b) => resolve(b), "image/jpeg", 0.9));
    if (!blob) return;
    const file = new File([blob], `photo_${Date.now()}.jpg`, { type: "image/jpeg" });
    const result = await uploadPhoto(file, token);
    onUploaded?.(result);
  }, [token, onUploaded]);

  return (
    <div className="grid gap-3">
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <video ref={videoRef} className="w-full max-w-[600px] rounded-xl overflow-hidden bg-black" playsInline muted />
      <canvas ref={canvasRef} className="hidden" />
      <button type="button" onClick={capture} className="px-4 py-3 bg-sky-500 text-white rounded-[10px] w-fit">Capturar y subir</button>
      <label className="text-sm">
        O seleccionar archivo
        <input
          className="block"
          type="file"
          accept="image/*"
          capture="environment"
          onChange={async (e) => {
            const f = e.target.files?.[0];
            if (!f) return;
            const result = await uploadPhoto(f, token);
            onUploaded?.(result);
          }}
        />
      </label>
    </div>
  );
}


