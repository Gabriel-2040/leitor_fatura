from pathlib import Path
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Faturas & Upload",layout="wide")

# Aplica CSS
css_path = Path(__file__).parent.parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

from src.core.database import SessionLocal
from src.services.auth_service import AuthService
from src.services.invoice_service import InvoiceService
from src.models.institution import Institution
from src.models.invoice import Invoice
from src.ui.metrics import render_info_banner

db = SessionLocal()
try:
    user = AuthService.get_or_create_default_user(db)
    user_id = user.id

    st.title("Importação e Gestão de Faturas")
    st.caption("Envie o arquivo PDF da fatura do seu cartão de crédito para extração automatizada e categorização.")

    # 1. Seção de Upload
    st.markdown("### Upload de Nova Fatura")
    
    col1, col2 = st.columns([1, 2])

    institutions = db.query(Institution).all()
    inst_dict = {inst.slug: inst.name for inst in institutions}

    with col1:
        selected_slug = st.selectbox(
            "Selecione a Instituição Emissora",
            options=list(inst_dict.keys()),
            format_func=lambda x: inst_dict[x],
            help="O sistema aplicará o extrator especializado correspondente a este leiaute bancário."
        )

        allow_overwrite = st.checkbox(
            "Sobrescrever se fatura do mesmo mês já existir",
            value=False,
            help="Ative caso esteja reimportando uma fatura corrigida ou atualizada."
        )

    with col2:
        uploaded_file = st.file_uploader(
            "Selecione ou arraste o arquivo PDF da fatura",
            type=["pdf"],
            help="Aceita apenas arquivos no formato PDF nativo do banco."
        )

    if uploaded_file is not None:
        btn_process = st.button("Processar Fatura", type="primary")

        if btn_process:
            with st.spinner(f"Processando fatura de {inst_dict[selected_slug]} e categorizando lançamentos..."):
                try:
                    pdf_bytes = uploaded_file.read()
                    invoice = InvoiceService.process_and_save_invoice(
                        db=db,
                        user_id=user_id,
                        institution_slug=selected_slug,
                        pdf_bytes=pdf_bytes,
                        allow_overwrite=allow_overwrite,
                    )

                    st.success(
                        f"**Fatura processada com sucesso!**<br>"
                        f"Emissor: **{invoice.institution.name}** | "
                        f"Referência: **{invoice.reference_month:02d}/{invoice.reference_year}** | "
                        f"Total: **R$ {invoice.total_amount:,.2f}** | "
                        f"Lançamentos: **{len(invoice.items)} itens extraídos**."
                    )
                    st.balloons()
                except ValueError as ve:
                    st.error(f"**Atenção:** {str(ve)}")
                except Exception as e:
                    st.error(f"**Erro no processamento:** {str(e)}")

    st.markdown("---")

    # 2. Histórico de Faturas Importadas
    st.markdown("### Faturas Já Cadastradas")
    existing_invoices = InvoiceService.list_invoices(db, user_id=user_id)

    if not existing_invoices:
        st.info("Nenhuma fatura cadastrada até o momento.")
    else:
        invoices_table = []
        for inv in existing_invoices:
            invoices_table.append({
                "ID": inv.id,
                "Instituição": inv.institution.name,
                "Referência": f"{inv.reference_month:02d}/{inv.reference_year}",
                "Vencimento": inv.due_date.strftime("%d/%m/%Y"),
                "Fechamento": inv.closing_date.strftime("%d/%m/%Y") if inv.closing_date else "-",
                "Lançamentos": len(inv.items),
                "Valor Total": f"R$ {inv.total_amount:,.2f}",
                "Importado em": inv.created_at.strftime("%d/%m/%Y %H:%M"),
            })

        df_inv = pd.DataFrame(invoices_table)
        st.dataframe(df_inv.drop(columns=["ID"]), use_container_width=True, hide_index=True)

        # Ações de exclusão com confirmação
        with st.expander("🗑️ Gerenciar / Excluir Fatura"):
            del_options = {inv.id: f"{inv.institution.name} • {inv.reference_month:02d}/{inv.reference_year} (R$ {inv.total_amount:,.2f})" for inv in existing_invoices}
            selected_to_delete = st.selectbox("Escolha a fatura que deseja excluir:", options=list(del_options.keys()), format_func=lambda x: del_options[x])

            if st.button("Confirmar Exclusão da Fatura", type="secondary"):
                if InvoiceService.delete_invoice(db, user_id, selected_to_delete):
                    st.success("Fatura e lançamentos removidos com sucesso.")
                    st.rerun()

finally:
    db.close()
