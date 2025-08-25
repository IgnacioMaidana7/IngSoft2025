"use client";
import React, { useState } from "react";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { useRouter } from "next/navigation";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { useToast } from "@/components/feedback/ToastProvider";

const mockDeposits = [{ id: '1', name: 'Depósito Central' }, { id: '2', name: 'Sucursal Norte' }];
const mockCategories = [{ label: 'Lácteos', value: 'lacteos' }, { label: 'Panadería', value: 'panaderia' }];

export default function NuevoProductoPage() {
  const router = useRouter();
  const [isEditing] = useState(false);
  const { showToast } = useToast();
  const [name, setName] = useState("");
  const [category, setCategory] = useState<string | null>(null);
  const [price, setPrice] = useState("");
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [initialStock, setInitialStock] = useState<Record<string, string>>({});

  const handlePickImage = async () => {
    // En web, usaremos input file
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.capture = 'environment';
    input.onchange = async () => {
      const file = (input.files && input.files[0]) || null;
      if (!file) return;
      const url = URL.createObjectURL(file);
      setImageUrl(url);
      // TODO: subir al backend y guardar URL
    };
    input.click();
  };

  const handleStockChange = (depositId: string, value: string) => {
    setInitialStock((prev) => ({ ...prev, [depositId]: value }));
  };

  const handleSave = () => {
    if (!name || !price) {
      alert('Nombre y Precio son obligatorios');
      return;
    }
    const productData = { name, category, price, imageUrl, initialStock: isEditing ? undefined : initialStock };
    console.log('Guardando producto', productData);
    showToast('Producto guardado', 'success');
    router.push('/productos');
  };

  return (
    <Container>
      <Card className="bg-background min-h-screen p-5">
        <h1 className="text-2xl font-bold text-text mb-5">{isEditing ? 'Editar Producto' : 'Nuevo Producto'}</h1>

        <button className="w-[150px] h-[150px] rounded-[10px] bg-[#eee] grid place-items-center mx-auto mb-5 border border-border cursor-pointer" onClick={handlePickImage}>
          {imageUrl ? <img src={imageUrl} alt="Producto" className="w-full h-full object-cover rounded-[10px]" /> : 'Tomar/Seleccionar Foto'}
        </button>

        <div className="max-w-[520px] mx-auto">
          <Input label="Nombre del Producto" value={name} onChange={(e) => setName(e.target.value)} />
          <div>
            <label className="block mb-2 font-semibold text-text">Categoría</label>
            <select className="w-full px-[14px] py-3 border border-border rounded-xl" value={category ?? ''} onChange={(e) => setCategory(e.target.value || null)}>
              <option value="">Selecciona la Categoría</option>
              {mockCategories.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>
          <Input label="Precio de Venta" value={price} onChange={(e) => setPrice(e.target.value)} type="number" />

          {!isEditing && (
            <div className="mt-5 pt-5 border-t border-[#eee]">
              <div className="text-lg font-bold text-text mb-2.5">Stock Inicial</div>
              {mockDeposits.map((d) => (
                <Input key={d.id} label={`Cantidad en ${d.name}`} type="number" onChange={(e) => handleStockChange(d.id, e.target.value)} />
              ))}
            </div>
          )}

          <div style={{ display: 'flex', gap: 12 }}>
            <Button onClick={handleSave}>Guardar</Button>
            <Button variant="secondary" onClick={() => router.back()}>Cancelar</Button>
          </div>
        </div>
      </Card>
    </Container>
  );
}


