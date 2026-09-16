# ==============================================================================
# BLOCO 1: IMPORTAÇÕES, DEPENDÊNCIAS E CONFIGURAÇÃO DA PÁGINA
# ==============================================================================
import streamlit as st
import pandas as pd
import requests
import base64
import os
from fpdf import FPDF
from io import BytesIO

# Configuração da interface do Streamlit
st.set_page_config(
    page_title="Gestão de Orçamentos Elétricos Integrada", 
    page_icon="⚡", 
    layout="wide"
)

# Links e endpoints de comunicação
WHATSAPP_NUMERO = "5531995392027"
LINK_WHATSAPP = f"https://wa.me{WHATSAPP_NUMERO}"
URL_QRCODE = f"https://googleapis.com{LINK_WHATSAPP}&choe=UTF-8"
# ==============================================================================
# BLOCO 2: CLASSE DO PDF RECONFIGURADA PARA PREENCHER TOTALMENTE A FOLHA A4
# ==============================================================================
class PDFOrcamento(FPDF):
    def __init__(self, logo_bytes=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_bytes = logo_bytes

    def header(self):
        # 1. LOGO ALINHADA À ESQUERDA
        if self.logo_bytes:
            with open("temp_logo.png", "wb") as f:
                f.write(self.logo_bytes)
            self.image("temp_logo.png", 10, 8, 30)
            if os.path.exists("temp_logo.png"):
                os.remove("temp_logo.png")
        
        self.set_y(8)
        
        # 2. DADOS CENTRALIZADOS COM INCLUSÃO DO E-MAIL REQUERIDO
        self.set_font("Helvetica", "B", 12)  
        self.cell(0, 5, "FENIX ENGENHARIA E COMERCIO LTDA", ln=True, align="C")
        
        self.set_font("Helvetica", "B", 8.5)
        self.cell(0, 4, "CNPJ: 52.769.953/0001-12", ln=True, align="C")
        
        self.set_font("Helvetica", "", 8)
        self.cell(0, 4, "Av. Getulio Vargas, nº 671, 9º Andar, Sala 1051, Savassi - Belo Horizonte - MG", ln=True, align="C")
        self.cell(0, 4, "Cep: 30112-021 / Tel: (31) 99539-2027 / E-mail: fenixengenharia28@gmail.com", ln=True, align="C")
        
        self.ln(3) 
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 5, "PRESTAÇÃO DE SERVIÇOS ELÉTRICOS E ENGENHARIA", ln=True, align="C")
        
        # 3. QR CODE DO WHATSAPP FIXADO NO CANTO DIREITO DO CABEÇALHO
        try:
            qr_res = requests.get(URL_QRCODE, timeout=5)
            if qr_res.status_code == 200:
                with open("temp_header_qr.png", "wb") as f:
                    f.write(qr_res.content)
                self.image("temp_header_qr.png", 172, 8, 28, 28)
                if os.path.exists("temp_header_qr.png"):
                    os.remove("temp_header_qr.png")
        except Exception:
            self.set_y(12)
            self.set_font("Helvetica", "B", 10)
            self.set_x(155)
            self.cell(45, 5, "(31) 99539-2027", ln=True, align="R")
        
        # Linha divisória fina cinza
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(10, 39, 200, 39)
        self.set_y(44)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(220, 220, 220)
        self.line(10, 282, 200, 282)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"FENIX ENGENHARIA E COMERCIO LTDA - Página {self.page_no()}/{{nb}}", align="C")
