import { Bot, MessageSquare, UserRound, Users } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { DashboardStats } from "../api/types";

const cards = [
  { key: "conversations_today" as const, label: "Conversaciones hoy", icon: MessageSquare },
  { key: "new_leads" as const, label: "Leads nuevos", icon: Users },
  { key: "qualified_leads" as const, label: "Leads calificados", icon: UserRound },
  { key: "ai_handled" as const, label: "Atendidas por IA", icon: Bot },
  { key: "handed_off" as const, label: "Derivadas", icon: UserRound },
];

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<DashboardStats>("/api/v1/dashboard/stats")
      .then(setStats)
      .catch(() => setError("No se pudieron cargar las métricas. ¿Está corriendo el backend?"));
  }, []);

  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Dashboard</p>
      <h1 className="text-3xl font-bold">Webxpert AI Assistant</h1>
      <p className="mt-2 max-w-2xl text-slate-300">
        Resumen operativo del asistente comercial. Los precios y el conocimiento se editan desde el panel, sin tocar código.
      </p>
      {error && <p className="mt-4 text-sm text-rose-400">{error}</p>}
      <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        {cards.map((card) => (
          <article key={card.key} className="rounded-2xl border border-white/10 bg-slate-900/70 p-5">
            <card.icon className="mb-3 text-brand-400" size={20} />
            <p className="text-sm text-slate-400">{card.label}</p>
            <p className="mt-2 text-3xl font-semibold">{stats ? stats[card.key] : "—"}</p>
          </article>
        ))}
      </div>
      <div className="mt-8 flex flex-wrap gap-3">
        <Link to="/admin/conversaciones" className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold hover:bg-brand-500">
          Abrir bandeja
        </Link>
        <Link to="/admin/conocimiento" className="rounded-lg border border-white/20 px-4 py-2 text-sm font-semibold">
          Editar conocimiento
        </Link>
      </div>
    </div>
  );
}
