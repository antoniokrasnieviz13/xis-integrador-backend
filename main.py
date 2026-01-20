
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.controller.health_controller import router as health_router
from app.controller.orders_controller import router as orders_router
from app.controller.customers_controller import router as customers_router
from app.controller.catalog_controller import router as catalog_router
from app.controller.stock_controller import router as stock_router

from app.models import init_db

app = FastAPI(
    title="XIS Integrador Backend",
    version="1.1.0",
    description="Backend do integrador iFood desenvolvido por Antonio"
)

ALLOWED_ORIGINS = ["*"]  # Trocar em produção
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "xis-integrador-backend",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
        "version": "1.1.0"
    }

@app.on_event("startup")
def _startup():
    init_db()

# Routers
app.include_router(health_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
app.include_router(customers_router, prefix="/api")
app.include_router(catalog_router, prefix="/api")
app.include_router(stock_router, prefix="/api")
