import pandas as pd
from datetime import date


def render(st, qdf, qexec, garantir_produto):
    st.header("Importar Excel")

    st.caption("A planilha deve ter colunas: CATEGORIA | PRODUTO | QUANTIDADE (e opcional DATA).")

    up = st.file_uploader("Envie o Excel (.xlsx)", type=["xlsx"])
    d = st.date_input("Data padrão (se a planilha não tiver DATA)", value=date.today())

    if not up:
        return

    if st.button("Processar"):
        try:
            df = pd.read_excel(up)
            df.columns = [c.strip().upper() for c in df.columns]

            required = {"CATEGORIA", "PRODUTO", "QUANTIDADE"}
            if not required.issubset(set(df.columns)):
                st.error(f"Faltando colunas: {required - set(df.columns)}")
                return

            if "DATA" not in df.columns:
                df["DATA"] = d

            df["CATEGORIA"] = df["CATEGORIA"].astype(str).str.strip().str.upper()
            df["PRODUTO"] = df["PRODUTO"].astype(str).str.strip().str.upper()
            df["QUANTIDADE"] = pd.to_numeric(df["QUANTIDADE"], errors="coerce").fillna(0).astype(int)

            st.dataframe(df, width="stretch", hide_index=True)
            st.session_state["_xl_df"] = df

            st.success("Processado. Agora clique em 'Salvar no banco'.")
        except Exception as e:
            st.error(f"Erro ao ler Excel: {e}")

    df2 = st.session_state.get("_xl_df")
    if df2 is not None:
        if st.button("Salvar no banco"):
            try:
                # Aqui salvamos como PRODUZIDO PLANEJADO (comportamento padrão do Excel)
                for _, r in df2.iterrows():
                    cat = r["CATEGORIA"]
                    prod = r["PRODUTO"]
                    qtd = int(r["QUANTIDADE"])
                    dt = r["DATA"]

                    pid = garantir_produto(cat, prod)

                    qexec("""
                        INSERT INTO movimentos (data, filial_id, product_id, produzido_planejado, observacoes)
                        VALUES (:data, 1, :pid, :qtd, :obs)
                        ON CONFLICT (data, filial_id, product_id)
                        DO UPDATE SET produzido_planejado = movimentos.produzido_planejado + EXCLUDED.produzido_planejado,
                                      observacoes = EXCLUDED.observacoes;
                    """, {"data": dt, "pid": pid, "qtd": qtd, "obs": "Import Excel (somar)"})

                st.success("Salvo! (Produzido planejado foi somado)")
                st.session_state.pop("_xl_df", None)
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
