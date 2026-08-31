import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import type { KnowledgeItem } from "../api/types";

const categories = ["SERVICES", "PRICING", "FAQ", "PROCESS", "TECHNICAL", "COMPANY", "CONTACT", "POLICIES"];

const empty = {
  category: "FAQ",
  title: "",
  content: "",
  keywords: "",
  active: true,
  priority: 0,
};

export function KnowledgePage() {
  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [query, setQuery] = useState("");
  const [form, setForm] = useState(empty);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function load(q = query) {
    const suffix = q ? `?q=${encodeURIComponent(q)}` : "";
    setItems(await api<KnowledgeItem[]>(`/api/v1/knowledge${suffix}`));
  }

  useEffect(() => {
    load().catch(() => setError("No se pudo cargar la base de conocimiento."));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const payload = {
      category: form.category,
      title: form.title,
      content: form.content,
      keywords: form.keywords.split(",").map((k) => k.trim()).filter(Boolean),
      active: form.active,
      priority: Number(form.priority) || 0,
    };
    if (editingId) {
      await api(`/api/v1/knowledge/${editingId}`, { method: "PATCH", body: JSON.stringify(payload) });
    } else {
      await api("/api/v1/knowledge", { method: "POST", body: JSON.stringify(payload) });
    }
    setForm(empty);
    setEditingId(null);
    await load();
  }

  function edit(item: KnowledgeItem) {
    setEditingId(item.id);
    setForm({
      category: item.category,
      title: item.title,
      content: item.content,
      keywords: item.keywords.join(", "),
      active: item.active,
      priority: item.priority,
    });
  }

  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Conocimiento</p>
      <h1 className="text-3xl font-bold">Knowledge Base</h1>
      <p className="mt-2 text-slate-300">Editá respuestas comerciales sin modificar código.</p>
      {error && <p className="mt-3 text-sm text-rose-400">{error}</p>}

      <div className="mt-6 flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Buscar..."
          className="flex-1 rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm"
        />
        <button type="button" onClick={() => load(query)} className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold">
          Buscar
        </button>
      </div>

      <form onSubmit={onSubmit} className="mt-6 space-y-3 rounded-2xl border border-white/10 bg-slate-900/70 p-5">
        <div className="grid gap-3 md:grid-cols-2">
          <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm">
            {categories.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </select>
          <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required placeholder="Título" className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        </div>
        <textarea value={form.content} onChange={(e) => setForm({ ...form, content: e.target.value })} required rows={4} placeholder="Respuesta autorizada" className="w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        <input value={form.keywords} onChange={(e) => setForm({ ...form, keywords: e.target.value })} placeholder="keywords, separadas, por coma" className="w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        <div className="flex items-center gap-4 text-sm">
          <label className="flex items-center gap-2">
            <input type="checkbox" checked={form.active} onChange={(e) => setForm({ ...form, active: e.target.checked })} />
            Activo
          </label>
          <input type="number" value={form.priority} onChange={(e) => setForm({ ...form, priority: Number(e.target.value) })} className="w-24 rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
          <button type="submit" className="rounded-lg bg-brand-600 px-4 py-2 font-semibold">
            {editingId ? "Guardar cambios" : "Crear"}
          </button>
        </div>
      </form>

      <div className="mt-6 grid gap-4">
        {items.map((item) => (
          <article key={item.id} className="rounded-2xl border border-white/10 bg-slate-900/70 p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-brand-400">{item.category}</p>
                <h3 className="text-lg font-semibold">{item.title}</h3>
              </div>
              <div className="flex gap-2">
                <button type="button" onClick={() => edit(item)} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs font-semibold">
                  Editar
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    await api(`/api/v1/knowledge/${item.id}`, { method: "PATCH", body: JSON.stringify({ active: !item.active }) });
                    await load();
                  }}
                  className="rounded-lg border border-white/20 px-3 py-1.5 text-xs font-semibold"
                >
                  {item.active ? "Desactivar" : "Activar"}
                </button>
                <button
                  type="button"
                  onClick={async () => {
                    await api(`/api/v1/knowledge/${item.id}`, { method: "DELETE" });
                    await load();
                  }}
                  className="rounded-lg border border-rose-400/40 px-3 py-1.5 text-xs font-semibold text-rose-300"
                >
                  Eliminar
                </button>
              </div>
            </div>
            <p className="mt-3 whitespace-pre-wrap text-sm text-slate-300">{item.content}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
