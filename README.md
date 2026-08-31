# webXpert + Webxpert AI Assistant

Sitio institucional de webXpert (React + Vite) y, en el mismo repositorio, el **Webxpert AI Assistant**: asistente comercial en el chat de la web, con panel administrativo.

El canal activo es el **widget del sitio público**. El visitante habla con el asistente desde cualquier página.

---

## 1. Arquitectura

```text
Visitante en www.webxpert.com.ar
        ↓  widget (todas las páginas públicas)
POST/GET /api/v1/chat/messages
        ↓
FastAPI  →  MessageProcessor (channel=web)
              ↓
    IntentClassifier (keywords)
              ↓
 FAQ / knowledge  ó  LLM acotado (OpenAI o Gemini)
              ↓
    LeadDetector + PostgreSQL
              ↓
Bandeja Admin (#/admin)  ·  respuesta en el mismo widget

Frontend Vite (Vercel)
  ├── sitio público  #/  #/servicios  #/contacto  …
  ├── widget de chat (solo páginas públicas)
  └── panel admin    #/admin

Backend FastAPI (Railway)
  └── PostgreSQL (plugin Railway o HeidiSQL)
```

La IA **no inventa precios ni plazos**. Si no hay un precio cargado en la base, responde que el proyecto se cotiza.

`tenant_id` está en los modelos desde el día 1 (tenant actual: `webxpert`).

---

## 2. Requisitos

- Node.js 18+ y npm
- Python 3.11+ (recomendado 3.12)
- Docker Desktop **opcional** (PostgreSQL). Sin Docker, el backend usa SQLite en localhost.
- Opcional: cuenta OpenAI y/o Google Gemini
- Producción: cuenta Railway (API + PostgreSQL) y HeidiSQL 12+ si querés administrar la base a mano

---

## 3. Instalación (localhost)

### Base de datos

Sin Docker (recomendado para el primer arranque local): dejar `DATABASE_URL=sqlite:///./webxpert.db` en `backend/.env`. El API crea tablas y seed al iniciar.

Con Docker y PostgreSQL:

```bash
docker compose up -d db
```

y en `backend/.env`:

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

En desarrollo el API también intenta crear tablas y hacer seed al arrancar.

### Frontend

En la raíz del repo:

```bash
copy .env.example .env
npm install
npm run dev
```

- Sitio: http://localhost:5173/
- Admin: http://localhost:5173/#/admin/login
- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Usuario inicial (solo local, definido en `backend/.env`):

```text
admin@webxpert.com
changeme
```

El chat público está en la esquina inferior derecha del sitio. Desde **Conversaciones** se puede simular un visitante sin abrir el widget.

---

## 4. Variables de entorno

Nunca commitear `.env`. Usar los ejemplos:

### Raíz — `.env.example`

| Variable | Uso |
|---|---|
| `VITE_API_URL` | Vacío en local (proxy Vite). En producción, URL pública del API. |
| `VITE_FORMSPREE_FORM_ID` | Formulario de contacto del sitio (ya existía). |

### Backend — `backend/.env.example`

| Variable | Uso |
|---|---|
| `DATABASE_URL=postgresql+psycopg://webxpert:webxpert@localhost:5432/webxpert` | PostgreSQL |
| `JWT_SECRET` | Cambiar sí o sí antes de producción |
| `CORS_ORIGINS` | Orígenes del frontend, separados por coma |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Usuario seed |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | OpenAI. Vacío = ese proveedor no está listo |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Google Gemini. El activo se elige en Admin → Assistant |
| `LOG_MESSAGE_BODY` | `false` por privacidad |

---

## 5. Base de datos

PostgreSQL 16 vía Docker (local):

```text
usuario: webxpert
password: webxpert
db: webxpert
puerto: 5432
```

En producción usá el Postgres de Railway. El DDL para HeidiSQL está en `backend/schema.sql` (es PostgreSQL, no MySQL).

Modelos principales: `Tenant`, `User`, `Assistant`, `Contact`, `Conversation`, `Message`, `Lead`, `KnowledgeItem`, `Intent`, `Service`, `Pricing`.

---

## 6. Migraciones

```bash
cd backend
alembic upgrade head
alembic revision -m "descripcion"   # cuando haya cambios de schema
```

La revisión inicial crea el schema a partir de los modelos SQLAlchemy.

---

## 7. Ejecución local

Terminal 1: `uvicorn` en `backend/`  
Terminal 2: `npm run dev` en la raíz  

Si usás PostgreSQL: `docker compose up -d db` antes del API.  

El proxy de Vite reenvía `/api` a `http://127.0.0.1:8000`.

Para levantar API también en Docker:

```bash
docker compose --profile full up --build
```

---

## 8. Chat en la web

El visitante habla con el mismo motor (FAQ, precios, IA, leads y derivación a humano) desde el widget.

- Público: `POST /api/v1/chat/messages` y `GET /api/v1/chat/messages?visitor_token=`
- El visitante no inicia sesión. El navegador guarda un `visitor_id` anónimo y un token JWT de chat.
- Si un operador toma la conversación en Admin, el bot se apaga y las respuestas humanas aparecen en el widget (polling cada 4 s).

