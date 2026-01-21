
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# IMPORTA OS ROUTERS
# - Certifique-se de que o caminho está correto conforme sua estrutura.
# - Este import pressupõe app/controller/orders_controller.py com "router = APIRouter()"
from app.controller.orders_controller import router as orders_router

# -----------------------------------------------------------------------------
# METADADOS DA API
# -----------------------------------------------------------------------------
app = FastAPI(
    title="XIS Integrador",
    version="1.0.0",
    description="API de integração (Pedidos, Catálogo, Financeiro) - iFood",
)

# -----------------------------------------------------------------------------
# CORS (liberando SOMENTE seu site do Netlify)
# -----------------------------------------------------------------------------
# Se publicar o frontend em outro domínio no futuro, acrescente-o aqui.
ALLOWED_ORIGINS = [
    "https://moonlit-cocada-f4d0f8.netlify.app",  # <— seu frontend atual
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,   # segurança: apenas seu domínio
    allow_credentials=True,
    allow_methods=["*"],             # GET, POST, PATCH, etc.
    allow_headers=["*"],
)

# -----------------------------------------------------------------------------
# HEALTHCHECK (útil para monitoramento e para seu frontend checar status)
# -----------------------------------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}

# -----------------------------------------------------------------------------
# REGISTRO DOS ROUTERS
# -----------------------------------------------------------------------------
# - Agrupa as rotas do módulo de pedidos (Orders) sob o caminho raiz.
# - Se tiver outros routers (ex.: catálogo, financeiro), inclua-os aqui.
app.include_router(orders_router)

# -----------------------------------------------------------------------------
# OBS: No Render, o processo é iniciado via Start Command:
#   uvicorn main:app --host 0.0.0.0 --port $PORT
# Não é necessário bloco "if __name__ == '__main__':" neste arquivo.
# -----------------------------------------------------------------------------
