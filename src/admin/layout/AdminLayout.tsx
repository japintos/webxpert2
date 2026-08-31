import {
  BookOpen,
  Bot,
  LayoutDashboard,
  LogOut,
  MessageSquare,
  Settings,
  Tag,
  Users,
} from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import logoSolito from "../../../assets/images/logos/logo_solito2.jpg";
import { clearToken } from "../api/client";

const links = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/conversaciones", label: "Conversaciones", icon: MessageSquare },
  { to: "/admin/leads", label: "Leads", icon: Users },
  { to: "/admin/conocimiento", label: "Knowledge Base", icon: BookOpen },
  { to: "/admin/servicios", label: "Servicios", icon: Settings },
  { to: "/admin/precios", label: "Precios", icon: Tag },
  { to: "/admin/assistant", label: "Assistant", icon: Bot },
];

export function AdminLayout() {
  const navigate = useNavigate();
  return (
    <div className="flex min-h-screen bg-ink text-slate-100">
      <aside className="hidden w-64 shrink-0 border-r border-white/10 bg-slate-950/80 md:flex md:flex-col">
        <div className="flex items-center gap-3 border-b border-white/10 px-5 py-5">
          <img src={logoSolito} alt="webXpert" className="h-9 w-9 rounded-md object-cover" />
          <div>
            <p className="text-sm font-semibold">webXpert</p>
            <p className="text-[11px] uppercase tracking-[0.16em] text-brand-400">AI Assistant</p>
          </div>
        </div>
        <nav className="flex flex-1 flex-col gap-1 p-3">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) =>
                `flex items-center gap-2 rounded-lg px-3 py-2 text-sm ${
                  isActive ? "bg-brand-600/30 text-white" : "text-slate-300 hover:bg-white/5"
                }`
              }
            >
              <link.icon size={16} />
              {link.label}
            </NavLink>
          ))}
        </nav>
        <button
          type="button"
          onClick={() => {
            clearToken();
            navigate("/admin/login");
          }}
          className="m-3 flex items-center gap-2 rounded-lg border border-white/10 px-3 py-2 text-sm text-slate-300 hover:border-brand-400"
        >
          <LogOut size={16} /> Salir
        </button>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-white/10 bg-ink/80 px-6 py-4 backdrop-blur md:hidden">
          <p className="text-sm font-semibold">webXpert Assistant</p>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
