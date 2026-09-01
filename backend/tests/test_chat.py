def test_chat_requires_contact_before_message(client):
    response = client.post(
        "/api/v1/chat/messages",
        json={
            "visitor_id": "11111111-2222-3333-4444-555555555555",
            "text": "Hola, necesito una página web",
        },
    )
    assert response.status_code == 422


def test_intake_then_public_chat(client):
    visitor_id = "11111111-2222-3333-4444-555555555555"
    intake = client.post(
        "/api/v1/chat/messages",
        json={
            "visitor_id": visitor_id,
            "intake": True,
            "first_name": "Ana",
            "last_name": "Gómez",
            "contact_phone": "3764724207",
        },
    )
    assert intake.status_code == 200, intake.text
    body = intake.json()
    assert body["status"] == "BOT"
    assert any("Ana" in item["content"] for item in body["messages"] if item["direction"] == "OUTBOUND")

    first = client.post(
        "/api/v1/chat/messages",
        json={
            "visitor_id": visitor_id,
            "first_name": "Ana",
            "last_name": "Gómez",
            "contact_phone": "3764724207",
            "text": "Hola, necesito una página web",
        },
    )
    assert first.status_code == 200, first.text
    assert any(item["direction"] == "INBOUND" for item in first.json()["messages"])
    assert any(item["direction"] == "OUTBOUND" for item in first.json()["messages"])

    history = client.get(
        "/api/v1/chat/messages",
        params={"visitor_token": first.json()["visitor_token"]},
    )
    assert history.status_code == 200
    assert len(history.json()["messages"]) == len(first.json()["messages"])


def test_chat_rejects_admin_token_as_visitor(client, auth_headers):
    admin_token = auth_headers["Authorization"].split(" ", 1)[1]
    response = client.get("/api/v1/chat/messages", params={"visitor_token": admin_token})
    assert response.status_code == 401


def test_chat_same_visitor_keeps_conversation(client):
    visitor_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    client.post(
        "/api/v1/chat/messages",
        json={
            "visitor_id": visitor_id,
            "intake": True,
            "first_name": "Luis",
            "last_name": "Pérez",
            "contact_phone": "5493764111111",
        },
    )
    first = client.post(
        "/api/v1/chat/messages",
        json={"visitor_id": visitor_id, "text": "Quiero un e-commerce"},
    )
    second = client.post(
        "/api/v1/chat/messages",
        json={"visitor_id": visitor_id, "text": "¿Cuánto sale?"},
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert first.json()["conversation_id"] == second.json()["conversation_id"]
    assert len(second.json()["messages"]) > len(first.json()["messages"])


def test_closing_conversation_hides_history_from_visitor(client, auth_headers):
    visitor_id = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
    client.post(
        "/api/v1/chat/messages",
        json={
            "visitor_id": visitor_id,
            "intake": True,
            "first_name": "Mara",
            "last_name": "Díaz",
            "contact_phone": "5493764222222",
        },
    )
    chat = client.post(
        "/api/v1/chat/messages",
        json={"visitor_id": visitor_id, "text": "Hola, busco una landing"},
    )
    assert chat.status_code == 200, chat.text
    token = chat.json()["visitor_token"]
    conversation_id = chat.json()["conversation_id"]
    assert len(chat.json()["messages"]) >= 2

    closed = client.patch(
        f"/api/v1/conversations/{conversation_id}",
        headers=auth_headers,
        json={"status": "CLOSED"},
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "CLOSED"

    history = client.get("/api/v1/chat/messages", params={"visitor_token": token})
    assert history.status_code == 200
    assert history.json()["status"] == "CLOSED"
    assert history.json()["messages"] == []

    detail = client.get(f"/api/v1/conversations/{conversation_id}", headers=auth_headers)
    assert detail.status_code == 200
    assert detail.json()["messages"] == []


def test_chat_handoff_offers_whatsapp_agents(client):
    visitor_id = "cccccccc-dddd-eeee-ffff-000000000000"
    client.post(
        "/api/v1/chat/messages",
        json={
            "visitor_id": visitor_id,
            "intake": True,
            "first_name": "Ana",
            "last_name": "Gómez",
            "contact_phone": "3765050111",
        },
    )
    response = client.post(
        "/api/v1/chat/messages",
        json={"visitor_id": visitor_id, "text": "Quiero hablar con alguien"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["handoff"] is True
    outbound = [item["content"] for item in body["messages"] if item["direction"] == "OUTBOUND"]
    text = "\n".join(outbound)
    assert "wa.me/5493764724207" in text
    assert "wa.me/5493765050885" in text
    assert "Ana" in text
    assert "3765050111" in text
