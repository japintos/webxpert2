import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import type { AIStatus, Assistant } from "../api/types";

export function AssistantPage() {
  const [item, setItem] = useState<Assistant | null>(null);
  const [aiStatus, setAiStatus] = useState<AIStatus | null>(null);
  const [saved, setSaved] = useState("");

  useEffect(() => {
    Promise.all([api<Assistant>("/api/v1/assistant"), api<AIStatus>("/api/v1/ai/status")])
      .then(([assistant, status]) => {
        setItem(assistant);
        setAiStatus(status);
      })
      .catch(() => undefined);
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!item) return;
    const updated = await api<Assistant>("/api/v1/assistant", {
      method: "PATCH",
      body: JSON.stringify({
        name: item.name,
        company_name: item.company_name,
        enabled: item.enabled,
        system_prompt: item.system_prompt,
        language: item.language,
        tone: item.tone,
        fallback_enabled: item.fallback_enabled,
        human_handoff_enabled: item.human_handoff_enabled,
        intent_threshold: item.intent_threshold,
        llm_provider: item.llm_provider,
        llm_model: item.llm_model,
      }),
    });
    setItem(updated);
    setSaved("Cambios guardados");
  }

  if (!item) return <p className="text-slate-400">Cargando configuración...</p>;

  const selected = aiStatus?.providers.find((p) => p.id === item.llm_provider);
  const selectedConfigured = selected?.configured ?? false;

  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Configuración</p>
      <h1 className="text-3xl font-bold">Assistant</h1>
      <form onSubmit={onSubmit} className="mt-6 space-y-4 rounded-2xl border border-white/10 bg-slate-900/70 p-5">
        <div className="grid gap-3 md:grid-cols-2">
          <label className="text-sm">Nombre
            <input value={item.name} onChange={(e) => setItem({ ...item, name: e.target.value })} className="mt-1 w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2" />
          </label>
          <label className="text-sm">Empresa
            <input value={item.company_name} onChange={(e) => setItem({ ...item, company_name: e.target.value })} className="mt-1 w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2" />
          </label>
        </div>

        <div className="rounded-xl border border-white/10 bg-slate-950/70 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">IA generativa</p>
          <p className="mt-1 text-sm text-slate-400">
            Se usa solo como fallback cuando no hay una FAQ o precio exacto. Las claves van en <code className="text-cyan-300">backend/.env</code>.
          </p>
          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <label className="text-sm">Proveedor
              <select
                value={item.llm_provider || "openai"}
                onChange={(e) => setItem({ ...item, llm_provider: e.target.value, llm_model: "" })}
                className="mt-1 w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2"
              >
                {(aiStatus?.providers || [
                  { id: "openai", label: "OpenAI", configured: false, default_model: "gpt-4o-mini" },
                  { id: "gemini", label: "Google Gemini", configured: false, default_model: "gemini-3.6-flash" },
                ]).map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.label} {provider.configured ? "" : "(sin API key)"}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-sm">Modelo (opcional)
              <input
                value={item.llm_model || ""}
                onChange={(e) => setItem({ ...item, llm_model: e.target.value || null })}
                placeholder={selected?.default_model || "modelo por defecto"}
                className="mt-1 w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2"
              />
            </label>
          </div>
          <p className={`mt-3 text-sm ${selectedConfigured ? "text-emerald-400" : "text-amber-300"}`}>
            {selectedConfigured
              ? `Listo: ${selected?.label} tiene API key cargada.`
              : `Falta ${item.llm_provider === "gemini" ? "GEMINI_API_KEY" : "OPENAI_API_KEY"} en backend/.env. El bot seguirá usando FAQ y knowledge.`}
          </p>
        </div>

        <label className="block text-sm">Tono
          <input value={item.tone} onChange={(e) => setItem({ ...item, tone: e.target.value })} className="mt-1 w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2" />
        </label>
        <label className="block text-sm">System prompt
          <textarea value={item.system_prompt} onChange={(e) => setItem({ ...item, system_prompt: e.target.value })} rows={14} className="mt-1 w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        </label>
        <label className="block text-sm">Umbral de intent ({item.intent_threshold})
          <input type="range" min={0.3} max={0.95} step={0.05} value={item.intent_threshold} onChange={(e) => setItem({ ...item, intent_threshold: Number(e.target.value) })} className="mt-2 w-full" />
        </label>
        <div className="flex flex-wrap gap-4 text-sm">
          <label className="flex items-center gap-2"><input type="checkbox" checked={item.enabled} onChange={(e) => setItem({ ...item, enabled: e.target.checked })} /> Bot activo</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={item.fallback_enabled} onChange={(e) => setItem({ ...item, fallback_enabled: e.target.checked })} /> Fallback IA</label>
          <label className="flex items-center gap-2"><input type="checkbox" checked={item.human_handoff_enabled} onChange={(e) => setItem({ ...item, human_handoff_enabled: e.target.checked })} /> Human handoff</label>
        </div>
        <button type="submit" className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold">Guardar</button>
        {saved && <span className="ml-3 text-sm text-emerald-400">{saved}</span>}
      </form>
    </div>
  );
}
