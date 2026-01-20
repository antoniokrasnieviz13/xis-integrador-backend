
@router.post("/orders/webhook", status_code=status.HTTP_200_OK, tags=["Orders"])
async def orders_webhook(request: Request):
    """
    Webhook para receber pedidos do iFood (ou outro integrador).
    - Aceita JSON genérico (dict).
    - Tenta mapear para o modelo interno.
    - Cria o pedido e itens em transação.
    - Sempre retorna 200 para evitar re-entregas em massa (trate idempotência se necessário).
    """
    db = _db_session()
    try:
        data = await request.json()
        if not isinstance(data, dict):
            raise HTTPException(status_code=400, detail="Payload inválido")

        # ---- Mapeamento defensivo do payload externo -> modelo interno ----
        # Ajuste aqui conforme o payload real do iFood.
        # Ex.: iFood pode enviar campos em outras chaves. Tente extrair com 'get'.
        external_code = (
            data.get("external_code")
            or data.get("orderId")
            or data.get("id")
        )
        customer_name = (
            data.get("customer_name")
            or (data.get("customer") or {}).get("name")
            or "Cliente"
        )
        note = data.get("note") or data.get("observation")

        # Os itens podem vir como 'items', 'orderItems' etc.
        raw_items = data.get("items") or data.get("orderItems") or []
        if not isinstance(raw_items, list) or len(raw_items) == 0:
            raise HTTPException(status_code=400, detail="Pedido sem itens")

        # Normaliza itens para o formato interno
        normalized_items = []
        for it in raw_items:
            # tenta diferentes chaves comuns
            sku = it.get("sku") or it.get("id") or it.get("code")
            name = it.get("name") or it.get("description") or "Item"
            qty = it.get("qty") or it.get("quantity") or 0
            unit_price = (
                it.get("unit_price")
                or it.get("unitPrice")
                or it.get("price")
                or 0
            )

            if not sku or not name or not qty:
                # Item inválido: ignore ou lance erro. Aqui vamos invalidar.
                raise HTTPException(status_code=422, detail="Item do pedido inválido")

            normalized_items.append({
                "sku": str(sku),
                "name": str(name),
                "qty": int(qty),
                "unit_price": float(unit_price),
            })

        # ---- Cria o pedido e os itens ----
        total = sum(i["qty"] * i["unit_price"] for i in normalized_items)

        order = Order(
            external_code=external_code,
            customer_name=customer_name,
            note=note,
            total_amount=total,
            status="CREATED"
