from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Dashboard BI - Faturas", layout="wide")

# Aplica CSS
css_path = Path(__file__).parent.parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from src.core.database import SessionLocal
from src.services.auth_service import AuthService
from src.services.analytics import AnalyticsService
from src.models.institution import Institution
from src.models.invoice import Invoice
from src.ui.metrics import render_kpi_card, render_info_banner
from src.ui.charts import render_category_donut_chart, render_monthly_history_chart
from src.ui.tables import render_invoice_items_editor

db = SessionLocal()
try:
    user = AuthService.get_or_create_default_user(db)
    user_id = user.id

    st.title("Painel BI de Gastos de Cartão")
    st.caption("Visão consolidada de macrocategorias, comparativo histórico e lançamentos detalhados.")

    # 1. Filtros Superiores
    institutions = db.query(Institution).all()
    inst_options = {"all": "Todas as Instituições"}
    for inst in institutions:
        inst_options[inst.slug] = inst.name

    # Busca faturas disponíveis para montar opções de seleção
    invoices = db.query(Invoice).filter(Invoice.user_id == user_id).order_by(Invoice.reference_year.desc(), Invoice.reference_month.desc()).all()

    if not invoices:
        render_info_banner(
            "⚠️ **Nenhuma fatura encontrada.**<br>Acesse a aba <b>💳 Faturas e Upload</b> para fazer o upload do seu primeiro PDF.",
            "warning"
        )
        st.stop()

    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        selected_inst_slug = st.selectbox(
            "Instituição Emissora",
            options=list(inst_options.keys()),
            format_func=lambda x: inst_options[x]
        )

    # Filtra as faturas pela instituição selecionada
    filtered_invoices = invoices
    if selected_inst_slug != "all":
        filtered_invoices = [inv for inv in invoices if inv.institution.slug == selected_inst_slug]

    if not filtered_invoices:
        st.warning(f"Nenhuma fatura cadastrada para {inst_options[selected_inst_slug]}.")
        st.stop()

    inv_options = {
        f"{inv.reference_year}_{inv.reference_month}_{inv.id}": f"{inv.institution.name} • {inv.reference_month:02d}/{inv.reference_year} (R$ {inv.total_amount:,.2f})"
        for inv in filtered_invoices
    }

    with col_f2:
        selected_inv_key = st.selectbox(
            "Fatura de Referência",
            options=list(inv_options.keys()),
            format_func=lambda x: inv_options[x]
        )

    # Extrai o ano e mês da seleção
    parts = selected_inv_key.split("_")
    sel_year = int(parts[0])
    sel_month = int(parts[1])

    # 2. Carrega dados consolidados
    data = AnalyticsService.get_dashboard_data(
        db=db,
        user_id=user_id,
        institution_slug=selected_inst_slug,
        year=sel_year,
        month=sel_month,
    )

    st.markdown("---")

    # 3. Cards de KPI
    target = data["target_invoice"]
    kpi = data["kpis"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_kpi_card(
            "Total da Fatura",
            f"R$ {kpi['current_total']:,.2f}",
            f"Vencimento: {target['due_date']}",
            "neutral"
        )

    with col2:
        diff = kpi["percentage_change"]
        trend = "up" if diff > 0 else ("down" if diff < 0 else "neutral")
        sign = "+" if diff > 0 else ""
        render_kpi_card(
            "Comparativo Mensal",
            f"{sign}{diff:.1f}%",
            f"vs anterior (R$ {kpi['previous_total']:,.0f})" if kpi['previous_total'] > 0 else "Sem histórico",
            trend
        )

    with col3:
        if kpi["top_category"]:
            top = kpi["top_category"]
            render_kpi_card(
                "Maior Macrocategoria",
                f"R$ {top['amount']:,.2f}",
                f"{top['name']} ({top['percentage']:.1f}%)",
                "up"
            )
        else:
            render_kpi_card("Maior Macrocategoria", "R$ 0,00", "-", "neutral")

    with col4:
        render_kpi_card(
            "Transações",
            f"{kpi['items_count']} itens",
            f"Fechamento: {target['closing_date']}",
            "neutral"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Gráficos de BI (Plotly)
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("##### Distribuição por Macrocategoria")
        fig_donut = render_category_donut_chart(data["by_category"])
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_chart2:
        st.markdown("##### Evolução Histórica das Faturas")
        fig_history = render_monthly_history_chart(data["monthly_history"])
        st.plotly_chart(fig_history, use_container_width=True)

    st.markdown("---")

    # 5. Tabela de Lançamentos com Reclassificação Inline
    render_invoice_items_editor(db, user_id, data["items"])

finally:
    db.close()
