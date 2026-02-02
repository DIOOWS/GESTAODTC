from datetime import date
from services.whatsapp_parser import parse_whatsapp_text

def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Importar WhatsApp (texto colado)")

    st.caption("Cole o texto do WhatsApp. O sistema identifica CATEGORIAS e itens (NOME + NÚMERO) e salva em MAIÚSCULO.")

    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        dia = st.date_input("Data", value=date.today())
    with c2:
        filial = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"])
        filial_id = get_filial_id(filial)
    with c3:
        modo = st.selectbox("Esse texto representa:", ["ESTOQUE (contagem)", "PRODUÇÃO PLANEJADA (amanhã)"])

    texto = st.text_area("Cole aqui o texto", height=250)

    if st.button("Pré-visualizar"):
        itens = parse_whatsapp_text(texto, categoria_default="GERAL")
        st.write(f"Itens lidos: **{len(itens)}**")
        for it in itens[:50]:
            st.write(f"- {it.categoria} • {it.produto} = {it.quantidade}")
        if len(itens) > 50:
            st.info("Mostrando só os 50 primeiros.")

    if st.button("Salvar no banco"):
        itens = parse_whatsapp_text(texto, categoria_default="GERAL")
        if not itens:
            st.warning("Nada foi reconhecido. Verifique se as linhas têm número (ex: LIMÃO 2).")
            return

        for it in itens:
            pid = garantir_produto(it.categoria, it.produto)

            if modo.startswith("ESTOQUE"):
                campo = "estoque"
            else:
                campo = "produzido_planejado"

            qexec(f"""
                INSERT INTO movimentos(data, filial_id, produto_id, {campo})
                VALUES (:data, :filial_id, :produto_id, :qtd)
                ON CONFLICT (data, filial_id, produto_id)
                DO UPDATE SET {campo}=EXCLUDED.{campo};
            """, {
                "data": dia,
                "filial_id": filial_id,
                "produto_id": pid,
                "qtd": int(it.quantidade),
            })

        st.success("Importação concluída!")
        st.rerun()
