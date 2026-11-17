"""Turns a student's word into a prediction (used by the API)."""
import difflib
import re

import joblib
import pandas as pd

from src.preprocess import (BINARY, FEATURES, MODEL_DIR, STATES, clean_name,
                            load_extra_names, load_materials)

EXPLAIN = {
    "solid": "A solid keeps its own shape. It does not flow or spread out.",
    "liquid": "A liquid flows. It has no shape of its own, so it takes the shape of its container.",
    "gas": "A gas spreads out everywhere and fills the whole container. We often cannot see it.",
}
CLUE_TEXT = {
    "keeps_shape": "it keeps its shape",
    "flows": "it can flow or pour",
    "compressible": "it can be squeezed smaller",
}
DEFAULT_EMOJI = {"solid": "🧱", "liquid": "💧", "gas": "💨"}
UNSURE_BELOW = 0.60
ARTICLES = re.compile(r"^(a|an|the|some)\s+")


class Predictor:
    def __init__(self):
        self.property_model = joblib.load(MODEL_DIR / "property_model.joblib")
        self.name_model = joblib.load(MODEL_DIR / "name_model.joblib")
        self.materials = load_materials().set_index("material")
        self.extra = load_extra_names().set_index("material")["state"].to_dict()
        self.known_names = sorted(set(self.materials.index) | set(self.extra))

    # ---------- finding the word ----------
    def _lookup_candidates(self, text):
        yield text
        stripped = ARTICLES.sub("", text)
        yield stripped
        for t in {text, stripped}:
            if len(t) > 3 and t.endswith("es"):
                yield t[:-2]
            if len(t) > 3 and t.endswith("s"):
                yield t[:-1]

    def _find(self, text):
        for cand in self._lookup_candidates(text):
            if cand in self.materials.index or cand in self.extra:
                return cand, False
        close = difflib.get_close_matches(text, self.known_names, n=1, cutoff=0.84)
        return (close[0], True) if close else (None, False)

    # ---------- predicting ----------
    @staticmethod
    def _probs(model, X):
        p = model.predict_proba(X)[0]
        return {c: float(v) for c, v in zip(model.classes_, p)}

    def predict(self, raw):
        text = clean_name(raw)
        if not text:
            raise ValueError("Please type the name of a material, like water or stone.")
        if len(text) > 60:
            raise ValueError("That name is too long. Try a short word like milk or iron.")

        match, typo = self._find(text)
        result = {"input": raw.strip(), "matched": match, "typo_fixed": typo, "properties": None}

        if match in self.materials.index:                      # AI model 1: physics
            row = self.materials.loc[[match]]
            probs = self._probs(self.property_model, row[FEATURES])
            result.update(source="property_model", emoji=row["emoji"].iloc[0] or None,
                          fact=row["fact"].iloc[0] if isinstance(row["fact"].iloc[0], str) else "")
            clues = [CLUE_TEXT[c] for c in BINARY if int(row[c].iloc[0]) == 1]
            temp = float(row["temp_c"].iloc[0])
            result["properties"] = {
                "temperature_c": temp,
                "melting_point_c": None if pd.isna(row["melting_point_c"].iloc[0]) else float(row["melting_point_c"].iloc[0]),
                "boiling_point_c": None if pd.isna(row["boiling_point_c"].iloc[0]) else float(row["boiling_point_c"].iloc[0]),
                "density_g_cm3": float(row["density_g_cm3"].iloc[0]),
                "clues": clues,
            }
        else:                                                    # AI model 2: the word itself
            name = match or text
            probs = self._probs(self.name_model, [name])
            result.update(source="name_model", emoji=None, fact="")

        state = max(probs, key=probs.get)
        conf = probs[state]
        result["probabilities"] = {s: round(probs.get(s, 0.0), 3) for s in STATES}
        result["confidence"] = round(conf, 3)
        if result["source"] == "name_model" and conf < UNSURE_BELOW:
            result.update(state=None, emoji="🤔",
                          explanation="I am not sure about this one. Try a simpler word, like 'water' or 'stone'.")
            return result
        result["state"] = state
        result["emoji"] = result["emoji"] or DEFAULT_EMOJI[state]
        result["explanation"] = EXPLAIN[state]
        if result["source"] == "name_model":
            result["note"] = "I have not studied this exact material, so I made a careful guess from its name."
        return result
