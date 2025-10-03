"use client";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { uploadPhoto } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

export default function CameraCapture({ onUploaded }: { onUploaded?: (result: { id: string; url: string }) => void }) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [cameraState, setCameraState] = useState<'loading' | 'ready' | 'error'>('loading');
  const [error, setError] = useState<string | null>(null);
  const [isCapturing, setIsCapturing] = useState(false);
  const { token } = useAuth();

  const stopStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });
      streamRef.current = null;
    }
  }, []);

  const initializeCamera = useCallback(async () => {
    try {
      setCameraState('loading');
      setError(null);

      // Verificar si getUserMedia está disponible
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Tu navegador no soporta acceso a la cámara');
      }

      console.log('Solicitando acceso a la cámara...');
      
      const constraints = {
        video: {
          facingMode: "environment", // Cámara trasera en móviles
          width: { ideal: 1280, max: 1920 },
          height: { ideal: 720, max: 1080 },
          frameRate: { ideal: 30 }
        },
        audio: false
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      console.log('Stream obtenido:', stream);
      
      streamRef.current = stream;

      if (videoRef.current && stream) {
        videoRef.current.srcObject = stream;
        
        // Esperar a que el video esté listo
        const waitForVideo = new Promise<void>((resolve, reject) => {
          const video = videoRef.current;
          if (!video) {
            reject(new Error('Referencia de video perdida'));
            return;
          }

          const onLoadedData = () => {
            console.log('Video cargado, dimensiones:', video.videoWidth, 'x', video.videoHeight);
            video.removeEventListener('loadeddata', onLoadedData);
            video.removeEventListener('error', onError);
            resolve();
          };

          const onError = (e: Event) => {
            console.error('Error en video:', e);
            video.removeEventListener('loadeddata', onLoadedData);
            video.removeEventListener('error', onError);
            reject(new Error('Error al cargar el video'));
          };

          video.addEventListener('loadeddata', onLoadedData);
          video.addEventListener('error', onError);
          
          // Timeout de seguridad
          setTimeout(() => {
            video.removeEventListener('loadeddata', onLoadedData);
            video.removeEventListener('error', onError);
            reject(new Error('Timeout al inicializar la cámara'));
          }, 10000);
        });

        // Reproducir el video
        await videoRef.current.play();
        await waitForVideo;
        
        setCameraState('ready');
        console.log('Cámara lista para usar');

      } else {
        throw new Error('No se pudo asignar el stream al elemento video');
      }

    } catch (err) {
      console.error('Error inicializando cámara:', err);
      stopStream();
      
      let errorMessage = 'Error desconocido al acceder a la cámara';
      
      if (err instanceof Error) {
        if (err.name === 'NotAllowedError') {
          errorMessage = 'Acceso a la cámara denegado. Por favor, permite el acceso y recarga la página.';
        } else if (err.name === 'NotFoundError') {
          errorMessage = 'No se encontró ninguna cámara en este dispositivo.';
        } else if (err.name === 'NotSupportedError') {
          errorMessage = 'Tu navegador no soporta acceso a la cámara.';
        } else if (err.name === 'NotReadableError') {
          errorMessage = 'La cámara está siendo usada por otra aplicación.';
        } else {
          errorMessage = err.message;
        }
      }
      
      setError(errorMessage);
      setCameraState('error');
    }
  }, [stopStream]);

  useEffect(() => {
    let mounted = true;
    
    const init = async () => {
      if (mounted) {
        await initializeCamera();
      }
    };
    
    init();
    
    return () => {
      mounted = false;
      stopStream();
    };
  }, [initializeCamera, stopStream]);

  const capture = useCallback(async () => {
    if (cameraState !== 'ready' || isCapturing) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    if (!video || !canvas || !streamRef.current) {
      setError('Elementos de captura no disponibles');
      return;
    }

    if (video.videoWidth === 0 || video.videoHeight === 0) {
      setError('Video no está listo para captura');
      return;
    }

    try {
      setIsCapturing(true);
      
      // Configurar canvas con las dimensiones del video
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        throw new Error('No se pudo obtener contexto 2D del canvas');
      }
      
      // Dibujar frame actual del video en el canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Convertir a blob
      const blob = await new Promise<Blob | null>((resolve) => {
        canvas.toBlob(resolve, 'image/jpeg', 0.92);
      });
      
      if (!blob) {
        throw new Error('No se pudo crear la imagen');
      }
      
      // Crear archivo y subir
      const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpeg' });
      console.log('Subiendo foto:', file.size, 'bytes');
      
      const result = await uploadPhoto(file, token);
      console.log('Foto subida exitosamente:', result);
      
      onUploaded?.(result);
      
    } catch (err) {
      console.error('Error capturando foto:', err);
      setError(err instanceof Error ? err.message : 'Error al capturar la foto');
    } finally {
      setIsCapturing(false);
    }
  }, [cameraState, isCapturing, token, onUploaded]);

  const retryCamera = useCallback(() => {
    initializeCamera();
  }, [initializeCamera]);

  return (
    <div className="space-y-4">
      {/* Contenedor del video */}
      <div className="relative bg-black rounded-xl overflow-hidden" style={{ aspectRatio: '16/9', minHeight: '200px' }}>
        {cameraState === 'loading' && (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <div className="text-center text-white">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-2"></div>
              <p className="text-sm">Iniciando cámara...</p>
            </div>
          </div>
        )}
        
        {cameraState === 'error' && (
          <div className="absolute inset-0 flex items-center justify-center z-10 p-4">
            <div className="text-center text-white">
              <div className="text-4xl mb-2">📷</div>
              <p className="text-sm mb-3">{error}</p>
              <button 
                onClick={retryCamera}
                className="px-3 py-1 bg-white text-black rounded text-sm"
              >
                Reintentar
              </button>
            </div>
          </div>
        )}
        
        <video 
          ref={videoRef}
          className={`w-full h-full object-cover transition-opacity duration-500 ${
            cameraState === 'ready' ? 'opacity-100' : 'opacity-0'
          }`}
          playsInline
          muted
          autoPlay
        />
      </div>
      
      <canvas ref={canvasRef} className="hidden" />
      
      {/* Controles */}
      <div className="space-y-3">
        <button 
          type="button" 
          onClick={capture} 
          disabled={cameraState !== 'ready' || isCapturing}
          className="w-full px-4 py-3 bg-blue-500 text-white rounded-lg font-medium disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {isCapturing ? 'Capturando...' : cameraState === 'ready' ? 'Capturar y Subir' : 'Cámara no disponible'}
        </button>
        
        <div className="border-t pt-3">
          <label className="block text-sm text-gray-600 mb-2">
            O seleccionar archivo desde tu dispositivo:
          </label>
          <input
            type="file"
            accept="image/*"
            capture="environment"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            onChange={async (e) => {
              const file = e.target.files?.[0];
              if (!file) return;
              try {
                const result = await uploadPhoto(file, token);
                onUploaded?.(result);
              } catch (err) {
                console.error('Error subiendo archivo:', err);
                setError('Error al subir el archivo');
              }
            }}
          />
        </div>
      </div>
      
      {/* Debug info (solo en desarrollo) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="text-xs text-gray-500 p-2 bg-gray-100 rounded">
          Estado: {cameraState}<br/>
          Stream: {streamRef.current ? 'Activo' : 'Inactivo'}<br/>
          Video dims: {videoRef.current ? `${videoRef.current.videoWidth}x${videoRef.current.videoHeight}` : 'N/A'}
        </div>
      )}
    </div>
  );
}


