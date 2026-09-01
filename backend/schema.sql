-- =============================================================================
-- Webxpert AI Assistant — schema PostgreSQL
-- =============================================================================
-- Este archivo es para PostgreSQL (Railway). HeidiSQL se conecta a Postgres,
-- no a MySQL: en la ventana de conexión elegí "PostgreSQL (TCP/IP)".
--
-- HeidiSQL 12 o superior:
--   1. Nueva sesión → Network type: PostgreSQL (TCP/IP)
--   2. Host / User / Password / Database / Port: los de Railway → Postgres
--      (Variables: PGHOST, PGUSER, PGPASSWORD, PGDATABASE, PGPORT
--      o DATABASE_PUBLIC_URL)
--   3. Si pide SSL: activar SSL Mode = require (URL pública de Railway)
--   4. Conectar → Query → cargar este archivo → Ejecutar (F9)
--
-- Correrlo sobre una base VACÍA. El API, al arrancar, completa el seed
-- (tenant webxpert, admin, knowledge, servicios e intents).
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug VARCHAR(80) NOT NULL,
    name VARCHAR(160) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_tenants_slug ON tenants (slug);

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    email VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(160) NOT NULL DEFAULT 'Administrador',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_users_tenant_id ON users (tenant_id);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS assistants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    name VARCHAR(160) NOT NULL DEFAULT 'Webxpert Assistant',
    company_name VARCHAR(160) NOT NULL DEFAULT 'Webxpert',
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    system_prompt TEXT NOT NULL,
    language VARCHAR(16) NOT NULL DEFAULT 'es',
    tone VARCHAR(255) NOT NULL DEFAULT 'Profesional, amable, claro, directo, natural, argentino',
    fallback_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    human_handoff_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    intent_threshold FLOAT NOT NULL DEFAULT 0.6,
    llm_provider VARCHAR(32) NOT NULL DEFAULT 'openai',
    llm_model VARCHAR(80),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_assistants_tenant_id ON assistants (tenant_id);

CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    phone VARCHAR(64) NOT NULL,
    name VARCHAR(160),
    last_name VARCHAR(160),
    mobile VARCHAR(32),
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_contact_tenant_phone UNIQUE (tenant_id, phone)
);

CREATE INDEX IF NOT EXISTS ix_contacts_phone ON contacts (phone);
CREATE INDEX IF NOT EXISTS ix_contacts_tenant_id ON contacts (tenant_id);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    contact_id UUID NOT NULL REFERENCES contacts (id),
    assistant_id UUID NOT NULL REFERENCES assistants (id),
    status VARCHAR(13) NOT NULL DEFAULT 'BOT',
    channel VARCHAR(32) NOT NULL DEFAULT 'web',
    bot_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    assigned_to UUID REFERENCES users (id),
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_conversations_tenant_id ON conversations (tenant_id);
CREATE INDEX IF NOT EXISTS ix_conversations_last_message_at ON conversations (last_message_at);
CREATE INDEX IF NOT EXISTS ix_conversations_assistant_id ON conversations (assistant_id);
CREATE INDEX IF NOT EXISTS ix_conversations_status ON conversations (status);
CREATE INDEX IF NOT EXISTS ix_conversations_contact_id ON conversations (contact_id);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations (id),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    direction VARCHAR(8) NOT NULL,
    sender VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    message_type VARCHAR(32) NOT NULL DEFAULT 'text',
    intent VARCHAR(80),
    confidence FLOAT,
    ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
    external_id VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_messages_created_at ON messages (created_at);
CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages (conversation_id);
CREATE INDEX IF NOT EXISTS ix_messages_tenant_id ON messages (tenant_id);
CREATE INDEX IF NOT EXISTS ix_messages_external_id ON messages (external_id);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    contact_id UUID NOT NULL REFERENCES contacts (id),
    conversation_id UUID NOT NULL REFERENCES conversations (id),
    status VARCHAR(9) NOT NULL DEFAULT 'NEW',
    score INTEGER NOT NULL DEFAULT 0,
    service_interest VARCHAR(160),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_leads_status ON leads (status);
CREATE INDEX IF NOT EXISTS ix_leads_contact_id ON leads (contact_id);
CREATE INDEX IF NOT EXISTS ix_leads_conversation_id ON leads (conversation_id);
CREATE INDEX IF NOT EXISTS ix_leads_tenant_id ON leads (tenant_id);

CREATE TABLE IF NOT EXISTS knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    category VARCHAR(9) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    keywords JSON NOT NULL DEFAULT '[]'::json,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    priority INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_knowledge_items_category ON knowledge_items (category);
CREATE INDEX IF NOT EXISTS ix_knowledge_items_tenant_id ON knowledge_items (tenant_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_items_active ON knowledge_items (active);

CREATE TABLE IF NOT EXISTS intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    slug VARCHAR(80) NOT NULL,
    name VARCHAR(160) NOT NULL,
    keywords JSON NOT NULL DEFAULT '[]'::json,
    response_template TEXT,
    knowledge_category VARCHAR(40),
    requires_handoff BOOLEAN NOT NULL DEFAULT FALSE,
    is_pricing BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    weight FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_intents_slug ON intents (slug);
CREATE INDEX IF NOT EXISTS ix_intents_tenant_id ON intents (tenant_id);

CREATE TABLE IF NOT EXISTS services (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    name VARCHAR(160) NOT NULL,
    description TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    starting_price VARCHAR(80),
    price_visible BOOLEAN NOT NULL DEFAULT TRUE,
    category VARCHAR(80) NOT NULL DEFAULT 'general',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_services_tenant_id ON services (tenant_id);

CREATE TABLE IF NOT EXISTS pricing (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants (id),
    service_id UUID NOT NULL REFERENCES services (id),
    price NUMERIC(12, 2),
    price_max NUMERIC(12, 2),
    currency VARCHAR(8) NOT NULL DEFAULT 'USD',
    price_type VARCHAR(13) NOT NULL DEFAULT 'STARTING_FROM',
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_pricing_service_id ON pricing (service_id);
CREATE INDEX IF NOT EXISTS ix_pricing_tenant_id ON pricing (tenant_id);
