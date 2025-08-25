"use client";
import React, { useState } from "react";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Checkbox from "@/components/ui/Checkbox";

import { useRouter } from "next/navigation";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { useToast } from "@/components/feedback/ToastProvider";

const mockProducts = [
  { id: 'p1', name: 'Leche Entera 1L' },
  { id: 'p2', name: 'Pan de Molde' },
  { id: 'p3', name: 'Queso Cremoso 500g' },
];
const promoTypes = ['2x1', '3x2', '4x3'];

export default function NuevaOfertaPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [offerType, setOfferType] = useState<'discount' | 'promo'>('discount');
  const [name, setName] = useState('');
  const [selectedProducts, setSelectedProducts] = useState<string[]>([]);
  const [discount, setDiscount] = useState('');
  const [promo, setPromo] = useState<string | null>(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const toggleProduct = (id: string) => {
    setSelectedProducts((prev) => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  return (
    <Container>
      <Card className="bg-background text-text min-h-screen p-5">
        <h1 className="text-2xl font-bold mb-5">Crear/Editar Ofertas</h1>
      <Input label="Nombre de la Oferta (ej: Semana de Lácteos)" value={name} onChange={(e) => setName(e.target.value)} />

      <div className="flex mb-5 border border-primary rounded-lg overflow-hidden">
        <button className={["flex-1 py-3 font-bold text-primary", offerType === 'discount' ? "bg-primary text-white" : ""].join(' ')} onClick={() => setOfferType('discount')}>Descuento %</button>
        <button className={["flex-1 py-3 font-bold text-primary", offerType === 'promo' ? "bg-primary text-white" : ""].join(' ')} onClick={() => setOfferType('promo')}>Promoción (2x1, etc)</button>
      </div>

      {offerType === 'discount' && (
        <Input label="Porcentaje de Descuento (ej: 15)" value={discount} onChange={(e) => setDiscount(e.target.value)} type="number" />
      )}
      {offerType === 'promo' && (
        <div className="mb-[14px]">
          <label className="block mb-2 font-medium text-text">Promoción</label>
          <select className="w-full px-[14px] py-3 border border-border rounded-xl" value={promo ?? ''} onChange={(e) => setPromo(e.target.value || null)}>
            <option value="">Selecciona una promoción</option>
            {promoTypes.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </div>
      )}

      <section className="my-5">
        <div className="text-lg font-bold mb-2.5">Productos Involucrados</div>
        {mockProducts.map((p) => (
          <Checkbox key={p.id} label={p.name} checked={selectedProducts.includes(p.id)} onChange={() => toggleProduct(p.id)} />
        ))}
      </section>

      <section className="my-5">
        <div className="text-lg font-bold mb-2.5">Vigencia</div>
        <label className="block mb-2 font-medium text-text">Fecha de Inicio</label>
        <input className="w-full px-[14px] py-3 border border-border rounded-xl" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
        <label className="block mb-2 font-medium text-text mt-[15px]">Fecha de Fin</label>
        <input className="w-full px-[14px] py-3 border border-border rounded-xl" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
      </section>

        <div style={{ display: 'flex', gap: 12 }}>
          <Button onClick={() => { showToast('Oferta guardada', 'success'); router.push('/ofertas'); }}>Guardar Oferta</Button>
          <Button variant="secondary" onClick={() => router.back()}>Cancelar</Button>
        </div>
      </Card>
    </Container>
  );
}


