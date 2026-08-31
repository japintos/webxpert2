from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.assistant import Assistant
from app.models.intent import Intent
from app.models.knowledge import KnowledgeCategory, KnowledgeItem
from app.models.pricing import PriceType, Pricing
from app.models.service import Service
from app.models.tenant import Tenant
from app.models.user import User
from app.seed_data import DEFAULT_SYSTEM_PROMPT

KNOWLEDGE = [
    {
        "category": KnowledgeCategory.COMPANY,
        "title": "¿Quién es Webxpert?",
        "content": (
            "Webxpert es un Software Studio de Posadas, Misiones. Diseñamos y desarrollamos "
            "productos digitales: sitios web, sistemas web, aplicaciones empresariales, "
            "e-commerce, automatizaciones, integraciones y soluciones con inteligencia artificial."
        ),
        "keywords": ["webxpert", "quien", "quién", "empresa", "estudio", "studio"],
        "priority": 100,
    },
    {
        "category": KnowledgeCategory.SERVICES,
        "title": "Desarrollo de sitios web",
        "content": (
            "¡Claro! Podemos ayudarte con eso. Hacemos landing pages, sitios institucionales "
            "y webs a medida, modernas, responsivas y orientadas a conversión. "
            "Para orientarte mejor, ¿buscás una web principalmente informativa o necesitás "
            "también funciones como reservas, usuarios, ventas o algún sistema personalizado?"
        ),
        "keywords": ["pagina", "página", "sitio", "web", "landing", "institucional"],
        "priority": 90,
    },
    {
        "category": KnowledgeCategory.SERVICES,
        "title": "E-commerce",
        "content": (
            "Sí, desarrollamos tiendas online con catálogo, carrito, checkout y pasarela de pago "
            "(por ejemplo Mercado Pago), más un panel para pedidos, clientes y stock. "
            "¿Ya tenés los productos y contenidos preparados o también habría que ayudarte con eso?"
        ),
        "keywords": ["tienda", "ecommerce", "e-commerce", "online", "vender", "carrito"],
        "priority": 90,
    },
    {
        "category": KnowledgeCategory.SERVICES,
        "title": "Sistemas y software a medida",
        "content": (
            "Desarrollamos sistemas web personalizados, paneles internos, ERP/CRM livianos y "
            "aplicaciones empresariales. El alcance se define según procesos, usuarios e integraciones. "
            "¿Qué procesos te gustaría digitalizar primero?"
        ),
        "keywords": ["sistema", "software", "medida", "erp", "crm", "stock", "gestion"],
        "priority": 85,
    },
    {
        "category": KnowledgeCategory.SERVICES,
        "title": "Automatizaciones, integraciones e IA",
        "content": (
            "También hacemos automatizaciones, integraciones entre sistemas y soluciones con IA, "
            "siempre a partir de un alcance claro. Si me contás qué herramientas usás hoy, te oriento."
        ),
        "keywords": ["automatizacion", "integracion", "integrar", "ia", "inteligencia", "api"],
        "priority": 80,
    },
    {
        "category": KnowledgeCategory.PRICING,
        "title": "¿Cuánto cuesta una web?",
        "content": (
            "Los valores de referencia en USD son estimativos y se ajustan al alcance: "
            "Landing Page USD 350-600; Sitio institucional USD 700-1.200. "
            "No son presupuestos finales: dependen de secciones, funcionalidades y contenidos."
        ),
        "keywords": ["precio", "cuesta", "sale", "web", "pagina", "landing", "institucional"],
        "priority": 95,
    },
    {
        "category": KnowledgeCategory.FAQ,
        "title": "¿Cuánto demora un desarrollo?",
        "content": (
            "Los plazos dependen del alcance, los contenidos y las revisiones. "
            "No te puedo confirmar una fecha exacta por acá. Si me contás el tipo de proyecto, "
            "un especialista te estima con más precisión."
        ),
        "keywords": ["demora", "tardan", "tiempo", "plazo", "cuando", "cuándo", "entrega"],
        "priority": 80,
    },
    {
        "category": KnowledgeCategory.PROCESS,
        "title": "¿Cómo es el proceso de contratación?",
        "content": (
            "En general: 1) conversamos el objetivo, 2) armamos una propuesta, 3) definimos alcance "
            "y forma de pago, 4) diseñamos y desarrollamos con revisiones, 5) publicamos y damos soporte. "
            "¿Querés que un especialista te contacte para avanzar?"
        ),
        "keywords": ["contratar", "proceso", "como trabajan", "cómo trabajan", "pasos"],
        "priority": 80,
    },
    {
        "category": KnowledgeCategory.TECHNICAL,
        "title": "¿Pueden integrar mi sistema actual?",
        "content": (
            "Podemos evaluar integraciones (pagos, APIs, ERPs, Mercado Pago, etc.). "
            "Hay que revisar el sistema actual para confirmar factibilidad. "
            "Si querés, derivo la consulta a un especialista técnico."
        ),
        "keywords": ["integrar", "integracion", "api", "mercado pago", "sistema actual"],
        "priority": 75,
    },
    {
        "category": KnowledgeCategory.TECHNICAL,
        "title": "Tecnologías",
        "content": (
            "Trabajamos con stacks modernos de desarrollo web (por ejemplo React, APIs y bases de datos). "
            "La tecnología se elige según el proyecto, no al revés."
        ),
        "keywords": ["tecnologia", "tecnologías", "react", "stack", "framework"],
        "priority": 60,
    },
    {
        "category": KnowledgeCategory.SERVICES,
        "title": "Mantenimiento y hosting",
        "content": (
            "Ofrecemos mantenimiento y soporte. El hosting se define según el proyecto "
            "(nube, rendimiento y seguridad). El valor depende del servicio contratado."
        ),
        "keywords": ["mantenimiento", "hosting", "soporte", "servidor", "nube"],
        "priority": 70,
    },
    {
        "category": KnowledgeCategory.CONTACT,
        "title": "Contacto",
        "content": (
            "Podés escribirnos desde el chat de esta web o al correo julioapintos1@gmail.com. "
            "Estamos en Posadas, Misiones. Teléfono: +54 9 3764724207. "
            "Si preferís, derivo esta conversación a una persona del equipo."
        ),
        "keywords": ["contacto", "telefono", "teléfono", "email", "mail", "ubicacion"],
        "priority": 70,
    },
    {
        "category": KnowledgeCategory.POLICIES,
        "title": "Políticas",
        "content": (
            "Respetamos la privacidad de tus datos y no compartimos información de proyectos "
            "con terceros. Los detalles legales están en el sitio webxpert.com.ar."
        ),
        "keywords": ["privacidad", "datos", "terminos", "términos", "legal"],
        "priority": 40,
    },
]

