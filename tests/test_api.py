import pytest
from fastapi.testclient import TestClient

from rag_gateway.main import build_app


@pytest.fixture
def client():
    return TestClient(build_app())


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["documents"] >= 1
    assert data["chunks"] >= 1


def test_tenants(client):
    r = client.get("/tenants")
    ids = [t["id"] for t in r.json()]
    assert "corp" in ids
    assert "project" in ids


def test_docs(client):
    r = client.get("/documents", params={"tenant_id": "corp"})
    docs = r.json()
    assert all(d["tenant_id"] == "corp" for d in docs)
    # doc-004 是受角色限制的
    by_id = {d["id"]: d for d in docs}
    assert by_id["doc-004"]["allowed_roles"] == ["hr"]
    assert by_id["doc-001"]["public"] is True


def test_query_permission(client):
    r = client.post("/query", json={
        "question": "涉密文件的借阅要求？",
        "user_id": "u-national", "tenant_id": "corp", "roles": ["national"],
    })
    assert r.status_code == 200
    data = r.json()
    assert any(s["doc_id"] == "doc-003" for s in data["sources"])


def test_query_restricted_hidden(client):
    r = client.post("/query", json={
        "question": "涉密文件的借阅要求？",
        "user_id": "u-prod", "tenant_id": "corp", "org": "生产部",
    })
    data = r.json()
    assert all(s["doc_id"] != "doc-003" for s in data["sources"])


def test_sync(client):
    r = client.post("/sync", json={
        "documents": [
            {"id": "doc-900", "tenant_id": "corp", "title": "差旅制度",
             "content": "住宿上限500元/晚", "allowed_roles": [], "allowed_orgs": []}
        ]
    })
    assert r.status_code == 200
    assert r.json()["added"] == 1


def test_audit(client):
    client.post("/query", json={
        "question": "报销流程", "user_id": "u", "tenant_id": "corp",
    })
    r = client.get("/audit")
    assert r.status_code == 200
    entries = r.json()
    assert len(entries) >= 1
    assert "question" in entries[0]
