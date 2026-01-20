
from fastapi import FastAPI
from app.controller.health_controller import router as health_router

app = FastAPI(title="XIS Integrador Backend", version="1.0.0")

@app.get("/")
def root():
    return {
        "service": "xis-integrador-backend",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
        "version": "1.0.0"
    }

app.include_router(health_router, prefix="/api")