INTENTS = [
    {
        "slug": "pricing_web",
        "name": "Precio web",
        "keywords": ["cuanto sale", "cuanto cuesta", "precio", "landing", "pagina web", "sitio institucional", "web"],
        "is_pricing": True,
        "knowledge_category": "PRICING",
        "weight": 1.2,
    },
    {
        "slug": "pricing_ecommerce",
        "name": "Precio e-commerce",
        "keywords": ["cuanto sale tienda", "precio ecommerce", "precio tienda", "tienda online", "ecommerce"],
        "is_pricing": True,
        "knowledge_category": "PRICING",
        "weight": 1.3,
    },
    {
        "slug": "pricing_custom_system",
        "name": "Precio sistema a medida",
        "keywords": ["sistema stock", "cuanto sale un sistema", "precio sistema", "erp", "crm"],
        "is_pricing": True,
        "knowledge_category": "PRICING",
        "weight": 1.2,
    },
    {
        "slug": "services_web",
        "name": "Servicio web",
        "keywords": ["quiero una pagina", "necesito una web", "pagina para mi empresa", "sitio web"],
        "knowledge_category": "SERVICES",
        "response_template": (
            "¡Claro! Podemos ayudarte con eso. Para orientarte mejor, ¿buscás una web "
            "principalmente informativa o necesitás también funciones como reservas, "
            "usuarios, ventas o algún sistema personalizado?"
        ),
        "weight": 1.3,
    },
    {
        "slug": "services_ecommerce",
        "name": "Servicio e-commerce",
        "keywords": ["hacen tiendas", "tienda online", "ecommerce", "vender online"],
        "knowledge_category": "SERVICES",
        "weight": 1.2,
    },
    {
        "slug": "services_software",
        "name": "Servicio software",
        "keywords": ["necesito un sistema", "software a medida", "sistema para stock", "aplicacion"],
        "knowledge_category": "SERVICES",
        "weight": 1.2,
    },
    {
        "slug": "development_time",
        "name": "Tiempos de desarrollo",
        "keywords": ["cuanto tardan", "demora", "plazo", "cuando queda listo", "tiempos"],
        "knowledge_category": "FAQ",
        "weight": 1.2,
    },
    {
        "slug": "how_we_work",
        "name": "Cómo trabajamos",
        "keywords": ["como trabajan", "proceso", "como contratar", "pasos"],
        "knowledge_category": "PROCESS",
        "weight": 1.1,
    },
    {
        "slug": "technologies",
        "name": "Tecnologías",
        "keywords": ["que tecnologias", "react", "stack", "framework"],
        "knowledge_category": "TECHNICAL",
        "weight": 1.0,
    },
    {
        "slug": "maintenance",
        "name": "Mantenimiento",
        "keywords": ["mantenimiento", "soporte mensual", "actualizar la web"],
        "knowledge_category": "SERVICES",
        "weight": 1.0,
    },
    {
        "slug": "hosting",
        "name": "Hosting",
        "keywords": ["hosting", "servidor", "donde se hostea", "nube"],
        "knowledge_category": "SERVICES",
        "weight": 1.0,
    },
    {
        "slug": "contact",
        "name": "Contacto",
        "keywords": ["telefono", "email", "contacto", "donde estan", "posadas"],
        "knowledge_category": "CONTACT",
        "weight": 1.0,
    },
    {
        "slug": "human_agent",
        "name": "Hablar con una persona",
        "keywords": ["hablar con alguien", "persona", "asesor", "humano", "operador"],
        "requires_handoff": True,
        "weight": 1.5,
    },
    {
        "slug": "quote_request",
        "name": "Pedido de presupuesto",
        "keywords": ["presupuesto", "cotizacion", "cotizar", "necesito que me coticen"],
        "is_pricing": True,
        "knowledge_category": "PRICING",
        "weight": 1.4,
    },
    {
        "slug": "custom_development",
        "name": "Desarrollo a medida",
        "keywords": ["a medida", "personalizado", "integrar mercado pago", "desarrollo custom"],
        "knowledge_category": "TECHNICAL",
        "weight": 1.1,
    },
]

