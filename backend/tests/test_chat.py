def test_public_chat_does_not_need_admin_jwt(client):
    first = client.post(
        "/api/v1/chat/messages",
        json={
            "visitor_id": "11111111-2222-3333-4444-555555555555",
            "name": "Visitante",
            "text": "Hola, necesito una página web",
        },
    )
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["visitor_token"]
    assert body["conversation_id"]
    assert body["status"] == "BOT"
    assert any(item["direction"] == "INBOUND" for item in body["messages"])
    assert any(item["direction"] == "OUTBOUND" for item in body["messages"])

    history = client.get(
        "/api/v1/chat/messages",
        params={"visitor_token": body["visitor_token"]},
    )
    assert history.status_code == 200
    assert len(history.json()["messages"]) == len(body["messages"])


def test_chat_rejects_admin_token_as_visitor(client, auth_headers):
    admin_token = auth_headers["Authorization"].split(" ", 1)[1]
    response = client.get("/api/v1/chat/messages", params={"visitor_token": admin_token})
    assert response.status_code == 401


def test_chat_same_visitor_keeps_conversation(client):
    visitor_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    first = client.post(
        "/api/v1/chat/messages",
        json={"visitor_id": visitor_id, "text": "Quiero un e-commerce"},
    )
    second = client.post(
        "/api/v1/chat/messages",
        json={"visitor_id": visitor_id, "text": "¿Cuánto sale?"},
    )
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["conversation_id"] == second.json()["conversation_id"]
    assert len(second.json()["messages"]) > len(first.json()["messages"])
