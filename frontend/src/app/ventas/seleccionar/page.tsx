"use client";
import React from "react";
import { COLORS } from "@/constants/colors";

const mockAllProducts = [
  { id: 'p1', name: 'Leche Entera 1L', price: 800 },
  { id: 'p2', name: 'Pan de Molde', price: 1200 },
  { id: 'p3', name: 'Queso Cremoso 500g', price: 2500 },
  { id: 'p4', name: 'Yogur de Fresa', price: 600 },
  { id: 'p5', name: 'Gaseosa Cola 2.25L', price: 1500 },
];

export default function SeleccionarProductoPage() {
  function handleSelect(p: { id: string; name: string; price: number }) {
    alert(`Seleccionado: ${p.name} ($${p.price}) - Integrar con estado global según sea necesario`);
    history.back();
  }

  return (
    <main style={{ background: COLORS.background, minHeight: '100vh' }}>
      <div>
        {mockAllProducts.map((item) => (
          <button key={item.id} onClick={() => handleSelect(item)} style={{ width: '100%', textAlign: 'left', border: 0, background: 'white', padding: 20, borderBottom: `1px solid ${COLORS.border}`, display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: COLORS.text }}>{item.name}</span>
            <span style={{ color: COLORS.primary, fontWeight: 700 }}>${item.price}</span>
          </button>
        ))}
      </div>
    </main>
  );
}


