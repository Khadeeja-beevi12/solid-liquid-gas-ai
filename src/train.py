"""
Train + evaluate both models.   Run:  python -m src.train

Task type: CLASSIFICATION  (the answer is a category: solid / liquid / gas).
Regression would be used if we wanted to predict a number (like a boiling point).
"""
import json
import warnings

import joblib
import matplotlib
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_score, recall_score)
from sklearn.model_selection import RepeatedStratifiedKFold, cross_validate, train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from src.preprocess import (FEATURES, MODEL_DIR, REPORT_DIR, STATES, build_preprocessor,
                            load_extra_names, load_materials)

SEED = 42
SCORING = {"accuracy": "accuracy", "precision": "precision_macro",
           "recall": "recall_macro", "f1": "f1_macro"}


def scores(y_true, y_pred):
    kw = dict(average="macro", zero_division=0)
    return {"accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, **kw),
            "recall": recall_score(y_true, y_pred, **kw),
            "f1": f1_score(y_true, y_pred, **kw)}


def save_confusion(y_true, y_pred, title, filename):
    cm = confusion_matrix(y_true, y_pred, labels=STATES)
    fig, ax = plt.subplots(figsize=(4.5, 4))
    ConfusionMatrixDisplay(cm, display_labels=STATES).plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(REPORT_DIR / filename, dpi=130)
    plt.close(fig)
    return cm.tolist()


def evaluate(name, pipe, X_tr, X_te, y_tr, y_te, cv):
    cvres = cross_validate(pipe, X_tr, y_tr, cv=cv, scoring=SCORING)
    cv_mean = {k: float(np.mean(cvres[f"test_{k}"])) for k in SCORING}
    cv_std = {k: float(np.std(cvres[f"test_{k}"])) for k in SCORING}
    pipe.fit(X_tr, y_tr)
    return cv_mean, cv_std, pipe.predict(X_te)


def print_row(label, d):
    print(f"  {label:<26} acc={d['accuracy']:.3f}  precision={d['precision']:.3f}  "
          f"recall={d['recall']:.3f}  f1={d['f1']:.3f}")


def train_property_model():
    print("\n=== MODEL 1: property model (temperature, melting point, boiling point, density) ===")
    df = load_materials(verbose=True)
    X, y = df[FEATURES], df["state"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)
    print(f"Train rows: {len(X_tr)} | Test rows: {len(X_te)}")
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=3000, class_weight="balanced"),
        "KNN": KNeighborsClassifier(n_neighbors=5),
        "SVM": SVC(kernel="rbf", probability=True, class_weight="balanced", random_state=SEED),
        "DecisionTree": DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=SEED),
        "RandomForest": RandomForestClassifier(n_estimators=300, class_weight="balanced", random_state=SEED),
    }
    results, best_name, best_f1 = {}, None, -1
    print("5-fold x 3 repeats cross-validation on the training data (macro averages):")
    for name, clf in candidates.items():
        pipe = Pipeline([("prep", build_preprocessor()), ("clf", clf)])
        cv_mean, cv_std, _ = evaluate(name, pipe, X_tr, X_te, y_tr, y_te, cv)
        results[name] = {"cv_mean": cv_mean, "cv_std": cv_std}
        print_row(name, cv_mean)
        if cv_mean["f1"] > best_f1:
            best_name, best_f1 = name, cv_mean["f1"]

    print(f"\nBest model by cross-validated F1: {best_name}")
    best = Pipeline([("prep", build_preprocessor()), ("clf", candidates[best_name])])
    best.fit(X_tr, y_tr)
    pred = best.predict(X_te)
    test = scores(y_te, pred)
    print("\nFinal TEST-set scores (data the model never saw):")
    print_row(best_name, test)
    print(classification_report(y_te, pred, labels=STATES, zero_division=0))
    cm = save_confusion(y_te, pred, f"Property model: {best_name}", "confusion_property_model.png")

    best.fit(X, y)  # refit on all data for the website
    joblib.dump(best, MODEL_DIR / "property_model.joblib")
    return {"algorithm": best_name, "train_rows": len(X_tr), "test_rows": len(X_te),
            "features": FEATURES, "test": test, "confusion_matrix": cm,
            "per_class": classification_report(y_te, pred, labels=STATES, output_dict=True,
                                               zero_division=0),
            "candidates": results}


def train_name_model():
    print("\n=== MODEL 2: name model (reads the letters of the word) ===")
    mats = load_materials()[["material", "state"]]
    data = pd.concat([mats, load_extra_names()]).drop_duplicates("material").reset_index(drop=True)
    X, y = data["material"], data["state"]
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, stratify=y, random_state=SEED)
    print(f"Names: {len(data)} | Train: {len(X_tr)} | Test: {len(X_te)}")
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=3, random_state=SEED)

    def make(C):
        return Pipeline([
            ("tfidf", TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)),
            ("clf", LogisticRegression(C=C, max_iter=3000, class_weight="balanced")),
        ])

    results, best_c, best_f1 = {}, None, -1
    for C in (1, 5, 20):
        cv_mean, cv_std, _ = evaluate(f"C={C}", make(C), X_tr, X_te, y_tr, y_te, cv)
        results[f"C={C}"] = {"cv_mean": cv_mean, "cv_std": cv_std}
        print_row(f"TF-IDF + LogReg C={C}", cv_mean)
        if cv_mean["f1"] > best_f1:
            best_c, best_f1 = C, cv_mean["f1"]

    best = make(best_c).fit(X_tr, y_tr)
    pred = best.predict(X_te)
    test = scores(y_te, pred)
    print(f"\nFinal TEST-set scores (C={best_c}):")
    print_row("name model", test)
    print(classification_report(y_te, pred, labels=STATES, zero_division=0))
    cm = save_confusion(y_te, pred, "Name model", "confusion_name_model.png")

    best.fit(X, y)
    joblib.dump(best, MODEL_DIR / "name_model.joblib")
    return {"algorithm": f"TF-IDF characters + LogisticRegression (C={best_c})",
            "train_rows": len(X_tr), "test_rows": len(X_te), "test": test,
            "confusion_matrix": cm, "candidates": results}


def main():
    MODEL_DIR.mkdir(exist_ok=True)
    REPORT_DIR.mkdir(exist_ok=True)
    report = {"property_model": train_property_model(), "name_model": train_name_model(),
              "task": "classification", "labels": STATES, "seed": SEED}
    (REPORT_DIR / "metrics.json").write_text(json.dumps(report, indent=2))
    print("\nSaved: models/*.joblib, reports/metrics.json, reports/*.png")


if __name__ == "__main__":
    main()
