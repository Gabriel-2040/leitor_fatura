import os
from pathlib import Path
import streamlit as st

# Configuração da página principal
st.set_page_config(
    page_title="Inteligência Financeira - Cartões",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carrega CSS customizado
css_path = Path(__file__).parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from src.core.database import SessionLocal
from src.core.seed import seed_database
from src.services.auth_service import AuthService
from src.services.analytics import AnalyticsService
from src.services.projections import ProjectionService
from src.ui.metrics import render_kpi_card, render_info_banner

# Garante que o banco e sementes estão carregados
if "db_initialized" not in st.session_state:
    seed_database()
    st.session_state["db_initialized"] = True

# Inicializa sessão do usuário
db = SessionLocal()
try:
    user = AuthService.get_or_create_default_user(db)
    st.session_state["user_id"] = user.id
    st.session_state["user_name"] = user.name
    st.session_state["user_email"] = user.email
finally:
    db.close()

# Sidebar de Perfil e Navegação
with st.sidebar:
    st.markdown("### **Fintech BI**")
    st.markdown(f"**Usuário:** {st.session_state.get('user_name', 'Gabriel')}")
    st.caption(f"Armazenamento 100% Local • `{st.session_state.get('user_email')}`")
    st.markdown("---")
    st.info(" **Dica de uso:** Acesse o menu lateral para importar suas faturas em PDF ou ver as projeções futuras de gastos.")

# Conteúdo da Página Principal
st.title("Inteligência Financeira Pessoal")
st.markdown("Transforme faturas de cartão de crédito em um painel BI analítico com **projeções preditivas de parcelamentos** e aprendizado contínuo.")

st.markdown("---")

# Obtém resumo rápido para a Home
db = SessionLocal()
try:
    data = AnalyticsService.get_dashboard_data(db, st.session_state["user_id"])
    proj = ProjectionService.calculate_future_projections(db, st.session_state["user_id"], months_ahead=6)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if data["has_data"]:
            inv = data["target_invoice"]
            render_kpi_card(
                "Fatura Recente",
                f"R$ {inv['total_amount']:,.2f}",
                f"{inv['institution_name']} • Ref. {inv['period']}",
                "neutral"
            )
        else:
            render_kpi_card("Fatura Recente", "R$ 0,00", "Nenhuma fatura importada", "neutral")

    with col2:
        if data["has_data"]:
            kpi = data["kpis"]
            diff = kpi["percentage_change"]
            trend = "up" if diff > 0 else ("down" if diff < 0 else "neutral")
            sub = "vs mês anterior"
            render_kpi_card("Variação Mensal", f"{diff:+.1f}%", sub, trend)
        else:
            render_kpi_card("Variação Mensal", "0%", "Sem histórico", "neutral")

    with col3:
        if data["has_data"] and data["kpis"]["top_category"]:
            top = data["kpis"]["top_category"]
            render_kpi_card(
                "Maior Impacto",
                f"R$ {top['amount']:,.2f}",
                f"{top['name']} ({top['percentage']:.1f}%)",
                "up"
            )
        else:
            render_kpi_card("Maior Impacto", "R$ 0,00", "Aguardando faturas", "neutral")

    with col4:
        tot_comm = proj["total_committed"]
        active_commitments = sum(p["items_count"] for p in proj["projections"])
        render_kpi_card(
            "Comprometido Futuro",
            f"R$ {tot_comm:,.2f}",
            f"{active_commitments} parcelas futuras ativas",
            "neutral"
        )

    st.markdown("<br>", unsafe_allow_html=True)

    if not data["has_data"]:
        render_info_banner(
            " **Bem-vindo ao seu painel financeiro!**<br>"
            "Você ainda não importou nenhuma fatura. Para começar, vá até a aba "
            "** Faturas e Upload** no menu à esquerda e envie seu primeiro arquivo PDF do "
            "<b>Nubank, Itaú, Bradesco ou Caixa</b>.",
            "info"
        )
    else:
        st.success(f"Sistema ativo com dados consolidados para {st.session_state.get('user_name')}. Utilize o menu lateral para navegar entre o Dashboard BI e as Projeções Futuras.")

finally:
    db.close()
