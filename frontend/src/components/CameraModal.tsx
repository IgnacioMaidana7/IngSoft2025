"use client";
import React, { useState } from "react";
import CameraCapture from "@/components/CameraCapture";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/feedback/ToastProvider";

interface CameraModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPhotoUploaded?: (result: { id: string; url: string }) => void;
}

export default function CameraModal({ isOpen, onClose, onPhotoUploaded }: CameraModalProps) {
  const [isUploading, setIsUploading] = useState(false);
  const { showToast } = useToast();

  if (!isOpen) return null;

  const handlePhotoUploaded = async (result: { id: string; url: string }) => {
    try {
      setIsUploading(true);
      showToast("Foto capturada y guardada exitosamente", "success");
      onPhotoUploaded?.(result);
      onClose();
    } catch (error) {
      showToast("Error al procesar la foto", "error");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-hidden border shadow-lg flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold">Capturar Productos</h3>
          <Button 
            variant="secondary" 
            onClick={onClose}
            disabled={isUploading}
          >
            ✕
          </Button>
        </div>
        
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            Usa la cámara para tomar una foto de los productos que deseas vender. 
            La imagen será guardada para su posterior procesamiento.
          </p>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isUploading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p>Guardando foto...</p>
            </div>
          ) : (
            <CameraCapture onUploaded={handlePhotoUploaded} />
          )}
        </div>
        
        <div className="mt-4 flex justify-end">
          <Button 
            variant="secondary" 
            onClick={onClose}
            disabled={isUploading}
          >
            Cancelar
          </Button>
        </div>
      </div>
    </div>
  );
}