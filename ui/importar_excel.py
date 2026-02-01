from services import excel_import


def render(st, qdf, qexec):
    st.header("Importar Excel")
    st.caption("Importe cadastro de produtos e tortas como cadastro.")

    tipo = st.radio(
        "O que você quer importar?",
        ["Cadastro (produtos + categoria) do RELATORIO",
         "Tortas (cadastro de produtos apenas)"]
    )

    arquivo = st.file_uploader("Selecione um arquivo .xlsx", type=["xlsx"])
    if arquivo is None:
        st.info("Envie um arquivo .xlsx para importar.")
        st.stop()

    if st.button("Importar agora"):
        try:
            if tipo.startswith("Cadastro"):
                r = excel_import.importar_cadastro_produtos_do_relatorio(qexec, qdf, arquivo)
                st.success(f"Cadastro importado! Abas: {r['abas']} | Processados: {r['processados']} | Ignorados: {r['ignorados']} | Total: {r['total']}")
            else:
                r = excel_import.importar_tortas_modelo_novo(qexec, qdf, arquivo)
                st.success(f"Tortas cadastradas! Aba: {r['aba']} | Produtos: {r['produtos_cadastrados']} | Ignorados: {r['ignorados']}")

            st.info("Resumo do banco")
            st.write("Produtos:", int(qdf("SELECT COUNT(*) AS n FROM produtos;")["n"].iloc[0]))
            st.write("Registros:", int(qdf("SELECT COUNT(*) AS n FROM registros_diarios;")["n"].iloc[0]))
            st.write("Transferências:", int(qdf("SELECT COUNT(*) AS n FROM transferencias;")["n"].iloc[0]))

            st.rerun()
        except Exception as e:
            st.error(f"Erro ao importar: {e}")
