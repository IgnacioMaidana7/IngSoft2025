"use client";
import React from "react";
import Link from "next/link";
import Container from "@/components/layout/Container";
import Card from "@/components/layout/Card";

const mock = [
  { id: "1", email: "123@gmail.com", rol: "Cajero", depositos: "Principal" },
  { id: "2", email: "1234@gmail.com", rol: "Reponedor", depositos: "Principal, Secundario" },
];

export default function EmpleadosPage() {
  return (
    <Container>
      <Card>
        <div className="flex items-center justify-between mb-2.5 pb-2.5 border-b border-border">
          <h1 className="m-0">Empleados</h1>
          <Link href="/empleados/nuevo" className="text-primary font-bold">+ Añadir Empleado</Link>
        </div>
        <ul className="list-none p-0">
          {mock.map((e) => (
            <li key={e.id} className="border-b border-border py-3">
              <div className="flex justify-between gap-2">
                <div>
                  <div className="font-semibold">{e.email}</div>
                  <div className="text-lightText text-sm">{e.rol} · {e.depositos}</div>
                </div>
                <div className="flex gap-3">
                  <Link href={`/empleados/${e.id}`}>Editar</Link>
                  <button onClick={() => alert(`Eliminar empleado ${e.email}`)} className="bg-transparent border-0 text-primary cursor-pointer">Eliminar</button>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </Card>
    </Container>
  );
}


