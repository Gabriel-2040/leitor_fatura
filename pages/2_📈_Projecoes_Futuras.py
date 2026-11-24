from pathlib import Path
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Projeções Futuras - Parcelamentos", layout="wide")

# Aplica CSS
css_path = Path(__file__).parent.parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from src.core.database import SessionLocal
from src.services.auth_service import AuthService
from src.services.projections import ProjectionService
from src.ui.metrics import render_kpi_card, render_info_banner
from src.ui.charts import render_projections_chart

db = SessionLocal()
try:
    user = AuthService.get_or_create_default_user(db)
    user_id = user.id

    st.title("Projeções de Gastos Futuros")
    st.caption("Previsão preditiva baseada nas parcelas restantes identificadas nas suas faturas.")

    # Controle de horizonte de projeção
    col_ctrl1, col_ctrl2 = st.columns([1, 3])
    with col_ctrl1:
        months_ahead = st.selectbox(
            "Horizonte de Previsão",
            options=[3, 6, 9, 12],
            index=1,
            format_func=lambda x: f"Próximos {x} meses"
        )

    # Executa cálculo de projeções (RN-03)
    proj_data = ProjectionService.calculate_future_projections(db, user_id, months_ahead=months_ahead)
    projections = proj_data["projections"]
    total_committed = proj_data["total_committed"]

    if not projections:
        render_info_banner(
            " **Nenhuma compra parcelada ativa identificada no momento.**<br>"
            "Quando você importar faturas contendo compras parceladas (ex: <i>01/06</i>, <i>02/10</i>), "
            "o sistema projetará aqui os valores exatos mês a mês até a quitação.",
            "info"
        )
        st.stop()

    # Cards de Indicadores de Projeção
    col1, col2, col3 = st.columns(3)

    # Identifica o mês de maior impacto futuro
    max_month = max(projections, key=lambda x: x["total_projected"])
    active_items_total = sum(p["items_count"] for p in projections)

    with col1:
        render_kpi_card(
            "Total Comprometido",
            f"R$ {total_committed:,.2f}",
            f"Soma de todas as parcelas contratadas ({months_ahead} meses)",
            "neutral"
        )

    with col2:
        render_kpi_card(
            "Mês de Maior Impacto",
            f"R$ {max_month['total_projected']:,.2f}",
            f"Período: {max_month['month']:02d}/{max_month['year']} ({max_month['items_count']} compras)",
            "up"
        )

    with col3:
        media_mensal = total_committed / len(projections) if projections else 0.0
        render_kpi_card(
            "Média Mensal Contratada",
            f"R$ {media_mensal:,.2f}",
            f"{len(projections)} meses com compromissos mapeados",
            "neutral"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico de Curva de Quitação e Barras de Gastos
    st.markdown("##### Curva de Quitação das Compras Parceladas")
    fig_proj = render_projections_chart(projections)
    st.plotly_chart(fig_proj, use_container_width=True)

    st.markdown("---")

    # Detalhamento Mês a Mês (Drill-down das parcelas)
    st.markdown("##### Detalhamento das Parcelas por Mês Futuro")
    
    # Abas por mês projetado
    tabs = st.tabs([f" {p['month']:02d}/{p['year']} (R$ {p['total_projected']:,.2f})" for p in projections])

    for idx, p in enumerate(projections):
        with tabs[idx]:
            commitments = p["commitments"]
            if commitments:
                df_comm = pd.DataFrame([
                    {
                        "Estabelecimento / Compra": c["description"],
                        "Parcela": c["installment"],
                        "Categoria": c["category"],
                        "Valor da Parcela": f"R$ {c['amount']:,.2f}",
                    }
                    for c in commitments
                ])
                st.dataframe(df_comm, use_container_width=True, hide_index=True)
            else:
                st.write("Nenhum lançamento previsto.")

finally:
    db.close()
