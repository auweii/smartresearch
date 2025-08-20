from fastapi import FastAPI

app = FastAPI(title="SmartResearch API (Minimal)")

@app.get("/health")
def health():
    return {"status": "ok"}
