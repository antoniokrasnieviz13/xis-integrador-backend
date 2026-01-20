
from fastapi import APIRouter, Request, status
import logging
from typing import Any, Dict

router = APIRouter()
logger = logging.getLogger("uvicorn.error")

@router.post("/orders/webhook", status_code=status.HTTP_200_OK, tags=["Orders"])
async def orders_webhook(request: Request) -> Dict[str, Any]:
    """
    Webhook para receber eventos/pedidos do iFood.
    Versão mínima: registra o payload no log e retorna 200.
    TODO: validar assinatura, persistir no banco, enfileirar processamento.
    """

    # Tenta interpretar JSON
    try:
        payload = await request.json()
        content_type = "application/json"
    except Exception:
        # Se não for JSON, captura o conteúdo cru
        raw_body = await request.body()
        payload = {"_raw": raw_body.decode("utf-8", errors="ignore")}
        content_type = request.headers.get("content-type", "unknown")

    # Informações úteis
    headers = dict(request.headers)
    ip = request.client.host if request.client else "unknown"

    # Log (vai aparecer no Render → Logs)
    logger.info(
        "[WEBHOOK] /orders/webhook ip=%s content_type=%s payload=%s",
        ip, content_type, payload
    )

    # Resposta padrão
    return {
        "received": True,
        "content_type": content_type,
        "message": "Webhook recebido com sucesso"
    }
