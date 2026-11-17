"""Data cleaning + preprocessing (imputation, log transform, scaling)."""
import re
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"

STATES = ["solid", "liquid", "gas"]
# Model features: real physics only.
CONTINUOUS = ["temp_c", "melting_point_c", "boiling_point_c", "log_density"]
FEATURES = CONTINUOUS
# keeps_shape / flows / compressible are only used to EXPLAIN answers to students.
# They are NOT model features: they are written from the answer itself, so using them
# would be "data leakage" (the model would cheat and always score 100%).
BINARY = ["keeps_shape", "flows", "compressible"]


def clean_name(text: str) -> str:
    """lower-case, remove odd characters, squeeze spaces: '  Ice  Cube! ' -> 'ice cube'."""
    text = re.sub(r"[^a-z0-9\s'-]", " ", str(text).lower())
    return re.sub(r"\s+", " ", text).strip()


def add_log_density(df: pd.DataFrame) -> pd.DataFrame:
    """Density goes from 0.00009 (hydrogen) to 19.3 (gold) -> log10 makes it fair."""
    df = df.copy()
    df["log_density"] = np.log10(df["density_g_cm3"])
    return df


def load_materials(verbose: bool = False) -> pd.DataFrame:
    """Load materials.csv and make the data 'perfect'."""
    df = pd.read_csv(DATA_DIR / "materials.csv")
    n0 = len(df)
    df["material"] = df["material"].map(clean_name)          # 1. tidy text
    df["state"] = df["state"].str.strip().str.lower()
    df = df.drop_duplicates(subset="material")               # 2. remove duplicates
    df = df[df["state"].isin(STATES)]                        # 3. valid labels only
    df = df.dropna(subset=["density_g_cm3", "temp_c"])       # 4. must-have values
    df = df[df["density_g_cm3"] > 0]                         # 5. density must be positive
    for col in BINARY:                                       # 6. binary columns are 0/1
        assert set(df[col].unique()) <= {0, 1}, f"{col} must be 0/1"
    df = add_log_density(df).reset_index(drop=True)          # 7. log transform
    if verbose:
        print(f"Cleaning: {n0} rows in -> {len(df)} rows out")
        print("Missing values (will be imputed):",
              df[CONTINUOUS].isna().sum()[lambda s: s > 0].to_dict())
    return df


def load_extra_names() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "extra_names.csv")
    df["material"] = df["material"].map(clean_name)
    df["state"] = df["state"].str.strip().str.lower()
    return df.drop_duplicates(subset="material")


def build_preprocessor() -> ColumnTransformer:
    """Missing numbers -> median (+ 'was missing' flag), then StandardScaler (mean 0, std 1)."""
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    return ColumnTransformer([("numeric", numeric, CONTINUOUS)])
