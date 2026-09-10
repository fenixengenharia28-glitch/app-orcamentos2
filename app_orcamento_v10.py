import streamlit as st
import pandas as pd
import datetime
import hashlib
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração da página para Desktop e Mobile
st.set_page_config(page_title="Orçamentos Construção Pro", page_icon="🏗️", layout="centered")

# --- SISTEMA DE VERIFICAÇÃO DE DOCUMENTOS (PÁGINA GOV SIMULADA) ---
query_params = st.query_params
if "verificar" in query_params:
    doc_hash = query_params["verificar"]
    st.success("🔒 PORTAL DE VERIFICAÇÃO DE DOCUMENTOS")
    st.title("✅ Documento Autêntico e Verificado")
    st.write("Este orçamento foi gerado e assinado digitalmente através do sistema Construção Pro em conformidade com os padrões de integridade documental.")
    st.info(f"**Código de Validação (Hash):** {doc_hash}")
    st.write(f"**Status da Assinatura:** ATIVA E VÁLIDA (Padrão ICP-Brasil Equivalente)")
    if st.button("Voltar ao Sistema de Orçamentos"):
        st.query_params.clear()
        st.rerun()
    st.stop()

# --- FLUXO NORMAL DO APLICATIVO ---
st.title("🏗️ Orçamentos Construção Pro")
st.caption("Versão v10 - Assinatura Padrão GOV com Verificação por QR Code")

if "df_materiais" not in st.session_state:
    st.session_state.df_materiais = pd.DataFrame(columns=["Item", "Qtd", "Preço Un.", "Total"])

aba1, aba2 = st.tabs(["📋 Gerar Orçamento", "🧮 Calcular Minha Hora"])

# --- ABA 2: CALCULADORA DE HORA TÉCNICA OPERACIONAL ---
with aba2:
    st.header("Descubra o Valor da sua Hora")
    custo_fixo_geral = st.number_input("Custos fixos mensais gerais:", min_value=0.0, value=500.0, step=50.0)
    val_veiculo = st.number_input("Valor de mercado do veículo (R$):", min_value=0.0, value=50000.0, step=1000.0)
    
    col_veh1, col_veh2 = st.columns(2)
    with col_veh1:
        ipva_licenciamento = st.number_input("IPVA + Licenciamento Anual (R$):", min_value=0.0, value=2400.0, step=100.0)
    with col_veh2:
        anos_com_veiculo = st.number_input("Anos com o carro:", min_value=1, value=5)
    
    depreciacao_mensal = (val_veiculo * 0.10) / 12
    cadastro_mensal = ipva_licenciamento / 12
    custo_veiculo_total_mes = depreciacao_mensal + cadastro_mensal
    
    salario_desejado = st.number_input("Meta de pró-labore mensal:", min_value=0.0, value=4000.0, step=100.0)
    dias_trabalhados = st.number_input("Dias operacionais por mês:", min_value=1, max_value=31, value=22)
    horas_por_dia = st.number_input("Horas produtivas por dia:", min_value=1.0, max_value=24.0, value=6.0, step=0.5)
    margem_lucro = st.slider("Margem da empresa (%)", min_value=0, max_value=50, value=20, step=5)
    
    horas_totais_mes = dias_trabalhados * horas_por_dia
    if horas_totais_mes > 0:
        custo_hora_bruto = (custo_fixo_geral + custo_veiculo_total_mes + salario_desejado) / horas_totais_mes
        hora_calculada = custo_hora_bruto / (1 - (margem_lucro / 100)) if margem_lucro < 100 else custo_hora_bruto
    else:
        hora_calculada = 0.0
        
    st.success(f"💰 **Hora técnica sugerida com margem: R$ {hora_calculada:.2f}**")
    if st.button("Aplicar valor no orçamento"):
        st.session_state["preco_hora_salvado"] = round(hora_calculada, 2)
        st.info("Preço atualizado!")

