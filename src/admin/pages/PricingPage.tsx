import { FormEvent, useEffect, useState } from "react";
import { api } from "../api/client";
import type { PricingItem, ServiceItem } from "../api/types";

export function PricingPage() {
  const [services, setServices] = useState<ServiceItem[]>([]);
  const [items, setItems] = useState<PricingItem[]>([]);
  const [serviceId, setServiceId] = useState("");
  const [price, setPrice] = useState("");
  const [priceMax, setPriceMax] = useState("");
  const [priceType, setPriceType] = useState("STARTING_FROM");
  const [description, setDescription] = useState("");

  async function load() {
    const [serviceRows, priceRows] = await Promise.all([
      api<ServiceItem[]>("/api/v1/services"),
      api<PricingItem[]>("/api/v1/pricing"),
    ]);
    setServices(serviceRows);
    setItems(priceRows);
    if (!serviceId && serviceRows[0]) setServiceId(serviceRows[0].id);
  }

  useEffect(() => {
    load().catch(() => undefined);
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await api("/api/v1/pricing", {
      method: "POST",
      body: JSON.stringify({
        service_id: serviceId,
        price: price ? Number(price) : null,
        price_max: priceMax ? Number(priceMax) : null,
        currency: "USD",
        price_type: priceType,
        description,
        active: true,
      }),
    });
    setPrice("");
    setPriceMax("");
    setDescription("");
    await load();
  }

  const nameById = Object.fromEntries(services.map((s) => [s.id, s.name]));

  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.2em] text-brand-500">Comercial</p>
      <h1 className="text-3xl font-bold">Precios</h1>
      <p className="mt-2 text-slate-300">La IA solo puede usar estos valores. Si no hay precio, debe decir que se cotiza.</p>
      <form onSubmit={onSubmit} className="mt-6 grid gap-3 rounded-2xl border border-white/10 bg-slate-900/70 p-5 md:grid-cols-2">
        <select value={serviceId} onChange={(e) => setServiceId(e.target.value)} className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm">
          {services.map((s) => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        <select value={priceType} onChange={(e) => setPriceType(e.target.value)} className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm">
          <option value="STARTING_FROM">Desde</option>
          <option value="FIXED">Fijo</option>
          <option value="ON_REQUEST">A cotizar</option>
        </select>
        <input value={price} onChange={(e) => setPrice(e.target.value)} placeholder="Precio" className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        <input value={priceMax} onChange={(e) => setPriceMax(e.target.value)} placeholder="Precio máximo (opcional)" className="rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        <input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Descripción" className="md:col-span-2 rounded-lg border border-white/20 bg-slate-950 px-3 py-2 text-sm" />
        <button type="submit" className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold">Agregar precio</button>
      </form>
      <div className="mt-6 grid gap-4">
        {items.map((item) => (
          <article key={item.id} className="flex items-center justify-between rounded-2xl border border-white/10 bg-slate-900/70 p-5">
            <div>
              <h3 className="font-semibold">{nameById[item.service_id] || "Servicio"}</h3>
              <p className="text-sm text-cyan-300">
                {item.price_type === "ON_REQUEST" || item.price == null
                  ? "A cotizar"
                  : `${item.currency} ${item.price}${item.price_max ? ` - ${item.price_max}` : ""}`}
              </p>
              {item.description && <p className="mt-1 text-sm text-slate-400">{item.description}</p>}
            </div>
            <button
              type="button"
              onClick={async () => {
                await api(`/api/v1/pricing/${item.id}`, { method: "DELETE" });
                await load();
              }}
              className="rounded-lg border border-rose-400/40 px-3 py-1.5 text-xs font-semibold text-rose-300"
            >
              Eliminar
            </button>
          </article>
        ))}
      </div>
    </div>
  );
}
