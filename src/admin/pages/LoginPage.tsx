import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import logoSolito from "../../../assets/images/logos/logo_solito2.jpg";
import { api, setToken } from "../api/client";

export function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("admin@webxpert.com");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await api<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(data.access_token);
      navigate("/admin");
    } catch {
      setError("Credenciales inválidas. Revisá email y contraseña.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-ink px-6 text-slate-100">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(99,102,241,.22),transparent_40%),radial-gradient(circle_at_70%_70%,rgba(34,211,238,.16),transparent_40%)]" />
      <form
        onSubmit={onSubmit}
        className="relative w-full max-w-md rounded-2xl border border-white/10 bg-slate-900/80 p-8 shadow-glow"
      >
        <div className="mb-6 flex items-center gap-3">
          <img src={logoSolito} alt="webXpert" className="h-10 w-10 rounded-md object-cover" />
          <div>
            <p className="text-lg font-semibold">webXpert Assistant</p>
            <p className="text-xs uppercase tracking-[0.18em] text-brand-400">Panel interno</p>
          </div>
        </div>
        <label className="mb-3 block text-sm">
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm"
            required
          />
        </label>
        <label className="mb-4 block text-sm">
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm"
            required
          />
        </label>
        {error && <p className="mb-3 text-sm text-rose-400">{error}</p>}
        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold hover:bg-brand-500 disabled:opacity-60"
        >
          {loading ? "Ingresando..." : "Ingresar"}
        </button>
      </form>
    </div>
  );
}
