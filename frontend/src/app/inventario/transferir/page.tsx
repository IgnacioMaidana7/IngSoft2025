"use client";
import React, { useState } from "react";
import Button from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";

export default function TransferSetupPage() {
  const router = useRouter();
  const [origen, setOrigen] = useState<string>("");
  const [destino, setDestino] = useState<string>("");
  const [fecha, setFecha] = useState<string>("");

  return (
    <Container>
      <Card>
        <h1 className="text-[22px] font-bold mb-5 text-center">Configurar Transferencia</h1>
        <div className="mb-[14px]">
          <label className="block mb-2 font-semibold text-text">Depósito Origen</label>
          <select className="w-full px-[14px] py-3 border border-border rounded-xl" value={origen} onChange={(e) => setOrigen(e.target.value)}>
            <option value="">Selecciona un depósito</option>
            <option value="central">Depósito Central</option>
            <option value="norte">Sucursal Norte</option>
          </select>
        </div>
        <div className="mb-[14px]">
          <label className="block mb-2 font-semibold text-text">Depósito Destino</label>
          <select className="w-full px-[14px] py-3 border border-border rounded-xl" value={destino} onChange={(e) => setDestino(e.target.value)}>
            <option value="">Selecciona un depósito</option>
            <option value="central">Depósito Central</option>
            <option value="norte">Sucursal Norte</option>
          </select>
        </div>
        <div className="mb-[14px]">
          <label className="block mb-2 font-semibold text-text">Fecha</label>
          <input className="w-full px-[14px] py-3 border border-border rounded-xl" type="date" value={fecha} onChange={(e) => setFecha(e.target.value)} />
        </div>
        <Button onClick={() => router.push("/inventario/transferir/producto")}>Siguiente</Button>
      </Card>
    </Container>
  );
}


