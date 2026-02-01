from datetime import date
import pandas as pd
from services.whatsapp_parser import parse_whatsapp_text


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Importar WhatsApp (texto livre)")

    filial = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"])
    data_ref = st.date_input("Data", value=date.today())

    modo = st.radio("Salvar como:", ["Estoque (contagem)", "Produzido planejado"], horizontal=True)

    texto = st.text_area("Cole o texto aqui", height=320)

    if st.button("Processar"):
        itens = parse_whatsapp_text(texto)
        if not itens:
            st.warning("Não identifiquei itens.")
            st.stop()

        df_prev = pd.DataFrame([{
            "Categoria": i.categoria,
            "Produto": i.produto,
            "Quantidade": i.quantidade
        } for i in itens])
        st.session_state["imp_itens"] = itens
        st.dataframe(df_prev, use_container_width=True, hide_index=True)

    if st.session_state.get("imp_itens"):
        if st.button("Salvar"):
            itens = st.session_state["imp_itens"]
            local_id = get_filial_id(filial)
            salvos = 0

            for it in itens:
                nome_prod = f"{it.categoria} - {it.produto}"
                pid = garantir_produto(nome_prod, it.categoria)

                if modo.startswith("Estoque"):
                    qexec("""
                        INSERT INTO registros_diarios (data, produto_id, local_id, estoque)
                        VALUES (:data, :pid, :lid, :qtd)
                        ON CONFLICT (data, produto_id, local_id)
                        DO UPDATE SET estoque=EXCLUDED.estoque;
                    """, {"data": data_ref, "pid": pid, "lid": local_id, "qtd": it.quantidade})
                else:
                    qexec("""
                        INSERT INTO registros_diarios (data, produto_id, local_id, produzido_planejado)
                        VALUES (:data, :pid, :lid, :qtd)
                        ON CONFLICT (data, produto_id, local_id)
                        DO UPDATE SET produzido_planejado=EXCLUDED.produzido_planejado;
                    """, {"data": data_ref, "pid": pid, "lid": local_id, "qtd": it.quantidade})

                salvos += 1

            st.success(f"Salvo! Itens: {salvos}")
            st.session_state["imp_itens"] = []
            st.rerun()
