"use client";
import React, { useState } from "react";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Checkbox from "@/components/ui/Checkbox";
import { COLORS } from "@/constants/colors";
import { useRouter } from "next/navigation";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";
import { useToast } from "@/components/feedback/ToastProvider";

export default function NuevoEmpleadoPage() {
  const router = useRouter();
  const { showToast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rol, setRol] = useState<string | null>(null);
  const [depositos, setDepositos] = useState({ principal: false, secundario: false, depositoFrio: false });

  return (
    <Container>
      <Card>
        <h1 className="mb-2.5">Registrar Empleado</h1>
        <div style={{ maxWidth: 520 }}>
          <Input label="Email" value={email} onChange={(e) => setEmail(e.target.value)} type="email" />
          <Input label="Contraseña" value={password} onChange={(e) => setPassword(e.target.value)} type="password" />

          <div style={{ marginBottom: 12 }}>
            <label style={{ display: "block", marginBottom: 6, color: COLORS.text }}>Rol</label>
            <select value={rol ?? ""} onChange={(e) => setRol(e.target.value || null)} style={{ padding: 12, borderRadius: 12, border: `1px solid ${COLORS.border}`, width: "100%" }}>
              <option value="">Selecciona un rol</option>
              <option value="cajero">Cajero</option>
              <option value="reponedor">Reponedor</option>
            </select>
          </div>

          <div style={{ margin: "10px 0 20px" }}>
            <label style={{ display: "block", marginBottom: 6, color: COLORS.text }}>Depósitos Asignados</label>
            <Checkbox label="Principal" checked={depositos.principal} onChange={(v) => setDepositos({ ...depositos, principal: v })} />
            <Checkbox label="Secundario" checked={depositos.secundario} onChange={(v) => setDepositos({ ...depositos, secundario: v })} />
            <Checkbox label="Depósito Frío" checked={depositos.depositoFrio} onChange={(v) => setDepositos({ ...depositos, depositoFrio: v })} />
          </div>

          <div style={{ display: "flex", gap: 12 }}>
          <Button onClick={() => { showToast("Empleado registrado con éxito", "success"); router.push("/empleados"); }}>Guardar</Button>
            <Button variant="secondary" onClick={() => router.back()}>Cancelar</Button>
          </div>
        </div>
      </Card>
    </Container>
  );
}