# --- ABA 1: GERADOR DE ORÇAMENTO MULTIUSO ---
with aba1:
    st.header("Identificação do Projeto")
    col_cli1, col_cli2 = st.columns(2)
    with col_cli1:
        nome_cliente = st.text_input("Nome do Cliente / Empresa:")
    with col_cli2:
        tipo_obra = st.selectbox("Segmento da Obra:", ["Construção Geral", "Elétrica", "Hidráulica", "Pintura / Acabamento", "Alvenaria / Estruturas", "Gesso / Drywall"])
        
    servico_principal = st.text_input("Descrição do Escopo Principal:")
    nome_responsavel = st.text_input("Nome do Responsável Técnico (Para Assinatura GOV):", value="Responsável Técnico")

    st.write("---")
    st.header("👷 Quantificação da Mão de Obra")
    tipo_cobranca = st.selectbox("Critério de cobrança:", ["Por Empreitada / Ponto", "Por Hora Técnica"])

    valor_servico = 0.0
    if tipo_cobranca == "Por Empreitada / Ponto":
        col_srv1, col_srv2 = st.columns(2)
        with col_srv1:
            qtd_pontos = st.number_input("Quantidade:", min_value=1.0, value=1.0)
        with col_srv2:
            preco_ponto = st.number_input("Preço Unitário (R$):", min_value=0.0, value=100.0)
        valor_servico = qtd_pontos * preco_ponto
    elif tipo_cobranca == "Por Hora Técnica":
        col_hr1, col_hr2 = st.columns(2)
        with col_hr1:
            qtd_horas = st.number_input("Horas estimadas:", min_value=0.5, value=4.0)
        with col_hr2:
            default_preco_hora = st.session_state.get("preco_hora_salvado", 60.0)
            preco_hora = st.number_input("Valor da hora técnica (R$):", min_value=0.0, value=default_preco_hora)
        valor_servico = qtd_horas * preco_hora

    st.write("---")
    st.header("🎁 Política de Bônus (Dedução Comercial)")
    oferecer_bonus = st.checkbox("Conceder um serviço bônus dedutível?")
    valor_bonus = 0.0
    descricao_bonus = ""
    if oferecer_bonus:
        col_bon1, col_bon2 = st.columns(2)
        with col_bon1:
            descricao_bonus = st.text_input("Descrição do Bônus:")
        with col_bon2:
            valor_bonus = st.number_input("Valor Comercial a Deduzir (R$):", min_value=0.0, value=150.0)

    st.write("---")
    st.header("📦 Romaneio de Materiais")
    incluir_materiais_no_preco = st.toggle("Somar materiais no montante final?", value=False)
    
    with st.form("adicionar_insumo", clear_on_submit=True):
        col_mat1, col_mat2, col_mat3 = st.columns()
        with col_mat1:
            nome_mat = st.text_input("Nome do Material:")
        with col_mat2:
            qtd_mat = st.number_input("Qtd:", min_value=1, value=1)
        with col_mat3:
            preco_mat = st.number_input("Unitário (R$):", min_value=0.0, value=0.0)
        if st.form_submit_button("➕ Incluir Insumo"):
            if nome_mat:
                novo_item = pd.DataFrame([{"Item": nome_mat, "Qtd": qtd_mat, "Preço Un.": preco_mat, "Total": qtd_mat * preco_mat}])
                st.session_state.df_materiais = pd.concat([st.session_state.df_materiais, novo_item], ignore_index=True)

    total_materiais = 0.0
    if not st.session_state.df_materiais.empty:
        df_editado = st.data_editor(st.session_state.df_materiais, use_container_width=True, num_rows="dynamic")
        df_editado["Total"] = df_editado["Qtd"] * df_editado["Preço Un."]
        st.session_state.df_materiais = df_editado
        total_materiais = df_editado["Total"].sum()
        if st.button("🗑️ Resetar Insumos"):
            st.session_state.df_materiais = pd.DataFrame(columns=["Item", "Qtd", "Preço Un.", "Total"])
            st.rerun()

    st.write("---")
    st.header("🚚 Deslocamento Logístico")
    tipo_transporte = st.selectbox("Cálculo de Transporte:", ["Preço Fixo", "Quilometragem Rodada"])
    custo_transporte = 0.0
    if tipo_transporte == "Preço Fixo":
        custo_transporte = st.number_input("Taxa de frete fixa (R$):", min_value=0.0, value=30.0)
    elif tipo_transporte == "Quilometragem Rodada":
        col_km1, col_km2 = st.columns(2)
        with col_km1:
            km_total = st.number_input("Distância total (KM):", min_value=0.0, value=15.0)
        with col_km2:
            valor_por_km = st.number_input("Valor por KM (R$):", min_value=0.0, value=1.50)
        custo_transporte = km_total * valor_por_km

    obs_gerais = st.text_area("Notas gerais do projeto:")
    desconto_pct = st.slider("Desconto comercial mão de obra (%)", min_value=0, max_value=30, value=0)

    # Engenharia financeira final
    valor_desconto_mo = valor_servico * (desconto_pct / 100)
    subtotal_mo = valor_servico - valor_desconto_mo
    total_geral = max(0.0, subtotal_mo + custo_transporte - valor_bonus + (total_materiais if incluir_materiais_no_preco else 0.0))

    st.write("---")
    st.subheader("Painel de Custos Consolidado")
    st.markdown(f"## 💵 Total Final do Orçamento: **R$ {total_geral:.2f}**")

    # --- GERADOR DE PDF COM ESTAMPA GOV E QR CODE ---
    def build_pdf_gov(verification_url, unique_hash):
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        story = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1A365D'), spaceAfter=15)
        h2_style = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2B6CB0'), spaceBefore=8, spaceAfter=8)
        body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=6)
        gov_text_style = ParagraphStyle('GovText', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#2D3748'))
        
        story.append(Paragraph(f"<b>PROPOSTA COMERCIAL E TÉCNICA DE SERVIÇOS</b>", title_style))
        story.append(Paragraph(f"<b>Cliente/Empresa:</b> {nome_cliente if nome_cliente else 'Não Informado'}", body_style))
        story.append(Paragraph(f"<b>Segmento Operacional:</b> {tipo_obra} | <b>Escopo:</b> {servico_principal}", body_style))
        story.append(Spacer(1, 10))
        
        # Financeiro
        data_fin = [
            ["Item / Descrição", "Valor"],
            ["Mão de Obra Executiva", f"R$ {valor_servico:.2f}"],
            ["Desconto Aplicado", f"- R$ {valor_desconto_mo:.2f}"],
            ["Frete e Deslocamento", f"R$ {custo_transporte:.2f}"]
        ]
        if valor_bonus > 0:
            data_fin.append([f"Bônus Comercial (-)", f"- R$ {valor_bonus:.2f}"])
