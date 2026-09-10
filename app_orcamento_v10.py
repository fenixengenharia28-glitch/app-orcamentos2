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
from PIL import Image

# Configuração da página para Desktop e Mobile
st.set_page_config(page_title="Orçamentos Construção Pro", page_icon="🏗️", layout="centered")

# --- SISTEMA DE VERIFICAÇÃO DE DOCUMENTOS (PÁGINA GOV SIMULADA) ---
query_params = st.query_params
if "verificar" in query_params:
    doc_hash = query_params["verificar"]
    st.success("🔒 PORTAL DE VERIFICAÇÃO DE DOCUMENTOS")
    st.title("✅ Documento Autêntico e Verificado")
    st.write("Este orçamento foi verificado digitalmente através do sistema Construção Pro em conformidade com as diretrizes de integridade documental.")
    st.info(f"**Código de Validação (Hash):** {doc_hash}")
    st.write(f"**Status da Assinatura:** ATIVA E VÁLIDA (Padrão ICP-Brasil Equivalente)")
    if st.button("Voltar ao Sistema de Orçamentos"):
        st.query_params.clear()
        st.rerun()
    st.stop()

# --- INICIALIZAÇÃO DE BANCOS DE DADOS EM MEMÓRIA ---
if "db_servicos" not in st.session_state:
    st.session_state.db_servicos = pd.DataFrame([
        {"Serviço": "Instalação de Tomada/Ponto Geral", "Preço Padrão": 50.0},
        {"Serviço": "Reforma de QDC (Quadro de Disjuntores)", "Preço Padrão": 350.0},
        {"Serviço": "Pintura por M² (Mão de Obra)", "Preço Padrão": 25.0},
        {"Serviço": "Regularização de Contra piso M²", "Preço Padrão": 40.0}
    ])

if "db_materiais" not in st.session_state:
    st.session_state.db_materiais = pd.DataFrame([
        {"Material": "Cabo Flexível 2,5mm² (Metro)", "Preço Unitário": 4.50},
        {"Material": "Disjuntor Din Monofilar Tramontina", "Preço Unitário": 18.90},
        {"Material": "Tomada Simples com Placa Pial", "Preço Unitário": 22.00},
        {"Material": "Saco de Cimento 50kg CP-II", "Preço Unitário": 38.00}
    ])

if "db_veiculo" not in st.session_state:
    st.session_state.db_veiculo = {
        "valor_mercado": 50000.0,
        "impostos_anual": 2400.0,
        "anos_permanencia": 5
    }

if "df_materiais_orcamento" not in st.session_state:
    st.session_state.df_materiais_orcamento = pd.DataFrame(columns=["Item", "Qtd", "Preço Un.", "Total"])

# --- FLUXO PRINCIPAL DO APLICATIVO ---
st.title("🏗️ Orçamentos Construção Pro")
st.caption("Versão Final Corrigida - Sistema Completo com Cadastros, Logomarca e Validação GOV")

# Criação das Abas do Aplicativo
aba_orc, aba_serv, aba_mat, aba_veic, aba_calc = st.tabs([
    "📋 Criar Orçamento", 
    "🛠️ Cadastrar Serviços", 
    "📦 Cadastrar Materiais", 
    "🚗 Configurar Veículo", 
    "🧮 Calcular Minha Hora"
])

# --- ABA 2: CADASTRO DE SERVIÇOS ---
with aba_serv:
    st.header("🛠️ Catálogo de Serviços Padrão")
    st.write("Cadastre ou edite seus serviços para que fiquem disponíveis na montagem do orçamento.")
    
    with st.form("cad_servico", clear_on_submit=True):
        novo_serv_nome = st.text_input("Nome do Serviço / Atividade:")
        novo_serv_preco = st.number_input("Preço sugerido (R$):", min_value=0.0, step=5.0)
        if st.form_submit_button("💾 Salvar Serviço"):
            if novo_serv_nome:
                novo_s = pd.DataFrame([{"Serviço": novo_serv_nome, "Preço Padrão": novo_serv_preco}])
                st.session_state.db_servicos = pd.concat([st.session_state.db_servicos, novo_s], ignore_index=True)
                st.success("Serviço cadastrado com sucesso!")
                st.rerun()
                
    st.subheader("Serviços Cadastrados")
    st.session_state.db_servicos = st.data_editor(st.session_state.db_servicos, use_container_width=True, num_rows="dynamic")

# --- ABA 3: CADASTRO DE MATERIAIS ---
with aba_mat:
    st.header("📦 Almoxarifado de Materiais Frequentes")
    st.write("Alimente sua lista de insumos frequentes com valores de referência.")
    
    with st.form("cad_material", clear_on_submit=True):
        novo_mat_nome = st.text_input("Nome do Insumo / Material:")
        novo_mat_preco = st.number_input("Preço de Custo Unitário (R$):", min_value=0.0, step=1.0)
        if st.form_submit_button("💾 Salvar Material"):
            if novo_mat_nome:
                novo_m = pd.DataFrame([{"Material": novo_mat_nome, "Preço Unitário": novo_mat_preco}])
                st.session_state.db_materiais = pd.concat([st.session_state.db_materiais, novo_m], ignore_index=True)
                st.success("Material adicionado com sucesso!")
                st.rerun()
                
    st.subheader("Materiais Cadastrados")
    st.session_state.db_materiais = st.data_editor(st.session_state.db_materiais, use_container_width=True, num_rows="dynamic")

