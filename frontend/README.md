# Frontend

This folder contains the frontend for **SmartResearch**.  
Currently it’s a simple static HTML + JS page that checks the backend’s `/health` endpoint.

## Run
Option A — open file directly:
- Open `index.html` in your browser while the backend is running.  

Option B — use a simple local server (avoids CORS issues):
```bash
cd frontend
python -m http.server 5173