# ==============================================================================
# BLOCO 3: SINCRONIZAÇÃO DE BANCO DE DADOS COM O REPOSITÓRIO DO GITHUB
# ==============================================================================
def salvar_no_github(nome_arquivo_csv, df_novo, sobrescrever=False):
    try:
        token = st.secrets["GITHUB_TOKEN"].strip()
        repo = st.secrets["GITHUB_REPO"].strip()
    except Exception:
        if isinstance(df_novo, pd.DataFrame):
            df_novo.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
        return False

    url = f"https://github.com{repo}/contents/{nome_arquivo_csv}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    sha = None
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            sha = response.json().get("sha")
            if not sobrescrever and isinstance(df_novo, pd.DataFrame):
                conteudo_antigo_b64 = response.json().get("content")
                conteudo_antigo = base64.b64decode(conteudo_antigo_b64).decode("utf-8")
                from io import StringIO
                df_antigo = pd.read_csv(StringIO(conteudo_antigo))
                
                if nome_arquivo_csv == "servicos.csv" and "Serviço" in df_antigo.columns:
                    df_antigo = df_antigo.rename(columns={"Serviço": "Descrição", "Preço Base": "Valor Compra Un. (R$)"})
                
                if nome_arquivo_csv == "veiculos.csv":
                    if "Consumo Médio (Km/Litro)" in df_antigo.columns:
                        df_antigo = df_antigo.rename(columns={"Consumo Médio (Km/Litro)": "Consumo (Km/L)"})
                    if "Custo/Km" in df_antigo.columns:
                        df_antigo = df_antigo.drop(columns=["Custo/Km"])
                
                for col in df_novo.columns:
                    if col not in df_antigo.columns: df_antigo[col] = None
                for col in df_antigo.columns:
                    if col not in df_novo.columns: df_novo[col] = None
                    
                df_final = pd.concat([df_antigo, df_novo]).drop_duplicates().reset_index(drop=True)
            else:
                df_final = df_novo
        else:
            df_final = df_novo

        if isinstance(df_final, pd.DataFrame):
            conteudo_final = df_final.to_csv(index=False, encoding="utf-8")
            conteudo_b64 = base64.b64encode(conteudo_final.encode("utf-8")).decode("utf-8")
        else:
            conteudo_b64 = df_final

        dados_commit = {"message": f"Atualizando arquivo: {nome_arquivo_csv}", "content": conteudo_b64}
        if sha: dados_commit["sha"] = sha
        
        requests.put(url, headers=headers, json=dados_commit, timeout=10)
        if isinstance(df_final, pd.DataFrame):
            df_final.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
        return True
    except Exception:
        if isinstance(df_novo, pd.DataFrame):
            df_novo.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
        return False
# ==============================================================================
# BLOCO 4: CARREGAMENTO DE DADOS HISTÓRICOS E LOGO DA SESSÃO
# ==============================================================================
def carregar_dados(nome_arquivo_csv):
    if os.path.exists(nome_arquivo_csv):
        try:
            df = pd.read_csv(nome_arquivo_csv)
            if nome_arquivo_csv == "servicos.csv" and "Serviço" in df.columns:
                df = df.rename(columns={"Serviço": "Descrição", "Preço Base": "Valor Compra Un. (R$)"})
            if nome_arquivo_csv == "veiculos.csv":
                if "Consumo Médio (Km/Litro)" in df.columns:
                    df = df.rename(columns={"Consumo Médio (Km/Litro)": "Consumo (Km/L)"})
                if "Custo/Km" in df.columns:
                    df = df.drop(columns=["Custo/Km"])
            return df.to_dict(orient="records")
        except Exception:
            return []
    return []

def carregar_logo_persistida():
    try:
        token = st.secrets["GITHUB_TOKEN"].strip()
        repo = st.secrets["GITHUB_REPO"].strip()
        url = f"https://github.com{repo}/contents/logo_persistida.txt"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            b64_content = res.json().get("content")
            txt_content = base64.b64decode(b64_content).decode("utf-8")
            return base64.b64decode(txt_content)
    except Exception:
        pass
    if os.path.exists("logo_local.png"):
        with open("logo_local.png", "rb") as f: return f.read()
    return None

# Inicialização dos estados da sessão Streamlit
if 'clientes' not in st.session_state: st.session_state.clientes = carregar_dados("clientes.csv")
if 'veiculos' not in st.session_state: st.session_state.veiculos = carregar_dados("veiculos.csv")
if 'materiais' not in st.session_state: st.session_state.materiais = carregar_dados("materiais.csv")
if 'servicos' not in st.session_state: st.session_state.servicos = carregar_dados("servicos.csv")
if 'materiais_orcamento' not in st.session_state: st.session_state.materiais_orcamento = []
if 'servicos_orcamento' not in st.session_state: st.session_state.servicos_orcamento = []
if 'logo_bytes' not in st.session_state: st.session_state.logo_bytes = carregar_logo_persistida()
# ==============================================================================
# BLOCO 5: INTERFACE GRÁFICA SUPERIOR E GERENCIAMENTO DE TABS
# ==============================================================================
col_topo1, col_topo2 = st.columns(2)
with col_topo1:
    st.markdown("### FENIX ENGENHARIA E COMERCIO LTDA")
    logo_upload = st.file_uploader("Upload da Logo (PNG/JPG):", type=["png", "jpg", "jpeg"])
    if logo_upload:
        bytes_da_logo = logo_upload.getvalue()
        st.session_state.logo_bytes = bytes_da_logo
        with open("logo_local.png", "wb") as f: f.write(bytes_da_logo)
        logo_b64_string = base64.b64encode(bytes_da_logo).decode("utf-8")
        salvar_no_github("logo_persistida.txt", logo_b64_string, sobrescrever=True)
        st.success("Logo persistida com sucesso!")
    if st.session_state.logo_bytes: st.image(st.session_state.logo_bytes, width=200)
