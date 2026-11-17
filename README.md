# 🧪 Matter Lab: Solid, Liquid, Gas (Class 3 AI activity)

A small AI project. Students learn about the three states of matter, type a material name and let an
AI guess its state, then take a quiz.

| Page | URL | What it does |
|------|-----|--------------|
| 1. Learn | `/` | Definition, explanation of each state, examples, "heat it up" particle box |
| 2. Ask the AI | `/predict` | Student types a material → AI predicts solid / liquid / gas |
| 3. Quiz | `/quiz` | 8 random questions (from 32), sounds, score and stars |

## Run it in VS Code

```bash
# 1. open the folder in VS Code, then open the terminal (Ctrl + `)
python -m venv .venv
.venv\Scripts\activate          # Windows      |  source .venv/bin/activate   (Mac/Linux)
pip install -r requirements.txt

python data/make_dataset.py     # build the CSV datasets
python -m src.train             # TRAIN the models + print accuracy, precision, recall, F1
python app.py                   # start the website
```

Open **http://localhost:5000**. (In VS Code you can also press F5 and choose *Run website*.)

## API links

| Method | Link | Purpose |
|--------|------|---------|
| GET | `http://localhost:5000/api/health` | Is the server running? |
| GET | `http://localhost:5000/api/info` | Lesson content (page 1) |
| POST | `http://localhost:5000/api/predict` body `{"material": "water"}` | Prediction (page 2) |
| GET | `http://localhost:5000/api/predict?material=water` | Same, easy to test in a browser |
| GET | `http://localhost:5000/api/materials` | Names for suggestions |
| GET | `http://localhost:5000/api/quiz?n=8` | Random quiz questions |
| POST | `http://localhost:5000/api/quiz/check` body `{"id":"q1","answer":"Solid"}` | Check an answer |
| GET | `http://localhost:5000/api/metrics` | Accuracy, precision, recall, F1 |

Example:
```bash
curl -X POST http://localhost:5000/api/predict -H "Content-Type: application/json" -d '{"material":"steam"}'
```

## How the AI works

**Task type: classification.** The answer is a category (solid / liquid / gas). Regression would be used
for predicting a number, such as a boiling point.

**Two models**

1. **Property model** (used when the material is in `materials.csv`): reads temperature, melting point,
   boiling point and density. The best of 5 algorithms is chosen by cross-validation
   (Logistic Regression, KNN, SVM, Decision Tree, Random Forest).
2. **Name model** (used for words it has not studied): reads the letters of the word
   (TF-IDF on character groups + Logistic Regression). It says "I am not sure" when confidence is below 60%.

**Preprocessing** (`src/preprocess.py`): tidy text, remove duplicates, validate labels, check density > 0,
physics check of every label while building the dataset, median imputation of missing melting/boiling
points (with a "was missing" flag), log10 of density, StandardScaler. All steps live inside one
scikit-learn `Pipeline`, so test data is never used to learn the scaling (no leakage).

**Evaluation:** stratified train/test split, repeated 5-fold cross-validation, then accuracy, precision,
recall and F1 (macro average) on the unseen test data. Confusion matrices are saved in `reports/`.
Run `python -m src.train` to see the numbers; they are also saved in `reports/metrics.json`.

### Honest notes (good talking points for class)
- The yes/no clues "keeps its shape / flows / can be squeezed" are **not** used for training. They are written
  from the answer, so a model using them would "cheat" and score 100% (data leakage). They only appear
  in the explanation.
- The dataset is small (115 materials). Scores on 29 test rows can change a lot with a different split.
- The name model can only guess from spelling, so it is less accurate than the property model.

## Docker

```bash
docker build -t matter-lab .          # trains the models during the build
docker run -p 5000:5000 matter-lab    # open http://localhost:5000
```

## Push to GitHub

```bash
git init
git add .
git commit -m "Solid, liquid, gas AI activity"
git branch -M main
# create an empty repository on github.com first, then:
git remote add origin https://github.com/<your-username>/solid-liquid-gas-ai.git
git push -u origin main
```

## Project layout

```
app.py              Flask website + API
data/               make_dataset.py, materials.csv, extra_names.csv, info.json, quiz.json
src/                preprocess.py, train.py, predictor.py
templates/ static/  the 3 web pages (HTML, CSS, JS, sounds made in the browser)
tests/              API tests (pytest)
reports/            metrics.json + confusion matrices
Dockerfile          container recipe
```

Add materials: edit `ROWS` in `data/make_dataset.py`, then re-run the dataset and train commands.
Add quiz questions: edit `data/quiz.json`.
