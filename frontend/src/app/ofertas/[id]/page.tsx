'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Button from '@/components/ui/Button'
import ProtectedRoute from '@/components/auth/ProtectedRoute'
import { useAuth } from '@/context/AuthContext'
import { obtenerOferta, obtenerProductosDeOferta, quitarProductosDeOferta } from '@/lib/api'
import { Oferta, ProductoOferta } from '@/lib/api'

interface DetalleOfertaPageProps {
  params: {
    id: string
  }
}

// Componentes simples para reemplazar shadcn/ui
const Card = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`bg-white border border-gray-200 rounded-lg shadow-sm ${className}`}>
    {children}
  </div>
)

const CardHeader = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`p-6 pb-4 ${className}`}>
    {children}
  </div>
)

const CardTitle = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <h3 className={`font-semibold ${className}`}>
    {children}
  </h3>
)

const CardContent = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => (
  <div className={`p-6 pt-0 ${className}`}>
    {children}
  </div>
)

const Badge = ({ children, className = '', variant = 'default' }: { 
  children: React.ReactNode; 
  className?: string; 
  variant?: 'default' | 'outline' 
}) => (
  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
    variant === 'outline' 
      ? 'bg-gray-100 text-gray-800 border border-gray-300' 
      : 'bg-blue-100 text-blue-800'
  } ${className}`}>
    {children}
  </span>
)

export default function DetalleOfertaPage({ params }: DetalleOfertaPageProps) {
  const router = useRouter()
  const { token } = useAuth()
  const [oferta, setOferta] = useState<Oferta | null>(null)
  const [productos, setProductos] = useState<ProductoOferta[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      cargarDatos()
    }
  }, [params.id, token])

  const cargarDatos = async () => {
    if (!token) return
    
    try {
      const [ofertaData, productosData] = await Promise.all([
        obtenerOferta(parseInt(params.id), token),
        obtenerProductosDeOferta(parseInt(params.id), token)
      ])
      setOferta(ofertaData)
      setProductos(productosData)
    } catch (error) {
      console.error('Error al cargar datos:', error)
      alert('Error al cargar los datos de la oferta')
    } finally {
      setLoading(false)
    }
  }

  const manejarQuitarProducto = async (productoId: number) => {
    if (!token) return
    
    try {
      await quitarProductosDeOferta(parseInt(params.id), [productoId], token)
      alert('Producto removido de la oferta')
      cargarDatos() // Recargar datos
    } catch (error) {
      console.error('Error al quitar producto:', error)
      alert('Error al quitar el producto de la oferta')
    }
  }

  const formatearFecha = (fecha: string) => {
    return new Date(fecha).toLocaleDateString('es-AR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const obtenerEstadoOferta = (oferta: Oferta) => {
    const hoy = new Date()
    const fechaInicio = new Date(oferta.fecha_inicio)
    const fechaFin = new Date(oferta.fecha_fin)

    if (hoy < fechaInicio) {
      return { texto: 'Próxima', color: 'bg-blue-100 text-blue-800' }
    } else if (hoy > fechaFin) {
      return { texto: 'Expirada', color: 'bg-red-100 text-red-800' }
    } else {
      return { texto: 'Activa', color: 'bg-green-100 text-green-800' }
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-6xl mx-auto">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-300 rounded mb-4"></div>
            <div className="h-4 bg-gray-300 rounded mb-2"></div>
            <div className="h-4 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  if (!oferta) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center">
            <h1 className="text-2xl font-bold text-text mb-4">Oferta no encontrada</h1>
            <Button onClick={() => router.back()}>Volver</Button>
          </div>
        </div>
      </div>
    )
  }

  const estado = obtenerEstadoOferta(oferta)

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-6xl mx-auto space-y-6">
        {/* Header con botones */}
        <div className="flex justify-between items-center">
          <Button 
            variant="outline" 
            onClick={() => router.back()}
          >
            ← Volver
          </Button>
          <div className="flex gap-2">
            <Button 
              variant="secondary"
              onClick={() => router.push(`/ofertas/${params.id}/editar`)}
            >
              Editar Oferta
            </Button>
            <Button onClick={() => router.push('/ofertas/productos')}>
              Gestionar Productos
            </Button>
          </div>
        </div>

        {/* Información de la oferta */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="text-2xl">{oferta.nombre}</CardTitle>
                {oferta.descripcion && (
                  <p className="text-muted-foreground mt-2">{oferta.descripcion}</p>
                )}
              </div>
              <Badge className={estado.color}>
                {estado.texto}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-semibold mb-2">Detalles de la Oferta</h3>
                <div className="space-y-2">
                  <div>
                    <span className="font-medium">Descuento:</span>
                    <span className="ml-2">
                      {oferta.valor_descuento}{oferta.tipo_descuento === 'porcentaje' ? '%' : '$'}
                    </span>
                  </div>
                  <div>
                    <span className="font-medium">Fecha de inicio:</span>
                    <span className="ml-2">{formatearFecha(oferta.fecha_inicio)}</span>
                  </div>
                  <div>
                    <span className="font-medium">Fecha de fin:</span>
                    <span className="ml-2">{formatearFecha(oferta.fecha_fin)}</span>
                  </div>
                  <div>
                    <span className="font-medium">Activa:</span>
                    <span className="ml-2">{oferta.activo ? 'Sí' : 'No'}</span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="font-semibold mb-2">Estadísticas</h3>
                <div className="space-y-2">
                  <div>
                    <span className="font-medium">Productos asociados:</span>
                    <span className="ml-2">{productos.length}</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Lista de productos asociados */}
        <Card>
          <CardHeader>
            <CardTitle>Productos Asociados ({productos.length})</CardTitle>
          </CardHeader>
          <CardContent>
            {productos.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-muted-foreground mb-4">
                  No hay productos asociados a esta oferta
                </p>
                <Button onClick={() => router.push('/ofertas/productos')}>
                  Agregar Productos
                </Button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left py-2">Producto</th>
                      <th className="text-left py-2">Categoría</th>
                      <th className="text-right py-2">Precio Original</th>
                      <th className="text-right py-2">Precio con Descuento</th>
                      <th className="text-right py-2">Descuento</th>
                      <th className="text-center py-2">Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {productos.map((producto) => (
                      <tr key={producto.id} className="border-b">
                        <td className="py-3">
                          <div>
                            <div className="font-medium">{producto.producto_nombre}</div>
                          </div>
                        </td>
                        <td className="py-3">
                          <Badge variant="outline">
                            {producto.producto_categoria}
                          </Badge>
                        </td>
                        <td className="py-3 text-right font-mono">
                          ${parseFloat(producto.precio_original).toFixed(2)}
                        </td>
                        <td className="py-3 text-right font-mono text-green-600">
                          ${parseFloat(producto.precio_con_descuento).toFixed(2)}
                        </td>
                        <td className="py-3 text-right">
                          <Badge className="bg-red-100 text-red-800">
                            -{producto.porcentaje_descuento}%
                          </Badge>
                        </td>
                        <td className="py-3 text-center">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => manejarQuitarProducto(producto.producto)}
                            className="text-red-600 hover:text-red-700"
                          >
                            Quitar
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
        </div>
      </div>
    </ProtectedRoute>
  )
}