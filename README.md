# test123 — G-Nome frontend + backend integration

A combined repo that wires the [`gnome_ui`](https://github.com/sofi-le/gnome_ui)
Expo React Native frontend to the [`G-Nome`](https://github.com/pn-le/G-Nome)
FastAPI backend. Both upstream repos are untouched — this repo is a
self-contained integration scaffold.

## Layout

```
test123/
├── frontend/   # Expo / React Native app (was: sofi-le/gnome_ui)
└── backend/    # FastAPI + ML inference (was: pn-le/G-Nome/backend)
```

## What changed vs. the originals

Only one thing — `frontend/lib/api.ts` was rewritten to call the real
FastAPI endpoints instead of returning the in-file demo fixtures. A small
`frontend/lib/config.ts` was added to resolve the API base URL from
`EXPO_PUBLIC_API_BASE_URL` with sensible per-platform localhost defaults.

Everything else (screens, components, types, backend modules) is verbatim
from upstream.

## Run the backend

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Configure secrets (Nebius LLM, optional Supabase)
cp .env.example .env
$EDITOR .env   # paste your NEBIUS_API_KEY

uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Verify it's up:

```bash
curl http://127.0.0.1:8000/api/health
# {"status":"ok","sessions":0,"supabase":false}
```

## Run the frontend

```bash
cd frontend
npm install

# Optional — override API base URL (otherwise platform defaults apply)
cp .env.example .env
$EDITOR .env

npx expo start
```

Then choose a target:

- **iOS simulator** (`i`) — uses `http://127.0.0.1:8000` automatically
- **Android emulator** (`a`) — uses `http://10.0.2.2:8000` automatically
- **Web** (`w`) — uses `http://127.0.0.1:8000` automatically
- **Physical phone via Expo Go** — set
  `EXPO_PUBLIC_API_BASE_URL=http://<your-lan-ip>:8000` in `frontend/.env`
  *before* starting `expo`, and make sure your phone and laptop are on the
  same Wi-Fi.

## Demo flow

1. **Upload screen** picks a 23andMe `.txt` / AncestryDNA `.csv` / `.zip` →
   uploads via `multipart/form-data` to `POST /api/parse` → backend returns
   `{ session_id, snp_count, chromosomes, ancestry }`.
2. **Processing screen** calls `POST /api/report?session_id=…` which runs
   pharmacogenomics, polygenic risk, carrier status, traits, and the
   Nebius LLM narrative.
3. **Main app** renders the resulting `ReportResult` across the Dashboard,
   Reports, Tree, Scan, and Profile tabs.

The `ParseResult` and `ReportResult` TypeScript shapes in
`frontend/lib/types.ts` line up 1:1 with the FastAPI response bodies, so
no transform layer is needed.

## Endpoints the frontend currently calls

| Method | Endpoint                              | Caller                       |
|:-------|:--------------------------------------|:-----------------------------|
| GET    | `/api/health`                         | `checkHealth()` (debug)      |
| POST   | `/api/parse`                          | `parseFile()` from upload    |
| POST   | `/api/report?session_id={id}`         | `getReport()` from processing|
| GET    | `/api/pdf/{session_id}`               | `getPdfUrl()` for downloads  |

`/api/cv/selfie` and `/api/cv/skin` are exposed by the backend but the
frontend `ScanScreen.tsx` does not yet wire them — that's the obvious
next integration step.

## Notes

- The backend's CORS middleware allows `*`, so calling from Expo web
  works out of the box.
- Don't commit `backend/.env` or `backend/sessions/` — both are in
  `.gitignore`. Genomic data should never be persisted in this repo.
- The frontend was *not* modified beyond `lib/api.ts` + new `lib/config.ts`,
  so future upstream UI changes can be rebased in cleanly.
