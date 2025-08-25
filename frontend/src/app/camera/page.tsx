"use client";
import React from "react";
import CameraCapture from "@/components/CameraCapture";

export default function CameraPage() {
  return (
    <main style={{ padding: 24 }}>
      <h1>Capturar foto</h1>
      <CameraCapture onUploaded={(r) => alert(`Subida OK: ${r.id}`)} />
    </main>
  );
}


