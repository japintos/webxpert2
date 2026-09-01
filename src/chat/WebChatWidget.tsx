import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { Bot, Send, X } from "lucide-react";
import logoSolito from "../../assets/images/logos/logo_solito2.jpg";
import { apiBase } from "../admin/api/client";
import { SafeMarkdown } from "./SafeMarkdown";

type ChatMessage = {
  id: string;
  direction: "INBOUND" | "OUTBOUND";
  sender: string;
  content: string;
  created_at: string;
};

type VisitorProfile = {
  first_name: string;
  last_name: string;
  contact_phone: string;
};

const VISITOR_KEY = "wx_visitor_id";
const TOKEN_KEY = "wx_chat_token";
const PROFILE_KEY = "wx_chat_profile";
const INTAKE_PROMPT =
  "¡Hola! Soy Webxpert Assistant. Para ayudarte, necesito tu **nombre**, **apellido** y **teléfono**.";

function visitorId(): string {
  const existing = localStorage.getItem(VISITOR_KEY);
  if (existing) return existing;
  const created = crypto.randomUUID();
  localStorage.setItem(VISITOR_KEY, created);
  return created;
}

function readProfile(): VisitorProfile | null {
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as VisitorProfile;
    if (parsed.first_name && parsed.last_name && parsed.contact_phone) return parsed;
  } catch {
    return null;
  }
  return null;
}

