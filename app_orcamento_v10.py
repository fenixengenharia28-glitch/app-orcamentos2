# ==============================================================================
# BLOCO 1: IMPORTAÇÕES, CONFIGURAÇÃO DA PÁGINA, CONEXÃO GITHUB E MOTOR DO PDF
# ==============================================================================
import streamlit as st
import pandas as pd
import requests
import base64
import os
from fpdf import FPDF

# Configuração da página web
st.set_page_config(
    page_title="Gestão de Orçamentos Elétricos Integrada", 
    page_icon="⚡", 
    layout="wide"
)

WHATSAPP_NUMERO = "5531995392027"
LINK_WHATSAPP = f"https://wa.me{WHATSAPP_NUMERO}"
URL_QRCODE = f"https://googleapis.com{LINK_WHATSAPP}&choe=UTF-8"

# ─── CLASSE DO PDF PERSONALIZADO COM SUPORTE A LOGO ───
class PDFOrcamento(FPDF):
    def __init__(self, logo_bytes=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_bytes = logo_bytes

    def header(self):
        if self.logo_bytes:
            # Salva temporariamente os bytes da imagem carregada para injetar no PDF
            with open("temp_logo.png", "wb") as f:
                f.write(self.logo_bytes.getbuffer())
            self.image("temp_logo.png", 10, 8, 33)
            if os.path.exists("temp_logo.png"):
                os.remove("temp_logo.png")
        
        self.set_font("Helvetica", "B", 14)
        self.cell(40) # Espaçamento para não sobrepor a logo
        self.cell(0, 10, "ORÇAMENTO DE SERVIÇOS ELÉTRICOS", ln=True, align="R")
        self.set_draw_color(220, 220, 220)
        self.line(10, 45, 200, 45)
        self.ln(20)

    def footer(self):
        self.set_y(-25)
        self.set_draw_color(220, 220, 220)
        self.line(10, 270, 200, 270)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C", ln=True)
        self.cell(0, 5, "Gerado por Fênix Empreendimento - Contato: (31) 99539-2027", align="C")

# ─── SCONECTIVIDADE DO BANCO DE DADOS GITHUB ───
def salvar_no_github(nome_arquivo_csv, df_novo):
    try:
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]
    except Exception:
        df_novo.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
        return False

    url = f"https://github.com{repo}/contents/{nome_arquivo_csv}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    sha = None
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        sha = response.json().get("sha")
        conteudo_antigo_b64 = response.json().get("content")
        conteudo_antigo = base64.b64decode(conteudo_antigo_b64).decode("utf-8")
        from io import StringIO
        df_antigo = pd.read_csv(StringIO(conteudo_antigo))
        df_final = pd.concat([df_antigo, df_novo]).drop_duplicates().reset_index(drop=True)
    else:
        df_final = df_novo

    csv_conteudo = df_final.to_csv(index=False, encoding="utf-8")
    conteudo_b64 = base64.b64encode(csv_conteudo.encode("utf-8")).decode("utf-8")
    
    dados_commit = {"message": f"Atualizando base de dados: {nome_arquivo_csv}", "content": conteudo_b64}
    if sha: dados_commit["sha"] = sha
    requests.put(url, headers=headers, json=dados_commit)
    df_final.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
    return True

def carregar_dados(nome_arquivo_csv):
    if os.path.exists(nome_arquivo_csv):
        return pd.read_csv(nome_arquivo_csv).to_dict(orient="records")
    return []

if 'clientes' not in st.session_state: st.session_state.clientes = carregar_dados("clientes.csv")
if 'veiculos' not in st.session_state: st.session_state.veiculos = carregar_dados("veiculos.csv")
if 'materiais' not in st.session_state: st.session_state.materiais = carregar_dados("materiais.csv")
if 'servicos' not in st.session_state: st.session_state.servicos = carregar_dados("servicos.csv")
if 'materiais_orcamento' not in st.session_state: st.session_state.materiais_orcamento = []

# Cabeçalho visual da plataforma
col_topo1, col_topo2 = st.columns()
with col_topo1:
    st.title("⚡ Painel de Gestão e Orçamentos Elétricos")
    logo_upload = st.file_uploader("Upload da Logo da sua Empresa (PNG/JPG):", type=["png", "jpg", "jpeg"])
    if logo_upload: st.image(logo_upload, width=200)
