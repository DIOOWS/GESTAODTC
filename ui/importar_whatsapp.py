# ui/importar_whatsapp.py
from datetime import date
import streamlit as st

from services.whatsapp_parser import parse_whatsapp_text


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Importar WhatsApp (texto livre)")

    col1, col2 = st.columns([2, 2])
    with col1:
        filial_nome = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    with col2:
        data_ref = st.date_input("Data", value=date.today())

    salvar_como = st.radio(
        "Salvar como:",
        ["Estoque (contagem)", "Produzido planejado"],
        index=1,
        horizontal=True,
    )

    txt = st.text_area("Cole o texto aqui", height=220, placeholder="Cole aqui a mensagem do WhatsApp...")

    if "itens_whats" not in st.session_state:
        st.session_state["itens_whats"] = []

    if st.button("Processar"):
        itens = parse_whatsapp_text(txt)

        st.session_state["itens_whats"] = itens
        st.success(f"Itens detectados: {len(itens)}")

    itens = st.session_state.get("itens_whats", [])

    if itens:
        st.subheader("Prévia")
        # mostra uma listinha
        for it in itens[:200]:
            st.write(f"- {it['categoria']} | {it['produto']} = {it['quantidade']}")

        if st.button("Salvar no banco"):
            try:
                filial_id = get_filial_id(filial_nome)

                # decide coluna a gravar
                col_alvo = "estoque" if salvar_como.startswith("Estoque") else "produzido_planejado"

                salvos = 0
                for it in itens:
                    categoria = it.get("categoria", "").strip()
                    produto = it.get("produto", "").strip()
                    quantidade = float(it.get("quantidade", 0) or 0)

                    if not categoria or not produto:
                        continue

                    product_id = garantir_produto(categoria, produto)

                    # UPSERT em movimentos
                    qexec(f"""
                        INSERT INTO movimentos(data, filial_id, product_id, {col_alvo})
                        VALUES (:data, :filial_id, :product_id, :qtd)
                        ON CONFLICT (data, filial_id, product_id)
                        DO UPDATE SET {col_alvo} = EXCLUDED.{col_alvo};
                    """, {
                        "data": data_ref,
                        "filial_id": filial_id,
                        "product_id": product_id,
                        "qtd": quantidade,
                    })

                    salvos += 1

                st.success(f"✅ Salvo! Registros processados: {salvos}")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
                raise
    else:
        st.info("Cole o texto e clique em **Processar**.")
