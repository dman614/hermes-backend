"""
Hermes - Home Services AI Platform
Minimal test version for Railway deployment
"""

from fastapi import FastAPI
import os

app = FastAPI(title="Hermes Backend")

@app.get("/")
async def root():
    return {"message": "Hermes is running!"}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "hermes-backend"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
