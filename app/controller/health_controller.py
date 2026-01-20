
# app/controller/health_controller.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "service": "xis-integrador-backend"}
