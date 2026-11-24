from pathlib import Path
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Categorias & Aprendizado", layout="wide")

# Aplica CSS
css_path = Path(__file__).parent.parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from src.core.database import SessionLocal
from src.services.auth_service import AuthService
from src.models.category import Category
from src.models.categorization_rule import CategorizationRule

db = SessionLocal()
try:
    user = AuthService.get_or_create_default_user(db)
    user_id = user.id

    st.title("Categorias & Aprendizado por Reforço")
    st.caption("Gerencie as macrocategorias de gastos e visualize as regras de classificação aprendidas automaticamente pelo sistema.")

    tab1, tab2 = st.tabs([" Regras Aprendidas do Usuário", " Macrocategorias do Sistema"])

    # 1. Regras de Aprendizado
    with tab1:
        st.markdown("### Padrões")
        st.markdown("Cada vez que você reclassifica uma compra no Dashboard BI, o sistema memoriza o padrão do estabelecimento aqui, aplicando automaticamente nas próximas faturas.")

        user_rules = (
            db.query(CategorizationRule)
            .filter(CategorizationRule.user_id == user_id)
            .order_by(CategorizationRule.created_at.desc())
            .all()
        )

        if not user_rules:
            st.info("Nenhuma regra personalizada aprendida ainda. Conforme você reclassificar lançamentos nas faturas, elas aparecerão aqui.")
        else:
            rules_data = [
                {
                    "ID": r.id,
                    "Padrão do Estabelecimento": r.pattern,
                    "Tipo de Match": r.match_type,
                    "Categoria Associada": r.category.name,
                    "Prioridade": r.priority,
                    "Data do Aprendizado": r.created_at.strftime("%d/%m/%Y %H:%M"),
                }
                for r in user_rules
            ]
            df_rules = pd.DataFrame(rules_data)
            st.dataframe(df_rules.drop(columns=["ID"]), use_container_width=True, hide_index=True)

            st.write("")
            with st.expander("Excluir Regra de Aprendizado"):
                rule_options = {r.id: f"{r.pattern} -> {r.category.name}" for r in user_rules}
                del_rule_id = st.selectbox(
                    "Selecione a regra para remover:",
                    options=list(rule_options.keys()),
                    format_func=lambda x: rule_options[x]
                )
                if st.button("Excluir Regra"):
                    rule_to_del = db.query(CategorizationRule).filter_by(id=del_rule_id, user_id=user_id).first()
                    if rule_to_del:
                        db.delete(rule_to_del)
                        db.commit()
                        st.success("Regra removida com sucesso.")
                        st.rerun()

        st.markdown("---")
        st.markdown("#### Adicionar Regra")
        categories = db.query(Category).order_by(Category.name.asc()).all()
        cat_choices = {c.id: c.name for c in categories}

        col_r1, col_r2, col_r3 = st.columns([2, 2, 1])
        with col_r1:
            new_pattern = st.text_input("Estabelecimento (ex: 'PADARIA REAL', 'MCDONALDS')")
        with col_r2:
            new_cat = st.selectbox("Categoria", options=list(cat_choices.keys()), format_func=lambda x: cat_choices[x])
        with col_r3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("Salvar Regra", type="primary"):
                if new_pattern.strip():
                    rule = CategorizationRule(
                        user_id=user_id,
                        category_id=new_cat,
                        pattern=new_pattern.strip().upper(),
                        match_type="CONTAINS",
                        priority=10,
                    )
                    db.add(rule)
                    db.commit()
                    st.success("Nova regra gravada com sucesso!")
                    st.rerun()
                else:
                    st.warning("Informe o termo ou estabelecimento.")

    # 2. Categorias Globais
    with tab2:
        st.markdown("### Macrocategorias Padrão")
        cats = db.query(Category).order_by(Category.name.asc()).all()

        cats_data = [
            {
                "Nome": c.name,
                "Cor": c.color_hex,
                "Ícone": c.icon_name,
                "Padrão do Sistema": "Sim" if c.is_default else "Personalizada",
            }
            for c in cats
        ]
        st.dataframe(pd.DataFrame(cats_data), use_container_width=True, hide_index=True)

finally:
    db.close()
