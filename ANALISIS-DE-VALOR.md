# Análisis de valor — webXpert (sitio + asistente IA + panel)

Fecha: 3 de septiembre de 2026  
Alcance: el producto **completo** de este repositorio (sitio institucional, widget de asistente, API FastAPI, motor de IA, panel admin, deploy Railway).  
Moneda: **dólares estadounidenses (USD)**.  
Método: costo de reposición + comparable de mercado. No hay DCF: no hay serie de ingresos del producto para descontar.

---

## 1. Qué se está valuando

No es solo una landing. Son tres capas que un cliente compraría juntas:

| Capa | Qué es |
|---|---|
| Sitio comercial | SPA React: home, 7 verticales de servicio, portfolio, SaaS, equipo, precios, contacto Formspree, legales, SEO, animaciones |
| Asistente | Chat en el sitio: intake de datos, intents, knowledge, precios controlados, OpenAI/Gemini opcional, leads, handoff a WhatsApp (Julio / Agustín) |
| Panel + backend | Login JWT, dashboard, bandeja, pipeline de leads, CRUD knowledge/servicios/precios, config del bot, manual de ayuda, Postgres, tests, Docker de producción |

Es software a medida en producción (Railway + Postgres), no un theme ni un Tidio pegado.

---

## 2. Inventario (activo)

**Front público**

- Identidad visual, logo hexagonal, Framer Motion, Tailwind
- Páginas: inicio, servicios + detalle, nosotros (2 socios + WhatsApp), contacto, privacidad, términos
- Lista de precios y rangos de presupuesto
- Portfolio (Kairos, audiencias laborales, e-commerce, etc.)
- Widget: logo + robotito, markdown seguro, intake obligatorio

**Producto de asistencia comercial**

- Clasificador de intención por keywords
- Knowledge base por categoría y prioridad
- Price guard: el bot no cita números que no estén en `pricing`
- Lead scoring y estados de pipeline
- Handoff humano + links `wa.me` con nombre y teléfono del visitante
- LLM acotado (OpenAI o Gemini) solo como fallback

**Operación**

- 11 tablas (tenant, users, assistant, contacts, conversations, messages, leads, knowledge, intents, services, pricing)
- Seed comercial + tests de API/chat/engine
- Un contenedor: build Vite + uvicorn; healthcheck `/health`
- Rate limit, headers de seguridad, JWT distinto para admin y visitante

Horas equivalentes de un fullstack senior (diseño + código + QA + deploy), no “horas de hobby”:

| Bloque | Horas |
|---|---|
| Sitio institucional (UI, copy, SEO, portfolio, legal) | 50–65 |
| Widget de chat (intake, markdown, launcher, polling) | 20–28 |
| Panel admin (9 pantallas + ayuda) | 45–60 |
| API, modelos, auth, seed, schema | 45–55 |
| Motor IA (intent, knowledge, precios, leads, WhatsApp, LLM) | 40–55 |
| Tests (~35 casos) | 15–22 |
| Docker / Railway / hardening prod | 15–22 |
| Carga de knowledge, precios, prompt | 12–18 |
| **Total** | **~240–325 h** |

Punto medio usado abajo: **280 horas**.

---

## 3. Costo de reposición (volver a construir hoy)

Tarifas de mercado 2026 para este tipo de trabajo, cobradas al cliente (no sueldo bruto):

| Perfil | USD / hora | 280 h |
|---|---|---|
| Fullstack LatAm (AR/UY/MX), senior de estudio | 40–55 | 11.200 – 15.400 |
| Estudio boutique LatAm (incluye PM y QA, ×1,25) | — | 14.000 – 19.250 |
| Freelance US / Europa | 100–140 | 28.000 – 39.200 |

En el mercado de webXpert (estudio en Posadas, cobro en USD) el número creíble de **reposición** es la fila LatAm con overhead de estudio.

**Reposición LatAm: USD 14.000 – 16.500**  
Punto medio: **USD 15.200**

---

## 4. Comparable: qué cobraría webXpert si lo vendiera a un cliente