with col_topo2:
    st.image(URL_QRCODE, caption="Fale Conosco no WhatsApp")

# Centralização do Orçamento Geral na primeira aba
aba_orc_geral, aba_clientes, aba_mao_obra, aba_materiais, aba_veiculos = st.tabs([
    "📋 Orçamento Geral", "👥 Cadastro de Clientes", "🛠️ Cadastro de Serviços", "🛒 Cadastro de Materiais", "🚚 Cadastro de Veículos"
])
# ==============================================================================
# BLOCO 6: CENTRAL DO ORÇAMENTO - PARTE 1: CLIENTES, ESCOPO E MÃO DE OBRA SELETIVA
# ==============================================================================
with aba_orc_geral:
    st.subheader("📋 Central Única de Emissão de Orçamentos")
    
    col_o1, col_o2 = st.columns(2)
    with col_o1:
        st.markdown("#### 1. Identificação Corporativa")
        if st.session_state.clientes:
            lista_cli = [c["Nome"] for c in st.session_state.clientes]
            cli_sel = st.selectbox("Selecione o Cliente Cadastrado:", lista_cli)
            dados_cli = next(item for item in st.session_state.clientes if item["Nome"] == cli_sel)
            contato_disp, endereco_disp = dados_cli["Contato"], dados_cli["Endereço"]
        else:
            cli_sel = st.text_input("Nome do Cliente (Manual):")
            contato_disp = st.text_input("Contato (Manual):")
            endereco_disp = st.text_input("Endereço (Manual):")

        orc_descricao = st.text_area("Memorial Descritivo / Resumo do Escopo:")

        # Escolha do serviço vinculado ao portfólio com atribuição de bônus
        st.markdown("#### 🛠️ Inserir Mão de Obra do Catálogo")
        if st.session_state.servicos:
            df_serv_disp = pd.DataFrame(st.session_state.servicos)
            lista_servicos_nomes = df_serv_disp["Descrição"].dropna().tolist()
            servico_escolhido = st.selectbox("Escolha qual tipo de serviço será prestado:", lista_servicos_nomes)
            
            servico_bonus = st.checkbox("Definir esta atividade como BÔNUS do orçamento (Valor zerado)")
            
            if st.button("➕ Adicionar Serviço ao Escopo"):
                dados_s = df_serv_disp[df_serv_disp["Descrição"] == servico_escolhido].iloc[0]
                st.session_state.servicos_orcamento.append({
                    "Descrição": servico_escolhido,
                    "Total": 0.0 if servico_bonus else float(dados_s["Total Bruto (R$)"]),
                    "Bônus": servico_bonus,
                    "Preço Original": float(dados_s["Total Bruto (R$)"])
                })
                st.rerun()
        else:
            st.warning("Cadastre os serviços na aba 'Cadastro de Serviços' primeiro.")

        if st.session_state.servicos_orcamento:
            st.markdown("**Serviços Vinculados:**")
            st.dataframe(pd.DataFrame(st.session_state.servicos_orcamento), use_container_width=True)
            if st.button("🗑️ Limpar Lista de Serviços"):
                st.session_state.servicos_orcamento = []
                st.rerun()
