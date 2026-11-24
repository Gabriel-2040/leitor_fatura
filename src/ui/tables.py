from typing import List, Dict, Any
import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from src.services.categorizer import CategorizerService
from src.models.category import Category

def render_invoice_items_editor(db: Session, user_id: str, items_data: List[Dict[str, Any]]):
    """
    Renderiza os lançamentos da fatura permitindo a reclassificação inline com feedback imediato
    e disparo do aprendizado por reforço.
    """
    if not items_data:
        st.info("Nenhum lançamento encontrado nesta fatura.")
        return

    # Obtém todas as categorias disponíveis no banco para o dropdown
    categories = db.query(Category).order_by(Category.name.asc()).all()
    cat_names = [c.name for c in categories]
    cat_map_by_name = {c.name: c.id for c in categories}

    # Monta DataFrame Pandas para o st.data_editor
    df = pd.DataFrame([
        {
            "id": item["id"],
            "Data": item["date"],
            "Descrição": item["description"],
            "Categoria": item["category_name"],
            "Parcela": item["installment"],
            "Valor (R$)": item["amount"],
        }
        for item in items_data
    ])

    st.markdown("##### 📝 Lançamentos da Fatura")
    st.caption("💡 *Altere a categoria diretamente na tabela abaixo. O sistema memorizará sua escolha para faturas futuras (Aprendizado por Reforço).*")

    # Configuração de colunas do st.data_editor
    column_config = {
        "id": None,  # Oculta o ID técnico
        "Data": st.column_config.TextColumn("Data da Compra", disabled=True, width="small"),
        "Descrição": st.column_config.TextColumn("Estabelecimento / Descrição", disabled=True, width="large"),
        "Categoria": st.column_config.SelectboxColumn(
            "Categoria",
            options=cat_names,
            required=True,
            width="medium"
        ),
        "Parcela": st.column_config.TextColumn("Parcela", disabled=True, width="small"),
        "Valor (R$)": st.column_config.NumberColumn(
            "Valor (R$)",
            format="R$ %.2f",
            disabled=True,
            width="small"
        ),
    }

    # Chave única baseada nos IDs presentes
    editor_key = f"editor_items_{items_data[0]['id'] if items_data else 'empty'}"

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key=editor_key,
    )

    # Detecta alterações feitas pelo usuário
    if editor_key in st.session_state and "edited_rows" in st.session_state[editor_key]:
        edited_rows = st.session_state[editor_key]["edited_rows"]
        if edited_rows:
            reclassified_count = 0
            for row_idx, changes in edited_rows.items():
                if "Categoria" in changes:
                    new_cat_name = changes["Categoria"]
                    new_cat_id = cat_map_by_name.get(new_cat_name)
                    item_id = df.iloc[row_idx]["id"]
                    item_desc = df.iloc[row_idx]["Descrição"]

                    if new_cat_id:
                        CategorizerService.reclassify_item(
                            db=db,
                            user_id=user_id,
                            item_id=item_id,
                            new_category_id=new_cat_id,
                            apply_to_future=True,
                        )
                        reclassified_count += 1

            if reclassified_count > 0:
                st.success(f"✨ {reclassified_count} lançamento(s) reclassificado(s) com sucesso! Regra de aprendizado gravada para faturas futuras.")
                st.rerun()
