from datetime import date
from services.whatsapp_parser import parse_whatsapp
from services.whatsapp_parser import parse_whatsapp_text


def render(st, qdf, qexec, garantir_produto, get_filial_id):
    st.header("Importar WhatsApp (texto)")

    filiais = qdf("SELECT nome FROM filiais ORDER BY nome;")["nome"].tolist()
    c1, c2 = st.columns([1, 1])
    with c1:
        filial_nome = st.selectbox("Filial", filiais)
        filial_id = get_filial_id(filial_nome)
    with c2:
        dia = st.date_input("Data", value=date.today())

    modo = st.radio("Salvar como:", ["Estoque (contagem)", "Produzido planejado"], horizontal=True)
    texto = st.text_area("Cole o texto aqui", height=260)

    if st.button("Processar"):
        itens = parse_whatsapp(texto)
        if not itens:
            st.warning("Não encontrei itens. Cole o texto no formato 'PRODUTO 10' e categorias em linhas separadas.")
            return

        st.write(f"Itens detectados: {len(itens)}")
        for it in itens[:10]:
            st.write(f"- {it.categoria} | {it.produto} = {it.quantidade}")

        if st.button("Salvar no banco"):
            for it in itens:
                pid = garantir_produto(it.categoria, it.produto)

                if modo == "Estoque (contagem)":
                    qexec("""
                    INSERT INTO movimentos(dia, filial_id, produto_id, estoque)
                    VALUES (:dia, :fid, :pid, :q)
                    ON CONFLICT (dia, filial_id, produto_id)
                    DO UPDATE SET estoque=EXCLUDED.estoque;
                    """, {"dia": dia, "fid": filial_id, "pid": pid, "q": it.quantidade})
                else:
                    qexec("""
                    INSERT INTO movimentos(dia, filial_id, produto_id, produzido_planejado)
                    VALUES (:dia, :fid, :pid, :q)
                    ON CONFLICT (dia, filial_id, produto_id)
                    DO UPDATE SET produzido_planejado=EXCLUDED.produzido_planejado;
                    """, {"dia": dia, "fid": filial_id, "pid": pid, "q": it.quantidade})

            st.success("OK! Importação salva.")
            st.rerun()