with col_topo2:
    st.image(URL_QRCODE, caption="Fale Conosco no WhatsApp")

aba_orcamento, aba_clientes, aba_mao_obra, aba_materiais, aba_veiculos = st.tabs([
    "📋 Criar Orçamento", "👥 Cadastro de Clientes", "⏱️ Mão de Obra & Serviços", "🛒 Cadastro de Materiais", "🚚 Cadastro de Veículos"
])
# ==============================================================================
# BLOCO 2: CADASTRO DE CLIENTES E VEÍCULOS COM ARQUIVAMENTO EM CSV
# ==============================================================================

# ABA - CADASTRO DE CLIENTES
with aba_clientes:
    st.subheader("👥 Cadastro de Clientes e Sincronização GitHub")
    with st.form("form_cliente", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            c_nome = st.text_input("Nome completo ou Razão Social:")
            c_doc = st.text_input("CPF ou CNPJ:")
        with col_c2:
            c_contato = st.text_input("WhatsApp / Telefone:")
            c_endereco = st.text_input("Endereço da Obra:")
        
        if st.form_submit_button("💾 Salvar Cliente no GitHub"):
            if c_nome:
                novo_df = pd.DataFrame([{"Nome": c_nome, "Documento": c_doc, "Contato": c_contato, "Endereço": c_endereco}])
                salvar_no_github("clientes.csv", novo_df)
                st.session_state.clientes = carregar_dados("clientes.csv")
                st.success(f"Cliente '{c_nome}' salvo e sincronizado com o GitHub!")

    if st.session_state.clientes:
        st.dataframe(pd.DataFrame(st.session_state.clientes), use_container_width=True)

# ABA - CADASTRO DE VEÍCULOS
with aba_veiculos:
    st.subheader("🚚 Gestão de Veículos e Custos de Frota")
    with st.form("form_veiculo", clear_on_submit=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v_modelo = st.text_input("Modelo do Veículo:")
            v_placa = st.text_input("Placa do Veículo:")
        with col_v2:
            v_km = st.number_input("Custo estimado por Km rodado (R$):", min_value=0.0, value=1.20, step=0.10)
            
        if st.form_submit_button("💾 Salvar Veículo no GitHub"):
            if v_modelo:
                novo_df = pd.DataFrame([{"Modelo": v_modelo, "Placa": v_placa, "Custo/Km": v_km}])
                salvar_no_github("veiculos.csv", novo_df)
                st.session_state.veiculos = carregar_dados("veiculos.csv")
                st.success(f"Veículo '{v_modelo}' cadastrado e atualizado na nuvem!")

    if st.session_state.veiculos:
        st.dataframe(pd.DataFrame(st.session_state.veiculos), use_container_width=True)
# ==============================================================================
# BLOCO 3: CADASTRO DE MATERIAIS E SERVIÇOS NO ALMOXARIFADO
# ==============================================================================

# ABA - CADASTRO DE MATERIAIS
with aba_materiais:
    st.subheader("🛒 Catálogo Geral de Materiais e Insumos")
    with st.form("form_catalogo_material", clear_on_submit=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            mat_nome = st.text_input("Nome do Material:")
        with col_m2:
            mat_marca = st.text_input("Marca / Fabricante:")
        with col_m3:
            mat_preco = st.number_input("Preço de Custo Padrão (R$):", min_value=0.0, value=0.0, step=5.0)
            
        if st.form_submit_button("💾 Salvar Material no GitHub"):
            if mat_nome:
                novo_df = pd.DataFrame([{"Item": mat_nome, "Marca": mat_marca, "Preço Unitário": mat_preco}])
                salvar_no_github("materiais.csv", novo_df)
                st.session_state.materiais = carregar_dados("materiais.csv")
                st.success(f"'{mat_nome}' adicionado ao inventário do GitHub!")

    if st.session_state.materiais:
        st.dataframe(pd.DataFrame(st.session_state.materiais), use_container_width=True)

# ABA - MÃO DE OBRA E TIPOS DE SERVIÇOS
with aba_mao_obra:
    st.subheader("🛠️ Tipos de Serviços e Precificação Base")
    with st.form("form_tipo_servico", clear_on_submit=True):
        col_ts1, col_ts2, col_ts3 = st.columns(3)
        with col_ts1:
            ts_nome = st.text_input("Nome do Serviço (Ex: Instalação de Padrão, Infraestrutura):")
        with col_ts2:
            ts_tipo = st.selectbox("Modelo de Cobrança Padrão:", ["Por Ponto Elétrico", "Por Hora Trabalhada", "Valor Fixo"])
        with col_ts3:
            ts_preco = st.number_input("Preço Base Referencial (R$):", min_value=0.0, value=100.0)
            
        if st.form_submit_button("💾 Salvar Tipo de Serviço no GitHub"):
            if ts_nome:
                novo_df = pd.DataFrame([{"Serviço": ts_nome, "Tipo Cobrança": ts_tipo, "Preço Base": ts_preco}])
                salvar_no_github("servicos.csv", novo_df)
                st.session_state.servicos = carregar_dados("servicos.csv")
                st.success("Tipo de serviço salvo com sucesso!")

    if st.session_state.servicos:
        st.dataframe(pd.DataFrame(st.session_state.servicos), use_container_width=True)
# ==============================================================================
# BLOCO 4: ORÇAMENTO COMPLETO, EXIBIÇÃO DE VALORES E DOWNLOAD DO PDF
# ==============================================================================

with aba_orcamento:
    st.subheader("📋 Montagem do Orçamento Dinâmico")
    col_orc1, col_orc2 = st.columns(2)
    
    with col_orc1:
        st.markdown("### 1. Dados do Cliente e Logística")
        if st.session_state.clientes:
            lista_cli = [c["Nome"] for c in st.session_state.clientes]
            cli_sel = st.selectbox("Selecione o Cliente Cadastrado:", lista_cli)
            dados_cli = next(item for item in st.session_state.clientes if item["Nome"] == cli_sel)
            contato_disp, endereco_disp = dados_cli["Contato"], dados_cli["Endereço"]
        else:
            cli_sel = st.text_input("Nome do Cliente (Manual):")
            contato_disp = st.text_input("Contato (Manual):")
            endereco_disp = st.text_input("Endereço da Obra (Manual):")
            
        if st.session_state.servicos:
            lista_serv = [s["Serviço"] for s in st.session_state.servicos]
            serv_sel = st.selectbox("Selecione o Tipo de Serviço Cadastrado:", lista_serv)
            dados_serv = next(item for item in st.session_state.servicos if item["Serviço"] == serv_sel)
            st.info(f"Modelo cadastrado: {dados_serv['Tipo Cobrança']} | Preço Ref: R$ {dados_serv['Preço Base']:.2f}")
        else:
            serv_sel = "Serviço Geral"

        orc_descricao = st.text_area("Descreva o escopo detalhado que será executado nessa obra:")
        mo_total_v = st.number_input("Valor Final definido para a Mão de Obra (R$):", min_value=0.0, value=500.0)

        if st.session_state.veiculos:
            lista_v = [f"{v['Modelo']} ({v['Placa']})" for v in st.session_state.veiculos]
            v_sel = st.selectbox("Veículo de Atendimento:", lista_v)
            km_r = st.number_input("KM Estimado (Ida + Volta):", min_value=0.0, value=0.0)
            idx = lista_v.index(v_sel)
            custo_transporte = km_r * st.session_state.veiculos[idx]["Custo/Km"]
        else:
            custo_transporte = st.number_input("Custo de Deslocamento Manual (R$):", min_value=0.0, value=0.0)

    with col_orc2:
        st.markdown("### 2. Adicionar Materiais Específicos")
        if st.session_state.materiais:
            lista_m = [m["Item"] for m in st.session_state.materiais]
            m_sel = st.selectbox("Buscar material do Catálogo:", lista_m)
            dados_m = next(item for item in st.session_state.materiais if item["Item"] == m_sel)
            p_sugerido = dados_m["Preço Unitário"]
        else:
            m_sel = st.text_input("Nome do Material Manual:")
            p_sugerido = 0.0
            
        m_qtd = st.number_input("Qtd para a Obra:", min_value=1, value=1)
        m_preco = st.number_input("Preço de Custo Praticado (R$):", min_value=0.0, value=p_sugerido)
        
        if st.button("➕ Inserir no Orçamento"):
            if m_sel:
                st.session_state.materiais_orcamento.append({
                    "Material": m_sel, "Qtd": m_qtd, "Custo Un. (R$)": m_preco, "Total (R$)": m_qtd * m_preco
                })
                st.rerun()

        custo_bruto_m = 0.0
        if st.session_state.materiais_orcamento:
            df_m_obra = pd.DataFrame(st.session_state.materiais_orcamento)
            st.dataframe(df_m_obra, use_container_width=True)
            custo_bruto_m = df_m_obra["Total (R$)"].sum()
            if st.button("🗑️ Limpar Lista de Materiais da Obra"):
                st.session_state.materiais_orcamento = []
                st.rerun()

    st.markdown("---")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        margem_m = st.number_input("Margem sobre materiais (%):", min_value=0.0, value=20.0)
        total_m_lucro = custo_bruto_m * (1 + (margem_m / 100))
    with col_f2:
        imposto_pc = st.number_input("Impostos / NF (%):", min_value=0.0, value=6.0)
    with col_f3:
        desc_v = st.number_input("Desconto Especial (R$):", min_value=0.0, value=0.0)

    subtotal = mo_total_v + total_m_lucro + custo_transporte
    impostos_finais = subtotal * (imposto_pc / 100)
    preco_final = subtotal + impostos_finais - desc_v

    def ler_arquivo_txt(n, d): return open(n, "r", encoding="utf-8").read() if os.path.exists(n) else d
    t_pag = ler_arquivo_txt("pagamento.txt", "A combinar.")
    t_gar = ler_arquivo_txt("garantia.txt", "90 dias.")
    t_obs = ler_arquivo_txt("observacoes.txt", "Sem alteração estrutural.")

    st.markdown("### 📊 Resumo de Fechamento")
    rm1, rm2, rm3, rm4, rm5 = st.columns(5)
    rm1.metric("Mão de Obra", f"R$ {mo_total_v:.2f}")
    rm2.metric("Materiais", f"R$ {total_m_lucro:.2f}")
    rm3.metric("Logística", f"R$ {custo_transporte:.2f}")
    rm4.metric("Impostos", f"R$ {impostos_finais:.2f}")
    rm5.metric("PREÇO FINAL", f"R$ {preco_final:.2f}", delta=f"- R$ {desc_v:.2f}" if desc_v > 0 else None)

    # ─── CONVERSOR DO DOCUMENTO TÉCNICO PARA PDF ───
    pdf = PDFOrcamento(logo_bytes=logo_upload)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 11)
    
    # Seção Cliente
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "DADOS DO CLIENTE", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Cliente: {cli_sel}", ln=True)
    pdf.cell(0, 6, f"Contato: {contato_disp}", ln=True)
    pdf.cell(0, 6, f"Endereço da Obra: {endereco_disp}", ln=True)
    pdf.ln(5)

    # Seção Escopo
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"SERVIÇO PRINCIPAL: {serv_sel}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, f"Escopo Tecnico:\n{orc_descricao if orc_descricao else 'Conforme especificações.'}")
    pdf.ln(5)

    # Valores
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "RESUMO FINANCEIRO DO INVESTIMENTO", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"- Mao de Obra Especializada: R$ {mo_total_v:.2f}", ln=True)
    pdf.cell(0, 6, f"- Fornecimento de Materiais/Insumos: R$ {total_m_lucro:.2f}", ln=True)
    pdf.cell(0, 6, f"- Custos de Deslocamento/Logistica: R$ {custo_transporte:.2f}", ln=True)
    pdf.cell(0, 6, f"- Encargos e Impostos Inclusos: R$ {impostos_finais:.2f}", ln=True)
    if desc_v > 0: pdf.cell(0, 6, f"- Desconto Especial: - R$ {desc_v:.2f}", ln=True)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"VALOR TOTAL DO ORÇAMENTO: R$ {preco_final:.2f}", ln=True)
    pdf.ln(5)

    # Termos Comerciais (.txt)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "CONDIÇÕES COMERCIAIS", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, f"Formas de Pagamento:\n{t_pag}\n\nGarantia:\n{t_gar}\n\nObservacoes:\n{t_obs}")
    
    pdf_output = pdf.output()

    st.markdown("### 🖨️ Ações de Envio")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            label="📥 Baixar Orçamento Oficial em PDF",
            data=bytes(pdf_output),
            file_name=f"Orcamento_{cli_sel.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
    with col_d2:
        st.link_button("💬 Enviar via WhatsApp", LINK_WHATSAPP)
