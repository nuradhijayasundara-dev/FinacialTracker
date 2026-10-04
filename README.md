# Finance Tracker

Full-stack personal finance app: track income and expenses, see charts.

| Layer    | Tech                              |
|----------|-----------------------------------|
| Frontend | HTML / CSS / vanilla JS, Chart.js |
| Backend  | FastAPI, JWT auth (PyJWT)         |
| Database | SQLite via SQLAlchemy 2.0         |

## Run
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000 (interactive API docs at /docs).

## Test
```bash
pytest
```

## Config (env vars)
- `SECRET_KEY` – JWT signing key (set a real one outside dev)
- `DATABASE_URL` – e.g. `postgresql+psycopg://user:pw@host/db` to use PostgreSQL
