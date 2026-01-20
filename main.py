
from fastapi import FastAPI
from app.controller.orders_controller import router as orders_router

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(orders_router)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # depois restringiremos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
