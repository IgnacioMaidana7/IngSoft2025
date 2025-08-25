"use client";
import React from "react";
import { COLORS } from "@/constants/colors";
import Button from "@/components/ui/Button";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";

type OfferItem = {
  id: string;
  name: string;
  type: 'discount' | 'promo';
  discount?: string;
  promo?: string;
  products: string[];
  startDate: string;
  endDate: string;
};

// Componente inline simple para reemplazar OfferListItem
function OfferListItem({ item, onEdit, onDelete }: { item: OfferItem; onEdit: () => void; onDelete: () => void }) {
  return (
    <div className="border border-border rounded-xl p-4 bg-white">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="font-semibold text-text">{item.name}</h3>
          <p className="text-lightText text-sm">
            {item.type === 'discount' ? `Descuento: ${item.discount}` : `Promoción: ${item.promo}`}
          </p>
          <p className="text-lightText text-sm">
            Productos: {item.products.join(', ')}
          </p>
          <p className="text-lightText text-sm">
            {item.startDate} - {item.endDate}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="ghost" size="sm" onClick={onEdit}>
            Editar
          </Button>
          <Button variant="ghost" size="sm" onClick={onDelete}>
            Eliminar
          </Button>
        </div>
      </div>
    </div>
  );
}

const mockOffers: OfferItem[] = [
  { id: '1', name: '15% OFF en Lácteos', type: 'discount', discount: '15%', products: ['Leche', 'Queso'], startDate: '2024-07-01', endDate: '2024-07-31' },
  { id: '2', name: 'Promo Panadería', type: 'promo', promo: '2x1', products: ['Pan de Molde'], startDate: '2024-08-01', endDate: '2024-08-15' },
  { id: '3', name: 'Oferta Finalizada', type: 'discount', discount: '10%', products: ['Yogur'], startDate: '2024-06-01', endDate: '2024-06-15' },
];

export default function OfertasPage() {
  return (
    <Container>
      <Card>
        <div style={{ paddingBottom: 12, borderBottom: `1px solid ${COLORS.border}`, marginBottom: 12 }}>
          <Button onClick={() => location.assign('/ofertas/nueva')}>+ Crear Nueva Oferta</Button>
        </div>
        <div>
          {mockOffers.map((o) => (
            <OfferListItem key={o.id} item={o} onEdit={() => location.assign(`/ofertas/${o.id}`)} onDelete={() => alert(`Eliminar ${o.name}`)} />
          ))}
        </div>
      </Card>
    </Container>
  );
}


