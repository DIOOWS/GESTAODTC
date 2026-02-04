from datetime import date
import pandas as pd
import streamlit as st

from services.whatsapp_parser import parse_whatsapp_text


def _to_num(x):
    try:
        if x is None:
            return 0.0
        if isinstance(x, str):
            x = x.replace(",", ".").strip()
        return float(x)
    except Exception:
        return 0.0


def _collect_ignored_lines(texto: str):
    """
    Retorna lista de dicts: {"linha": "...", "motivo": "..."}
    Baseado em regras simples:
    - Linha vazia -> ignora
    - Header -> não é item
    - Sem número -> ignora
    """
    import re
    from services.whatsapp_parser import _clean, _is_header

    ignored = []
    for raw in (texto or "").splitlines():
        line = _clean(raw)
        if not line:
            continue
        if _is_header(line):
            ignored.append({"linha": line, "motivo": "Categoria/título"})
            continue
        if not re.search(r"\d", line):
            ignored.append({"linha": line, "motivo": "Sem número (não parece item)"})
            continue
        # tem número mas o parser pode não pegar (ex: formato estranho)
        # aqui a gente marca como "não reconhecido" só se não entrar nos itens
        # (essa parte é tratada depois comparando com os itens detectados)
    return ignored


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Importar WhatsApp (texto livre)")

    col1, col2 = st.columns(2)
    filial = col1.selectbox("Filial", ["AUSTIN", "QUEIMADOS"], index=0)
    d = col2.date_input("Data", value=date.today())

    salvar_como = st.radio(
        "Salvar como:",
        ["Estoque (contagem)", "Produzido planejado"],
        index=0,
        horizontal=True,
    )

    somar = st.checkbox("Somar ao valor já salvo (em vez de substituir)", value=False)

    texto = st.text_area("Cole o texto aqui", height=280)

    if st.button("Processar"):
        itens = parse_whatsapp_text(texto)

        if not itens:
            st.warning("Não detectei itens. Confere se as linhas têm número (ex: '24 torrada temperada').")
            st.session_state.pop("_wa_df", None)
            st.session_state.pop("_wa_raw", None)
            return

        df = pd.DataFrame(itens)

        # normaliza tipos
        df["categoria"] = df["categoria"].astype(str)
        df["produto"] = df["produto"].astype(str)
        df["quantidade"] = df["quantidade"].apply(_to_num)

        st.session_state["_wa_df"] = df
        st.session_state["_wa_raw"] = texto
        st.session_state["_wa_filial"] = filial
        st.session_state["_wa_data"] = d
        st.session_state["_wa_salvar_como"] = salvar_como
        st.session_state["_wa_somar"] = somar

    df = st.session_state.get("_wa_df")
    if df is not None and not df.empty:
        st.subheader(f"Itens detectados: {len(df)}")

        # Editor pra corrigir antes de salvar
        edited = st.data_editor(
            df,
            width="stretch",
            hide_index=True,
            num_rows="dynamic",
            column_config={
                "categoria": st.column_config.TextColumn("categoria"),
                "produto": st.column_config.TextColumn("produto"),
                "quantidade": st.column_config.NumberColumn("quantidade", step=1),
            },
        )

        st.session_state["_wa_df"] = edited

        # Linhas ignoradas
        st.subheader("Linhas ignoradas (para você conferir)")
        ignored = _collect_ignored_lines(st.session_state.get("_wa_raw", ""))

        # marca também linhas “com número” que não viraram item detectado
        raw_lines = []
        for raw in (st.session_state.get("_wa_raw", "") or "").splitlines():
            raw_lines.append(raw.strip())
        detected_set = set()
        for _, r in edited.iterrows():
            detected_set.add(f"{str(r.get('categoria','')).strip()}|{str(r.get('produto','')).strip()}|{_to_num(r.get('quantidade'))}")

        # só uma exibição simples (sem ficar pesado)
        if ignored:
            st.dataframe(pd.DataFrame(ignored), width="stretch", hide_index=True)
        else:
            st.caption("Nenhuma linha foi ignorada como 'categoria' ou 'sem número'.")

        # Salvar
        if st.button("Salvar no banco"):
            try:
                filial = st.session_state["_wa_filial"]
                d = st.session_state["_wa_data"]
                salvar_como = st.session_state["_wa_salvar_como"]
                somar = st.session_state["_wa_somar"]

                filial_id = get_filial_id(filial)

                campo = "estoque" if salvar_como.startswith("Estoque") else "produzido_planejado"

                # salva linha a linha
                for _, r in edited.iterrows():
                    categoria = str(r.get("categoria", "")).strip().upper()
                    produto = str(r.get("produto", "")).strip().upper()
                    quantidade = _to_num(r.get("quantidade", 0))

                    if not categoria or not produto:
                        continue
                    if quantidade == 0:
                        continue

                    product_id = garantir_produto(categoria, produto)

                    if somar:
                        # soma no valor já existente
                        qexec(f"""
                            INSERT INTO movimentos (data, filial_id, product_id, {campo})
                            VALUES (:data, :filial, :pid, :qtd)
                            ON CONFLICT (data, filial_id, product_id)
                            DO UPDATE SET {campo} = COALESCE(movimentos.{campo},0) + EXCLUDED.{campo};
                        """, {
                            "data": d,
                            "filial": filial_id,
                            "pid": product_id,
                            "qtd": quantidade
                        })
                    else:
                        # substitui
                        qexec(f"""
                            INSERT INTO movimentos (data, filial_id, product_id, {campo})
                            VALUES (:data, :filial, :pid, :qtd)
                            ON CONFLICT (data, filial_id, product_id)
                            DO UPDATE SET {campo} = EXCLUDED.{campo};
                        """, {
                            "data": d,
                            "filial": filial_id,
                            "pid": product_id,
                            "qtd": quantidade
                        })

                st.success("Salvo com sucesso!")
                st.session_state.pop("_wa_df", None)
                st.session_state.pop("_wa_raw", None)

            except Exception as e:
                st.error(f"Erro ao salvar: {e}")