export function WebChatWidget() {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("BOT");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [profile, setProfile] = useState<VisitorProfile | null>(() => readProfile());
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [phone, setPhone] = useState("");
  const scroller = useRef<HTMLDivElement>(null);
  const needsIntake = !profile;

  const visibleMessages = useMemo(() => messages, [messages]);

  useEffect(() => {
    if (!open || needsIntake) return;
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;
    loadHistory(token).catch(() => {
      localStorage.removeItem(TOKEN_KEY);
    });
  }, [open, needsIntake]);

  useEffect(() => {
    if (!open || needsIntake) return;
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) return;
    const timer = window.setInterval(() => {
      loadHistory(token).catch(() => undefined);
    }, 4000);
    return () => window.clearInterval(timer);
  }, [open, needsIntake]);

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: "smooth" });
  }, [messages, open]);

  function resetVisitorSession() {
    localStorage.removeItem(TOKEN_KEY);
    setMessages([]);
    setStatus("BOT");
  }

  async function loadHistory(token: string) {
    const response = await fetch(`${apiBase()}/api/v1/chat/messages?visitor_token=${encodeURIComponent(token)}`);
    if (response.status === 401) {
      resetVisitorSession();
      return;
    }
    if (!response.ok) return;
    const data = await response.json();
    if (data.status === "CLOSED") {
      resetVisitorSession();
      return;
    }
    setMessages(data.messages || []);
    setStatus(data.status || "BOT");
  }

  async function postChat(body: Record<string, unknown>) {
    const response = await fetch(`${apiBase()}/api/v1/chat/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        visitor_id: visitorId(),
        visitor_token: localStorage.getItem(TOKEN_KEY),
        ...body,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      const detail = typeof data.detail === "string" ? data.detail : "No se pudo enviar";
      throw new Error(detail);
    }
    localStorage.setItem(TOKEN_KEY, data.visitor_token);
    setMessages(data.messages || []);
    setStatus(data.status || "BOT");
    if (data.status === "CLOSED") {
      resetVisitorSession();
    }
  }

  async function onIntake(event: FormEvent) {
    event.preventDefault();
    if (loading) return;
    const next: VisitorProfile = {
      first_name: firstName.trim(),
      last_name: lastName.trim(),
      contact_phone: phone.trim(),
    };
    if (!next.first_name || !next.last_name || !next.contact_phone) {
      setError("Completá nombre, apellido y teléfono.");
      return;
    }
    setLoading(true);
    setError("");
    try {
      await postChat({
        intake: true,
        first_name: next.first_name,
        last_name: next.last_name,
        contact_phone: next.contact_phone,
      });
      localStorage.setItem(PROFILE_KEY, JSON.stringify(next));
      setProfile(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudieron guardar tus datos.");
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text || loading || !profile) return;
    setDraft("");
    setLoading(true);
    setError("");
    try {
      await postChat({
        first_name: profile.first_name,
        last_name: profile.last_name,
        contact_phone: profile.contact_phone,
        text,
      });
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
            <div className="flex items-center gap-3">
              <span className="relative shrink-0">
                <img src={logoSolito} alt="" className="h-9 w-9 rounded-lg object-cover ring-1 ring-white/20" />
                <span className="absolute -bottom-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-cyan-400 text-slate-950">
                  <Bot size={10} strokeWidth={2.5} />
                </span>
              </span>
              <div>
                <p className="text-sm font-semibold text-slate-100">Asistente Webxpert</p>
                <p className="text-[11px] uppercase tracking-[0.16em] text-brand-400">
                  {status === "WAITING_HUMAN" || status === "HUMAN" ? "Un especialista continúa" : "Te respondemos acá"}
                </p>
              </div>
            </div>
            <button type="button" onClick={() => setOpen(false)} className="rounded-lg p-1 text-slate-400 hover:text-white" aria-label="Cerrar chat">
              <X size={18} />
            </button>
          </header>
          <div ref={scroller} className="flex-1 space-y-3 overflow-auto p-4">
            {visibleMessages.length === 0 && (
              <div className="max-w-[85%] rounded-2xl bg-slate-800 px-3 py-2 text-sm text-slate-100">
                <SafeMarkdown text={needsIntake ? INTAKE_PROMPT : "¡Hola! Contame qué necesitás."} />
              </div>
            )}
            {visibleMessages.map((message) => (
              <div
                key={message.id}
                className={`max-w-[85%] rounded-2xl px-3 py-2 text-sm ${
                  message.direction === "INBOUND" ? "ml-auto bg-brand-600/40 text-white" : "bg-slate-800 text-slate-100"
                }`}
              >
                <SafeMarkdown text={message.content} />
              </div>
            ))}
          </div>
          {needsIntake ? (
            <form onSubmit={onIntake} className="space-y-2 border-t border-white/10 p-3">
              {error && <p className="text-xs text-rose-400">{error}</p>}
              <input
                value={firstName}
                onChange={(event) => setFirstName(event.target.value)}
                placeholder="Nombre"
                className="w-full rounded-lg border border-white/20 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
              <input
                value={lastName}
                onChange={(event) => setLastName(event.target.value)}
                placeholder="Apellido"
                className="w-full rounded-lg border border-white/20 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
              <input
                value={phone}
                onChange={(event) => setPhone(event.target.value)}
                placeholder="Teléfono"
                className="w-full rounded-lg border border-white/20 bg-slate-900 px-3 py-2 text-sm text-slate-100"
              />
              <button type="submit" disabled={loading} className="w-full rounded-lg bg-brand-600 px-3 py-2 text-sm font-semibold text-white hover:bg-brand-500 disabled:opacity-50">
                Empezar chat
              </button>
            </form>
          ) : (
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
          )}
        </section>
      )}
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className={`flex items-center gap-3 rounded-2xl bg-brand-600 text-white shadow-glow transition hover:bg-brand-500 ${
          open ? "h-14 w-14 justify-center" : "py-1.5 pl-1.5 pr-4"
        }`}
        aria-label={open ? "Cerrar asistente de Webxpert" : "Abrir asistente de Webxpert"}
      >
        {open ? (
          <X size={22} />
        ) : (
          <>
            <span className="relative shrink-0">
              <img src={logoSolito} alt="" className="h-11 w-11 rounded-xl object-cover ring-2 ring-white/25" />
              <span className="absolute -bottom-0.5 -right-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-cyan-400 text-slate-950 shadow">
                <Bot size={12} strokeWidth={2.5} />
              </span>
            </span>
            <span className="pr-1 text-left leading-tight">
              <span className="block text-sm font-semibold">Asistente</span>
              <span className="block text-[11px] font-medium text-indigo-100">¿En qué te ayudo?</span>
            </span>
          </>
        )}
      </button>
    </div>
  );
}
