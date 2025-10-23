"use client";
import React, { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useRouter } from "next/navigation";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { obtenerPerfilEmpleado } from "@/lib/api";

interface EmpleadoData {
  nombre: string;
  nombre_completo: string;
  email: string;
  dni: string;
  puesto: 'REPONEDOR' | 'CAJERO';
  supermercado_nombre: string;
  fecha_registro: string;
}

export default function EmpleadoDashboard() {
  const { token } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [empleadoData, setEmpleadoData] = useState<EmpleadoData | null>(null);

  useEffect(() => {
    if (!token) {
      router.replace("/login");
      return;
    }

    // Verificar que sea un empleado
    const userType = localStorage.getItem('user_type');
    if (userType !== 'empleado') {
      router.replace("/dashboard");
      return;
    }

    // Redirigir a dashboard específico del rol si existe
    const userRole = localStorage.getItem('user_role');
    if (userRole === 'CAJERO') {
      router.replace('/empleado/cajero/dashboard');
      return;
    } else if (userRole === 'REPONEDOR') {
      router.replace('/empleado/reponedor/dashboard');
      return;
    }

    // Cargar datos del empleado
    const cargarDatosEmpleado = async () => {
      try {
        setLoading(true);
        
        // Primero intentar obtener desde localStorage (más rápido)
        const empleadoInfo = localStorage.getItem('empleado_info');
        if (empleadoInfo) {
          const parsedInfo = JSON.parse(empleadoInfo);
          setEmpleadoData({
            nombre: parsedInfo.nombre,
            nombre_completo: parsedInfo.nombre_completo,
            email: parsedInfo.email,
            dni: parsedInfo.dni,
            puesto: parsedInfo.puesto,
            supermercado_nombre: parsedInfo.supermercado_nombre,
            fecha_registro: new Date().toISOString() // Placeholder
          });
        } else {
          // Si no hay datos en localStorage, obtener desde API
          const datosEmpleado = await obtenerPerfilEmpleado(token);
          setEmpleadoData({
            nombre: datosEmpleado.nombre,
            nombre_completo: datosEmpleado.nombre_completo,
            email: datosEmpleado.email,
            dni: datosEmpleado.dni,
            puesto: datosEmpleado.puesto,
            supermercado_nombre: datosEmpleado.supermercado_nombre,
            fecha_registro: datosEmpleado.fecha_registro
          });
        }
      } catch (error) {
        console.error('Error al cargar datos del empleado:', error);
        // Fallback a datos básicos si hay error
        const userRole = localStorage.getItem('user_role');
        setEmpleadoData({
          nombre: 'Empleado',
          nombre_completo: 'Empleado',
          email: 'empleado@supermercado.com',
          dni: '00000000',
          puesto: (userRole as 'REPONEDOR' | 'CAJERO') || 'REPONEDOR',
          supermercado_nombre: 'Supermercado',
          fecha_registro: new Date().toISOString()
        });
      } finally {
        setLoading(false);
      }
    };

    cargarDatosEmpleado();
  }, [token, router]);



  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="text-xl font-semibold text-gray-600">Cargando...</div>
        </div>
      </div>
    );
  }

  const puesto = empleadoData?.puesto || 'REPONEDOR';

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Main Content */}
      <Container className="py-8">
        <div className="grid gap-6">
          {/* Bienvenida personalizada */}
          <Card>
            <div className="p-6">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 bg-primary rounded-full flex items-center justify-center text-white text-2xl">
                  {puesto === 'CAJERO' ? '💰' : '📦'}
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    ¡Bienvenido, {empleadoData?.nombre}!
                  </h2>
                  <p className="text-gray-600">
                    {puesto === 'CAJERO' ? 'Cajero' : 'Reponedor'} en {empleadoData?.supermercado_nombre}
                  </p>
                </div>
              </div>
              
              {/* Información del empleado */}
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm bg-gray-50 rounded-lg p-4">
                <div>
                  <span className="font-medium text-gray-700 block">Email</span>
                  <span className="text-gray-600">{empleadoData?.email}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700 block">DNI</span>
                  <span className="text-gray-600">{empleadoData?.dni}</span>
                </div>
                <div>
                  <span className="font-medium text-gray-700 block">Puesto</span>
                  <span className="text-gray-600">
                    {puesto === 'CAJERO' ? 'Cajero' : 'Reponedor'}
                  </span>
                </div>
                <div>
                  <span className="font-medium text-gray-700 block">Supermercado</span>
                  <span className="text-gray-600">{empleadoData?.supermercado_nombre}</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Acciones principales según el rol */}
          {puesto === 'REPONEDOR' ? (
            <div className="grid md:grid-cols-2 gap-6">
              {/* Productos */}
              <div 
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
                onClick={() => router.push('/productos')}
              >
                <div className="p-6 text-center">
                  <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">🛍️</span>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    Gestión de Productos
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Administra el catálogo de productos, categorías y precios
                  </p>
                  <div className="text-primary font-medium">
                    Ver Productos →
                  </div>
                </div>
              </div>

              {/* Inventario */}
              <div 
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
                onClick={() => router.push('/inventario')}
              >
                <div className="p-6 text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">📦</span>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    Control de Inventario
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Gestiona stock, depósitos y movimientos de inventario
                  </p>
                  <div className="text-primary font-medium">
                    Ver Inventario →
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Cajero - Ventas e Historial */
            <div className="grid md:grid-cols-2 gap-6">
              <div 
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
                onClick={() => router.push('/ventas')}
              >
                <div className="p-6 text-center">
                  <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">💰</span>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    Sistema de Ventas
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Procesa ventas y transacciones del supermercado
                  </p>
                  <div className="text-primary font-medium">
                    Ir a Ventas →
                  </div>
                </div>
              </div>

              <div 
                className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow cursor-pointer border border-gray-200"
                onClick={() => router.push('/ventas/historial')}
              >
                <div className="p-6 text-center">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <span className="text-3xl">📊</span>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">
                    Mis Ventas
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Consulta el historial de tus ventas realizadas
                  </p>
                  <div className="text-primary font-medium">
                    Ver Historial →
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Resumen rápido */}
          <Card>
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Tu Información de Trabajo
              </h3>
              <div className="text-center py-4">
                <p className="text-gray-600">
                  {puesto === 'CAJERO' 
                    ? 'Como cajero, tienes acceso al sistema de ventas para procesar transacciones y consultar tu historial de ventas realizadas.' 
                    : 'Como reponedor, puedes gestionar productos e inventario para mantener el supermercado abastecido.'
                  }
                </p>
              </div>
            </div>
          </Card>
        </div>
      </Container>
    </div>
  );
}