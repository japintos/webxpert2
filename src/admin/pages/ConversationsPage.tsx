import { FormEvent, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { Conversation, Message } from "../api/types";

const statusLabel: Record<string, string> = {
  BOT: "Bot",
  WAITING_HUMAN: "Espera humana",
  HUMAN: "Humano",
  CLOSED: "Cerrada",
};

export function ConversationsPage() {
  const [items, setItems] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Conversation | null>(null);
  const [draft, setDraft] = useState("");
  const [simPhone, setSimPhone] = useState("5493764000000");
  const [simName, setSimName] = useState("Cliente demo");
  const [simText, setSimText] = useState("");
  const [error, setError] = useState("");

  async function loadList(selectId?: string) {
    const data = await api<Conversation[]>("/api/v1/conversations");
    setItems(data);
    const next = selectId || selectedId || data[0]?.id || null;
    setSelectedId(next);
    if (next) {
      const full = await api<Conversation>(`/api/v1/conversations/${next}`);
      setDetail(full);
    } else {
      setDetail(null);
    }
  }

  useEffect(() => {
    loadList().catch(() => setError("No se pudieron cargar las conversaciones."));
  }, []);

  async function selectConversation(id: string) {
    setSelectedId(id);
    const full = await api<Conversation>(`/api/v1/conversations/${id}`);
    setDetail(full);
  }

  async function sendReply(event: FormEvent) {
    event.preventDefault();
    if (!selectedId || !draft.trim()) return;
    await api(`/api/v1/conversations/${selectedId}/messages`, {
      method: "POST",
      body: JSON.stringify({ content: draft.trim() }),
    });
    setDraft("");
    await loadList(selectedId);
  }

  async function simulate(event: FormEvent) {
    event.preventDefault();
    if (!simText.trim()) return;
    const result = await api<{ conversation_id: string }>("/api/v1/simulate/inbound", {
      method: "POST",
      body: JSON.stringify({ phone: simPhone, name: simName, text: simText.trim() }),
    });
    setSimText("");
    await loadList(result.conversation_id);
  }

  async function patchStatus(status: string) {
    if (!selectedId) return;
    await api(`/api/v1/conversations/${selectedId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    });
    await loadList(selectedId);
  }

  const messages: Message[] = useMemo(() => detail?.messages || [], [detail]);

  return (
    <div className="flex h-[calc(100vh-5rem)] min-h-[520px] flex-col">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Bandeja</p>
        <h1 className="text-3xl font-bold">Conversaciones</h1>
      </div>
      {error && <p className="mb-3 text-sm text-rose-400">{error}</p>}
      <div className="grid min-h-0 flex-1 gap-4 md:grid-cols-[320px_1fr]">
        <aside className="overflow-auto rounded-2xl border border-white/10 bg-slate-900/70">
          {items.length === 0 && <p className="p-4 text-sm text-slate-400">Todavía no hay conversaciones.</p>}
          {items.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => selectConversation(item.id)}
              className={`block w-full border-b border-white/5 px-4 py-3 text-left ${
                selectedId === item.id ? "bg-brand-600/20" : "hover:bg-white/5"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold">{item.contact?.name || item.contact?.phone || "Contacto"}</p>
                {item.needs_human && <span className="text-[11px] font-semibold text-amber-300">Humano</span>}
              </div>
              <p className="truncate text-xs text-slate-400">{item.contact?.phone}</p>
              <p className="mt-1 truncate text-sm text-slate-300">{item.last_message}</p>
              <div className="mt-1 flex gap-2 text-[11px] text-slate-400">
                <span>{statusLabel[item.status]}</span>
                <span>{item.channel === "web" ? "Web" : item.channel}</span>
                {item.lead_score != null && <span>🔥 {item.lead_score}</span>}
              </div>
            </button>
          ))}
        </aside>
        <section className="flex min-h-0 flex-col rounded-2xl border border-white/10 bg-slate-900/70">
          {detail ? (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-white/10 px-5 py-4">
                <div>
                  <h2 className="text-lg font-semibold">{detail.contact?.name || "Contacto"}</h2>
                  <p className="text-sm text-slate-400">{detail.contact?.phone}</p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <button type="button" onClick={() => patchStatus("HUMAN")} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs font-semibold">
                    Tomar
                  </button>
                  <button type="button" onClick={() => patchStatus("BOT")} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs font-semibold">
                    Reactivar bot
                  </button>
                  <button type="button" onClick={() => patchStatus("CLOSED")} className="rounded-lg border border-white/20 px-3 py-1.5 text-xs font-semibold">
                    Cerrar
                  </button>
                </div>
              </div>
              <div className="flex-1 space-y-3 overflow-auto p-5">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
                      message.direction === "INBOUND"
                        ? "bg-slate-800 text-slate-100"
                        : "ml-auto bg-brand-600/30 text-slate-50"
                    }`}
                  >
                    <p className="mb-1 text-[11px] uppercase tracking-wide text-slate-400">
                      {message.direction === "INBOUND" ? detail.contact?.name || "Cliente" : "Webxpert"}
                      {message.ai_generated ? " · IA" : ""}
                      {message.intent ? ` · ${message.intent}` : ""}
                    </p>
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                ))}
              </div>
              <form onSubmit={sendReply} className="border-t border-white/10 p-4">
                <div className="flex gap-2">
                  <input
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    placeholder="Escribir respuesta..."
                    className="flex-1 rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm"
                  />
                  <button type="submit" className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold">
                    Enviar
                  </button>
                </div>
              </form>
            </>
          ) : (
            <p className="p-6 text-sm text-slate-400">Seleccioná una conversación o simulá un mensaje.</p>
          )}
        </section>
      </div>
      <form onSubmit={simulate} className="mt-4 rounded-2xl border border-white/10 bg-slate-900/70 p-4">
        <p className="mb-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">Simular visitante web (localhost)</p>
        <div className="grid gap-2 md:grid-cols-4">
          <input value={simPhone} onChange={(e) => setSimPhone(e.target.value)} className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" placeholder="Teléfono" />
          <input value={simName} onChange={(e) => setSimName(e.target.value)} className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" placeholder="Nombre" />
          <input value={simText} onChange={(e) => setSimText(e.target.value)} className="md:col-span-2 rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" placeholder="Mensaje del cliente..." />
        </div>
        <button type="submit" className="mt-3 rounded-lg border border-cyan-300/40 px-4 py-2 text-sm font-semibold text-cyan-200">
          Enviar simulación
        </button>
      </form>
    </div>
  );
}
