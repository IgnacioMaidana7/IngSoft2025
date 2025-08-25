"use client";
import React, { useState } from "react";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import { COLORS } from "@/constants/colors";

export default function NuevoDepositoPage() {
  const router = useRouter();
  const [nombre, setNombre] = useState("");
  const [direccion, setDireccion] = useState("");

  return (
    <main style={{ background: COLORS.background, minHeight: '100vh', padding: 20 }}>
      <h1 style={{ marginBottom: 16 }}>Nuevo Depósito</h1>
      <div style={{ maxWidth: 520 }}>
        <Input label="Nombre" value={nombre} onChange={(e) => setNombre(e.target.value)} />
        <Input label="Dirección" value={direccion} onChange={(e) => setDireccion(e.target.value)} />
        <div style={{ display: 'flex', gap: 12 }}>
          <Button onClick={() => { alert('Depósito guardado (mock)'); router.push('/inventario/depositos'); }}>Guardar</Button>
          <Button variant="secondary" onClick={() => router.back()}>Cancelar</Button>
        </div>
      </div>
    </main>
  );
}


