export type DashboardStats = {
  conversations_today: number;
  new_leads: number;
  qualified_leads: number;
  ai_handled: number;
  handed_off: number;
};

export type Contact = {
  id: string;
  phone: string;
  name: string | null;
  last_name: string | null;
  mobile: string | null;
  email: string | null;
};

export type Message = {
  id: string;
  conversation_id: string;
  direction: "INBOUND" | "OUTBOUND";
  sender: string;
  content: string;
  message_type: string;
  intent: string | null;
  confidence: number | null;
  ai_generated: boolean;
  created_at: string;
};

export type Conversation = {
  id: string;
  contact_id: string;
  status: "BOT" | "WAITING_HUMAN" | "HUMAN" | "CLOSED";
  channel: string;
  bot_enabled: boolean;
  last_message_at: string;
  started_at: string;
  contact: Contact | null;
  last_message: string | null;
  lead_score: number | null;
  needs_human: boolean;
  messages?: Message[];
};

export type Lead = {
  id: string;
  contact_id: string;
  conversation_id: string;
  status: string;
  score: number;
  service_interest: string | null;
  notes: string | null;
  created_at: string;
  contact: Contact | null;
};

export type KnowledgeItem = {
  id: string;
  category: string;
  title: string;
  content: string;
  keywords: string[];
  active: boolean;
  priority: number;
};

export type ServiceItem = {
  id: string;
  name: string;
  description: string;
  active: boolean;
  starting_price: string | null;
  price_visible: boolean;
  category: string;
};

export type PricingItem = {
  id: string;
  service_id: string;
  price: number | null;
  price_max: number | null;
  currency: string;
  price_type: string;
  description: string | null;
  active: boolean;
};

export type Assistant = {
  id: string;
  name: string;
  company_name: string;
  enabled: boolean;
  system_prompt: string;
  language: string;
  tone: string;
  fallback_enabled: boolean;
  human_handoff_enabled: boolean;
  intent_threshold: number;
  llm_provider: string;
  llm_model: string | null;
};

export type AIProviderInfo = {
  id: string;
  label: string;
  configured: boolean;
  default_model: string;
};

export type AIStatus = {
  active_provider: string;
  providers: AIProviderInfo[];
};