# ==============================================================================
# BLOCO 7: CENTRAL DO ORÇAMENTO - PARTE 2: MATERIAIS, FRETE E FECHAMENTO COM CORREÇÃO
# ==============================================================================
    with col_o2:
        st.markdown("#### 🛒 Inserir Materiais Necessários")
        if st.session_state.materiais:
            lista_m = [m["Item"] for m in st.session_state.materiais]
            m_sel = st.selectbox("Buscar material no Almoxarifado:", lista_m)
            dados_m = next(item for item in st.session_state.materiais if item["Item"] == m_sel)
            p_sugerido = dados_m["Preço Unitário"]
        else:
            m_sel = st.text_input("Material (Manual):")
            p_sugerido = 0.0
            
        col_mq1, col_mq2 = st.columns(2)
        m_qtd = col_mq1.number_input("Qtd Requerida:", min_value=1, value=1)
        m_preco = col_mq2.number_input("Preço Unitário (R$):", min_value=0.0, value=float(p_sugerido))
        
        if st.button("➕ Adicionar Material à Obra"):
            if m_sel:
                st.session_state.materiais_orcamento.append({
                    "Material": m_sel, "Qtd": m_qtd, "Preço": m_preco, "Total": m_qtd * m_preco
                })
                st.rerun()

        if st.session_state.materiais_orcamento:
            st.markdown("**Materiais Vinculados:**")
            st.dataframe(pd.DataFrame(st.session_state.materiais_orcamento), use_container_width=True)
            if st.button("🗑️ Limpar Lista de Materiais"):
                st.session_state.materiais_orcamento = []
                st.rerun()

        st.markdown("#### 🚚 Logística de Deslocamento")
        if st.session_state.veiculos:
            df_v_orc = pd.DataFrame(st.session_state.veiculos)
            lista_v = [f"{v['Modelo']} ({v['Placa']})" for v in st.session_state.veiculos]
            v_sel = st.selectbox("Veículo de Frota:", lista_v)
            km_r = st.number_input("Distância em KM (Ida + Volta):", min_value=0.0, value=20.0)
            preco_combustivel = st.number_input("Preço Combustível (R$/L):", min_value=0.0, value=5.90)
            
            idx = lista_v.index(v_sel)
            cons_carro = float(df_v_orc.iloc[idx]["Consumo (Km/L)"])
            custo_transporte = (km_r / cons_carro) * preco_combustivel
        else:
            custo_transporte = st.number_input("Custo de Logística Manual (R$):", min_value=0.0, value=0.0)

        st.markdown("#### 📊 Configurações Comerciais")
        imposto_pc = st.number_input("Porcentagem de Imposto para Diluir na Mão de Obra (%):", min_value=0.0, value=6.0)
        desconto_avista_pc = st.number_input("Desconto para Pagamento À VISTA (%):", min_value=0.0, value=10.0, step=1.0)

    # PROCESSAMENTO DE FECHAMENTO COM A CORREÇÃO DA LINHA 326 (REMOVIDO CÓDIGO MALFORMADO)
    custo_bruto_materiais = sum([item["Total"] for item in st.session_state.materiais_orcamento])
    custo_bruto_servicos = sum([item["Total"] for item in st.session_state.servicos_orcamento])
    
    valor_imposto_diluido = (custo_bruto_servicos + custo_bruto_materiais + custo_transporte) * (imposto_pc / 100)
    custo_final_servicos_com_imposto = custo_bruto_servicos + valor_imposto_diluido + custo_transporte
    
    preco_final_cheio = custo_final_servicos_com_imposto + custo_bruto_materiais
    preco_final_avista = preco_final_cheio * (1 - (desconto_avista_pc / 100))
    preco_final_parcelado_com_taxa = preco_final_cheio * 1.08
    valor_parcela_10x = preco_final_parcelado_com_taxa / 10

    st.markdown("---")
    st.markdown("### 📊 Fechamento Geral do Orçamento")
    rm1, rm2, rm3 = st.columns(3)
    rm1.metric("Mão de Obra (Com Imposto Diluído)", f"R$ {custo_final_servicos_com_imposto:.2f}")
    # LINHA 326 TOTALMENTE CORRIGIDA: Exibição limpa sem atribuições malformadas internamente
    rm2.metric("Materiais Separados", f"R$ {custo_bruto_materiais:.2f}")
    rm3.metric("VALOR TOTAL DO INVESTIMENTO", f"R$ {preco_final_cheio:.2f}")
    
    st.info(f"💵 À VISTA COM DESCONTO: R$ {preco_final_avista:.2f} ({int(desconto_avista_pc)}% Off) | 💳 PARCELADO (Até 10x de R$ {valor_parcela_10x:.2f})")
