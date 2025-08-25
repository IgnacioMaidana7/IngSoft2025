"use client";
import React, { useState } from "react";
import ProductListItem, { ProductItem } from "@/components/feature/ProductListItem";
import Button from "@/components/ui/Button";
import Input from "@/components/ui/Input";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";

const mock: ProductItem[] = [
  { id: "1", name: "Manzana Roja", category: "Frutas", price: "$1200", imageUri: "https://picsum.photos/seed/a/100" },
  { id: "2", name: "Leche Entera", category: "Lácteos", price: "$1800", imageUri: "https://picsum.photos/seed/b/100" },
  { id: "3", name: "Pan Integral", category: "Panadería", price: "$800" },
  { id: "4", name: "Agua Mineral", category: "Bebidas", price: "$500", imageUri: "https://picsum.photos/seed/c/100" },
  { id: "5", name: "Queso Cremoso", category: "Lácteos", price: "$2400", imageUri: "https://picsum.photos/seed/d/100" },
];

export default function ProductosPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");

  const categories = ["all", ...Array.from(new Set(mock.map(p => p.category)))];
  
  const filteredProducts = mock.filter(product => {
    const matchesSearch = product.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         product.category.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory === "all" || product.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <Container size="xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 bg-gradient-to-br from-primary to-primary/80 rounded-2xl flex items-center justify-center text-white text-2xl shadow-xl shadow-primary/30">
            🏷️
          </div>
          <div>
            <h1 className="text-3xl font-bold text-text mb-1">Gestión de Productos</h1>
            <p className="text-lightText">Administra tu catálogo de productos</p>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <Card variant="gradient" padding="sm" className="text-center">
          <div className="text-2xl font-bold text-primary mb-1">{mock.length}</div>
          <div className="text-sm text-lightText">Total Productos</div>
        </Card>
        <Card variant="gradient" padding="sm" className="text-center">
          <div className="text-2xl font-bold text-primary mb-1">{categories.length - 1}</div>
          <div className="text-sm text-lightText">Categorías</div>
        </Card>
        <Card variant="gradient" padding="sm" className="text-center">
          <div className="text-2xl font-bold text-green-600 mb-1">4</div>
          <div className="text-sm text-lightText">En Stock</div>
        </Card>
        <Card variant="gradient" padding="sm" className="text-center">
          <div className="text-2xl font-bold text-orange-600 mb-1">1</div>
          <div className="text-sm text-lightText">Stock Bajo</div>
        </Card>
      </div>

      {/* Filters and Actions */}
      <Card variant="elevated" className="mb-8">
        <div className="flex flex-col lg:flex-row gap-4 lg:items-center lg:justify-between">
          <div className="flex flex-col sm:flex-row gap-4 flex-1">
            <div className="flex-1">
              <Input
                placeholder="Buscar productos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                icon={
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
            </div>
            <div className="sm:w-48">
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full py-4 px-4 rounded-2xl border-2 border-border bg-white text-text focus:border-primary focus:ring-4 focus:ring-primary/10 transition-all duration-300"
              >
                <option value="all">Todas las categorías</option>
                {categories.slice(1).map(cat => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="flex gap-3">
            <Button
              variant="ghost"
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
              onClick={() => alert('Exportar datos')}
            >
              Exportar
            </Button>
            <Button
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              }
              onClick={() => location.assign('/productos/nuevo')}
            >
              Nuevo Producto
            </Button>
          </div>
        </div>
      </Card>

      {/* Products List */}
      <Card>
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-text">
              Productos ({filteredProducts.length})
            </h2>
            {searchTerm && (
              <div className="text-sm text-lightText">
                Mostrando resultados para &ldquo;{searchTerm}&rdquo;
              </div>
            )}
          </div>
        </div>
        
        {filteredProducts.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-20 h-20 bg-primary/10 rounded-3xl flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10 text-primary/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 009.586 13H7" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-text mb-2">No se encontraron productos</h3>
            <p className="text-lightText mb-6">
              {searchTerm ? 'Intenta con otros términos de búsqueda' : 'Agrega tu primer producto para comenzar'}
            </p>
            <Button
              onClick={() => location.assign('/productos/nuevo')}
              icon={
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              }
            >
              Agregar Producto
            </Button>
          </div>
        ) : (
          <div className="space-y-1">
            {filteredProducts.map((product) => (
              <ProductListItem 
                key={product.id} 
                item={product} 
                onEdit={() => alert('Editar ' + product.name)} 
                onDelete={() => alert('Eliminar ' + product.name)} 
              />
            ))}
          </div>
        )}
      </Card>
    </Container>
  );
}


