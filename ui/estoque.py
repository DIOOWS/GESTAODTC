import pandas as pd
import streamlit as st
from sqlalchemy.exc import IntegrityError


def _find_existing_product_id(qdf, categoria, produto, exclude_id=None):
    sql = "SELECT id FROM products WHERE categoria=:c AND produto=:p"
    params = {"c": categoria, "p": produto}
    df = qdf(sql + (" AND id<>:id" if exclude_id else "") + ";",
             {**params, **({"id": exclude_id} if exclude_id else {})})
    if df.empty:
        return None
    return int(df.iloc[0]["id"])


def _merge_products(qexec, from_id: int, to_id: int):
    # move movimentos
    qexec("""
        UPDATE movimentos
        SET product_id = :to_id
        WHERE product_id = :from_id;
    """, {"from_id": from_id, "to_id": to_id})

    # move transferencias (se existir tabela)
    try:
        qexec("""
            UPDATE transferencias
            SET product_id = :to_id
            WHERE product_id = :from_id;
        """, {"from_id": from_id, "to_id": to_id})
    except Exception:
        pass

    # apaga produto antigo
    qexec("DELETE FROM products WHERE id=:id;", {"id": from_id})


def render(st, qdf, qexec):
    st.header("Produtos")

    df = qdf("""
        SELECT id, categoria, produto, ativo
        FROM products
        ORDER BY categoria, produto;
    """)

    st.caption("Você pode editar categoria/nome/ativo aqui. Depois clique em **Salvar alterações**.")

    edited = st.data_editor(
        df,
        width="stretch",
        hide_index=True,
        num_rows="fixed",
        disabled=["id"],
        column_config={
            "id": st.column_config.NumberColumn("id"),
            "categoria": st.column_config.TextColumn("categoria"),
            "produto": st.column_config.TextColumn("produto"),
            "ativo": st.column_config.CheckboxColumn("ativo"),
        },
        key="prod_editor",
    )

    col1, col2 = st.columns(2)

    if col1.button("Salvar alterações"):
        try:
            # salva linha a linha
            for _, r in edited.iterrows():
                pid = int(r["id"])
                c = str(r["categoria"]).strip().upper()
                p = str(r["produto"]).strip().upper()
                ativo = bool(r["ativo"])

                qexec("""
                    UPDATE products
                    SET categoria=:c, produto=:p, ativo=:a
                    WHERE id=:id;
                """, {"c": c, "p": p, "a": ativo, "id": pid})

            st.success("Alterações salvas.")
            st.rerun()

        except IntegrityError as e:
            # normalmente pega UniqueViolation aqui
            st.error(f"Erro ao salvar (duplicado): {e}")
            st.info("Se você tentou renomear para um produto que já existe, use a opção **Mesclar** abaixo.")
            st.session_state["_prod_save_error"] = str(e)

        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    # Excluir / Mesclar
    st.divider()
    st.subheader("Excluir ou Mesclar produtos")

    pid = col2.selectbox(
        "Escolha um produto (id) para excluir/mesclar",
        options=df["id"].tolist(),
        format_func=lambda x: f"{int(x)} - {df.loc[df['id']==x,'categoria'].iloc[0]} / {df.loc[df['id']==x,'produto'].iloc[0]}",
    )

    st.warning("⚠️ Excluir produto remove também os movimentos/transferências ligados a ele (por cascade).")

    c_del = str(df.loc[df["id"] == pid, "categoria"].iloc[0]).strip().upper()
    p_del = str(df.loc[df["id"] == pid, "produto"].iloc[0]).strip().upper()

    colA, colB = st.columns(2)

    if colA.button("Excluir produto"):
        try:
            qexec("DELETE FROM products WHERE id=:id;", {"id": int(pid)})
            st.success("Produto excluído.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao excluir: {e}")

    st.caption("Mesclar serve quando você criou duplicado e quer juntar em um só (movimentos vão junto).")

    target_id = _find_existing_product_id(qdf, c_del, p_del, exclude_id=int(pid))

    if target_id:
        st.info(f"Já existe outro produto com mesmo nome/categoria: ID {target_id}. Você pode mesclar.")
        if colB.button("Mesclar (mover tudo pro existente e apagar este)"):
            try:
                _merge_products(qexec, from_id=int(pid), to_id=int(target_id))
                st.success("Mesclado com sucesso.")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao mesclar: {e}")
    else:
        colB.button("Mesclar", disabled=True)