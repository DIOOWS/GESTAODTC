from datetime import date
import pandas as pd
from services.whatsapp_parser import parse_whatsapp_text


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Importar WhatsApp (texto)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    dia = col2.date_input("Data", value=date.today())

    modo = st.radio(
        "Salvar como:",
        ["Estoque (contagem)", "Produzido planejado", "Produzido real", "Vendido", "Desperdício"],
        index=0
    )
    acumular = st.checkbox("Somar ao invés de substituir (útil quando manda em partes)", value=False)

    texto = st.text_area("Cole o texto aqui", height=260)

    if st.button("Processar"):
        itens = parse_whatsapp_text(texto)

        if not itens:
            st.warning("Não detectei itens. Dica: linhas com produto precisam terminar com número (ex: 'LIMÃO 2').")
            st.stop()

        st.write(f"Itens detectados: {len(itens)}")
        df = pd.DataFrame(itens)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.session_state["_wa_itens"] = itens
        st.session_state["_wa_filial"] = filial
        st.session_state["_wa_dia"] = dia
        st.session_state["_wa_modo"] = modo
        st.session_state["_wa_acumular"] = acumular

    if st.session_state.get("_wa_itens"):
        if st.button("Salvar no banco"):
            try:
                itens = st.session_state["_wa_itens"]
                filial = st.session_state["_wa_filial"]
                dia = st.session_state["_wa_dia"]
                modo = st.session_state["_wa_modo"]
                acumular = st.session_state["_wa_acumular"]

                filial_id = get_filial_id(filial)

                campo_map = {
                    "Estoque (contagem)": "estoque",
                    "Produzido planejado": "produzido_planejado",
                    "Produzido real": "produzido_real",
                    "Vendido": "vendido",
                    "Desperdício": "desperdicio",
                }
                campo = campo_map[modo]

                for it in itens:
                    categoria = it["categoria"]
                    produto = it["produto"]
                    qtd = float(it["quantidade"])

                    pid = garantir_produto(categoria, produto)

                    # garante linha
                    qexec("""
                        INSERT INTO movimentacoes (dia, filial_id, produto_id)
                        VALUES (:dia, :filial, :pid)
                        ON CONFLICT (dia, filial_id, produto_id) DO NOTHING;
                    """, {"dia": dia, "filial": filial_id, "pid": pid})

                    if acumular:
                        qexec(f"""
                            UPDATE movimentacoes
                            SET {campo} = COALESCE({campo},0) + :qtd
                            WHERE dia=:dia AND filial_id=:filial AND produto_id=:pid;
                        """, {"dia": dia, "filial": filial_id, "pid": pid, "qtd": qtd})
                    else:
                        qexec(f"""
                            UPDATE movimentacoes
                            SET {campo} = :qtd
                            WHERE dia=:dia AND filial_id=:filial AND produto_id=:pid;
                        """, {"dia": dia, "filial": filial_id, "pid": pid, "qtd": qtd})

                st.success("Salvo com sucesso!")
                st.session_state.pop("_wa_itens", None)
                st.rerun()

            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