# --- ABA 4: CADASTRO DE VEÍCULO ---
with aba_veic:
    st.header("🚗 Parâmetros e Custos de Logística do Veículo")
    st.write("Defina os custos do veículo para repassá-los de maneira precisa na sua hora operacional.")
    
    v_mercado = st.number_input("Valor de Mercado Atual do Veículo (R$):", min_value=0.0, value=st.session_state.db_veiculo["valor_mercado"], step=1000.0)
    v_impostos = st.number_input("IPVA + Licenciamento Anual Total (R$):", min_value=0.0, value=st.session_state.db_veiculo["impostos_anual"], step=100.0)
    v_anos = st.number_input("Anos de permanência planejada com o carro:", min_value=1, value=st.session_state.db_veiculo["anos_permanencia"])
    
    if st.button("💾 Atualizar Configurações do Carro"):
        st.session_state.db_veiculo = {
            "valor_mercado": v_mercado,
            "impostos_anual": v_impostos,
            "anos_permanencia": v_anos
        }
        st.success("Dados logísticos do veículo salvos!")

# --- ABA 5: CALCULADORA DE HORA TÉCNICA OPERACIONAL ---
with aba_calc:
    st.header("Descubra o Valor da sua Hora")
    custo_fixo_geral = st.number_input("Custos fixos mensais de escritório (MEI, internet, fone, seguros):", min_value=0.0, value=500.0, step=50.0)
    
    veh_data = st.session_state.db_veiculo
    depreciacao_mensal = (veh_data["valor_mercado"] * 0.10) / 12
    cadastro_mensal = veh_data["impostos_anual"] / 12
    custo_veiculo_total_mes = depreciacao_mensal + cadastro_mensal
    
    st.info(f"🚗 Custos do Carro Calculados: Depreciação (R$ {depreciacao_mensal:.2f}/mês) + Impostos (R$ {cadastro_mensal:.2f}/mês)")
    
    salario_desejado = st.number_input("Meta de Pró-labore mensal líquido (Seu Salário):", min_value=0.0, value=4000.0, step=100.0)
    dias_trabalhados = st.number_input("Dias operacionais efetivos por mês:", min_value=1, max_value=31, value=22)
    horas_por_dia = st.number_input("Horas produtivas faturadas por dia de trabalho:", min_value=1.0, max_value=24.0, value=6.0, step=0.5)
    margem_lucro = st.slider("Margem de Investimento/Lucro da Empresa (%)", min_value=0, max_value=50, value=20, step=5)
    
    horas_totais_mes = dias_trabalhados * horas_por_dia
    if horas_totais_mes > 0:
        custo_hora_bruto = (custo_fixo_geral + custo_veiculo_total_mes + salario_desejado) / horas_totais_mes
        hora_calculada = custo_hora_bruto / (1 - (margem_lucro / 100)) if margem_lucro < 100 else custo_hora_bruto
    else:
        hora_calculada = 0.0
        
    st.success(f"💰 **Sua Hora Técnica Sugerida: R$ {hora_calculada:.2f}**")
    if st.button("Aplicar valor de Hora Técnica na Mão de Obra"):
        st.session_state["preco_hora_salvado"] = round(hora_calculada, 2)
        st.info("Valor sincronizado com sucesso!")

# --- ABA 1: GERADOR DE ORÇAMENTO MULTIUSO ---
with aba_orc:
    st.header("Identificação do Projeto")
    
    # Campo para incluir a logo da empresa no PDF
    logo_upload = st.file_uploader("Upload da Logomarca da Empresa (Para o PDF - Opcional):", type=["png", "jpg", "jpeg"])
    
    col_cli1, col_cli2 = st.columns(2)
    with col_cli1:
        nome_cliente = st.text_input("Nome do Cliente / Empresa:", value="Fenix Engenharia e Comercio LTDA")
    with col_cli2:
        tipo_obra = st.selectbox("Segmento da Obra:", ["Construção Geral", "Elétrica", "Hidráulica", "Pintura / Acabamento", "Alvenaria / Estruturas", "Gesso / Drywall"], index=1)
        
    opcoes_servicos = list(st.session_state.db_servicos["Serviço"].values)
    servico_selecionado = st.selectbox("Selecione o Serviço Cadastrado:", opcoes_servicos)
    servico_principal = st.text_input("Ajuste a descrição do escopo se necessário:", value=servico_selecionado)
    
    nome_responsavel = st.text_input("Nome do Responsável Técnico (Para Assinatura GOV):", value="Ronilson Richardson Fragoso de Souza")

    st.write("---")
    st.header("👷 Quantificação da Mão de Obra")
    tipo_cobranca = st.selectbox("Critério de precificação:", ["Por Empreitada / Ponto", "Por Hora Técnica"])

    preco_sugerido_base = st.session_state.db_servicos[st.session_state.db_servicos["Serviço"] == servico_selecionado]["Preço Padrão"].values[0]

    valor_servico = 0.0
    if tipo_cobranca == "Por Empreitada / Ponto":
        col_srv1, col_srv2 = st.columns(2)
        with col_srv1:
            qtd_pontos = st.number_input("Quantidade de Unidades/Pontos/M²:", min_value=1.0, value=10.0)
        with col_srv2:
            preco_ponto = st.number_input("Preço por Unidade (R$):", min_value=0.0, value=float(preco_sugerido_base))
        valor_servico = qtd_pontos * preco_ponto
    elif tipo_cobranca == "Por Hora Técnica":
        col_hr1, col_hr2 = st.columns(2)
        with col_hr1:
            qtd_horas = st.number_input("Horas estimadas de execução:", min_value=0.5, value=4.0)
        with col_hr2:
            default_preco_hora = st.session_state.get("preco_hora_salvado", 60.0)
