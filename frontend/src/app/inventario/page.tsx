"use client";
import React from "react";
import HomeButton from "@/components/common/HomeButton";
import { COLORS } from "@/constants/colors";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";

export default function InventarioHomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Container>
        <Card>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: COLORS.text, textAlign: 'center', marginBottom: 30 }}>¿Qué desea hacer?</h2>
          <div style={{ width: '100%', maxWidth: 520, margin: '0 auto' }}>
            <HomeButton title="Gestionar mis Depósitos" icon="🏢" href="/inventario/depositos" />
            <HomeButton title="Gestionar Transferencias" icon="🔁" href="/inventario/transferencias" />
            <HomeButton title="Historial de Movimientos" icon="🧾" href="/inventario/movimientos" />
          </div>
        </Card>
      </Container>
    </div>
  );
}


