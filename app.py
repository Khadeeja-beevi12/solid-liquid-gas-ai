"""Flask web app + JSON API for the Solid / Liquid / Gas AI activity.

Run:  python app.py        (then open http://localhost:5000)
"""
import json
import os
import random

from flask import Flask, jsonify, render_template, request

from src.predictor import Predictor
from src.preprocess import DATA_DIR, REPORT_DIR

app = Flask(__name__)
app.json.ensure_ascii = False

predictor = Predictor()
INFO = json.loads((DATA_DIR / "info.json").read_text(encoding="utf-8"))
QUIZ = json.loads((DATA_DIR / "quiz.json").read_text(encoding="utf-8"))
QUIZ_BY_ID = {q["id"]: q for q in QUIZ}


def metrics():
    return json.loads((REPORT_DIR / "metrics.json").read_text())


# ------------------------------- pages -------------------------------
@app.get("/")
def page_learn():
    return render_template("learn.html", page="learn")


@app.get("/predict")
def page_predict():
    return render_template("predict.html", page="predict")


@app.get("/quiz")
def page_quiz():
    return render_template("quiz.html", page="quiz")


# -------------------------------- API --------------------------------
@app.get("/api/health")
def api_health():
    return jsonify(status="ok", materials=len(predictor.materials), names=len(predictor.known_names))


@app.get("/api/info")
def api_info():
    """Page 1: definition, the 3 states, examples."""
    return jsonify(INFO)


@app.route("/api/predict", methods=["GET", "POST"])
def api_predict():
    """Page 2: POST {"material": "water"}  or  GET /api/predict?material=water"""
    if request.method == "POST":
        material = (request.get_json(silent=True) or {}).get("material", "")
    else:
        material = request.args.get("material", "")
    try:
        return jsonify(predictor.predict(str(material)))
    except ValueError as err:
        return jsonify(error=str(err)), 400


@app.get("/api/materials")
def api_materials():
    """Names the AI knows well (for the suggestion list)."""
    m = predictor.materials
    return jsonify([{"name": n, "emoji": m.loc[n, "emoji"] if isinstance(m.loc[n, "emoji"], str) else ""}
                    for n in m.index])


@app.get("/api/quiz")
def api_quiz():
    """Page 3: GET /api/quiz?n=8  -> random questions (answers are checked on the server)."""
    n = max(1, min(request.args.get("n", 8, type=int), len(QUIZ)))
    out = []
    for q in random.sample(QUIZ, n):
        options = q["wrong"] + [q["correct"]]
        random.shuffle(options)
        out.append({"id": q["id"], "question": q["question"], "options": options})
    return jsonify(out)


@app.post("/api/quiz/check")
def api_quiz_check():
    """POST {"id": "q1", "answer": "Solid"}"""
    body = request.get_json(silent=True) or {}
    q = QUIZ_BY_ID.get(body.get("id"))
    if q is None:
        return jsonify(error="Unknown question."), 404
    return jsonify(correct=body.get("answer") == q["correct"], answer=q["correct"], why=q["why"])


@app.get("/api/metrics")
def api_metrics():
    """Accuracy, precision, recall and F1 of both models."""
    m = metrics()
    return jsonify(task=m["task"], property_model=m["property_model"], name_model=m["name_model"])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)),
            debug=os.environ.get("FLASK_DEBUG") == "1")
