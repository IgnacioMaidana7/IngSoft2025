"use client";
import React from "react";
import { COLORS } from "@/constants/colors";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";

const mock = [
  { id: 1, fecha: '2024-08-10', tipo: 'Ingreso', producto: 'Leche Entera 1L', cantidad: 50, deposito: 'Central' },
  { id: 2, fecha: '2024-08-11', tipo: 'Transferencia', producto: 'Pan de Molde', cantidad: 20, deposito: 'Norte' },
];

export default function MovimientosPage() {
  return (
    <Container>
      <Card>
        <h1 style={{ color: COLORS.text, marginBottom: 12 }}>Historial de Movimientos</h1>
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full bg-white">
            <thead className="bg-primary/10">
              <tr>
                <th className="text-left p-3">Fecha</th>
                <th className="text-left p-3">Tipo</th>
                <th className="text-left p-3">Producto</th>
                <th className="text-left p-3">Cantidad</th>
                <th className="text-left p-3">Depósito</th>
              </tr>
            </thead>
            <tbody>
              {mock.map((m) => (
                <tr key={m.id} className="border-t border-border">
                  <td className="p-3">{m.fecha}</td>
                  <td className="p-3">{m.tipo}</td>
                  <td className="p-3">{m.producto}</td>
                  <td className="p-3">{m.cantidad}</td>
                  <td className="p-3">{m.deposito}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </Container>
  );
}


