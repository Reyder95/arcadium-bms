from fastapi import FastAPI

from app.api import api_router

app = FastAPI()
app.include_router(api_router)

@app.get("/health")
def health():
    return { "status": "ok" }