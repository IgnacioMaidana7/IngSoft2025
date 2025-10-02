"use client";
import React, { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useNotifications } from "@/context/NotificationsContext";
import Link from "next/link";

export default function Navbar() {
  const { logout } = useAuth();
  const { 
    notifications: notis, 
    unreadCount, 
    markAsRead, 
    hasNewNotifications, 
    clearNewNotifications 
  } = useNotifications();
  const router = useRouter();
  const pathname = usePathname();
  const [userType, setUserType] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<string | null>(null);
  const [empleadoData, setEmpleadoData] = useState<{
    nombre: string;
    puesto: string;
    supermercado_nombre: string;
  } | null>(null);
  const [openNotis, setOpenNotis] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const tipo = localStorage.getItem('user_type');
      const rol = localStorage.getItem('user_role'); // Obtenemos el rol específico
      setUserType(tipo);
      setUserRole(rol);
      
      // Para empleados, obtener datos reales del localStorage
      if (tipo === 'empleado') {
        const empleadoInfo = localStorage.getItem('empleado_info');
        if (empleadoInfo) {
          try {
            const parsedInfo = JSON.parse(empleadoInfo);
            setEmpleadoData(parsedInfo);
          } catch (error) {
            console.error('Error parsing empleado info:', error);
            // Fallback a datos mock si hay error
            setEmpleadoData({
              nombre: 'Empleado',
              puesto: rol || 'REPONEDOR',
              supermercado_nombre: 'Supermercado'
            });
          }
        } else {
          // Usar rol del localStorage como fallback
          setEmpleadoData({
            nombre: 'Empleado',
            puesto: rol || 'REPONEDOR',
            supermercado_nombre: 'Supermercado'
          });
        }
      }
    }
  }, []);

  // Limpiar indicador de nuevas notificaciones cuando se abre el panel
  const handleOpenNotifications = () => {
    setOpenNotis(!openNotis);
    if (!openNotis && hasNewNotifications) {
      clearNewNotifications();
    }
  };

  const handleLogout = async () => {
    await logout();
    router.replace("/login");
  };

  const getHomeLink = () => {
    return userType === 'empleado' ? '/empleado/dashboard' : '/dashboard';
  };

  const getNavItems = () => {
    if (userType === 'empleado') {
      // Opciones según el rol del empleado
      if (userRole === 'REPONEDOR' || empleadoData?.puesto === 'REPONEDOR') {
        return [
          { href: '/productos', label: 'Productos', icon: '🛍️' },
          { href: '/inventario', label: 'Inventario', icon: '📦' }
        ];
      } else if (userRole === 'CAJERO' || empleadoData?.puesto === 'CAJERO') {
        return [
          { href: '/ventas', label: 'Ventas', icon: '💰' }
        ];
      } else {
        // Fallback para empleados sin rol específico
        return [
          { href: '/productos', label: 'Productos', icon: '🛍️' },
          { href: '/inventario', label: 'Inventario', icon: '📦' }
        ];
      }
    } else {
      // Mostrar todas las opciones para administradores
      return [
        { href: '/productos', label: 'Productos', icon: '🛍️' },
        { href: '/inventario', label: 'Inventario', icon: '📦' },
        { href: '/ventas', label: 'Ventas', icon: '💰' },
        { href: '/ventas/historial', label: 'Historial', icon: '📋' },
        { href: '/empleados', label: 'Empleados', icon: '👥' },
        { href: '/ofertas', label: 'Ofertas', icon: '🏷️' }
      ];
    }
  };

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo y título */}
          <div className="flex items-center">
            <Link href={getHomeLink()} className="flex items-center gap-3">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-white font-bold text-sm">
                🏪
              </div>
              <div>
                <div className="font-bold text-gray-900">
                  {userType === 'empleado' ? 'Panel Empleado' : 'Panel Admin'}
                </div>
                {userType === 'empleado' && empleadoData && (
                  <div className="text-xs text-gray-600">
                    {empleadoData.nombre} - {empleadoData.puesto === 'REPONEDOR' ? 'Reponedor' : 'Cajero'}
                  </div>
                )}
              </div>
            </Link>
          </div>

          {/* Navegación */}
          <div className="hidden md:flex items-center space-x-4">
            {getNavItems().map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  pathname === item.href
                    ? 'bg-primary text-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>

          {/* Usuario y logout */}
          <div className="flex items-center gap-4">
            {/* Campana de notificaciones */}
            <div className="relative">
              <button
                onClick={handleOpenNotifications}
                className={`p-2 rounded-xl border ${openNotis ? 'bg-gray-100' : 'bg-white'} hover:bg-gray-100 relative ${
                  hasNewNotifications ? 'animate-pulse ring-2 ring-blue-300' : ''
                }`}
                title="Notificaciones"
              >
                <span className="sr-only">Notificaciones</span>
                <svg className="w-5 h-5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
                {unreadCount > 0 && (
                  <span className={`absolute -top-1 -right-1 text-white text-xs rounded-full px-1.5 py-0.5 ${
                    hasNewNotifications ? 'bg-red-600 animate-pulse' : 'bg-red-500'
                  }`}>
                    {unreadCount}
                  </span>
                )}
                {hasNewNotifications && (
                  <span className="absolute -top-1 -right-1 bg-blue-500 w-3 h-3 rounded-full animate-ping"></span>
                )}
              </button>
              {openNotis && (
                <div className="absolute right-0 mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-lg z-50 max-h-96 overflow-auto">
                  <div className="p-3 border-b font-semibold text-gray-800 flex items-center justify-between">
                    <span>Notificaciones</span>
                    <button className="text-sm text-gray-500 underline" onClick={() => setOpenNotis(false)}>Cerrar</button>
                  </div>
                  {notis.length === 0 ? (
                    <div className="p-4 text-sm text-gray-600">No hay notificaciones</div>
                  ) : (
                    <ul className="divide-y">
                      {notis.map((n) => (
                        <li key={n.id} className="p-3 text-sm">
                          <div className="flex items-start gap-2">
                            <div className="mt-1">{n.tipo === 'STOCK_MINIMO' ? '⚠️' : '🔔'}</div>
                            <div className="flex-1">
                              <div className="font-medium text-gray-900">{n.titulo}</div>
                              <div className="text-gray-700 mt-0.5">{n.mensaje}</div>
                              <div className="text-xs text-gray-500 mt-1">{new Date(n.creada_en).toLocaleString()}</div>
                            </div>
                          </div>
                          {!n.leida && (
                            <div className="mt-2 text-right">
                              <button
                                onClick={() => markAsRead(n.id)}
                                className="text-xs text-primary hover:underline"
                              >
                                Marcar como leída
                              </button>
                            </div>
                          )}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
            <div className="text-sm text-gray-600 hidden sm:block">
              {userType === 'empleado' ? empleadoData?.supermercado_nombre : 'Administrador'}
            </div>
            <button
              onClick={handleLogout}
              className="p-2 rounded-xl bg-red-100 hover:bg-red-200 text-red-600 transition-all duration-300 hover:scale-110 active:scale-95"
              title="Cerrar sesión"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
            </button>
          </div>
        </div>

        {/* Navegación móvil */}
        <div className="md:hidden pb-3">
          <div className="flex space-x-1 overflow-x-auto">
            {getNavItems().map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium whitespace-nowrap transition-colors ${
                  pathname === item.href
                    ? 'bg-primary text-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <span>{item.icon}</span>
                {item.label}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}