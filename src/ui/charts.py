from typing import List, Dict, Any
import plotly.graph_objects as go

DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#e2e8f0"),
    margin=dict(t=30, b=30, l=20, r=20),
)

def render_category_donut_chart(by_category: List[Dict[str, Any]]) -> go.Figure:
    """Gera um gráfico de rosca (donut chart) com a distribuição de gastos por categoria."""
    if not by_category:
        fig = go.Figure()
        fig.update_layout(
            **DARK_LAYOUT,
            annotations=[dict(text="Sem dados de categorias", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#94a3b8"))]
        )
        return fig

    labels = [c["name"] for c in by_category if c["amount"] > 0]
    values = [c["amount"] for c in by_category if c["amount"] > 0]
    colors = [c["color"] for c in by_category if c["amount"] > 0]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
                textinfo="percent+label",
                textposition="inside",
                insidetextorientation="radial",
                hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<br>(%{percent})<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        **DARK_LAYOUT,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(size=11, color="#94a3b8"),
        ),
        height=380,
    )
    return fig

def render_monthly_history_chart(monthly_history: List[Dict[str, Any]]) -> go.Figure:
    """Gera um gráfico de barras com a evolução histórica das faturas."""
    if not monthly_history:
        fig = go.Figure()
        fig.update_layout(
            **DARK_LAYOUT,
            annotations=[dict(text="Nenhuma fatura histórica disponível", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#94a3b8"))]
        )
        return fig

    x_labels = [h["label"] for h in monthly_history]
    y_values = [h["amount"] for h in monthly_history]
    colors = [h["color"] for h in monthly_history]
    institutions = [h["institution"] for h in monthly_history]

    fig = go.Figure(
        data=[
            go.Bar(
                x=x_labels,
                y=y_values,
                marker=dict(
                    color=colors,
                    line=dict(color="rgba(255,255,255,0.15)", width=1),
                    opacity=0.9
                ),
                text=[f"R$ {val:,.2f}" for val in y_values],
                textposition="auto",
                customdata=institutions,
                hovertemplate="<b>%{x}</b> (%{customdata})<br>Total: R$ %{y:,.2f}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        **DARK_LAYOUT,
        height=350,
        xaxis=dict(showgrid=False, linecolor="rgba(255,255,255,0.1)", tickfont=dict(color="#94a3b8")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickprefix="R$ ", tickfont=dict(color="#94a3b8")),
    )
    return fig

def render_projections_chart(projections: List[Dict[str, Any]]) -> go.Figure:
    """Gera um gráfico analítico com as projeções futuras de gastos por parcelamento."""
    if not projections:
        fig = go.Figure()
        fig.update_layout(
            **DARK_LAYOUT,
            annotations=[dict(text="Nenhum parcelamento ativo projetado", x=0.5, y=0.5, showarrow=False, font=dict(size=14, color="#94a3b8"))]
        )
        return fig

    periods = [f"{p['month']:02d}/{p['year']}" for p in projections]
    totals = [p["total_projected"] for p in projections]
    items_count = [p["items_count"] for p in projections]

    fig = go.Figure()

    # Barras de total projetado
    fig.add_trace(
        go.Bar(
            x=periods,
            y=totals,
            name="Gastos Contratados",
            marker=dict(
                color="#6366F1",
                line=dict(color="rgba(255,255,255,0.2)", width=1),
                opacity=0.85
            ),
            text=[f"R$ {v:,.2f}" for v in totals],
            textposition="auto",
            customdata=items_count,
            hovertemplate="<b>%{x}</b><br>Comprometido: R$ %{y:,.2f}<br>Compras parceladas ativas: %{customdata}<extra></extra>",
        )
    )

    # Linha de tendência
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=totals,
            mode="lines+markers",
            name="Curva de Quitação",
            line=dict(color="#10B981", width=3, shape="spline"),
            marker=dict(size=8, color="#10B981"),
            hoverinfo="skip",
        )
    )

    fig.update_layout(
        **DARK_LAYOUT,
        height=380,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        xaxis=dict(showgrid=False, linecolor="rgba(255,255,255,0.1)", tickfont=dict(color="#94a3b8")),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.06)", tickprefix="R$ ", tickfont=dict(color="#94a3b8")),
    )
    return fig
