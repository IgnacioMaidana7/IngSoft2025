"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import { registerSupermercado } from "@/lib/api";

export default function RegisterPage() {
	const router = useRouter();
	const [username, setUsername] = useState("");
	const [nombreSuper, setNombreSuper] = useState("");
	const [cuil, setCuil] = useState("");
	const [provincia, setProvincia] = useState<string | null>(null);
	const [localidad, setLocalidad] = useState<string | null>(null);
	const [email, setEmail] = useState("");
	const [password, setPassword] = useState("");
	const [confirmPassword, setConfirmPassword] = useState("");
	const [logo, setLogo] = useState<File | null>(null);
	const [provincias, setProvincias] = useState<{ label: string; value: string }[]>([]);
	const [localidades, setLocalidades] = useState<{ label: string; value: string }[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState("");

	useEffect(() => {
		(async () => {
			try {
				const res = await fetch('https://apis.datos.gob.ar/georef/api/provincias?campos=id,nombre');
                const data: { provincias: { id: string; nombre: string }[] } = await res.json();
                setProvincias(
                    data.provincias
                        .map((p: { id: string; nombre: string }) => ({ label: p.nombre, value: String(p.id) }))
                        .sort((a: { label: string; value: string }, b: { label: string; value: string }) => a.label.localeCompare(b.label))
                );
			} catch {}
		})();
	}, []);

	useEffect(() => {
		if (!provincia) return;
		(async () => {
			try {
				const res = await fetch(`https://apis.datos.gob.ar/georef/api/localidades?provincia=${provincia}&campos=id,nombre&max=1000`);
                const data: { localidades: { id: string; nombre: string }[] } = await res.json();
                
                // Eliminar duplicados usando Set para nombres únicos
                const uniqueLocalidades = Array.from(
                    new Map(
                        data.localidades.map((l: { id: string; nombre: string }) => [l.nombre, l])
                    ).values()
                );
                
                setLocalidades(
                    uniqueLocalidades
                        .map((l: { id: string; nombre: string }) => ({ label: l.nombre, value: String(l.nombre) }))
                        .sort((a: { label: string; value: string }, b: { label: string; value: string }) => a.label.localeCompare(b.label))
                );
			} catch {
				console.error('Error al cargar localidades');
				setLocalidades([]);
			}
		})();
	}, [provincia]);

	const onSubmit = async (e: React.FormEvent) => {
		e.preventDefault();
		setError("");
		
		// Validación de campos obligatorios
		if (!username.trim()) {
			setError('El nombre de usuario es obligatorio');
			return;
		}
		
		if (!nombreSuper.trim()) {
			setError('El nombre del supermercado es obligatorio');
			return;
		}
		
		if (!cuil.trim()) {
			setError('El CUIL es obligatorio');
			return;
		}
		
		// Validación de formato de CUIL (debe tener exactamente 11 dígitos)
		const cuilClean = cuil.replace(/[-\s]/g, '');
		if (!/^\d{11}$/.test(cuilClean)) {
			setError('El CUIL debe tener exactamente 11 dígitos');
			return;
		}
		
		if (!provincia) {
			setError('Debe seleccionar una provincia');
			return;
		}
		
		if (!localidad) {
			setError('Debe seleccionar una localidad');
			return;
		}
		
		if (!email.trim()) {
			setError('El email es obligatorio');
			return;
		}
		
		// Validación de formato de email
		const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
		if (!emailRegex.test(email)) {
			setError('Por favor ingrese un email válido');
			return;
		}
		
		if (!password) {
			setError('La contraseña es obligatoria');
			return;
		}
		
		if (password.length < 8) {
			setError('La contraseña debe tener al menos 8 caracteres');
			return;
		}
		
		// Validación de complejidad de contraseña
		const hasNumber = /\d/.test(password);
		const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
		
		if (!hasNumber) {
			setError('La contraseña debe contener al menos un número');
			return;
		}
		
		if (!hasSpecialChar) {
			setError('La contraseña debe contener al menos un carácter especial');
			return;
		}
		
		if (!confirmPassword) {
			setError('Debe confirmar la contraseña');
			return;
		}
		
		if (password !== confirmPassword) {
			setError('Las contraseñas no coinciden');
			return;
		}
		
		// Validación de logo
		if (logo && logo.size > 1024 * 1024) { // 1MB
			setError('El logo no puede ser mayor a 1MB');
			return;
		}
		
		if (logo && !['image/jpeg', 'image/jpg'].includes(logo.type)) {
			setError('El logo debe ser un archivo JPG');
			return;
		}
		
		setLoading(true);
		try {
			const data = {
				username,
				password,
				nombre_supermercado: nombreSuper,
				cuil: cuil.replace(/[-\s]/g, ''), // Eliminar guiones y espacios del CUIL
				email,
				provincia: provincias.find(p => p.value === provincia)?.label || '',
				localidad,
				...(logo && { logo })
			};
			
			await registerSupermercado(data);
			
			alert('¡Registro exitoso! Ahora puedes iniciar sesión con tu cuenta.');
			router.push('/login');
		} catch (error: unknown) {
			console.error('Error en registro:', error);
			const errorMessage = error instanceof Error ? error.message : 'Error al crear la cuenta. Por favor intenta nuevamente.';
			setError(errorMessage);
		} finally {
			setLoading(false);
		}
	};

    return (
        <div className="min-h-screen grid place-items-center px-4">
            <div className="w-full max-w-[560px]">
                <div className="bg-white/80 border border-border rounded-2xl p-1.5 shadow-soft backdrop-blur">
                    <div className="grid grid-cols-2 gap-1.5">
                        <button className="py-2 rounded-xl font-semibold text-primary bg-primary/10">Registro</button>
                        <Link href="/login" className="py-2 rounded-xl font-semibold text-text hover:bg-primary/10 text-center">Iniciar sesión</Link>
                    </div>
                </div>
                <form onSubmit={onSubmit} className="bg-white/90 border border-border rounded-2xl p-6 shadow-soft animate-pop backdrop-blur mt-3">
                    <h1 className="m-0 mb-4 text-center text-2xl font-extrabold tracking-tight">Crear una cuenta</h1>
                    
                    {error && (
                        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
                            {error}
                        </div>
                    )}
                    
                    <Input 
                        label="Nombre de usuario" 
                        value={username} 
                        onChange={(e) => setUsername(e.target.value)} 
                        placeholder="Ej: supermercado123"
                        helper="Será usado para iniciar sesión"
                    />
                    <Input 
                        label="Nombre del supermercado" 
                        value={nombreSuper} 
                        onChange={(e) => setNombreSuper(e.target.value)} 
                        placeholder="Ej: Supermercado San Martín"
                    />
                    <Input 
                        label="CUIL" 
                        value={cuil} 
                        onChange={(e) => setCuil(e.target.value)} 
                        placeholder="20-12345678-9"
                        helper="11 dígitos, puede incluir guiones"
                    />
                    <label className="block mt-3 mb-1 text-sm text-text font-medium">Provincia</label>
                    <select 
                        className="w-full px-4 py-3 border border-border rounded-xl outline-none focus:ring-2 focus:ring-primary/40 bg-white" 
                        value={provincia ?? ''} 
                        onChange={(e) => setProvincia(e.target.value || null)}
                    >
                        <option value="">Selecciona una provincia</option>
                        {provincias.map((p) => <option key={p.value} value={p.value}>{p.label}</option>)}
                    </select>
                    <label className="block mt-3 mb-1 text-sm text-text font-medium">Localidad</label>
                    <select 
                        className="w-full px-4 py-3 border border-border rounded-xl outline-none focus:ring-2 focus:ring-primary/40 bg-white" 
                        value={localidad ?? ''} 
                        onChange={(e) => setLocalidad(e.target.value || null)}
                        disabled={!provincia}
                    >
                        <option value="">Selecciona una localidad</option>
                        {localidades.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
                    </select>
                    <Input 
                        label="E-mail" 
                        value={email} 
                        onChange={(e) => setEmail(e.target.value)} 
                        type="email" 
                        placeholder="tu@correo.com"
                    />
                    <Input 
                        label="Contraseña" 
                        value={password} 
                        onChange={(e) => setPassword(e.target.value)} 
                        type="password" 
                        placeholder="Mínimo 8 caracteres"
                        helper="Debe incluir al menos un número y un carácter especial"
                    />
                    <Input 
                        label="Confirmar contraseña" 
                        value={confirmPassword} 
                        onChange={(e) => setConfirmPassword(e.target.value)} 
                        type="password" 
                        placeholder="Confirma tu contraseña"
                        error={confirmPassword && password !== confirmPassword ? "Las contraseñas no coinciden" : undefined}
                    />
                    
                    <label className="block mt-3 mb-1 text-sm text-text font-medium">Logo del supermercado (opcional)</label>
                    <input
                        type="file"
                        accept=".jpg,.jpeg"
                        onChange={(e) => setLogo(e.target.files?.[0] || null)}
                        className="w-full px-4 py-3 border border-border rounded-xl outline-none focus:ring-2 focus:ring-primary/40 bg-white file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
                    />
                    <p className="text-xs text-gray-500 mt-1">Solo archivos JPG, máximo 1MB</p>
                    
                    <Button className="mt-4 w-full" type="submit" disabled={loading || !username || !nombreSuper || !cuil || !provincia || !localidad || !email || !password || !confirmPassword}>
                        {loading ? 'Creando cuenta...' : 'Registrarse'}
                    </Button>
                    <div className="text-center mt-2.5">
                        <Link href="/login" className="text-primary font-semibold hover:text-primary/80 transition-colors">
                            Ya tengo cuenta
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
}