Usando **su propio listado** (ya con el −40 %):

| Ítem del catálogo | Rango USD |
|---|---|
| Sitio institucional “completo” (este sitio es más que 3–6 secciones) | 720 – 1.200 (techo del institucional + e-commerce light) |
| Sistema web a medida | desde 1.200 |
| Aplicación empresarial | 1.500 – 2.400 |
| IA / automatización | a cotizar |

Ese listado **subvalúa** este repo: el asistente + panel es un producto, no un extra de landing. Un presupuesto honesto a un tercero sería:

| Paquete | USD | Comentario |
|---|---|---|
| Solo sitio institucional de este nivel | 1.800 – 2.800 | Por encima del institucional simple; portfolio + 7 servicios + legal |
| Solo asistente IA + panel + API (white-label) | 7.000 – 11.000 | Equivale a un sistema + módulo IA |
| **Llave en mano (sitio + bot + admin + deploy)** | **11.000 – 16.000** | Lo que un cliente pagaría por “quedarse con esto andando” |

Intercom / Chatwoot / ManyChat no reemplazan esto 1:1 (no traen el sitio, ni el price guard, ni el knowledge de webXpert). Un Tidio + WordPress sale mucho menos (~USD 800–2.000 de armado) y **no es el mismo activo**.

---

## 5. Qué no entra en el número

- Dominio, hosting recurrente (Railway + Postgres: ~USD 10–25 / mes)
- Tokens OpenAI/Gemini (opex, no asset)
- Marca “webXpert”, cartera de clientes, dominio `.com.ar`
- Ingresos futuros del chat (no hay histórico de conversión para capitalizar)
- Contenido de terceros en el portfolio (casos de clientes: valor comercial, no código revendible)

Esto es valuación del **software y del sitio**, no de la empresa.

---

## 6. Riesgos que bajan el múltiplo

- Seed puede reescribir precios de catálogo al reiniciar el API
- Un solo tenant hardcodeado (`webxpert`): no es SaaS multi-cliente listo para vender suscripciones
- HashRouter + un contenedor: bien para este tamaño; no es un marketplace
- Dependencia de claves LLM opcionales: el valor no exige OpenAI; el FAQ ya funciona

Por eso no se aplica un múltiplo de SaaS (8–12× ARR). Acá el techo es **costo de reposición + prima de producto terminado en producción**.

Prima razonable por “ya está en Railway, testeado, con copy y knowledge cargados”: **+10–15 %** sobre reposición pura.

15.200 × 1,12 ≈ **USD 17.000** como techo interno. Para **vender el paquete a un cliente** conviene anclar más abajo, en la tabla del §4.

---

## 7. Número

Tres lecturas, la del medio es la que hay que usar:

| Lectura | USD | Para qué |
|---|---|---|
| Piso (sitio + bot mínimo, LatAm apurado) | **8.500** | Liquidación / “lo hago en dos sprints” |
| **Valor de uso / cotización justa** | **14.500** | Lo que vale el producto armado, en el mercado de webXpert |
| Techo (reposición US o venta white-label premium) | **32.000** | Si se cotiza con tarifa norte / producto empaquetado para revender |

### Valor expresado en dólares

# **USD 14.500**

(catorce mil quinientos dólares estadounidenses)

Rango defendible en una negociación: **USD 12.000 – 16.000**.  
Abajo de USD 10.000 se estaría regalando el módulo de IA y el panel.  
Arriba de USD 20.000 hay que justificarlo con tarifa US o con un contrato de soporte/licencia, no solo con este código.

---

## 8. Cómo usarlo

- **Presupuesto a un cliente** que quiera “un sitio como el de ustedes + el mismo asistente”: partir de **USD 14.500**, desglosado sitio ~2.500 + sistema/IA ~12.000.
- **Aporte de socios / equity interno**: anclar **USD 14.500** como valor del activo digital (no de la marca).
- **Seguro / balance**: reposición **USD 15.200**; valor neto conservador **USD 12.000**.

Revisar este número si: se convierte en SaaS multi-tenant, hay ARR, o se vende licencia a otros estudios.
