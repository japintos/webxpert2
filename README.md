# webXpert + Webxpert AI Assistant

Sitio institucional de webXpert y, en el mismo repositorio, el **asistente comercial** del chat público más el **panel admin**.

Producción: **un solo servicio en Railway** sirve el sitio, el API y el widget. PostgreSQL es un plugin aparte en el mismo proyecto. **Ya no se usa Vercel.**

---

## 1. Arquitectura

```text
Visitante (www.webxpert.com.ar o *.up.railway.app)
        ↓  botón Asistente (logo Webxpert + robotito)
POST/GET /api/v1/chat/messages
        ↓
FastAPI  →  intake (nombre, apellido, teléfono)
              ↓
         MessageProcessor
              ↓
    IntentClassifier → Knowledge / Precios  ó  LLM (OpenAI o Gemini)
              ↓
    LeadDetector + handoff WhatsApp (Julio / Agustín)
              ↓
PostgreSQL
              ↓
Panel Admin  #/admin  ·  bandeja, leads, knowledge, precios
```

Un contenedor Docker:

1. Build Vite (`dist/`)
2. FastAPI sirve el SPA en `/` y el API en `/api/v1` y `/health`

Mismo origen: el front llama a `/api` relativo. `VITE_API_URL` queda **vacío**.

La IA **no inventa precios ni plazos**. Si no hay un precio en la base, dice que se cotiza.

Tenant actual: `webxpert` (`tenant_id` en todos los modelos).

---

## 2. Requisitos

- Node.js 18+ y npm
- Python 3.11+ (recomendado 3.12)
- Docker Desktop **opcional** (Postgres local). Sin Docker, el backend usa SQLite
- Opcional: OpenAI y/o Gemini
- Producción: Railway (sitio+API + PostgreSQL). HeidiSQL 12+ opcional para mirar la base

---

## 3. Instalación (localhost)

### Base de datos

Sin Docker: en `backend/.env` dejar `DATABASE_URL=sqlite:///./webxpert.db`. El API crea tablas y seed al arrancar.

Con Docker:

```bash
docker compose up -d db
```

```text
DATABASE_URL=postgresql+psycopg://webxpert:webxpert@localhost:5432/webxpert
```

### Backend

```bash
cd backend
copy .env.example .env
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000
```

Al arrancar también corre `create_all` + seed (idempotente: no duplica tenant/admin/knowledge; el catálogo de precios del seed se sincroniza).

### Frontend

```bash
copy .env.example .env
npm install
npm run dev
```

- Sitio: http://localhost:5173/
- Admin: http://localhost:5173/#/admin/login
- Ayuda del panel: http://localhost:5173/#/admin/ayuda
- API docs: http://localhost:8000/docs (oculto si `ENVIRONMENT=production`)
- Health: http://localhost:8000/health

Usuario seed (solo local, `backend/.env`):

```text
ADMIN_EMAIL / ADMIN_PASSWORD
```

El login del panel **no precarga el email**. Hay ojito para ver la contraseña.

El asistente está abajo a la derecha (logo Webxpert + “¿En qué te ayudo?”). En **Conversaciones** se puede simular un visitante.

---

## 4. Variables de entorno

Nunca commitear `.env`.

### Raíz — `.env.example`

| Variable | Uso |
|---|---|
| `VITE_API_URL` | Vacío en local **y** en Railway (mismo origen). |
| `VITE_FORMSPREE_FORM_ID` | Formulario de contacto del sitio. |

### Backend — `backend/.env.example`

| Variable | Uso |
|---|---|
| `ENVIRONMENT` | `development` local. En Railway: **`production`**. |
| `DATABASE_URL` | SQLite local o Postgres. Railway la inyecta al ligar el plugin. |
| `JWT_SECRET` | En producción: **32+ caracteres**, no el valor `dev-only-...`. Si no, el API no arranca. |
| `JWT_EXPIRE_MINUTES` | Default 720. |
| `CORS_ORIGINS` | Local: Vite. En Railway, mismo origen; agregá el dominio propio. El `*.up.railway.app` se suma solo. |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Usuario seed (solo la primera vez). |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Opcional. Default modelo `gpt-4o-mini`. |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Opcional. Default `gemini-3.6-flash`. |
| `LLM_MAX_OUTPUT_TOKENS` | Default 1536. |
| `LOG_LEVEL` / `LOG_MESSAGE_BODY` | `LOG_MESSAGE_BODY=false` por privacidad. |

`PORT` lo pone Railway. Start command: no hace falta. El Dockerfile ya corre `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`. **No** uses `uvicorn main:app`.

---

## 5. Base de datos

11 tablas: `tenants`, `users`, `assistants`, `contacts`, `conversations`, `messages`, `leads`, `knowledge_items`, `intents`, `services`, `pricing`.

Postgres local (Docker): usuario/password/db `webxpert`, puerto 5432.

DDL para HeidiSQL: `backend/schema.sql` (PostgreSQL, no MySQL). En Railway no hace falta ejecutarlo a mano: `create_all` + seed al boot.

Contactos del chat: `name`, `last_name`, `mobile`. El `phone` interno del widget es `web:<visitor_id>`.

---

## 6. Migraciones

```bash
cd backend
alembic upgrade head
alembic revision -m "descripcion"
```

---

## 7. Ejecución local

Terminal 1: `uvicorn` en `backend/`  
Terminal 2: `npm run dev` en la raíz  

Vite proxy: `/api` y `/health` → `http://127.0.0.1:8000`.

API + front en Docker:

```bash
docker compose --profile full up --build
```

(Ese compose usa el Dockerfile de `backend/`, solo API. El Dockerfile de la **raíz** es el de producción: sitio + API.)

