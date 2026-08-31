import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { MessageCircle, Send, X } from "lucide-react";
import { apiBase } from "../admin/api/client";

type ChatMessage = {
  id: string;
  direction: "INBOUND" | "OUTBOUND";
  sender: string;
  content: string;
  created_at: string;
};

const VISITOR_KEY = "wx_visitor_id";
const TOKEN_KEY = "wx_chat_token";
const GREETING =
  "¡Hola! Soy Webxpert Assistant. Contame qué necesitás: una web, un e-commerce, un sistema o una idea a medida.";

function visitorId(): string {
  const existing = localStorage.getItem(VISITOR_KEY);
  if (existing) return existing;
  const created = crypto.randomUUID();
  localStorage.setItem(VISITOR_KEY, created);
  return created;
}

export function WebChatWidget() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("BOT");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const scroller = useRef<HTMLDivElement>(null);

  const visibleMessages = useMemo(() => messages, [messages]);

  useEffect(() => {
    if (!open) return;
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;
    loadHistory(token).catch(() => {
      localStorage.removeItem(TOKEN_KEY);
    });
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;
    const timer = window.setInterval(() => {
      loadHistory(token).catch(() => undefined);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [open]);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [messages, open]);

  async function loadHistory(token: string) {
    const response = await fetch(`${apiBase()}/api/v1/chat/messages?visitor_token=${encodeURIComponent(token)}`);
    if (response.status === 401) {
      localStorage.removeItem(TOKEN_KEY);
      return;
    }
    if (!response.ok) return;
    const data = await response.json();
    setMessages(data.messages || []);
    setStatus(data.status || "BOT");
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || loading) return;
    setDraft("");
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${apiBase()}/api/v1/chat/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          visitor_id: visitorId(),
          visitor_token: localStorage.getItem(TOKEN_KEY),
          name: "Visitante web",
          text,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(typeof data.detail === "string" ? data.detail : "No se pudo enviar");
      }
      localStorage.setItem(TOKEN_KEY, data.visitor_token);
      setMessages(data.messages || []);
      setStatus(data.status || "BOT");
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo enviar el mensaje.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed bottom-5 right-5 z-[80]">
      {open && (
        <section className="mb-3 flex h-[min(520px,70vh)] w-[min(380px,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-2xl border border-white/15 bg-slate-950/95 shadow-glow backdrop-blur">
          <header className="flex items-center justify-between border-b border-white/10 px-4 py-3">
            <div>
              <p className="text-sm font-semibold text-slate-100">Webxpert Assistant</p>
              <p className="text-[11px] uppercase tracking-[0.16em] text-brand-400">
                {status === "WAITING_HUMAN" || status === "HUMAN" ? "Un especialista continúa" : "Chat en vivo"}
              </p>
            </div>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg p-1 text-slate-400 hover:text-white" aria-label="Cerrar chat">
              <X size={18} />
            </button>
          </header>
          <div ref={scroller} className="flex-1 space-y-3 overflow-auto p-4">
            {visibleMessages.length === 0 && (
              <div className="max-w-[85%] rounded-2xl bg-slate-800 px-3 py-2 text-sm text-slate-100">{GREETING}</div>
            )}
            {visibleMessages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                  message.direction === "INBOUND" ? "ml-auto bg-brand-600/40 text-white" : "bg-slate-800 text-slate-100"
                }`}
              >
                {message.content}
              </div>
            ))}
          </div>
          <form onSubmit={onSubmit} className="border-t border-white/10 p-3">
            {error && <p className="mb-2 text-xs text-rose-400">{error}</p>}
            <div className="flex gap-2">
              <input
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Escribí tu consulta..."
                className="flex-1 rounded-lg border border-white/20 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
              <button type="submit" disabled={loading} className="rounded-lg bg-brand-600 px-3 py-2 text-white hover:bg-brand-500 disabled:opacity-50" aria-label="Enviar">
                <Send size={16} />
              </button>
            </div>
          </form>
        </section>
      )}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-white shadow-glow hover:bg-brand-500"
        aria-label="Abrir chat de Webxpert"
      >
        {open ? <X size={22} /> : <MessageCircle size={22} />}
      </button>
    </div>
  );
}