---

## 9. Configuración OpenAI y Gemini

Las claves van en `backend/.env`. El proveedor **activo** se elige en **Admin → Assistant**.

### OpenAI

1. Crear una API key en OpenAI.
2. `OPENAI_API_KEY` y opcionalmente `OPENAI_MODEL` (por defecto `gpt-4o-mini`).

### Gemini

1. Crear una API key en [Google AI Studio](https://aistudio.google.com/apikey).
2. `GEMINI_API_KEY` y opcionalmente `GEMINI_MODEL` (por defecto `gemini-3.6-flash`).

Si el proveedor elegido no tiene clave, el bot responde con FAQ, templates e información de la knowledge base. No llama al LLM.

El system prompt se edita en **Admin → Assistant**, no está hardcodeado en el código de runtime (el seed carga el valor inicial).

---

## 10. Producción: Railway + HeidiSQL + Vercel

El frontend sigue en Vercel. El API y PostgreSQL van a Railway. No hace falta Docker en tu PC para este paso.

### 10.1 PostgreSQL en Railway y `schema.sql` en Heidi

1. En Railway: New Project → Empty Project → Add Service → **Database → PostgreSQL**.
2. Abrí el servicio Postgres → Variables. Copiá host, puerto, user, password y database (o `DATABASE_PUBLIC_URL`).
3. HeidiSQL 12+ → Nueva sesión:
   - Network type: **PostgreSQL (TCP/IP)** (no MySQL)
   - Host / User / Password / Port / Database de Railway
   - SSL Mode: **require** si usás la URL pública
4. Conectá → Query → abrí `backend/schema.sql` → Ejecutar (F9) sobre una base vacía.
5. Ligá Postgres al servicio API (Add variable reference). Railway inyecta `DATABASE_URL`; el API la convierte a `postgresql+psycopg://`.

El seed corre al arrancar el API (tenant, admin, knowledge, servicios). No hace falta insertar datos a mano en Heidi.

Si el API arranca antes del SQL, `create_all` también crea las tablas. `schema.sql` es para controlarlo desde Heidi.

### 10.2 API en Railway

1. New Service → GitHub (o deploy desde esta carpeta) → **Root Directory = `backend`**.
2. El `Dockerfile` usa `$PORT`. Healthcheck: `GET /health`.
3. Variables del servicio API:

| Variable | Valor |
|---|---|
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | la que inyecta el plugin Postgres (no la edites a mano) |
| `JWT_SECRET` | string aleatorio de 32+ caracteres |
| `CORS_ORIGINS` | `https://www.webxpert.com.ar,https://webxpert.com.ar` |
| `ADMIN_EMAIL` | el login del panel |
| `ADMIN_PASSWORD` | contraseña fuerte (solo se usa en el seed si el admin no existe) |
| `OPENAI_API_KEY` / `GEMINI_API_KEY` | opcional |
| `OPENAI_MODEL` / `GEMINI_MODEL` | opcional |

En producción `/docs` queda oculto. Si `JWT_SECRET` es el de desarrollo, el API **no arranca**.

Probá: `https://TU-SERVICIO.up.railway.app/health` → `{"status":"ok",...}`.

### 10.3 Frontend en Vercel

En el proyecto Vite (build de producción):

| Variable | Valor |
|---|---|
| `VITE_API_URL` | `https://TU-SERVICIO.up.railway.app` (sin barra final) |

Rebuild de Vercel después de cambiarla. El admin queda en `https://www.webxpert.com.ar/#/admin`.

Login seed (cambiá la clave en Railway): `admin@webxpert.com` / la `ADMIN_PASSWORD` que definiste.

---

## 11. Testing

```bash
cd backend
.venv\Scripts\activate
pytest -q
```

Cubre: intents, protección de precios, scoring de leads, fallback/handoff, chat web público, CRUD de knowledge/services/pricing, conversaciones simuladas.

---

## 12. Troubleshooting

| Problema | Qué revisar |
|---|---|
| Admin no carga datos | Backend en `:8000`, login hecho, `VITE_API_URL` vacío en local |
| `connection refused` Postgres | Usá SQLite en local, o instalá Docker y `docker compose up -d db` |
| El bot no responde | Assistant `enabled`, conversación `bot_enabled`, no está en `WAITING_HUMAN` |
| Inventa precios | No debería: revisar ítems de **Precios** activos; el engine usa solo la DB |
| OpenAI error | Clave, billing, o dejar la clave vacía para modo FAQ |
| CORS en producción | `CORS_ORIGINS` con el origen exacto del frontend |

---

## Sitio público (ya existente)

SPA React 19 + Vite + Tailwind + HashRouter + Formspree.

```text
#/  #/servicios  #/servicios/:slug  #/nosotros  #/contacto  #/privacidad  #/terminos
```

No reemplazar esas rutas ni el formulario de contacto. El panel admin es una rama de rutas nueva (`#/admin`).

---

## Estructura nueva relevante

```text
backend/app/          FastAPI, modelos, AI engine, chat web
backend/tests/
src/admin/            Panel TypeScript (identidad visual webXpert)
docker-compose.yml    PostgreSQL local
```
