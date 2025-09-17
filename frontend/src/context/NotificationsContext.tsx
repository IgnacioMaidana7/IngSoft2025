'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import { obtenerMisNotificaciones, marcarNotificacionLeida, type Notificacion } from '@/lib/api';

interface NotificationsContextType {
  notifications: Notificacion[];
  unreadCount: number;
  loading: boolean;
  markAsRead: (id: number) => Promise<void>;
  refreshNotifications: () => Promise<void>;
  hasNewNotifications: boolean;
  clearNewNotifications: () => void;
}

const NotificationsContext = createContext<NotificationsContextType | undefined>(undefined);

export function useNotifications() {
  const context = useContext(NotificationsContext);
  if (context === undefined) {
    throw new Error('useNotifications debe ser usado dentro de un NotificationsProvider');
  }
  return context;
}

interface NotificationsProviderProps {
  children: React.ReactNode;
}

export function NotificationsProvider({ children }: NotificationsProviderProps) {
  const { token, isLoggedIn } = useAuth();
  const [notifications, setNotifications] = useState<Notificacion[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasNewNotifications, setHasNewNotifications] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const previousCountRef = useRef<number>(0);

  const refreshNotifications = useCallback(async () => {
    if (!token || !isLoggedIn) return;
    
    try {
      setLoading(true);
      const data = await obtenerMisNotificaciones(token);
      
      // Verificar si hay nuevas notificaciones no leídas
      const newUnreadCount = data.filter(n => !n.leida).length;
      const previousUnreadCount = previousCountRef.current;
      
      if (newUnreadCount > previousUnreadCount && previousUnreadCount > 0) {
        setHasNewNotifications(true);
      }
      
      previousCountRef.current = newUnreadCount;
      setNotifications(data);
    } catch (error) {
      console.error('Error cargando notificaciones:', error);
    } finally {
      setLoading(false);
    }
  }, [token, isLoggedIn]);

  const markAsRead = useCallback(async (id: number) => {
    if (!token) return;
    
    try {
      const updated = await marcarNotificacionLeida(id, token);
      setNotifications(prev => prev.map(n => n.id === id ? updated : n));
    } catch (error) {
      console.error('Error marcando notificación como leída:', error);
    }
  }, [token]);

  const clearNewNotifications = useCallback(() => {
    setHasNewNotifications(false);
  }, []);

  // Función para manejar la visibilidad del documento
  const handleVisibilityChange = useCallback(() => {
    if (document.hidden) {
      // Pausar polling cuando el documento está oculto
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    } else {
      // Reanudar polling cuando el documento vuelve a ser visible
      if (isLoggedIn && token && !intervalRef.current) {
        refreshNotifications(); // Cargar inmediatamente
        intervalRef.current = setInterval(refreshNotifications, 30000); // Cada 30 segundos
      }
    }
  }, [isLoggedIn, token, refreshNotifications]);

  // Configurar polling automático
  useEffect(() => {
    if (!isLoggedIn || !token) {
      // Limpiar polling si no está logueado
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      setNotifications([]);
      previousCountRef.current = 0;
      return;
    }

    // Cargar notificaciones inmediatamente
    refreshNotifications();

    // Configurar polling cada 30 segundos
    intervalRef.current = setInterval(refreshNotifications, 30000);

    // Configurar listener para visibilidad del documento
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [isLoggedIn, token, refreshNotifications, handleVisibilityChange]);

  const unreadCount = notifications.filter(n => !n.leida).length;

  const value: NotificationsContextType = {
    notifications,
    unreadCount,
    loading,
    markAsRead,
    refreshNotifications,
    hasNewNotifications,
    clearNewNotifications,
  };

  return (
    <NotificationsContext.Provider value={value}>
      {children}
    </NotificationsContext.Provider>
  );
}