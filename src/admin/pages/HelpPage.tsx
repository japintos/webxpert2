import { useMemo, useState } from "react";
import {
  BookOpen,
  Bot,
  CircleHelp,
  LayoutDashboard,
  MessageSquare,
  Search,
  Settings,
  Tag,
  Users,
} from "lucide-react";
import { Link } from "react-router-dom";

type Topic = {
  id: string;
  title: string;
  icon: typeof CircleHelp;
  blurb: string;
  to: string;
  cta: string;
  steps: string[];
  tips: string[];
  warn?: string;
};

const TOPICS: Topic[] = [
  {
    id: "entrar",
    title: "Cómo entrar al panel",
    icon: CircleHelp,
    blurb: "Es la puerta del panel. Sin login no se ve nada de lo interno.",
    to: "/admin/login",
    cta: "Ir al login",
    steps: [
      "Entrá a la web de Webxpert y agregá #/admin (ejemplo: tusitio/#/admin).",
      "Escribí el email del administrador. No viene precargado a propósito.",
      "Escribí la contraseña. El ojito a la derecha sirve para ver lo que tipeaste.",
      "Tocá Ingresar. Si está bien, caés en el Dashboard.",
    ],
    tips: [
      "Si te dice credenciales inválidas, revisá mayúsculas y que no haya un espacio de más.",
      "Salir (abajo a la izquierda) cierra la sesión de este navegador.",
    ],
  },
  {
    id: "dashboard",
    title: "Dashboard",
    icon: LayoutDashboard,
    blurb: "La foto del día: cuántos chats hubo, cuántos leads y cuántos se derivaron.",
    to: "/admin",
    cta: "Abrir Dashboard",
    steps: [
      "Mirá las tarjetas: conversaciones de hoy, leads nuevos, calificados, atendidas por IA y derivadas.",
      "Si un número sube mucho, alguien está chateando: andá a Conversaciones.",
      "Usá Abrir bandeja para saltar a los chats, o Editar conocimiento si el bot contestó mal.",
    ],
    tips: [
      "No se edita nada acá. Solo se mira.",
      "Si ves rayas (—) y un error rojo, el backend no está contestando.",
    ],
  },
  {
    id: "conversaciones",
    title: "Conversaciones",
    icon: MessageSquare,
    blurb: "La bandeja: todos los chats del widget. Acá contestás vos si el bot pide ayuda.",
    to: "/admin/conversaciones",
    cta: "Abrir bandeja",
    steps: [
      "A la izquierda está la lista. El nombre es el del visitante. El teléfono es el que cargó al empezar.",
      "Estados: Bot (contesta solo), Espera humana (pidió una persona), Humano (lo tomaste vos), Cerrada.",
      "Tocá un chat para ver los mensajes. Los del visitante a la izquierda, los de Webxpert a la derecha.",
      "Si dice Humano o Espera humana, escribí abajo y tocá Enviar. Eso llega al widget del visitante.",
      "Tomar: pasás el chat a Humano y el bot se calla.",
      "Reactivar bot: el asistente vuelve a contestar solo.",
      "Cerrar: termina el chat. El visitante ya no ve el historial.",
    ],
    tips: [
      "Si el visitante pidió un agente, el bot también le muestra WhatsApp de Julio y de Agustín.",
      "Simular visitante (abajo) es para probar el bot sin abrir el sitio. Sirve en local.",
    ],
    warn: "Cerrar borra los mensajes de esa conversación. No se puede deshacer. Usalo solo cuando el tema quedó resuelto.",
  },
  {
    id: "leads",
    title: "Leads",
    icon: Users,
    blurb: "Personas que parecen interesadas en contratar. El bot las marca solo.",
    to: "/admin/leads",
    cta: "Ver leads",
    steps: [
      "Cada fila es un posible cliente: nombre, teléfono, qué le interesó y un puntaje (score).",
      "Score alto (cerca de 80 o más) = viene con ganas. Priorizalo.",
      "Cambiá el estado con el menú: NEW (nuevo), QUALIFIED (bueno), CONTACTED (ya lo llamaste), PROPOSAL (presupuesto), WON (cerró), LOST (no va).",
      "Cuando avances con esa persona, actualizá el estado para que el equipo no pise el trabajo.",
    ],
    tips: [
      "Un lead nace si el chat huele a compra o si pidió hablar con un humano.",
      "El teléfono de la lista a veces es el interno del widget (web:…). El celular real está en Conversaciones.",
    ],
  },
  {
    id: "conocimiento",
    title: "Knowledge Base",
    icon: BookOpen,
    blurb: "Las respuestas autorizadas. Si está escrito acá, el bot lo puede decir. Si no, no lo inventa.",
    to: "/admin/conocimiento",
    cta: "Editar conocimiento",
    steps: [
      "Buscá arriba si ya existe un tema (precios, plazos, contacto, etc.).",
      "Para uno nuevo: elegí categoría, título, la respuesta completa, y keywords separadas por coma.",
      "Keywords = palabras que usa la gente (cuesta, sale, presupuesto, Posadas…). Sin eso el bot no lo encuentra fácil.",
      "Prioridad más alta = se elige antes si hay varios textos parecidos.",
      "Activo tiene que estar tildado para que el bot lo use.",
      "Guardá. El cambio vale para el próximo mensaje del chat, no hace falta tocar código.",
    ],
    tips: [
      "Escribí como si hablaras con el cliente: claro, corto, en argentino.",
      "No pongas precios inventados acá. Los números van en Precios.",
      "Desactivar deja el texto guardado pero el bot lo ignora. Eliminar lo borra.",
    ],
  },
  {
    id: "servicios",
    title: "Servicios",
    icon: Settings,
    blurb: "El catálogo: landing, institucional, e-commerce, sistemas, etc.",
    to: "/admin/servicios",
    cta: "Ver servicios",
    steps: [
      "Creá un servicio con nombre, categoría y descripción.",
      "Precio visible es un texto lindo para humanos (ej. USD 210 - 360). El número oficial se carga en Precios.",
      "Activo = el bot puede mencionarlo.",
      "Editar cambia el que ya existe. Eliminar lo saca del catálogo.",
    ],
    tips: [
      "Primero el servicio, después su precio en la pantalla Precios.",
      "Si el nombre no coincide con lo que pregunta la gente, el bot no lo relaciona.",
    ],
  },
  {
    id: "precios",
    title: "Precios",
    icon: Tag,
    blurb: "La única lista de números que el bot puede decir. Si no está acá, tiene que decir que se cotiza.",
    to: "/admin/precios",
    cta: "Editar precios",
    steps: [
      "Elegí el servicio.",
      "Tipo: Desde (rango), Fijo, o A cotizar (sin número).",
      "Completá precio y, si aplica, precio máximo. Moneda USD.",
      "Agregar precio. El bot usa eso en la próxima pregunta de “cuánto sale”.",
    ],
    tips: [
      "Si alguien pregunta un precio que no cargaste, el bot no debe inventarlo.",
      "Para bajar o subir un valor: eliminá el viejo y cargá el nuevo.",
    ],
    warn: "Estos números son los que ve el chat. Si el servidor se reinicia, el catálogo inicial del seed puede volver a escribirse. Revisá Precios después de un deploy.",
  },
  {
    id: "assistant",
    title: "Assistant",
    icon: Bot,
    blurb: "El cerebro: si el bot está prendido, cómo habla, y si puede pasar a un humano.",
    to: "/admin/assistant",
    cta: "Configurar Assistant",
    steps: [
      "Bot activo: si lo destildás, el widget no responde solo.",
      "Tono: cómo suena (profesional, argentino, etc.).",
      "System prompt: las reglas largas. Tocá solo si sabés qué estás pidiendo.",
      "Umbral de intent: más alto = más exigente para “entender” la pregunta. Si no pesca nada, bajalo un poco.",
      "Fallback IA: si no hay FAQ, puede usar OpenAI o Gemini. Hace falta la API key en el servidor.",
      "Human handoff: si está tildado, puede derivar y mostrar WhatsApp de Julio y Agustín.",
      "Siempre tocá Guardar. Si no, no cambia nada.",
    ],
    tips: [
      "Sin API key el bot igual anda con Knowledge y precios. No se rompe.",
      "No pongas precios en el system prompt. Van en Precios.",
    ],
  },
  {
    id: "sitio",
    title: "El chat del sitio (visitante)",
    icon: MessageSquare,
    blurb: "Lo que ve el cliente en la bolita de chat de la web pública.",
    to: "/admin/conversaciones",
    cta: "Ver un chat real",
    steps: [
      "El visitante toca el botón Asistente (logo Webxpert) abajo a la derecha.",
      "Primero pide nombre, apellido y teléfono. Sin eso no arranca.",
      "Después escribe. El bot responde con Knowledge, precios o IA.",
      "Si pide un humano, aparecen dos links de WhatsApp (Julio y Agustín) con sus datos ya escritos.",
      "Ese mismo chat aparece acá en Conversaciones para que lo tomes si hace falta.",
    ],
    tips: [
      "WhatsApp no manda el mensaje solo: se abre la app y el cliente toca Enviar.",
      "El admin (este panel) no se ve en el sitio público. Solo #/admin.",
    ],
  },
];