SERVICES = [
    {
        "name": "Web institucional",
        "description": "Web corporativa de 3 a 6 secciones, adaptable y escalable.",
        "starting_price": "USD 700 - 1.200",
        "category": "web",
    },
    {
        "name": "Landing Page",
        "description": "Página única optimizada para conversión y performance.",
        "starting_price": "USD 350 - 600",
        "category": "web",
    },
    {
        "name": "E-commerce",
        "description": "Tienda online con carrito, pasarela de pago y panel de gestión.",
        "starting_price": "USD 1.200 - 2.000",
        "category": "commerce",
    },
    {
        "name": "Sistema web personalizado",
        "description": "Desarrollo a medida según procesos del cliente.",
        "starting_price": "Desde USD 2.000",
        "category": "software",
    },
    {
        "name": "Aplicaciones empresariales",
        "description": "ERP, CRM o paneles internos para administración y control.",
        "starting_price": "USD 2.500 - 4.000",
        "category": "software",
    },
    {
        "name": "Automatizaciones",
        "description": "Automatización de procesos e integraciones entre herramientas.",
        "starting_price": None,
        "price_visible": False,
        "category": "automation",
    },
    {
        "name": "Integraciones",
        "description": "Conexión con APIs, pagos, ERPs y sistemas existentes.",
        "starting_price": None,
        "price_visible": False,
        "category": "automation",
    },
    {
        "name": "IA",
        "description": "Asistentes, automatizaciones y funcionalidades con inteligencia artificial.",
        "starting_price": None,
        "price_visible": False,
        "category": "ai",
    },
    {
        "name": "Mantenimiento",
        "description": "Soporte, actualizaciones y monitoreo del producto publicado.",
        "starting_price": None,
        "price_visible": False,
        "category": "support",
    },
]


