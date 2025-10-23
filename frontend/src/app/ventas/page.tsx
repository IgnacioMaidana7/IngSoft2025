"use client";
import React, { useState, useEffect, useMemo } from "react";
import { COLORS } from "@/constants/colors";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/feedback/ToastProvider";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import ProtectedRoute from "@/components/auth/ProtectedRoute";
import CameraModal from "@/components/CameraModal";
import { useAuth } from "@/context/AuthContext";
import {
	crearVenta,
	agregarProductoAVenta,
	actualizarItemVenta,
	eliminarItemVenta,
	finalizarVenta,
	cancelarVenta,
	obtenerProductosDisponibles,
	buscarProductos,
	descargarTicketPDF,
	reconocerProductosImagen,
	type Venta,
	type ProductoDisponible,
	type ProductoReconocido
} from "@/lib/api";

export default function VentasPage() {
	const [phoneNumber, setPhoneNumber] = useState("");
	const [ventaActual, setVentaActual] = useState<Venta | null>(null);
	const [productosDisponibles, setProductosDisponibles] = useState<ProductoDisponible[]>([]);
	const [busquedaProducto, setBusquedaProducto] = useState("");
	const [productosFiltrados, setProductosFiltrados] = useState<ProductoDisponible[]>([]);
	const [mostrarProductos, setMostrarProductos] = useState(false);
	const [cargando, setCargando] = useState(false);
	const [isModalVisible, setModalVisible] = useState(false);
	const [cantidadEditando, setCantidadEditando] = useState<{ [key: number]: number }>({});
	const [isCameraModalOpen, setIsCameraModalOpen] = useState(false);
	
	// Estados para reconocimiento de productos
	const [reconociendo, setReconociendo] = useState(false);
	const [productosDetectados, setProductosDetectados] = useState<ProductoReconocido[]>([]);
	const [mostrarProductosDetectados, setMostrarProductosDetectados] = useState(false);
	const [cantidadesDetectados, setCantidadesDetectados] = useState<{ [key: number]: number }>({});
	
	const { showToast } = useToast();
	const { token } = useAuth();

	const total = useMemo(() => {
		if (!ventaActual || !ventaActual.items) return 0;
		return ventaActual.items.reduce((sum, item) => {
			return sum + parseFloat(item.subtotal);
		}, 0);
	}, [ventaActual?.items]);

	// Cargar productos disponibles al inicializar
	useEffect(() => {
		if (token) {
			cargarProductosDisponibles();
		}
	}, [token]);

	// Filtrar productos cuando cambie la búsqueda
	useEffect(() => {
		if (busquedaProducto.trim().length >= 2) {
			buscarProductosEnTiempoReal();
		} else {
			setProductosFiltrados(productosDisponibles.slice(0, 10));
		}
	}, [busquedaProducto, productosDisponibles]);

	const cargarProductosDisponibles = async () => {
		if (!token) return;
		
		try {
			setCargando(true);
			const productos = await obtenerProductosDisponibles(token);
			setProductosDisponibles(productos);
			setProductosFiltrados(productos.slice(0, 10));
		} catch (error) {
			showToast("Error al cargar productos", "error");
			console.error(error);
		} finally {
			setCargando(false);
		}
	};

	const buscarProductosEnTiempoReal = async () => {
		if (!token || busquedaProducto.trim().length < 2) return;
		
		try {
			const productos = await buscarProductos(busquedaProducto.trim(), token);
			setProductosFiltrados(productos);
		} catch (error) {
			console.error("Error en búsqueda:", error);
		}
	};

	const iniciarNuevaVenta = async () => {
		if (!token) return;
		
		try {
			setCargando(true);
			const nuevaVenta = await crearVenta({}, token);
			setVentaActual(nuevaVenta);
			showToast("Nueva venta iniciada", "success");
		} catch (error) {
			showToast("Error al crear venta", "error");
			console.error(error);
		} finally {
			setCargando(false);
		}
	};

	const agregarProducto = async (producto: ProductoDisponible, cantidad: number = 1) => {
		if (!ventaActual || !token) {
			await iniciarNuevaVenta();
			return;
		}

		try {
			setCargando(true);
			const resultado = await agregarProductoAVenta(
				ventaActual.id,
				{ producto_id: producto.id, cantidad },
				token
			);
			setVentaActual(resultado.venta);
			setMostrarProductos(false);
			setBusquedaProducto("");
			showToast(`${producto.nombre} agregado al ticket`, "success");
		} catch (error: any) {
			showToast(error.message || "Error al agregar producto", "error");
			console.error(error);
		} finally {
			setCargando(false);
		}
	};

	const actualizarCantidadItem = async (itemId: number, nuevaCantidad: number) => {
		if (!ventaActual || !token || nuevaCantidad < 1) return;

		try {
			setCargando(true);
			const resultado = await actualizarItemVenta(
				ventaActual.id,
				{ item_id: itemId, cantidad: nuevaCantidad },
				token
			);
			setVentaActual(resultado.venta);
			setCantidadEditando(prev => ({ ...prev, [itemId]: nuevaCantidad }));
			showToast("Cantidad actualizada", "success");
		} catch (error: any) {
			showToast(error.message || "Error al actualizar cantidad", "error");
		} finally {
			setCargando(false);
		}
	};

	const eliminarItem = async (itemId: number) => {
		if (!ventaActual || !token) return;

		try {
			setCargando(true);
			const resultado = await eliminarItemVenta(ventaActual.id, itemId, token);
			setVentaActual(resultado.venta);
			showToast("Producto eliminado", "success");
		} catch (error: any) {
			showToast(error.message || "Error al eliminar producto", "error");
		} finally {
			setCargando(false);
		}
	};

	const finalizarVentaActual = async () => {
		if (!ventaActual || !token) return;

		try {
			setCargando(true);
			const resultado = await finalizarVenta(
				ventaActual.id,
				{
					cliente_telefono: phoneNumber || undefined,
					enviar_whatsapp: !!phoneNumber
				},
				token
			);
			
			showToast("¡Venta finalizada exitosamente!", "success");
			
			if (phoneNumber) {
				setModalVisible(true);
			} else {
				limpiarVenta();
			}
		} catch (error: any) {
			showToast(error.message || "Error al finalizar venta", "error");
		} finally {
			setCargando(false);
		}
	};

	const limpiarVenta = () => {
		setVentaActual(null);
		setPhoneNumber("");
		setBusquedaProducto("");
		setCantidadEditando({});
		setMostrarProductos(false);
	};

	const handlePhotoUploaded = async (resultadoReconocimiento: any) => {
		if (!token) {
			showToast("No hay sesión activa", "error");
			return;
		}
		
		try {
			setReconociendo(true);
			setIsCameraModalOpen(false);
			showToast("🔍 Procesando productos reconocidos...", "info");
			
			console.log("� Resultado del reconocimiento recibido:", resultadoReconocimiento);
			console.log("📡 Respuesta recibida:", resultadoReconocimiento);
			
			if (resultadoReconocimiento.success && resultadoReconocimiento.productos.length > 0) {
				// Filtrar solo productos que existen en la BD
				const productosValidos = resultadoReconocimiento.productos.filter(
					p => p.existe_en_bd && p.ingsoft_product_id
				);
				
				if (productosValidos.length === 0) {
					showToast(
						"No se detectaron productos registrados en el sistema",
						"info"
					);
					setReconociendo(false);
					return;
				}
				
				// Inicializar cantidades en 1 para cada producto detectado
				const cantidadesIniciales: { [key: number]: number } = {};
				productosValidos.forEach(producto => {
					if (producto.ingsoft_product_id) {
						cantidadesIniciales[producto.ingsoft_product_id] = 1;
					}
				});
				
				setProductosDetectados(productosValidos);
				setCantidadesDetectados(cantidadesIniciales);
				setMostrarProductosDetectados(true);
				
				showToast(
					`✅ Se detectaron ${productosValidos.length} producto(s)`,
					"success"
				);
			} else {
				showToast(
					resultadoReconocimiento.error || "No se detectaron productos en la imagen",
					"info"
				);
			}
		} catch (error: any) {
			console.error('❌ Error en reconocimiento de productos:');
			console.error('  - Mensaje:', error.message);
			console.error('  - Error completo:', error);
			
			// Intentar extraer más información del error
			let errorMessage = "Error al reconocer productos";
			
			if (error.message) {
				// Si el error viene de apiFetch, incluye el mensaje del servidor
				if (error.message.includes("HTTP 500")) {
					errorMessage = "Error del servidor al procesar la imagen. Verifica los logs del backend.";
				} else if (error.message.includes("HTTP 503") || error.message.includes("HTTP 504")) {
					errorMessage = "El servidor de reconocimiento no está disponible. Verifica que esté corriendo en puerto 8080.";
				} else if (error.message.includes("HTTP 400")) {
					errorMessage = "Error en los datos enviados. Verifica el formato de la imagen.";
				} else {
					errorMessage = error.message;
				}
			}
			
			showToast(errorMessage, "error");
		} finally {
			setReconociendo(false);
		}
	};

	const confirmarProductosDetectados = async () => {
		if (!ventaActual && token) {
			// Si no hay venta activa, crear una nueva
			await iniciarNuevaVenta();
		}
		
		if (!token) return;
		
		try {
			setCargando(true);
			let productosAgregados = 0;
			
			for (const productoDetectado of productosDetectados) {
				if (productoDetectado.ingsoft_product_id) {
					const cantidad = cantidadesDetectados[productoDetectado.ingsoft_product_id] || 1;
					
					// Buscar el producto en la lista de disponibles
					const productoDisponible = productosDisponibles.find(
						p => p.id === productoDetectado.ingsoft_product_id
					);
					
					if (productoDisponible && ventaActual) {
						try {
							const resultado = await agregarProductoAVenta(
								ventaActual.id,
								{ 
									producto_id: productoDetectado.ingsoft_product_id, 
									cantidad 
								},
								token
							);
							setVentaActual(resultado.venta);
							productosAgregados++;
						} catch (error) {
							console.error(`Error agregando ${productoDetectado.nombre_db}:`, error);
						}
					}
				}
			}
			
			if (productosAgregados > 0) {
				showToast(
					`${productosAgregados} producto(s) agregado(s) al ticket`,
					"success"
				);
			}
			
			// Limpiar estado de detección
			setMostrarProductosDetectados(false);
			setProductosDetectados([]);
			setCantidadesDetectados({});
		} catch (error: any) {
			showToast(error.message || "Error al agregar productos", "error");
		} finally {
			setCargando(false);
		}
	};

	const cancelarProductosDetectados = () => {
		setMostrarProductosDetectados(false);
		setProductosDetectados([]);
		setCantidadesDetectados({});
		showToast("Detección cancelada", "info");
	};

	const actualizarCantidadDetectado = (productoId: number, nuevaCantidad: number) => {
		if (nuevaCantidad < 1) return;
		setCantidadesDetectados(prev => ({
			...prev,
			[productoId]: nuevaCantidad
		}));
	};

	const enviarWhatsApp = () => {
		if (phoneNumber && ventaActual) {
			const mensaje = encodeURIComponent(
				`🧾 Ticket de Venta\n` +
				`Número: ${ventaActual.numero_venta}\n` +
				`Total: $${ventaActual.total}\n` +
				`¡Gracias por tu compra!`
			);
			window.open(`https://wa.me/${phoneNumber}?text=${mensaje}`, "_blank");
		}
		setModalVisible(false);
		limpiarVenta();
	};

	const descargarPDF = async () => {
		if (!ventaActual || !token) return;
		
		try {
			await descargarTicketPDF(ventaActual.id, token);
			showToast("PDF descargado exitosamente", "success");
		} catch (error) {
			showToast("Error al descargar PDF", "error");
			console.error(error);
		}
	};

	return (
		<ProtectedRoute>
			<Container>
				<Card>
					{/* Header con información del sistema */}
					<div className="px-4 py-3 border-b border-border">
						<h1 className="text-xl font-bold text-center">Sistema de Ventas</h1>
						<p className="text-sm text-gray-600 text-center">
							Terminal de Cajero
						</p>
						{ventaActual && (
							<p className="text-sm text-blue-600 text-center">
								Venta #{ventaActual.numero_venta} - Estado: {ventaActual.estado}
							</p>
						)}
					</div>

					{/* Campo teléfono del cliente */}
					<div className="p-4">
						<div className="flex items-center gap-2 border border-border rounded-xl bg-white px-3 py-2">
							<span className="text-green-600 font-extrabold">📱</span>
							<input 
								className="flex-1 py-1.5 outline-none border-0" 
								placeholder="N° de celular del cliente (opcional)" 
								value={phoneNumber} 
								onChange={(e) => setPhoneNumber(e.target.value)}
								type="tel"
							/>
						</div>
					</div>

					{/* Búsqueda y selección de productos */}
					<div className="px-4">
						<div className="mb-3">
							<div className="flex gap-2">
								<input
									className="flex-1 px-3 py-2 border border-border rounded-lg"
									placeholder="Buscar productos..."
									value={busquedaProducto}
									onChange={(e) => setBusquedaProducto(e.target.value)}
									onFocus={() => setMostrarProductos(true)}
								/>
								<Button 
									onClick={() => setIsCameraModalOpen(true)}
									variant="secondary"
									title="Capturar productos con cámara"
									disabled={reconociendo || cargando}
									className="min-w-[48px]"
								>
									📸
								</Button>
								<Button 
									onClick={() => setMostrarProductos(!mostrarProductos)}
									variant="secondary"
								>
									{mostrarProductos ? "Ocultar" : "Mostrar"}
								</Button>
							</div>							{/* Lista de productos */}
							{mostrarProductos && (
								<div className="mt-2 border border-border rounded-lg max-h-60 overflow-y-auto bg-white">
									{cargando ? (
										<div className="p-4 text-center">Cargando productos...</div>
									) : productosFiltrados.length > 0 ? (
										productosFiltrados.map((producto) => (
											<div key={producto.id} className="p-3 border-b border-border hover:bg-gray-50 flex justify-between items-center">
												<div className="flex-1">
													<div className="font-medium">{producto.nombre}</div>
													<div className="text-sm text-gray-600">
														{producto.categoria} • ${producto.precio}
													</div>
													<div className="text-xs text-blue-600">
														Stock: {producto.stock_disponible}
													</div>
												</div>
												<Button
													size="sm"
													onClick={() => agregarProducto(producto)}
													disabled={producto.stock_disponible === 0}
												>
													Agregar
												</Button>
											</div>
										))
									) : (
										<div className="p-4 text-center text-gray-500">
											{busquedaProducto ? "No se encontraron productos" : "No hay productos disponibles"}
										</div>
									)}
								</div>
							)}
						</div>
					</div>

					{/* Ticket de venta */}
					<div className="px-4">
						<h2 className="text-center my-3 font-bold text-lg">Ticket de Venta</h2>
						
						{ventaActual && ventaActual.items.length > 0 ? (
							<div className="space-y-2">
								{ventaActual.items.map((item) => (
									<div key={item.id} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
										<div className="flex-1">
											<div className="font-medium">{item.producto_nombre}</div>
											<div className="text-sm text-gray-600">
												{item.precio_original ? (
													<>
														<span className="line-through text-gray-400 mr-2">
															${item.precio_original}
														</span>
														<span className="text-green-600 font-semibold">
															${item.precio_unitario} c/u
														</span>
														{item.oferta_nombre && (
															<div className="text-xs text-green-600 mt-1">
																🎉 {item.oferta_nombre}
															</div>
														)}
													</>
												) : (
													<span>${item.precio_unitario} c/u</span>
												)}
											</div>
										</div>
										
										{/* Controles de cantidad */}
										<div className="flex items-center gap-2">
											<button
												className="w-8 h-8 rounded-full bg-red-100 text-red-600 flex items-center justify-center text-sm"
												onClick={() => actualizarCantidadItem(item.id, item.cantidad - 1)}
												disabled={cargando}
											>
												-
											</button>
											<span className="w-8 text-center font-medium">
												{cantidadEditando[item.id] ?? item.cantidad}
											</span>
											<button
												className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-sm"
												onClick={() => actualizarCantidadItem(item.id, item.cantidad + 1)}
												disabled={cargando}
											>
												+
											</button>
										</div>

										<div className="ml-4 text-right">
											<div className="font-bold">${item.subtotal}</div>
											<button 
												onClick={() => eliminarItem(item.id)}
												className="text-red-600 text-xs hover:underline"
												disabled={cargando}
											>
												Eliminar
											</button>
										</div>
									</div>
								))}
								
								{/* Total */}
								<div className="flex justify-between mt-4 pt-3 border-t-2 border-primary">
									<div className="font-bold text-lg">Total</div>
									<div className="font-bold text-lg text-primary">${total.toFixed(2)}</div>
								</div>
							</div>
						) : (
							<div className="text-center py-8 text-gray-500">
								<p>No hay productos en el ticket</p>
								<p className="text-sm">Busca y agrega productos para comenzar</p>
							</div>
						)}
					</div>

					{/* Acciones */}
					<div className="p-4 border-t border-border space-y-3">
						{!ventaActual ? (
							<Button 
								onClick={iniciarNuevaVenta} 
								disabled={cargando}
								className="w-full"
							>
								{cargando ? "Iniciando..." : "Iniciar Nueva Venta"}
							</Button>
						) : (
							<>
								<Button 
									onClick={finalizarVentaActual} 
									disabled={cargando || !ventaActual.items.length}
									className="w-full"
								>
									{cargando ? "Procesando..." : "Finalizar Venta"}
								</Button>
								
								{/* Mostrar botón de PDF solo si la venta está completada */}
								{ventaActual.estado === 'COMPLETADA' && (
									<Button 
										onClick={descargarPDF} 
										variant="secondary"
										className="w-full"
									>
										📄 Descargar PDF
									</Button>
								)}
								
								<Button 
									onClick={limpiarVenta} 
									variant="secondary"
									className="w-full"
								>
									{ventaActual.estado === 'COMPLETADA' ? 'Nueva Venta' : 'Cancelar Venta'}
								</Button>
							</>
						)}
					</div>
				</Card>
			</Container>

			{/* Modal WhatsApp */}
			{isModalVisible && (
				<div className="fixed inset-0 bg-black/50 grid place-items-center z-50">
					<div className="bg-white rounded-2xl p-6 w-[360px] max-w-[90%] border border-border shadow-lg">
						<h3 className="mt-0 font-bold text-lg mb-4">¡Venta Completada!</h3>
						<p className="mb-4">
							¿Desea enviar el ticket al número {phoneNumber} por WhatsApp?
						</p>
						
						{/* Botón para descargar PDF */}
						<div className="mb-4">
							<Button 
								onClick={descargarPDF} 
								variant="secondary"
								className="w-full"
							>
								📄 Descargar Ticket PDF
							</Button>
						</div>
						
						<div className="flex gap-3 justify-end">
							<Button 
								variant="secondary" 
								onClick={() => {
									setModalVisible(false);
									limpiarVenta();
								}}
							>
								No, solo guardar
							</Button>
							<Button onClick={enviarWhatsApp}>
								Sí, enviar por WhatsApp
							</Button>
						</div>
					</div>
				</div>
			)}

			{/* Modal de Cámara */}
			<CameraModal 
				isOpen={isCameraModalOpen}
				onClose={() => setIsCameraModalOpen(false)}
				onPhotoCapture={handlePhotoUploaded}
			/>

			{/* Modal de Reconocimiento en Proceso */}
			{reconociendo && (
				<div className="fixed inset-0 bg-black/70 grid place-items-center z-50">
					<div className="bg-white rounded-2xl p-8 w-[360px] max-w-[90%] text-center">
						<div className="mb-4">
							<div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto"></div>
						</div>
						<h3 className="font-bold text-lg mb-2">Analizando imagen...</h3>
						<p className="text-gray-600">
							Detectando productos en la fotografía
						</p>
					</div>
				</div>
			)}

			{/* Modal de Productos Detectados */}
			{mostrarProductosDetectados && (
				<div className="fixed inset-0 bg-black/50 grid place-items-center z-50 p-4 overflow-y-auto">
					<div className="bg-white rounded-2xl p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
						<h3 className="font-bold text-xl mb-4 text-center">
							🎯 Productos Detectados
						</h3>
						<p className="text-center text-gray-600 mb-4">
							Se detectaron {productosDetectados.length} producto(s). 
							Ajusta las cantidades y confirma para agregarlos al ticket.
						</p>

						<div className="space-y-3 mb-6">
							{productosDetectados.map((producto) => {
								const productoId = producto.ingsoft_product_id!;
								const cantidad = cantidadesDetectados[productoId] || 1;
								
								return (
									<div key={productoId} className="border border-gray-200 rounded-lg p-4 bg-gray-50">
										<div className="flex items-start justify-between mb-3">
											<div className="flex-1">
												<div className="font-bold text-lg">{producto.nombre_db}</div>
												<div className="text-sm text-gray-600">
													{producto.categoria_db}
												</div>
												<div className="text-sm font-semibold text-green-600 mt-1">
													Precio: ${producto.precio_db}
												</div>
												{producto.stock_disponible !== undefined && (
													<div className={`text-xs mt-1 ${
														producto.stock_bajo ? 'text-orange-600' : 'text-blue-600'
													}`}>
														Stock disponible: {producto.stock_disponible} unidades
														{producto.stock_bajo && ' (⚠️ Stock bajo)'}
													</div>
												)}
											</div>
											
											<div className="ml-4">
												<div className="text-xs text-gray-500 mb-1">Confianza</div>
												<div className="text-sm font-medium">
													{Math.round(producto.classification_confidence * 100)}%
												</div>
											</div>
										</div>

										{/* Control de cantidad */}
										<div className="flex items-center justify-between bg-white rounded-lg p-2 border border-gray-300">
											<span className="text-sm font-medium">Cantidad:</span>
											<div className="flex items-center gap-3">
												<button
													className="w-8 h-8 rounded-full bg-red-100 text-red-600 flex items-center justify-center font-bold hover:bg-red-200 transition-colors"
													onClick={() => actualizarCantidadDetectado(productoId, cantidad - 1)}
												>
													-
												</button>
												<span className="w-12 text-center font-bold text-lg">
													{cantidad}
												</span>
												<button
													className="w-8 h-8 rounded-full bg-green-100 text-green-600 flex items-center justify-center font-bold hover:bg-green-200 transition-colors"
													onClick={() => actualizarCantidadDetectado(productoId, cantidad + 1)}
													disabled={producto.stock_disponible !== undefined && cantidad >= producto.stock_disponible}
												>
													+
												</button>
											</div>
										</div>

										{/* Subtotal */}
										<div className="mt-2 text-right">
											<span className="text-sm text-gray-600">Subtotal: </span>
											<span className="font-bold text-lg text-primary">
												${(parseFloat(producto.precio_db || '0') * cantidad).toFixed(2)}
											</span>
										</div>
									</div>
								);
							})}
						</div>

						{/* Total de productos detectados */}
						<div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
							<div className="flex justify-between items-center">
								<span className="font-semibold text-lg">Total a agregar:</span>
								<span className="font-bold text-2xl text-primary">
									${productosDetectados.reduce((sum, p) => {
										const cantidad = cantidadesDetectados[p.ingsoft_product_id!] || 1;
										return sum + (parseFloat(p.precio_db || '0') * cantidad);
									}, 0).toFixed(2)}
								</span>
							</div>
						</div>

						{/* Botones de acción */}
						<div className="flex gap-3">
							<Button 
								variant="secondary" 
								onClick={cancelarProductosDetectados}
								className="flex-1"
								disabled={cargando}
							>
								Cancelar
							</Button>
							<Button 
								onClick={confirmarProductosDetectados}
								className="flex-1"
								disabled={cargando}
							>
								{cargando ? "Agregando..." : "Confirmar y Agregar"}
							</Button>
						</div>
					</div>
				</div>
			)}
		</ProtectedRoute>
	);
}
