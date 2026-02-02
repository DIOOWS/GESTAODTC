from datetime import date
import pandas as pd
from services.whatsapp_parser import parse_whatsapp_text


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Importar WhatsApp (texto livre)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())

    salvar_como = st.radio("Salvar como:", ["Estoque (contagem)", "Produzido planejado"], index=0)

    texto = st.text_area("Cole o texto aqui", height=250)

    if st.button("Processar"):
        itens = parse_whatsapp_text(texto)

        if not itens:
            st.warning("Não detectei itens. Confere se cada linha termina com um número (ex: 'PRESTÍGIO 2').")
            st.stop()

        st.write(f"Itens detectados: {len(itens)}")

        df = pd.DataFrame(itens)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.session_state["_wa_itens"] = itens
        st.session_state["_wa_filial"] = filial
        st.session_state["_wa_data"] = d
        st.session_state["_wa_salvar_como"] = salvar_como

    if st.session_state.get("_wa_itens"):
        if st.button("Salvar no banco"):
            try:
                itens = st.session_state["_wa_itens"]
                filial = st.session_state["_wa_filial"]
                d = st.session_state["_wa_data"]
                salvar_como = st.session_state["_wa_salvar_como"]

                filial_id = get_filial_id(filial)

                # define qual coluna atualizar
                campo = "estoque" if salvar_como.startswith("Estoque") else "produzido_planejado"

                sql = f"""
                INSERT INTO movimentos (data, filial_id, product_id, {campo})
                VALUES (:data, :filial, :pid, :qtd)
                ON CONFLICT (data, filial_id, product_id)
                DO UPDATE SET {campo} = EXCLUDED.{campo};
                """

                for it in itens:
                    categoria = it["categoria"]
                    produto = it["produto"]
                    quantidade = it["quantidade"]

                    product_id = garantir_produto(categoria, produto)

                    qexec(sql, {
                        "data": d,
                        "filial": filial_id,
                        "pid": product_id,
                        "qtd": quantidade
                    })

                st.success("Salvo com sucesso!")
                st.session_state.pop("_wa_itens", None)

            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
