import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def client():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return TestClient(app)


def auth(client, name="alice"):
    r = client.post("/api/register", json={"username": name, "password": "secret1"})
    assert r.status_code == 201
    return {"Authorization": "Bearer " + r.json()["access_token"]}


def tx(kind, amount, cat="Food", date="2026-10-01"):
    return {"kind": kind, "amount": amount, "category": cat, "description": "", "date": date}


def test_auth_required(client):
    assert client.get("/api/transactions").status_code in (401, 403)


def test_duplicate_and_bad_login(client):
    auth(client)
    assert client.post("/api/register", json={"username": "alice", "password": "secret1"}).status_code == 409
    assert client.post("/api/login", json={"username": "alice", "password": "wrong!!"}).status_code == 401


def test_crud_and_summary(client):
    h = auth(client)
    client.post("/api/transactions", json=tx("income", 1000, "Salary"), headers=h)
    r = client.post("/api/transactions", json=tx("expense", 40), headers=h)
    tx_id = r.json()["id"]
    s = client.get("/api/summary", headers=h).json()
    assert (s["income"], s["expense"], s["balance"]) == (1000, 40, 960)
    assert s["by_category"] == {"Food": 40}
    client.put(f"/api/transactions/{tx_id}", json=tx("expense", 60), headers=h)
    assert client.get("/api/summary", headers=h).json()["expense"] == 60
    assert client.delete(f"/api/transactions/{tx_id}", headers=h).status_code == 204
    assert len(client.get("/api/transactions", headers=h).json()) == 1


def test_users_are_isolated(client):
    a, b = auth(client, "alice"), auth(client, "bobby")
    tx_id = client.post("/api/transactions", json=tx("expense", 5), headers=a).json()["id"]
    assert client.get("/api/transactions", headers=b).json() == []
    assert client.delete(f"/api/transactions/{tx_id}", headers=b).status_code == 404


def test_validation(client):
    h = auth(client)
    assert client.post("/api/transactions", json=tx("expense", -5), headers=h).status_code == 422
