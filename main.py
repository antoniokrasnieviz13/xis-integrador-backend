
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importação dos controllers
from app.controller.health_controller import router as health_router
from app.controller.orders_controller import router as orders_router

# Instância da aplicação FastAPI
app = FastAPI(
    title="XIS Integrador Backend",
    version="1.0.0",
    description="Backend do integrador iFood desenvolvido por Antonio"
)

# ==============================
# 🔐 Configuração de CORS
# ==============================
# Em produção, substitua "*" pelo domínio do frontend:
# Exemplo: ["https://xis-integrador-frontend.onrender.com"]
ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],    # GET, POST, PUT, DELETE, OPTIONS etc.
    allow_headers=["*"],    # Content-Type, Authorization etc.
)

# ==============================
# 🌐 Rota raiz (home)
# ==============================
@app.get("/")
def root():
    return {
        "service": "xis-integrador-backend",
        "status": "running",
        "docs": "/docs",
        "health": "/api/health",
        "version": "1.0.0"
    }

# ==============================
# 🔌 Registro dos routers
# ==============================
app.include_router(health_router, prefix="/api")
app.include_router(orders_router, prefix="/api")
