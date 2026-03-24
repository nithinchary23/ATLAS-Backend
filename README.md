# ATLAS Backend

## Setup

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Local Run

```powershell
copy .env.example .env
python app.py
```

## Tests

```powershell
pytest
```

## Production Environment

Set these environment variables:

- `FLASK_HOST`
- `FLASK_PORT`
- `FLASK_DEBUG=false`
- `CORS_ORIGINS=https://your-frontend-domain`

## Production Start

```powershell
gunicorn wsgi:app
```

## API Coverage

- `/api/risk/top10`
- `/api/risk/history`
- `/api/risk/summary`
- `/api/forecast`
- `/api/forecast/aggregated`
- `/api/forecast/timeline`
- `/api/geo-hotspots`
- `/api/geo-future-areas`