# ==============================================================================
# BLOCO 8: CONVERSOR E EXPORTADOR DO PROJETO EM ARQUIVO PDF COMPLETO A4
# ==============================================================================
    pdf = PDFOrcamento(logo_bytes=st.session_state.logo_bytes)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Dados do Cliente
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "DADOS DO CLIENTE E LOCALIDADE", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8.5, f"Cliente / Razao Social: {cli_sel}", ln=True)
    pdf.cell(0, 8.5, f"Contato Directo: {contato_disp}", ln=True)
    pdf.cell(0, 8.5, f"Endereco da Execucao: {endereco_disp}", ln=True)
    pdf.ln(10)

    # Escopo Técnico
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "ESCOPO TÉCNICO DA PROPOSTA", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 9, f"{orc_descricao if orc_descricao else 'Execucao conforme escopo acordado.'}")
    pdf.ln(10)

    # Apresentação separada de Mão de Obra e Material com imposto diluído
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, "DETALHAMENTO ANALÍTICO DE INVESTIMENTO", ln=True)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(130, 9.5, " Descricao da Categoria", border=1, fill=True)
    pdf.cell(60, 9.5, " Valor Comercial (R$)", border=1, fill=True, ln=True)
    
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(130, 9.5, " Mao de Obra Especializada (Tributos e Encargos Inclusos)", border=1)
    pdf.cell(60, 9.5, f" R$ {custo_final_servicos_com_imposto:.2f}", border=1, ln=True)
    
    pdf.cell(130, 9.5, " Fornecimento de Materiais e Insumos Homologados", border=1)
    pdf.cell(60, 9.5, f" R$ {custo_bruto_materiais:.2f}", border=1, ln=True)
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(130, 9.5, " VALOR TOTAL DO INVESTIMENTO LIQUIDO", border=1, fill=True)
    pdf.cell(60, 9.5, f" R$ {preco_final_cheio:.2f}", border=1, fill=True, ln=True)
    pdf.ln(14)
# ==============================================================================
# BLOCO 9: INJEÇÃO VISUAL DE BÔNUS E OPÇÕES DE PARCELAMENTO NO DOCUMENTO IMPRESSO
# ==============================================================================
    tem_bonus = any([item["Bônus"] for item in st.session_state.servicos_orcamento])
    if tem_bonus:
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 10, "ATIVIDADES ADICIONAIS CONCEDIDAS COMO BÔNUS (CORTESIA)", ln=True)
        pdf.set_font("Helvetica", "I", 10)
        for serv in st.session_state.servicos_orcamento:
            if serv["Bônus"]:
                pdf.cell(0, 7, f" - {serv['Descrição']} (Preco Original: R$ {serv['Preço Original']:.2f}) -> INCLUSO COMO BÔNUS", ln=True)
        pdf.ln(10)

    # Condições de pagamento estruturadas verticalmente com espaçamento duplo
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "CONDIÇÕES DE PAGAMENTO", ln=True)
    
    y_condicoes = pdf.get_y()
    pdf.set_font("Helvetica", "B", 10.5)
    
    pdf.cell(135, 7, "Formas de Pagamento:", ln=True)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.multi_cell(135, 7, f"OPCAO 01 - A VISTA COM DESCONTO ESPECIAL:\nValor total com desconto aplicado: R$ {preco_final_avista:.2f}\n\nOPCAO 02 - PARCELAMENTO FACILITADO CORPORATIVO:\nPagamento em ate 10x mensais fixas de R$ {valor_parcela_10x:.2f}\nValor total final parcelado: R$ {preco_final_parcelado_com_taxa:.2f}")
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.cell(135, 7, "Garantia dos Servicos:", ln=True)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.multi_cell(135, 7, f"{t_gar}")
    pdf.ln(4)
    
    pdf.set_font("Helvetica", "B", 10.5)
    pdf.cell(135, 7, "Observacoes Importantes:", ln=True)
    pdf.set_font("Helvetica", "", 10.5)
    pdf.multi_cell(135, 7, f"{t_obs}")
    
    try:
        qr_res = requests.get(URL_QRCODE, timeout=5)
        if qr_res.status_code == 200:
            with open("temp_pdf_qr.png", "wb") as f:
                f.write(qr_res.content)
            pdf.image("temp_pdf_qr.png", 158, y_condicoes, 38, 38)
            pdf.set_y(y_condicoes + 39)
            pdf.set_x(158)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.cell(38, 5, "Aprovar via WhatsApp", ln=True, align="C")
            if os.path.exists("temp_pdf_qr.png"):
                os.remove("temp_pdf_qr.png")
    except Exception:
        pass
    
    pdf_output = pdf.output()

    st.markdown("### 🖨️ Ações de Envio")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            label="📥 Baixar Orçamento Customizado em PDF",
            data=bytes(pdf_output),
            file_name=f"Orcamento_Fenix_{cli_sel.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )
    with col_d2:
        st.link_button("💬 Enviar via WhatsApp", LINK_WHATSAPP)
