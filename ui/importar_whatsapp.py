from datetime import date
import pandas as pd

from services.whatsapp_parser import parse_whatsapp_text


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Importar WhatsApp (texto)")

    c1, c2 = st.columns([1, 1])
    with c1:
        filial = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"])
    with c2:
        data_ref = st.date_input("Data", value=date.today())

    filial_id = get_filial_id(filial)

    modo = st.radio(
        "Salvar como:",
        ["Estoque (contagem)", "Produzido planejado"],
        horizontal=True
    )

    texto = st.text_area("Cole o texto aqui", height=200)

    # Estado para manter itens entre cliques
    if "wa_items" not in st.session_state:
        st.session_state["wa_items"] = []
    if "wa_raw" not in st.session_state:
        st.session_state["wa_raw"] = ""

    if st.button("Processar"):
        try:
            items = parse_whatsapp_text(texto)
            st.session_state["wa_items"] = items
            st.session_state["wa_raw"] = texto or ""
            st.success(f"Itens detectados: {len(items)}")
        except Exception as e:
            st.session_state["wa_items"] = []
            st.error(f"Erro ao processar: {e}")

    items = st.session_state.get("wa_items", [])

    if items:
        st.subheader(f"Itens detectados: {len(items)}")

        # Mostrar lista amigável
        for it in items[:200]:
            cat = (it.get("categoria") or "(SEM)").strip().upper()
            prod = (it.get("produto") or "").strip().upper()
            qtd = float(it.get("quantidade") or 0)
            st.write(f"• ({cat}) | {prod} = {qtd}")

        st.divider()

        if st.button("Salvar no banco"):
            salvos = 0
            erros = 0
            erros_lista = []

            for it in items:
                try:
                    categoria = (it.get("categoria") or "(SEM)").strip().upper()
                    produto = (it.get("produto") or "").strip().upper()
                    quantidade = float(it.get("quantidade") or 0)

                    if not produto:
                        continue
                    if quantidade <= 0:
                        continue

                    # garante produto e pega id
                    produto_id = garantir_produto(categoria, produto)

                    # monta campos conforme modo
                    if modo == "Estoque (contagem)":
                        sql = """
                            INSERT INTO movimentos(data, filial_id, produto_id, estoque, observacoes)
                            VALUES (:d, :f, :p, :q, :o)
                            ON CONFLICT (data, filial_id, produto_id)
                            DO UPDATE SET
                              estoque = EXCLUDED.estoque,
                              observacoes = EXCLUDED.observacoes;
                        """
                    else:
                        sql = """
                            INSERT INTO movimentos(data, filial_id, produto_id, produzido_planejado, observacoes)
                            VALUES (:d, :f, :p, :q, :o)
                            ON CONFLICT (data, filial_id, produto_id)
                            DO UPDATE SET
                              produzido_planejado = EXCLUDED.produzido_planejado,
                              observacoes = EXCLUDED.observacoes;
                        """

                    qexec(sql, {
                        "d": data_ref,
                        "f": filial_id,
                        "p": int(produto_id),
                        "q": float(quantidade),
                        "o": "IMPORT_WHATSAPP"
                    })
                    salvos += 1

                except Exception as e:
                    erros += 1
                    erros_lista.append(f"{it} -> {e}")

            if salvos > 0:
                st.success(f"✅ Salvo(s): {salvos} item(ns)")
            if erros > 0:
                st.error(f"⚠️ Erros: {erros} item(ns)")
                st.code("\n".join(erros_lista[:30]))

            # Preview do que entrou no banco
            st.subheader("Preview do que ficou gravado (movimentos)")
            df_prev = qdf("""
                SELECT
                    m.data, f.nome AS filial, p.categoria, p.produto,
                    COALESCE(m.estoque,0) AS estoque,
                    COALESCE(m.produzido_planejado,0) AS produzido_planejado,
                    COALESCE(m.produzido_real,0) AS produzido_real,
                    COALESCE(m.vendido,0) AS vendido,
                    COALESCE(m.desperdicio,0) AS desperdicio,
                    m.observacoes
                FROM movimentos m
                JOIN filiais f ON f.id = m.filial_id
                JOIN products p ON p.id = m.produto_id
                WHERE m.data=:d AND m.filial_id=:f
                ORDER BY p.categoria, p.produto;
            """, {"d": data_ref, "f": filial_id})
            st.dataframe(df_prev, use_container_width=True, hide_index=True)

    else:
        st.info("Cole o texto e clique em **Processar**.")