const MISSIONS = [
  { id: "conversaciones", label: "Quiero contestar un chat" },
  { id: "precios", label: "Quiero cambiar un precio" },
  { id: "conocimiento", label: "El bot dijo algo mal" },
  { id: "leads", label: "Quiero ver quién quiere contratar" },
  { id: "assistant", label: "Quiero apagar o prender el bot" },
  { id: "entrar", label: "No sé cómo entrar" },
];

export function HelpPage() {
  const [query, setQuery] = useState("");
  const [openId, setOpenId] = useState<string>("entrar");

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return TOPICS;
    return TOPICS.filter((topic) => {
      const haystack = [topic.title, topic.blurb, ...topic.steps, ...topic.tips, topic.warn || ""]
        .join(" ")
        .toLowerCase();
      return haystack.includes(needle);
    });
  }, [query]);

  function openTopic(id: string) {
    setOpenId(id);
    window.requestAnimationFrame(() => {
      document.getElementById(`ayuda-${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  return (
    <div className="mx-auto max-w-5xl">
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Manual</p>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">Ayuda para humanos</h1>
          <p className="mt-2 max-w-2xl text-slate-300">
            Guía paso a paso del panel. Sin jerga. Elegí qué querés hacer, o abrí cada pantalla.
          </p>
        </div>
        <div className="rounded-2xl border border-cyan-300/30 bg-cyan-300/10 px-4 py-3 text-sm text-cyan-100">
          Regla de oro: el bot solo dice lo que está en Knowledge y en Precios.
        </div>
      </div>

      <div className="relative mt-6">
        <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Buscar: precio, WhatsApp, cerrar chat, lead..."
          className="w-full rounded-xl border border-white/20 bg-slate-950 py-3 pl-10 pr-4 text-sm"
        />
      </div>

      <div className="mt-6">
        <p className="mb-3 text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">¿Qué querés hacer ahora?</p>
        <div className="flex flex-wrap gap-2">
          {MISSIONS.map((mission) => (
            <button
              key={mission.id}
              type="button"
              onClick={() => openTopic(mission.id)}
              className={`rounded-full border px-3 py-1.5 text-sm ${
                openId === mission.id
                  ? "border-brand-400 bg-brand-600/30 text-white"
                  : "border-white/15 bg-slate-900/70 text-slate-200 hover:border-brand-400/50"
              }`}
            >
              {mission.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-8 grid gap-6 xl:grid-cols-[minmax(0,1fr)_220px]">
        <div className="space-y-4">
          {visible.length === 0 && (
            <p className="rounded-2xl border border-white/10 bg-slate-900/70 p-5 text-sm text-slate-400">
              No hay un capítulo con esa búsqueda. Probá “precio”, “bot” o “WhatsApp”.
            </p>
          )}
          {visible.map((topic, index) => {
            const Icon = topic.icon;
            const open = openId === topic.id;
            return (
              <article
                key={topic.id}
                id={`ayuda-${topic.id}`}
                className="overflow-hidden rounded-2xl border border-white/10 bg-slate-900/70"
              >
                <button
                  type="button"
                  onClick={() => setOpenId(open ? "" : topic.id)}
                  className="flex w-full items-start gap-4 p-5 text-left"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600/25 text-brand-200">
                    <Icon size={18} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-500">
                      Capítulo {String(index + 1).padStart(2, "0")}
                    </span>
                    <span className="mt-1 block text-lg font-semibold">{topic.title}</span>
                    <span className="mt-1 block text-sm text-slate-400">{topic.blurb}</span>
                  </span>
                  <span className="mt-1 text-xs text-slate-500">{open ? "Cerrar" : "Abrir"}</span>
                </button>
                {open && (
                  <div className="space-y-4 border-t border-white/10 px-5 pb-5 pt-4">
                    <ol className="space-y-3">
                      {topic.steps.map((step, stepIndex) => (
                        <li key={step} className="flex gap-3 text-sm text-slate-200">
                          <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-600 text-[11px] font-bold">
                            {stepIndex + 1}
                          </span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ol>
                    {topic.tips.length > 0 && (
                      <div className="rounded-xl border border-white/10 bg-slate-950/70 p-4">
                        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">Tips</p>
                        <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-slate-300">
                          {topic.tips.map((tip) => (
                            <li key={tip}>{tip}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {topic.warn && (
                      <p className="rounded-xl border border-amber-300/30 bg-amber-300/10 px-4 py-3 text-sm text-amber-100">
                        Cuidado: {topic.warn}
                      </p>
                    )}
                    <Link
                      to={topic.to}
                      className="inline-flex rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold hover:bg-brand-500"
                    >
                      {topic.cta}
                    </Link>
                  </div>
                )}
              </article>
            );
          })}
        </div>

        <aside className="hidden xl:block">
          <div className="sticky top-6 rounded-2xl border border-white/10 bg-slate-900/70 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Capítulos</p>
            <nav className="mt-3 space-y-1">
              {TOPICS.map((topic) => (
                <button
                  key={topic.id}
                  type="button"
                  onClick={() => openTopic(topic.id)}
                  className={`block w-full rounded-lg px-2 py-1.5 text-left text-sm ${
                    openId === topic.id ? "bg-brand-600/30 text-white" : "text-slate-400 hover:bg-white/5 hover:text-white"
                  }`}
                >
                  {topic.title}
                </button>
              ))}
            </nav>
          </div>
        </aside>
      </div>
    </div>
  );
}
