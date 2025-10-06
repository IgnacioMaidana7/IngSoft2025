'use client';

import React from 'react';
import { CategoriaSimple } from '@/lib/api';

interface FiltroCategoriasProps {
  categorias: CategoriaSimple[];
  value: number | '';
  onChange: (value: number | '') => void;
  placeholder?: string;
  incluirTodas?: boolean;
  className?: string;
}

export default function FiltroCategorias({
  categorias,
  value,
  onChange,
  placeholder = "Filtrar por categoría",
  incluirTodas = true,
  className = ""
}: FiltroCategoriasProps) {
  return (
    <select
      className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent ${className}`}
      value={value || ""}
      onChange={(e) => onChange(e.target.value ? Number(e.target.value) : '' as const)}
    >
      {incluirTodas && <option value="">{placeholder}</option>}
      {categorias.map((categoria) => (
        <option key={categoria.id} value={categoria.id}>
          {categoria.nombre}
        </option>
      ))}
    </select>
  );
}