---

## 8. Chat público

1. El visitante toca **Asistente**.
2. Carga nombre, apellido y teléfono (intake). Sin eso no chatea.
3. Pregunta. El motor usa intents, knowledge y precios; si hace falta, LLM.
4. Si pide un humano: dos links WhatsApp (Julio Pintos `5493764724207`, Agustín Burgos `5493765050885`) con nombre y teléfono precargados. WhatsApp no envía solo: el usuario toca Enviar.
5. La conversación queda en Admin. Estados: `BOT` → `WAITING_HUMAN` → `HUMAN` → `CLOSED`.
6. **Cerrar borra los mensajes** de esa conversación. No se deshace.

Endpoints:

- `POST /api/v1/chat/messages` (intake o mensaje)
- `GET /api/v1/chat/messages?visitor_token=`

El visitante no se loguea. Hay `visitor_id` en localStorage y JWT de chat. Polling cada 4 s si un operador responde.

---

## 9. Panel admin (`#/admin`)

| Ruta | Qué hace |
|---|---|
| `#/admin/login` | Email vacío + ojito en la clave |
| `#/admin` | Dashboard |
| `#/admin/conversaciones` | Bandeja, tomar / reactivar bot / cerrar, simular visitante |
| `#/admin/leads` | Pipeline (NEW → … → WON/LOST) |
| `#/admin/conocimiento` | FAQ y textos que el bot puede decir |
| `#/admin/servicios` | Catálogo |
| `#/admin/precios` | Únicos números que la IA puede citar |
| `#/admin/assistant` | Prompt, tono, LLM, umbral, handoff |
| `#/admin/ayuda` | Manual paso a paso |

---

## 10. OpenAI y Gemini

Claves en `backend/.env` (Railway: variables del servicio). Proveedor activo: **Admin → Assistant**.

Sin clave, el bot sigue con FAQ y knowledge. No llama al LLM.

System prompt: se edita en Admin → Assistant (el seed carga el inicial).

---

## 11. Producción en Railway

Sitio + API en **un** servicio. Postgres en otro, ligado al primero.

### 11.1 Postgres

1. Add Service → Database → PostgreSQL.
2. En el servicio del sitio/API: Connect / Add variable reference (inyecta `DATABASE_URL`).
3. HeidiSQL opcional: red **PostgreSQL**, SSL require si usás URL pública.

### 11.2 Servicio web (sitio + API)

1. New Service → GitHub de este repo.
2. **Root Directory vacío** (raíz del repo, **no** `backend`). Usa el `Dockerfile` y `railway.toml` de la raíz.
3. Variables:

| Variable | Valor |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | la del plugin (no editar, no SQLite) |
| `JWT_SECRET` | random 32+ caracteres |
| `CORS_ORIGINS` | `https://www.webxpert.com.ar,https://webxpert.com.ar` si el dominio apunta acá |
| `ADMIN_EMAIL` | login del panel |
| `ADMIN_PASSWORD` | fuerte (solo seed si el admin no existe) |
| `OPENAI_API_KEY` / `GEMINI_API_KEY` | opcional |

No pegues `uvicorn main:app`. Healthcheck: `GET /health`.

Pruebas:

- `https://TU-SERVICIO.up.railway.app/health` → `{"status":"ok","service":"webxpert-assistant"}`
- `https://TU-SERVICIO.up.railway.app/` → el sitio (no Not Found)
- `https://TU-SERVICIO.up.railway.app/#/admin` → panel

Logs `handled request` después de `Starting Container` son el proxy de Railway, no un error.

---

## 12. Testing

```bash
cd backend
.venv\Scripts\activate
pytest -q
```

Cubre intents, price guard, leads, handoff WhatsApp, chat con intake, CRUD, conversaciones.

---

## 13. Troubleshooting

| Problema | Qué revisar |
|---|---|
| `/` da Not Found | Root Directory tiene que estar **vacío** y el deploy tiene que usar el Dockerfile de la raíz |
| API no arranca en prod | `JWT_SECRET` corto o `dev-only-...` |
| Sitio sin chat / admin sin datos | Mismo origen; no hace falta `VITE_API_URL` |
| `connection refused` Postgres | SQLite local, o `docker compose up -d db` |
| Bot mudo | Assistant `enabled`, chat `bot_enabled`, no está en `WAITING_HUMAN` |
| Inventa precios | Admin → Precios; el engine solo usa la DB |
| CORS | `CORS_ORIGINS` + dominio Railway automático |
| Login con email ya escrito | Ya no: el campo arranca vacío. Si el browser lo completa, es el gestor de contraseñas |

---

## Sitio público

SPA React 19 + Vite + Tailwind + HashRouter + Formspree + Framer Motion.

```text
#/  #/servicios  #/servicios/:slug  #/nosotros  #/contacto  #/privacidad  #/terminos
#/admin  …
```

Widget de asistente en las páginas públicas (no en el admin).

Precios de referencia publicados (USD, estimativos, −40 % respecto del listado anterior): landing 210–360, institucional 420–720, e-commerce 720–1.200, a medida desde 1.200, sistemas 1.500–2.400, auditorías 150–300, SEO 180–480.

---

## Estructura

```text
Dockerfile              producción: Vite + FastAPI
railway.toml            healthcheck /health
docker-compose.yml      Postgres local (+ API opcional)
src/                    sitio, widget, panel admin
src/admin/pages/HelpPage.tsx
src/chat/WebChatWidget.tsx
backend/app/            FastAPI, modelos, AI, seed
backend/schema.sql      DDL Postgres / HeidiSQL
backend/tests/
ANALISIS-DE-VALOR.md    valuación del producto (USD)
```
