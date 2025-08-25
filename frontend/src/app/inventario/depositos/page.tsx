"use client";
import React, { useState } from "react";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";

type DepositItem = {
  id: string;
  nombre: string;
  direccion: string;
};

// Componente inline simple para reemplazar DepositListItem
function DepositListItem({ item, onEdit, onViewStock }: { item: DepositItem; onEdit: () => void; onViewStock: () => void }) {
  return (
    <div className="border border-border rounded-xl p-4 bg-white">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-text">{item.nombre}</h3>
          <p className="text-lightText text-sm">{item.direccion}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={onViewStock}>
            Ver Stock
          </Button>
          <Button variant="ghost" size="sm" onClick={onEdit}>
            Editar
          </Button>
        </div>
      </div>
    </div>
  );
}

const mockDeposits: DepositItem[] = [
  { id: '1', nombre: 'Depósito Central', direccion: 'Av. Siempre Viva 742' },
  { id: '2', nombre: 'Sucursal Norte', direccion: 'Calle Falsa 123' },
  { id: '3', nombre: 'Almacén Sur', direccion: 'Boulevar Libertad 456' },
  { id: '4', nombre: 'Centro Logístico', direccion: 'Ruta Nacional 67 Km 15' },
];

export default function DepositosPage() {
  const [searchTerm, setSearchTerm] = useState("");

  const filteredDeposits = mockDeposits.filter(deposit =>
    deposit.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
    deposit.direccion.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <Container size="xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/80 rounded-2xl flex items-center justify-center text-white text-2xl shadow-xl shadow-primary/30">
            🏪
          </div>
          <div>
            <h1 className="text-3xl font-bold text-text mb-1">Gestión de Depósitos</h1>
            <p className="text-lightText">Administra tus ubicaciones de almacenamiento</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card variant="gradient" padding="sm" className="text-center">
          <div className="text-2xl font-bold text-primary mb-1">{mockDeposits.length}</div>
          <div className="text-sm text-lightText">Total Depósitos</div>
        </Card>
        <Card variant="gradient" padding="sm" className="text-center">
          <div className="text-2xl font-bold text-green-600 mb-1">3</div>
          <div className="text-sm text-lightText">Activos</div>
        </Card>
        <Card variant="gradient" padding="sm" className="text-center">
          <div className="text-2xl font-bold text-blue-600 mb-1">85%</div>
          <div className="text-sm text-lightText">Ocupación Promedio</div>
        </Card>
        <Card variant="gradient" padding="sm" className="text-center">
          <div className="text-2xl font-bold text-orange-600 mb-1">2</div>
          <div className="text-sm text-lightText">Alertas Pendientes</div>
        </Card>
      </div>

      {/* Search and Actions */}
      <Card variant="elevated" className="mb-8">
        <div className="flex flex-col md:flex-row gap-4 md:items-center md:justify-between">
          <div className="flex-1 max-w-md">
            <Input
              placeholder="Buscar depósitos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              }
            />
          </div>
          
          <div className="flex gap-3">
            <Button
              variant="ghost"
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              }
              onClick={() => alert('Ver reportes')}
            >
              Reportes
            </Button>
            <Button
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              }
              onClick={() => alert('Nuevo depósito')}
            >
              Nuevo Depósito
            </Button>
          </div>
        </div>
      </Card>

      {/* Deposits List */}
      <Card>
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-text">
              Depósitos ({filteredDeposits.length})
            </h2>
            {searchTerm && (
              <div className="text-sm text-lightText">
                Mostrando resultados para &ldquo;{searchTerm}&rdquo;
              </div>
            )}
          </div>
        </div>
        
        {filteredDeposits.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-primary/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h4a1 1 0 011 1v5m-6 0V9a1 1 0 011-1h4a1 1 0 011 1v11" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-text mb-2">No se encontraron depósitos</h3>
            <p className="text-lightText mb-6">
              {searchTerm ? 'Intenta con otros términos de búsqueda' : 'Agrega tu primer depósito para comenzar'}
            </p>
            <Button
              onClick={() => alert('Nuevo depósito')}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              }
            >
              Agregar Depósito
            </Button>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredDeposits.map((deposit) => (
              <DepositListItem 
                key={deposit.id} 
                item={deposit} 
                onEdit={() => alert('Editar ' + deposit.nombre)} 
                onViewStock={() => alert('Ver stock ' + deposit.nombre)} 
              />
            ))}
          </div>
        )}
      </Card>
    </Container>
  );
}


