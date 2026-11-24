import streamlit as st

def render_kpi_card(title: str, value: str, subtext: str = "", trend: str = "neutral"):
    """
    Renderiza um card KPI estilizado com HTML/CSS executivo.
    trend pode ser: 'up', 'down', 'neutral'
    """
    trend_class = f"kpi-{trend}" if trend in ["up", "down", "neutral"] else "kpi-neutral"
    
    html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-subtext {trend_class}">{subtext}</div>' if subtext else ''}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_info_banner(message: str, box_type: str = "info"):
    """Renderiza uma caixa de aviso estilizada ('info', 'success', 'warning')."""
    html = f"""
    <div class="{box_type}-box">
        {message}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
