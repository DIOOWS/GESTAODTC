import pandas as pd
from sqlalchemy import text
from datetime import date
from services.whatsapp_parser import parse_whatsapp_text

def render(st, engine, garantir_produto, get_branch_id):
    st.header("Importar WhatsApp (texto)")

    branch = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"])
    branch_id = get_branch_id(branch)

    day = st.date_input("Data", value=date.today())

    mode = st.radio("Salvar como:", ["Estoque (contagem)", "Produzido planejado"], horizontal=True)

    txt = st.text_area("Cole o texto aqui", height=220)
    if st.button("Processar"):
        items = parse_whatsapp_text(txt)
        if not items:
            st.warning("Não consegui identificar linhas com quantidade.")
            return

        df = pd.DataFrame([{"categoria": i.category, "produto": i.product, "qtd": i.qty} for i in items])
        st.session_state["_wa_preview"] = df
        st.success(f"Itens encontrados: {len(df)}")

    if "_wa_preview" in st.session_state:
        df = st.session_state["_wa_preview"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("Salvar no banco"):
            with engine.begin() as conn:
                for _, r in df.iterrows():
                    pid = garantir_produto(conn, r["produto"], r["categoria"])

                    if mode.startswith("Estoque"):
                        conn.execute(text("""
                            INSERT INTO daily_records(day, branch_id, product_id, stock_qty)
                            VALUES (:day,:bid,:pid,:v)
                            ON CONFLICT (day, branch_id, product_id)
                            DO UPDATE SET stock_qty = EXCLUDED.stock_qty;
                        """), {"day": day, "bid": branch_id, "pid": pid, "v": float(r["qtd"] or 0)})
                    else:
                        conn.execute(text("""
                            INSERT INTO daily_records(day, branch_id, product_id, produced_planned)
                            VALUES (:day,:bid,:pid,:v)
                            ON CONFLICT (day, branch_id, product_id)
                            DO UPDATE SET produced_planned = EXCLUDED.produced_planned;
                        """), {"day": day, "bid": branch_id, "pid": pid, "v": float(r["qtd"] or 0)})

            st.success("Salvo!")
            del st.session_state["_wa_preview"]
            st.rerun()
