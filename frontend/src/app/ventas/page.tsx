"use client";
import React, { useMemo, useState } from "react";
import { COLORS } from "@/constants/colors";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/feedback/ToastProvider";
import Link from "next/link";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import ProtectedRoute from "@/components/auth/ProtectedRoute";

type TicketItem = { id: string; name: string; quantity: number; price: number };

const initialTicketItems: TicketItem[] = [];

export default function VentasPage() {
	const [phoneNumber, setPhoneNumber] = useState("");
	const [ticketItems, setTicketItems] = useState<TicketItem[]>(initialTicketItems);
	const [isModalVisible, setModalVisible] = useState(false);
    const { showToast } = useToast();

	const total = useMemo(() => ticketItems.reduce((sum, i) => sum + i.price, 0), [ticketItems]);

	function handleDeleteItem(id: string) {
		setTicketItems((prev) => prev.filter((i) => i.id !== id));
	}

	function handleSaveTicket() {
		console.log("Ticket guardado:", { items: ticketItems, total });
		if (phoneNumber) setModalVisible(true);
		else {
			showToast("Ticket guardado correctamente", "success");
			setTicketItems([]);
		}
	}

	function addProduct(product: { id: string; name: string; price: number }) {
		setTicketItems((prev) => {
			const existing = prev.find((p) => p.id === product.id);
			if (existing) {
				return prev.map((p) =>
					p.id === product.id
						? { ...p, quantity: p.quantity + 1, price: p.price + product.price }
						: p
				);
			}
			return [...prev, { ...product, quantity: 1 }];
		});
	}

	return (
		<ProtectedRoute>
			<Container>
				<Card>
				<div>
					<div className="flex items-center gap-2 border border-border rounded-xl bg-white px-3 py-2">
						<span className="text-green-600 font-extrabold">WA</span>
						<input className="flex-1 py-1.5 outline-none border-0" placeholder="N° de celular del cliente" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} />
					</div>
				</div>

				<div className="px-[15px]">
					<h2 className="text-center my-2.5 font-bold">Ticket de Venta</h2>
					{ticketItems.map((item) => (
						<div key={item.id} className="flex justify-between border-b border-border py-2.5">
							<div>{item.name} (x{item.quantity})</div>
							<div className="font-bold">${item.price}</div>
							<button onClick={() => handleDeleteItem(item.id)} className="text-red-600">Eliminar</button>
						</div>
					))}
					<div className="flex justify-between mt-3 pt-3 border-t-2" style={{ borderColor: COLORS.primary }}>
						<div className="font-bold">Total</div>
						<div className="font-bold text-primary">${total}</div>
					</div>
				</div>

				<div className="p-[15px] border-t border-border grid gap-2.5">
					<Button onClick={() => addProduct({ id: Math.random().toString(), name: "Producto demo", price: 1000 })}>Agregar Producto</Button>
					<Button onClick={handleSaveTicket}>Salvar Ticket</Button>
					<Link href="/camera"><Button>Tomar foto</Button></Link>
				</div>
				</Card>
			</Container>
			{isModalVisible && (
					<div className="fixed inset-0 bg-black/50 grid place-items-center">
						<div className="bg-white rounded-2xl p-6 w-[360px] max-w-[90%] border border-border shadow-soft">
							<h3 className="mt-0 font-bold text-lg">Enviar Ticket</h3>
							<p>¿Desea enviar el ticket al número {phoneNumber} por WhatsApp?</p>
							<div className="flex gap-3 justify-end mt-4">
								<Button variant="secondary" onClick={() => setModalVisible(false)}>No, sólo guardar</Button>
								<Button onClick={() => { const msg = encodeURIComponent(`Gracias por tu compra! Total: $${total}`); window.open(`https://wa.me/${phoneNumber}?text=${msg}`, "_blank"); setModalVisible(false); setTicketItems([]); }}>Sí, enviar</Button>
							</div>
						</div>
					</div>
				)}
		</ProtectedRoute>
	);
}
