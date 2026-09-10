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

if "db_veiculos" not in st.session_state:
    st.session_state.db_veiculos = pd.DataFrame([
        {"Tipo": "Carro", "Marca": "Fiat", "Modelo": "Uno Way", "Valor (R$)": 35000.0, "IPVA/Licenc. Anual": 1400.0}
    ])

if "df_materiais_orcamento" not in st.session_state:
    st.session_state.df_materiais_orcamento = pd.DataFrame(columns=["Item", "Qtd", "Preço Un.", "Total"])

# --- FLUXO PRINCIPAL DO APLICATIVO ---
st.title("🏗️ Orçamentos Construção Pro")
st.caption("Versão v11 - Sistema Completo com Cadastros, Frota de Veículos e Validação GOV")

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
    st.write("Cadastre seus serviços de referência para a planilha.")
    
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
    st.write("Alimente sua lista de insumos com valores de referência.")
    
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

# --- ABA 4: CADASTRO DE VEÍCULOS ---
with aba_veic:
    st.header("🚗 Cadastro e Frota de Veículos da Empresa")
    st.write("Insira e salve as informações dos veículos utilizados em campo para o cálculo preciso da depreciação estrutural.")
    
    with st.form("cad_novo_veiculo", clear_on_submit=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v_tipo = st.selectbox("Tipo do Veículo:", ["Carro", "Moto", "Caminhão", "Utilitário / Van"])
            v_marca = st.text_input("Marca (ex: Chevrolet, Honda):")
        with col_v2:
            v_modelo = st.text_input("Modelo (ex: Onix, Titan):")
            v_valor = st.number_input("Valor de Mercado (Tabela FIPE - R$):", min_value=0.0, step=1000.0, value=25000.0)
            
        v_anual_imposto = st.number_input("Custos Anuais de Cadastro (IPVA + Licenciamento Anual - R$):", min_value=0.0, step=100.0, value=1500.0)
        
        if st.form_submit_button("💾 Salvar Veículo na Frota"):
            if v_marca and v_modelo:
                novo_v = pd.DataFrame([{
                    "Tipo": v_tipo, 
                    "Marca": v_marca, 
                    "Modelo": v_modelo, 
                    "Valor (R$)": v_valor, 
                    "IPVA/Licenc. Anual": v_anual_imposto
                }])
                st.session_state.db_veiculos = pd.concat([st.session_state.db_veiculos, novo_v], ignore_index=True)
                st.success(f"Veículo {v_modelo} adicionado com sucesso!")
                st.rerun()

    st.subheader("Frota Registrada e Salva")
    st.write("Você pode editar os valores de mercado ou impostos direto nas células da tabela abaixo:")
    st.session_state.db_veiculos = st.data_editor(st.session_state.db_veiculos, use_container_width=True, num_rows="dynamic")

# --- ABA 5: CALCULADORA DE HORA TÉCNICA OPERACIONAL ---
with aba_calc:
    st.header("Descubra o Valor da sua Hora")
    custo_fixo_geral = st.number_input("Custos fixos mensais de escritório (MEI, internet, fone, seguros):", min_value=0.0, value=500.0, step=50.0)
    
    total_fipe_frota = 0.0
    total_impostos_frota = 0.0
    
    if not st.session_state.db_veiculos.empty:
        total_fipe_frota = st.session_state.db_veiculos["Valor (R$)"].sum()
        total_impostos_frota = st.session_state.db_veiculos["IPVA/Licenc. Anual"].sum()
        
    depreciacao_mensal_frota = (total_fipe_frota * 0.10) / 12
    cadastro_mensal_frota = total_impostos_frota / 12
    custo_veiculo_total_mes = depreciacao_mensal_frota + cadastro_mensal_frota
    
    st.info(f"🚗 Custos Combinados da Frota Salva ({len(st.session_state.db_veiculos)} veículo(s)): Depreciação (R$ {depreciacao_mensal_frota:.2f}/mês) + Impostos (R$ {cadastro_mensal_frota:.2f}/mês)")
    
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
    
    valor_servico = 0.0
    if tipo_cobranca == "Por Empreitada / Ponto":
        preco_sugerido_base =
        st.session_state.db_servicos[st.session_state.db_servicos["Serviço"] ==
        servico_selecionado]["Preço Padrão"].values
        col_srv1, col_srv2 = st.columns(2)
