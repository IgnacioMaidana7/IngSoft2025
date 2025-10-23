'use client';

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { crearCategoriaPersonalizada, type CategoriaSimple } from '@/lib/api';
import { useAuth } from '@/context/AuthContext';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';

interface ModalNuevaCategoriaProps {
  isOpen: boolean;
  onClose: () => void;
  onCategoriaCreada: (categoria: CategoriaSimple) => void;
}

export default function ModalNuevaCategoria({ isOpen, onClose, onCategoriaCreada }: ModalNuevaCategoriaProps) {
  const { token } = useAuth();
  const [nombre, setNombre] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!token || !nombre.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const nuevaCategoria = await crearCategoriaPersonalizada({
        nombre: nombre.trim(),
        descripcion: descripcion.trim() || undefined
      }, token);

      onCategoriaCreada(nuevaCategoria);
      
      // Limpiar formulario y cerrar
      setNombre('');
      setDescripcion('');
      onClose();
    } catch (err: any) {
      console.error('Error creando categoría:', err);
      if (err.message?.includes('Ya tienes una categoría con este nombre')) {
        setError('Ya tienes una categoría con este nombre');
      } else {
        setError('Error al crear la categoría. Inténtalo de nuevo.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setNombre('');
      setDescripcion('');
      setError(null);
      onClose();
    }
  };

  // Manejar tecla Escape
  useEffect(() => {
    if (!isOpen) return;

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, loading]);

  if (!isOpen) return null;

  const modalContent = (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[9999]"
      onClick={handleClose}
    >
      <div 
        className="bg-white rounded-lg p-6 w-full max-w-md mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Nueva Categoría</h2>
          <button
            onClick={handleClose}
            disabled={loading}
            className="text-gray-400 hover:text-gray-600 text-xl font-semibold"
          >
            ×
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nombre de la categoría *
            </label>
            <Input
              type="text"
              value={nombre}
              onChange={(e) => setNombre(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && nombre.trim() && !loading) {
                  handleSubmit();
                }
              }}
              placeholder="Ej: Productos Personalizados"
              required
              disabled={loading}
              maxLength={100}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Descripción (opcional)
            </label>
            <textarea
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent disabled:bg-gray-100"
              rows={3}
              value={descripcion}
              onChange={(e) => setDescripcion(e.target.value)}
              placeholder="Descripción de la categoría..."
              disabled={loading}
              maxLength={500}
            />
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={handleClose}
              disabled={loading}
              className="flex-1"
            >
              Cancelar
            </Button>
            <Button
              type="button"
              onClick={handleSubmit}
              disabled={loading || !nombre.trim()}
              className="flex-1"
            >
              {loading ? 'Creando...' : 'Crear Categoría'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
}