def seed(db: Session) -> None:
    tenant = db.scalar(select(Tenant).where(Tenant.slug == "webxpert"))
    if not tenant:
        tenant = Tenant(slug="webxpert", name="Webxpert")
        db.add(tenant)
        db.flush()

    user = db.scalar(select(User).where(User.email == settings.ADMIN_EMAIL.lower()))
    if not user:
        db.add(
            User(
                tenant_id=tenant.id,
                email=settings.ADMIN_EMAIL.lower(),
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                full_name="Administrador Webxpert",
            )
        )

    assistant = db.scalar(select(Assistant).where(Assistant.tenant_id == tenant.id))
    if not assistant:
        db.add(
            Assistant(
                tenant_id=tenant.id,
                name="Webxpert Assistant",
                company_name="Webxpert",
                enabled=True,
                system_prompt=DEFAULT_SYSTEM_PROMPT,
                language="es",
                tone="Profesional, amable, claro, directo, natural, argentino",
                fallback_enabled=True,
                human_handoff_enabled=True,
                intent_threshold=0.6,
                llm_provider="openai",
                llm_model=None,
            )
        )

    if not db.scalar(select(KnowledgeItem).where(KnowledgeItem.tenant_id == tenant.id)):
        for item in KNOWLEDGE:
            db.add(KnowledgeItem(tenant_id=tenant.id, **item))

    if not db.scalar(select(Intent).where(Intent.tenant_id == tenant.id)):
        for item in INTENTS:
            db.add(Intent(tenant_id=tenant.id, **item))

    existing_services = list(db.scalars(select(Service).where(Service.tenant_id == tenant.id)))
    if not existing_services:
        created: dict[str, Service] = {}
        for item in SERVICES:
            service = Service(
                tenant_id=tenant.id,
                name=item["name"],
                description=item["description"],
                starting_price=item.get("starting_price"),
                price_visible=item.get("price_visible", True),
                category=item["category"],
                active=True,
            )
            db.add(service)
            db.flush()
            created[service.name] = service

        price_rows = [
            ("Landing Page", 350, 600, PriceType.STARTING_FROM, "Rango estimativo en USD."),
            ("Web institucional", 700, 1200, PriceType.STARTING_FROM, "Rango estimativo en USD."),
            ("E-commerce", 1200, 2000, PriceType.STARTING_FROM, "Rango estimativo en USD."),
            ("Sistema web personalizado", 2000, None, PriceType.STARTING_FROM, "Desde USD 2.000 según alcance."),
            ("Aplicaciones empresariales", 2500, 4000, PriceType.STARTING_FROM, "Rango estimativo en USD."),
            ("Automatizaciones", None, None, PriceType.ON_REQUEST, "Requiere evaluación."),
            ("Integraciones", None, None, PriceType.ON_REQUEST, "Requiere evaluación."),
            ("IA", None, None, PriceType.ON_REQUEST, "Requiere evaluación."),
            ("Mantenimiento", None, None, PriceType.ON_REQUEST, "Según el producto publicado."),
        ]
        for name, price, price_max, price_type, description in price_rows:
            service = created[name]
            db.add(
                Pricing(
                    tenant_id=tenant.id,
                    service_id=service.id,
                    price=price,
                    price_max=price_max,
                    currency="USD",
                    price_type=price_type,
                    description=description,
                    active=True,
                )
            )

    db.commit()


def main() -> None:
    init_db()
    db = SessionLocal()
    try:
        seed(db)
        print("Seed OK — tenant Webxpert, assistant, knowledge, services y admin creados.")
        print(f"Admin: {settings.ADMIN_EMAIL}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