# ==============================================================================
# BLOCO 10: FORMULÁRIOS DE CADASTROS DE RETAGUARDA (SERVIÇOS, MATERIAIS E VEÍCULOS)
# ==============================================================================

# ABA - PORTFÓLIO DE SERVIÇOS
with aba_mao_obra:
    st.subheader("🛠️ Gestão de Portfólio de Serviços")
    with st.form("form_novo_servico_detalhado", clear_on_submit=True):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            ts_qtd = st.number_input("Quantidade Estimada Padrão:", min_value=0.0, value=1.0)
            ts_desc = st.text_input("Descrição Completa da Atividade:")
        with col_s2:
            ts_unidade = st.text_input("Unidade Comercial:", value="UN")
            ts_compra = st.number_input("Preço Unitário de Execução (R$):", min_value=0.0, value=0.0)
            
        if st.form_submit_button("💾 Salvar Serviço no Portfólio"):
            if ts_desc:
                ts_total_linha = ts_qtd * ts_compra
                novo_serv_df = pd.DataFrame([{
                    "Quantidade": ts_qtd, "Descrição": ts_desc, "Unidade": ts_unidade, "Valor Compra Un. (R$)": ts_compra, "Total Bruto (R$)": ts_total_linha
                }])
                salvar_no_github("servicos.csv", novo_serv_df)
                st.session_state.servicos = carregar_dados("servicos.csv")
                st.success("Serviço catalogado com sucesso!")
                st.rerun()

    if st.session_state.servicos:
        st.dataframe(pd.DataFrame(st.session_state.servicos), use_container_width=True)

# ABA - CATALOGAÇÃO DE PRODUTOS
with aba_materiais:
    st.subheader("🛒 Almoxarifado de Materiais")
    with st.form("form_catalogo_material", clear_on_submit=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            mat_nome = st.text_input("Nome do Material / Insumo:")
            mat_marca = st.text_input("Fabricante:")
        with col_m2:
            mat_unidade = st.text_input("Unidade de Fracionamento:", value="UN")
            mat_preco = st.number_input("Preço de Custo (R$):", min_value=0.0, value=0.0)
            
        if st.form_submit_button("💾 Catalogar Produto"):
            if mat_nome:
                novo_df = pd.DataFrame([{"Item": mat_nome, "Marca": mat_marca, "Unidade": mat_unidade, "Preço Unitário": mat_preco}])
                salvar_no_github("materiais.csv", novo_df)
                st.session_state.materiais = carregar_dados("materiais.csv")
                st.success("Material adicionado!")
                st.rerun()

    if st.session_state.materiais:
        st.dataframe(pd.DataFrame(st.session_state.materiais), use_container_width=True)

# ABA - CADASTRO DE FROTAS
with aba_veiculos:
    st.subheader("🚚 Frota e Logística")
    with st.form("form_veiculo_simplificado", clear_on_submit=True):
        v_modelo = st.text_input("Modelo:")
        v_placa = st.text_input("Placa:")
        v_compra = st.number_input("Valor de Aquisição (R$):", min_value=0.0, value=50000.0)
        v_tempo_uso = st.number_input("Tempo de Uso (Anos):", min_value=1, value=3)
        v_consumo = st.number_input("Consumo (Km/L):", min_value=1.0, value=11.0)
        
        if st.form_submit_button("💾 Registrar Veículo"):
            if v_modelo and v_placa:
                novo_veic_df = pd.DataFrame([{
                    "Modelo": v_modelo, "Placa": v_placa, "Valor Compra": v_compra, "Tempo de Uso (Anos)": v_tempo_uso, "Consumo (Km/L)": v_consumo, "Depreciação Anual Est.": round(v_compra/v_tempo_uso, 2)
                }])
                salvar_no_github("veiculos.csv", novo_veic_df)
                st.session_state.veiculos = carregar_dados("veiculos.csv")
                st.success("Veículo integrado!")
                st.rerun()

    if st.session_state.veiculos:
        st.dataframe(pd.DataFrame(st.session_state.veiculos), use_container_width=True)
