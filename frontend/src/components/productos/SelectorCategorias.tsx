'use client';

import React, { useState } from 'react';
import { CategoriaSimple } from '@/lib/api';
import ModalNuevaCategoria from './ModalNuevaCategoria';

interface SelectorCategoriasProps {
  categorias: CategoriaSimple[];
  value: number | string;
  onChange: (value: number) => void;
  onCategoriaCreada: (categoria: CategoriaSimple) => void;
  required?: boolean;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
}

export default function SelectorCategorias({
  categorias,
  value,
  onChange,
  onCategoriaCreada,
  required = false,
  disabled = false,
  placeholder = "Seleccionar categoría",
  className = ""
}: SelectorCategoriasProps) {
  const [modalOpen, setModalOpen] = useState(false);

  const handleCategoriaCreada = (nuevaCategoria: CategoriaSimple) => {
    onCategoriaCreada(nuevaCategoria);
    // Seleccionar automáticamente la nueva categoría
    onChange(nuevaCategoria.id);
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <select
          className={`flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100 disabled:cursor-not-allowed ${className}`}
          value={value || ""}
          onChange={(e) => onChange(Number(e.target.value))}
          required={required}
          disabled={disabled}
        >
          <option value="">{placeholder}</option>
          {categorias.map((categoria) => (
            <option key={categoria.id} value={categoria.id}>
              {categoria.nombre}
            </option>
          ))}
        </select>

        <button
          type="button"
          onClick={() => setModalOpen(true)}
          disabled={disabled}
          className="px-3 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center min-w-[44px]"
          title="Crear nueva categoría"
        >
          <span className="text-lg font-semibold">+</span>
        </button>
      </div>

      <ModalNuevaCategoria
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onCategoriaCreada={handleCategoriaCreada}
      />
    </div>
  );
}