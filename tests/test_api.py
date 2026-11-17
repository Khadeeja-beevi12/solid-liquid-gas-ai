"""Run with:  pytest -q   (train first: python -m src.train)"""
import pytest

from app import app


@pytest.fixture()
def client():
    return app.test_client()


def test_health(client):
    assert client.get("/api/health").get_json()["status"] == "ok"


@pytest.mark.parametrize("word,state", [("water", "liquid"), ("stone", "solid"), ("air", "gas"),
                                         ("ice", "solid"), ("steam", "gas"), ("Milk ", "liquid")])
def test_predict_known(client, word, state):
    r = client.post("/api/predict", json={"material": word}).get_json()
    assert r["state"] == state


def test_predict_get_link(client):
    assert client.get("/api/predict?material=helium").get_json()["state"] == "gas"


def test_predict_empty_is_400(client):
    assert client.post("/api/predict", json={"material": "  "}).status_code == 400


def test_pages_load(client):
    for url in ("/", "/predict", "/quiz"):
        assert client.get(url).status_code == 200


def test_quiz_flow(client):
    qs = client.get("/api/quiz?n=3").get_json()
    assert len(qs) == 3 and all(len(q["options"]) >= 2 for q in qs)
    r = client.post("/api/quiz/check", json={"id": qs[0]["id"], "answer": "nonsense"}).get_json()
    assert r["correct"] is False
    ok = client.post("/api/quiz/check", json={"id": qs[0]["id"], "answer": r["answer"]}).get_json()
    assert ok["correct"] is True


def test_metrics(client):
    m = client.get("/api/metrics").get_json()
    assert {"accuracy", "precision", "recall", "f1"} <= set(m["property_model"]["test"])
