"use client";
import React from "react";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import HistorialVentas from "@/components/feature/HistorialVentas";

export default function HistorialVentasPage() {
  return (
    <ProtectedRoute>
      <HistorialVentas />
    </ProtectedRoute>
  );
}