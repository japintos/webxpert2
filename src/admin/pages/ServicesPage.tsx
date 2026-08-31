import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import type { ServiceItem } from "../api/types";

const empty = { name: "", description: "", category: "general", starting_price: "", active: true, price_visible: true };

export function ServicesPage() {
  const [items, setItems] = useState<ServiceItem[]>([]);
  const [form, setForm] = useState(empty);
  const [editingId, setEditingId] = useState<string | null>(null);

  async function load() {
    setItems(await api<ServiceItem[]>("/api/v1/services"));
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const payload = { ...form, starting_price: form.starting_price || null };
    if (editingId) {
      await api(`/api/v1/services/${editingId}`, { method: "PATCH", body: JSON.stringify(payload) });
    } else {
      await api("/api/v1/services", { method: "POST", body: JSON.stringify(payload) });
    }
    setForm(empty);
    setEditingId(null);
    await load();
  }

  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Catálogo</p>
      <h1 className="text-3xl font-bold">Servicios</h1>
      <form onSubmit={onSubmit} className="mt-6 grid gap-3 rounded-2xl border border-white/10 bg-slate-900/70 p-5 md:grid-cols-2">
        <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Nombre" className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        <input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder="Categoría" className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        <textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Descripción" className="md:col-span-2 rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        <input value={form.starting_price} onChange={(e) => setForm({ ...form, starting_price: e.target.value })} placeholder="Precio visible (texto)" className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        <div className="flex items-center gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} /> Activo
          </label>
          <button type="submit" className="rounded-lg bg-brand-600 px-4 py-2 font-semibold">{editingId ? "Guardar" : "Crear"}</button>
        </div>
      </form>
      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {items.map((item) => (
          <article key={item.id} className="rounded-2xl border border-white/10 bg-slate-900/70 p-5">
            <h3 className="text-lg font-semibold">{item.name}</h3>
            <p className="mt-2 text-sm text-slate-300">{item.description}</p>
            {item.starting_price && <p className="mt-3 text-sm font-semibold text-cyan-300">{item.starting_price}</p>}
            <div className="mt-4 flex gap-2">
              <button type="button" onClick={() => { setEditingId(item.id); setForm({ name: item.name, description: item.description, category: item.category, starting_price: item.starting_price || "", active: item.active, price_visible: item.price_visible }); }} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs font-semibold">Editar</button>
              <button type="button" onClick={async () => { await api(`/api/v1/services/${item.id}`, { method: "DELETE" }); await load(); }} className="rounded-lg border border-rose-400/40 px-3 py-1.5 text-xs font-semibold text-rose-300">Eliminar</button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
