# Backend

This folder contains the backend for **SmartResearch**.  
Currently it is a minimal [FastAPI](https://fastapi.tiangolo.com/) app with a single `/health` endpoint for proof of life.

## Run
Set up a virtual environment and install dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
