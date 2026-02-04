from datetime import date
import pandas as pd

from services.whatsapp_parser import parse_whatsapp_text, corrigir_itens_com_base_no_banco


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Importar WhatsApp (texto)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())

    salvar_como = st.radio(
        "Salvar como:",
        ["Estoque (contagem do fim do dia)", "Produzido planejado (pedido p/ amanhã)"],
        index=0
    )

    modo = st.radio(
        "Como gravar no banco?",
        ["Somar (recomendado)", "Substituir"],
        index=0
    )

    texto = st.text_area("Cole o texto do WhatsApp aqui", height=260)

    if st.button("Processar"):
        itens_raw = parse_whatsapp_text(texto)

        if not itens_raw:
            st.warning("Não detectei itens. Dica: cada linha de produto precisa terminar com um número (ex: 'PRESTÍGIO 2').")
            st.stop()

        df_prod = qdf("SELECT id, categoria, produto FROM products WHERE ativo=TRUE;")
        produtos_exist = df_prod.to_dict(orient="records")
        itens = corrigir_itens_com_base_no_banco(itens_raw, produtos_exist)

        df = pd.DataFrame(itens)
        st.write(f"Itens detectados: {len(itens)}")
        st.dataframe(df, width="stretch", hide_index=True)

        st.session_state["_wa_itens"] = itens
        st.session_state["_wa_filial"] = filial
        st.session_state["_wa_data"] = d
        st.session_state["_wa_salvar_como"] = salvar_como
        st.session_state["_wa_modo"] = modo

    itens = st.session_state.get("_wa_itens")
    if not itens:
        return

    st.divider()
    st.subheader("Ajustar antes de salvar (você pode corrigir nome e número)")

    df_edit = pd.DataFrame(itens)

    edited = st.data_editor(
        df_edit,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        column_config={
            "product_id": st.column_config.NumberColumn("product_id", disabled=True),
            "quantidade": st.column_config.NumberColumn("quantidade", step=1),
            "corrigido": st.column_config.CheckboxColumn("corrigido", disabled=True),
        },
    )

    if st.button("Salvar no banco"):
        try:
            filial_id = get_filial_id(st.session_state["_wa_filial"])
            d = st.session_state["_wa_data"]
            salvar_como = st.session_state["_wa_salvar_como"]
            modo = st.session_state["_wa_modo"]

            campo = "estoque" if salvar_como.startswith("Estoque") else "produzido_planejado"

            for _, row in edited.iterrows():
                categoria = str(row["categoria"]).strip().upper()
                produto = str(row["produto"]).strip().upper()
                qtd = int(row["quantidade"] or 0)

                # garante produto (se usuário corrigiu, vira o novo padrão)
                pid = garantir_produto(categoria, produto)

                if modo.startswith("Substituir"):
                    qexec(f"""
                        INSERT INTO movimentos (data, filial_id, product_id, {campo}, observacoes)
                        VALUES (:data, :filial, :pid, :qtd, :obs)
                        ON CONFLICT (data, filial_id, product_id)
                        DO UPDATE SET {campo} = EXCLUDED.{campo},
                                      observacoes = EXCLUDED.observacoes;
                    """, {
                        "data": d,
                        "filial": filial_id,
                        "pid": pid,
                        "qtd": qtd,
                        "obs": f"Import WhatsApp ({campo}) - substituir"
                    })
                else:
                    qexec(f"""
                        INSERT INTO movimentos (data, filial_id, product_id, {campo}, observacoes)
                        VALUES (:data, :filial, :pid, :qtd, :obs)
                        ON CONFLICT (data, filial_id, product_id)
                        DO UPDATE SET {campo} = movimentos.{campo} + EXCLUDED.{campo},
                                      observacoes = EXCLUDED.observacoes;
                    """, {
                        "data": d,
                        "filial": filial_id,
                        "pid": pid,
                        "qtd": qtd,
                        "obs": f"Import WhatsApp ({campo}) - somar"
                    })

            st.success("Salvo com sucesso!")
            st.session_state.pop("_wa_itens", None)

        except Exception as e:
            st.error(f"Erro ao salvar: {e}")
