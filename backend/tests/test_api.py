from app.models.conversation import ConversationStatus


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_login_and_knowledge_crud(client, auth_headers):
    listed = client.get("/api/v1/knowledge", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) >= 1

    created = client.post(
        "/api/v1/knowledge",
        headers=auth_headers,
        json={
            "category": "FAQ",
            "title": "¿Trabajan sábados?",
            "content": "Coordinamos horarios con cada cliente.",
            "keywords": ["sabado", "horario"],
            "active": True,
            "priority": 1,
        },
    )
    assert created.status_code == 201
    item_id = created.json()["id"]

    patched = client.patch(
        f"/api/v1/knowledge/{item_id}",
        headers=auth_headers,
        json={"active": False},
    )
    assert patched.status_code == 200
    assert patched.json()["active"] is False

    deleted = client.delete(f"/api/v1/knowledge/{item_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_services_and_pricing(client, auth_headers):
    services = client.get("/api/v1/services", headers=auth_headers)
    assert services.status_code == 200
    first = services.json()[0]
    prices = client.get("/api/v1/pricing", headers=auth_headers)
    assert prices.status_code == 200
    assert any(row["service_id"] == first["id"] for row in prices.json())


def test_simulate_conversation_and_lead(client, auth_headers):
    inbound = client.post(
        "/api/v1/simulate/inbound",
        headers=auth_headers,
        json={"phone": "5493764000000", "name": "Juan Pérez", "text": "Hola, necesito una página para mi empresa."},
    )
    assert inbound.status_code == 200
    body = inbound.json()
    assert body["outbound"]
    assert body["conversation_id"]

    conversations = client.get("/api/v1/conversations", headers=auth_headers)
    assert conversations.status_code == 200
    assert len(conversations.json()) >= 1

    detail = client.get(f"/api/v1/conversations/{body['conversation_id']}", headers=auth_headers)
    assert detail.status_code == 200
    assert len(detail.json()["messages"]) >= 2


def test_switch_llm_provider(client, auth_headers):
    status = client.get("/api/v1/ai/status", headers=auth_headers)
    assert status.status_code == 200
    ids = [row["id"] for row in status.json()["providers"]]
    assert "openai" in ids
    assert "gemini" in ids

    patched = client.patch(
        "/api/v1/assistant",
        headers=auth_headers,
        json={"llm_provider": "gemini", "llm_model": "gemini-3.6-flash"},
    )
    assert patched.status_code == 200
    assert patched.json()["llm_provider"] == "gemini"
    assert patched.json()["llm_model"] == "gemini-3.6-flash"


def test_handoff_disables_bot(client, auth_headers):
    inbound = client.post(
        "/api/v1/simulate/inbound",
        headers=auth_headers,
        json={"phone": "5493764111111", "name": "María", "text": "Quiero hablar con alguien"},
    )
    assert inbound.status_code == 200
    assert inbound.json()["handoff"] is True
    assert inbound.json()["bot_enabled"] is False
    assert inbound.json()["status"] == ConversationStatus.WAITING_HUMAN.value

    conversation_id = inbound.json()["conversation_id"]
    taken = client.patch(
        f"/api/v1/conversations/{conversation_id}",
        headers=auth_headers,
        json={"status": "HUMAN"},
    )
    assert taken.status_code == 200
    assert taken.json()["status"] == "HUMAN"
    assert taken.json()["bot_enabled"] is False


def test_admin_routes_require_auth(client):
    assert client.get("/api/v1/conversations").status_code == 401
    assert client.get("/api/v1/leads").status_code == 401
