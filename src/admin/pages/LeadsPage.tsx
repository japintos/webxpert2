import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Lead } from "../api/types";

const statuses = ["NEW", "QUALIFIED", "CONTACTED", "PROPOSAL", "WON", "LOST"];

export function LeadsPage() {
  const [items, setItems] = useState<Lead[]>([]);
  const [error, setError] = useState("");

  async function load() {
    setItems(await api<Lead[]>("/api/v1/leads"));
  }

  useEffect(() => {
    load().catch(() => setError("No se pudieron cargar los leads."));
  }, []);

  async function updateStatus(id: string, status: string) {
    await api(`/api/v1/leads/${id}`, { method: "PATCH", body: JSON.stringify({ status }) });
    await load();
  }

  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Pipeline</p>
      <h1 className="text-3xl font-bold">Leads</h1>
      {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}
      <div className="mt-6 overflow-hidden rounded-2xl border border-white/10">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-900/90 text-slate-400">
            <tr>
              <th className="px-4 py-3 font-medium">Contacto</th>
              <th className="px-4 py-3 font-medium">Interés</th>
              <th className="px-4 py-3 font-medium">Score</th>
              <th className="px-4 py-3 font-medium">Estado</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t border-white/5 bg-slate-900/50">
                <td className="px-4 py-3">
                  <p>{item.contact?.name || "Sin nombre"}</p>
                  <p className="text-xs text-slate-400">{item.contact?.phone}</p>
                </td>
                <td className="px-4 py-3">{item.service_interest || "—"}</td>
                <td className="px-4 py-3 font-semibold text-cyan-300">{item.score}</td>
                <td className="px-4 py-3">
                  <select
                    value={item.status}
                    onChange={(e) => updateStatus(item.id, e.target.value)}
                    className="rounded-lg border border-white/20 bg-slate-950 px-2 py-1 text-xs"
                  >
                    {statuses.map((status) => (
                      <option key={status} value={status}>
                        {status}
                      </option>
                    ))}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {items.length === 0 && <p className="p-4 text-sm text-slate-400">Todavía no hay leads detectados.</p>}
      </div>
    </div>
  );
}
