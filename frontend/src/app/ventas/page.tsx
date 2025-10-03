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
	type Venta,
	type ProductoDisponible
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

	const handlePhotoUploaded = (result: { id: string; url: string }) => {
		// La foto ha sido guardada exitosamente
		// Por ahora solo mostramos un mensaje, más adelante aquí se implementará
		// la lógica de reconocimiento de productos
		console.log('Foto guardada:', result);
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
												${item.precio_unitario} c/u
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
				onPhotoUploaded={handlePhotoUploaded}
			/>
		</ProtectedRoute>
	);
}
