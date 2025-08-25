"use client";
import React, { useState } from "react";
import Button from "@/components/ui/Button";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";

export default function TransferProductPage() {
  const [producto, setProducto] = useState("");
  const [cantidad, setCantidad] = useState<number>(1);

  return (
    <Container>
      <Card>
        <h1 className="text-[22px] font-bold mb-5 text-center">Seleccionar Producto</h1>
        <div className="mb-[14px]">
          <label className="block mb-2 font-semibold text-text">Producto</label>
          <input className="w-full px-[14px] py-3 border border-border rounded-xl" placeholder="Código o nombre" value={producto} onChange={(e) => setProducto(e.target.value)} />
        </div>
        <div className="mb-[14px]">
          <label className="block mb-2 font-semibold text-text">Cantidad</label>
          <input className="w-full px-[14px] py-3 border border-border rounded-xl" type="number" min={1} value={cantidad} onChange={(e) => setCantidad(Number(e.target.value))} />
        </div>
        <Button onClick={() => alert(`Transferencia registrada (mock): ${cantidad} x ${producto}`)}>Registrar</Button>
      </Card>
    </Container>
  );
}


