# ui/lancamentos.py
from datetime import date
import pandas as pd
from PIL import Image

from services.whatsapp_parser import parse_whatsapp_text
from services.ocr_producao import ocr_image_to_text, parse_producao_from_ocr_text


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Lançamentos")

    tab1, tab2, tab3 = st.tabs([
        "📦 Contagem (Texto WhatsApp)",
        "🧾 Produção (Foto)",
        "🚚 Transferência (Envio)"
    ])

    # =========================
    # TAB 1: CONTAGEM (texto)
    # =========================
    with tab1:
        st.subheader("Contagem de fechamento (vira estoque)")
        filial = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], key="ct_filial")
        data_ref = st.date_input("Data da contagem", value=date.today(), key="ct_data")

        texto = st.text_area("Cole aqui a contagem (texto do WhatsApp)", height=260, key="ct_texto")

        if st.button("Processar contagem", key="ct_processar"):
            itens = parse_whatsapp_text(texto)
            if not itens:
                st.warning("Não identifiquei itens. Cole novamente e tente.")
            else:
                df_prev = pd.DataFrame([{
                    "Categoria": i.categoria,
                    "Produto": i.produto,
                    "Quantidade (estoque)": i.quantidade
                } for i in itens])
                st.session_state["ct_itens"] = itens
                st.dataframe(df_prev, use_container_width=True, hide_index=True)

        if st.session_state.get("ct_itens"):
            if st.button("Salvar contagem como estoque", key="ct_salvar"):
                itens = st.session_state["ct_itens"]
                local_id = get_filial_id(filial)

                salvos = 0
                for it in itens:
                    # produto único e organizado
                    nome_prod = f"{it.categoria} - {it.produto}"
                    pid = garantir_produto(nome_prod, it.categoria)

                    # estoque = contagem
                    qexec("""
                        INSERT INTO registros_diarios (data, produto_id, local_id, estoque)
                        VALUES (:data, :pid, :lid, :estoque)
                        ON CONFLICT (data, produto_id, local_id)
                        DO UPDATE SET estoque = EXCLUDED.estoque;
                    """, {"data": data_ref, "pid": pid, "lid": local_id, "estoque": it.quantidade})
                    salvos += 1

                st.success(f"Contagem salva! Itens: {salvos} | Filial: {filial} | Data: {data_ref}")
                st.session_state["ct_itens"] = []
                st.rerun()

        st.divider()
        st.subheader("Excluir contagem do dia (filial + data)")
        if st.button("Excluir estoque desse dia/filial", key="ct_excluir"):
            local_id = get_filial_id(filial)
            qexec("""
                UPDATE registros_diarios
                SET estoque = NULL
                WHERE data = :d AND local_id = :lid;
            """, {"d": data_ref, "lid": local_id})
            st.success("Estoque apagado para esse dia/filial (apenas o campo estoque).")
            st.rerun()

    # =========================
    # TAB 2: PRODUÇÃO (foto)
    # =========================
    with tab2:
        st.subheader("Produção planejada (foto) — sempre Austin")
        data_prod = st.date_input("Data da produção planejada", value=date.today(), key="pf_data")
        st.caption("Você escolhe a data. A produção será salva em 'produzido_planejado' na filial AUSTIN.")

        img_file = st.file_uploader("Envie a foto (PNG/JPG)", type=["png", "jpg", "jpeg"], key="pf_img")
        if img_file:
            pil = Image.open(img_file)
            st.image(pil, caption="Imagem enviada", use_container_width=True)

            if st.button("Extrair (OCR)", key="pf_ocr"):
                texto_ocr = ocr_image_to_text(pil)
                itens = parse_producao_from_ocr_text(texto_ocr)

                if not itens:
                    st.warning("Não consegui extrair itens. Tente uma foto mais nítida/sem sombra.")
                else:
                    df_prev = pd.DataFrame([{
                        "Categoria": i.categoria,
                        "Produto": i.produto,
                        "Quantidade (planejado)": i.quantidade
                    } for i in itens])

                    st.session_state["pf_itens"] = itens
                    st.dataframe(df_prev, use_container_width=True, hide_index=True)

        if st.session_state.get("pf_itens"):
            if st.button("Salvar produção planejada", key="pf_salvar"):
                itens = st.session_state["pf_itens"]
                local_id = get_filial_id("AUSTIN")

                salvos = 0
                for it in itens:
                    nome_prod = f"{it.categoria} - {it.produto}"
                    pid = garantir_produto(nome_prod, it.categoria)

                    qexec("""
                        INSERT INTO registros_diarios (data, produto_id, local_id, produzido_planejado)
                        VALUES (:data, :pid, :lid, :qtd)
                        ON CONFLICT (data, produto_id, local_id)
                        DO UPDATE SET produzido_planejado = EXCLUDED.produzido_planejado;
                    """, {"data": data_prod, "pid": pid, "lid": local_id, "qtd": it.quantidade})
                    salvos += 1

                st.success(f"Produção planejada salva! Itens: {salvos} | Data: {data_prod} | Filial: AUSTIN")
                st.session_state["pf_itens"] = []
                st.rerun()

        st.divider()
        st.subheader("Excluir produção planejada do dia (Austin + data)")
        if st.button("Excluir planejado (Austin)", key="pf_excluir_planejado"):
            local_id = get_filial_id("AUSTIN")
            qexec("""
                UPDATE registros_diarios
                SET produzido_planejado = NULL
                WHERE data = :d AND local_id = :lid;
            """, {"d": data_prod, "lid": local_id})
            st.success("Produzido planejado apagado para Austin nessa data.")
            st.rerun()

        st.divider()
        st.subheader("Limpeza rápida (duas opções)")
        st.caption("Use quando importar/colar algo errado. Você escolhe a data acima.")

        cA, cB = st.columns(2)

        # ✅ OPÇÃO 1: Limpar só a produção planejada (Austin, data)
        with cA:
            st.markdown("**Opção 1 — Limpar SÓ Produção Planejada (Austin)**")
            if st.button("Limpar planejado do dia (Austin)", key="limpar_op1"):
                local_id = get_filial_id("AUSTIN")
                qexec("""
                    UPDATE registros_diarios
                    SET produzido_planejado = NULL
                    WHERE data = :d AND local_id = :lid;
                """, {"d": data_prod, "lid": local_id})
                st.success("OK: produção planejada removida (Austin).")
                st.rerun()

        # ✅ OPÇÃO 2: Limpar tudo do dia (Austin) + transferências do dia
        with cB:
            st.markdown("**Opção 2 — Limpar TUDO do dia (Austin) + Transferências**")
            incluir_transferencias = st.checkbox("Também apagar transferências dessa data", value=True, key="limpar_trf_check")

            if st.button("Limpar tudo do dia (Austin)", key="limpar_op2"):
                local_id = get_filial_id("AUSTIN")

                # zera campos do dia (Austin)
                qexec("""
                    UPDATE registros_diarios
                    SET
                      estoque = NULL,
                      produzido_planejado = NULL,
                      produzido = NULL,
                      vendido = NULL,
                      desperdicio = NULL,
                      total = NULL,
                      observacoes = NULL
                    WHERE data = :d AND local_id = :lid;
                """, {"d": data_prod, "lid": local_id})

                # opcional: apagar transferências da data
                if incluir_transferencias:
                    qexec("DELETE FROM transferencias WHERE data = :d;", {"d": data_prod})

                st.success("OK: limpeza completa feita (Austin).")
                st.rerun()

    # =========================
    # TAB 3: TRANSFERÊNCIA
    # =========================
    with tab3:
        st.subheader("Registrar envio (origem → destino)")
        data_t = st.date_input("Data", value=date.today(), key="tr_data")

        origem = st.selectbox("Origem", ["AUSTIN", "QUEIMADOS"], index=0, key="tr_origem")
        destino = st.selectbox("Destino", ["QUEIMADOS", "AUSTIN"], index=0, key="tr_destino")

        if origem == destino:
            st.warning("Origem e destino não podem ser iguais.")

        produtos = qdf("SELECT id, nome FROM produtos WHERE ativo = TRUE ORDER BY nome;")
        if produtos.empty:
            st.info("Cadastre / importe produtos primeiro.")
            st.stop()

        nome_produto = st.selectbox("Produto", produtos["nome"].tolist(), key="tr_prod")
        produto_id = int(produtos.loc[produtos["nome"] == nome_produto, "id"].iloc[0])

        qtd = st.number_input("Quantidade enviada", min_value=0.0, step=1.0, key="tr_qtd")
        obs = st.text_input("Observações (opcional)", key="tr_obs")

        if st.button("Salvar transferência", key="tr_salvar"):
            if origem == destino or qtd <= 0:
                st.warning("Verifique origem/destino e quantidade.")
            else:
                origem_id = get_filial_id(origem)
                destino_id = get_filial_id(destino)
                qexec("""
                    INSERT INTO transferencias (data, produto_id, origem_local_id, destino_local_id, quantidade, observacoes)
                    VALUES (:data, :pid, :orig, :dest, :qtd, :obs)
                    ON CONFLICT (data, produto_id, origem_local_id, destino_local_id)
                    DO UPDATE SET quantidade=EXCLUDED.quantidade, observacoes=EXCLUDED.observacoes;
                """, {"data": data_t, "pid": produto_id, "orig": origem_id, "dest": destino_id, "qtd": qtd, "obs": obs or None})
                st.success("Transferência salva!")
                st.rerun()

        st.divider()
        st.subheader("Transferências do dia")
        df_t = qdf("""
            SELECT t.id,
                   t.data AS "Data",
                   p.nome AS "Produto",
                   o.nome AS "Origem",
                   d.nome AS "Destino",
                   t.quantidade AS "Quantidade",
                   t.observacoes AS "Observações"
            FROM transferencias t
            JOIN produtos p ON p.id = t.produto_id
            JOIN locais o ON o.id = t.origem_local_id
            JOIN locais d ON d.id = t.destino_local_id
            WHERE t.data = :d
            ORDER BY o.nome, d.nome, p.nome;
        """, {"d": data_t})

        if df_t.empty:
            st.info("Sem transferências nessa data.")
        else:
            st.dataframe(df_t.drop(columns=["id"]), use_container_width=True, hide_index=True)

            st.subheader("Excluir 1 transferência")
            labels = (df_t["Produto"] + " | " + df_t["Origem"] + "→" + df_t["Destino"]).tolist()
            escolha = st.selectbox("Selecione", labels, key="tr_del_sel")
            tid = int(df_t.loc[(df_t["Produto"] + " | " + df_t["Origem"] + "→" + df_t["Destino"]) == escolha, "id"].iloc[0])

            if st.button("Excluir transferência selecionada", key="tr_del"):
                qexec("DELETE FROM transferencias WHERE id=:id;", {"id": tid})
                st.success("Transferência excluída.")
                st.rerun()

        st.divider()
        st.subheader("Excluir TODAS as transferências do dia")
        if st.button("Excluir tudo dessa data (transferências)", key="tr_del_all"):
            qexec("DELETE FROM transferencias WHERE data=:d;", {"d": data_t})
            st.success("Todas as transferências dessa data foram excluídas.")
            st.rerun()
