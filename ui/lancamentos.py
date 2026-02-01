import pandas as pd
from sqlalchemy import text
from datetime import date
from PIL import Image

from services.ocr_producao import ocr_image_to_text, parse_producao_from_ocr_text

def render(st, engine, garantir_produto, get_branch_id):
    st.header("Lançamentos do dia")

    branch = st.selectbox("Filial", ["AUSTIN", "QUEIMADOS"])
    branch_id = get_branch_id(branch)

    day = st.date_input("Data", value=date.today())

    # Manual
    st.subheader("Lançamento manual (venda / desperdício / produção real)")
    with engine.begin() as conn:
        prods = pd.read_sql(text("""
            SELECT id, name AS produto, COALESCE(category,'') AS categoria
            FROM products WHERE active=TRUE
            ORDER BY category NULLS LAST, name;
        """), conn)

    if prods.empty:
        st.info("Cadastre produtos primeiro.")
        return

    prod_label = st.selectbox(
        "Produto",
        [f"{r['categoria']} | {r['produto']}".strip(" |") for _, r in prods.iterrows()]
    )
    idx = [f"{r['categoria']} | {r['produto']}".strip(" |") for _, r in prods.iterrows()].index(prod_label)
    pid = int(prods.iloc[idx]["id"])

    c1,c2,c3,c4 = st.columns(4)
    produced_real = c1.number_input("Produção real", min_value=0.0, step=1.0)
    sold = c2.number_input("Vendido", min_value=0.0, step=1.0)
    waste = c3.number_input("Desperdício", min_value=0.0, step=1.0)
    notes = c4.text_input("Obs")

    if st.button("Salvar lançamento"):
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO daily_records(day, branch_id, product_id, produced_real, sold_qty, waste_qty, notes)
                VALUES (:day,:bid,:pid,:pr,:s,:w,:n)
                ON CONFLICT (day, branch_id, product_id)
                DO UPDATE SET
                  produced_real = EXCLUDED.produced_real,
                  sold_qty = EXCLUDED.sold_qty,
                  waste_qty = EXCLUDED.waste_qty,
                  notes = EXCLUDED.notes;
            """), {"day": day, "bid": branch_id, "pid": pid, "pr": produced_real, "s": sold, "w": waste, "n": notes or None})
        st.success("Salvo!")
        st.rerun()

    st.divider()

    # OCR
    st.subheader("Produção por foto (OCR) — salva como PRODUZIDO PLANEJADO")
    img = st.file_uploader("Enviar imagem (JPG/PNG)", type=["jpg","jpeg","png"])
    if img:
        pil = Image.open(img)
        st.image(pil, caption="Imagem enviada", use_container_width=True)

        if st.button("Extrair (OCR)"):
            texto = ocr_image_to_text(pil)
            st.text_area("OCR bruto", texto, height=200)

            itens = parse_producao_from_ocr_text(texto)
            if not itens:
                st.warning("Não consegui extrair itens úteis. Tente uma foto mais reta/mais clara.")
                return

            df = pd.DataFrame([{"categoria": i.categoria, "produto": i.produto, "qtd": i.quantidade} for i in itens])
            st.session_state["_ocr_preview"] = df
            st.success(f"Itens: {len(df)}")

    if "_ocr_preview" in st.session_state:
        df = st.session_state["_ocr_preview"]
        st.dataframe(df, use_container_width=True, hide_index=True)

        if st.button("Salvar produção planejada"):
            with engine.begin() as conn:
                for _, r in df.iterrows():
                    pid = garantir_produto(conn, r["produto"], r["categoria"])
                    conn.execute(text("""
                        INSERT INTO daily_records(day, branch_id, product_id, produced_planned)
                        VALUES (:day,:bid,:pid,:v)
                        ON CONFLICT (day, branch_id, product_id)
                        DO UPDATE SET produced_planned = EXCLUDED.produced_planned;
                    """), {"day": day, "bid": branch_id, "pid": pid, "v": float(r["qtd"] or 0)})

            st.success("Produção planejada salva!")
            del st.session_state["_ocr_preview"]
            st.rerun()
