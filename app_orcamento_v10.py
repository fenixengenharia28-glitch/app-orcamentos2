# ==============================================================================
# BLOCO 1: IMPORTAÇÕES, ENGINE DO GITHUB, PERSISTÊNCIA E NOVO CABEÇALHO COMPLETO PDF
# ==============================================================================
import streamlit as st
import pandas as pd
import requests
import base64
import os
from fpdf import FPDF
from io import BytesIO

# Configuração da página web
st.set_page_config(
    page_title="Gestão de Orçamentos Elétricos Integrada", 
    page_icon="⚡", 
    layout="wide"
)

WHATSAPP_NUMERO = "5531995392027"
LINK_WHATSAPP = f"https://wa.me{WHATSAPP_NUMERO}"
URL_QRCODE = f"https://googleapis.com{LINK_WHATSAPP}&choe=UTF-8"

# ─── CLASSE DO PDF COM DESIGN DE CABEÇALHO EM TRÊS SEÇÕES DADOS COMPLETOS FENIX ───
class PDFOrcamento(FPDF):
    def __init__(self, logo_bytes=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_bytes = logo_bytes

    def header(self):
        # 1. LOGO NO CANTO ESQUERDO
        if self.logo_bytes:
            with open("temp_logo.png", "wb") as f:
                f.write(self.logo_bytes)
            self.image("temp_logo.png", 10, 8, 32)
            if os.path.exists("temp_logo.png"):
                os.remove("temp_logo.png")
        
        self.set_y(10)
        
        # 2. DADOS DA EMPRESA CENTRALIZADOS (RAZÃO SOCIAL, CNPJ E ENDEREÇO DA SAVASSI)
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 5, "Fenix Engenharia e Comercio LTDA / CNPJ: 52.769.953/0001-12", ln=True, align="C")
        self.set_font("Helvetica", "", 8)
        self.cell(0, 4, "Avenida Getulio Vargas, nº 671, 9º Andar, Sala 1051, Bairro Savassi", ln=True, align="C")
        self.cell(0, 4, "Cidade de Belo Horizonte - MG, Cep: 30112-021", ln=True, align="C")
        
        # 3. WHATSAPP NO CANTO DIREITO 
        self.set_y(10)
        self.set_font("Helvetica", "B", 10)
        self.set_x(155)
        self.cell(45, 5, "WhatsApp:", ln=True, align="R")
        self.set_x(155)
        self.set_font("Helvetica", "", 10)
        self.cell(45, 4, "(31) 99539-2027", ln=True, align="R")
        
        # Linha divisória cinza reposicionada abaixo do endereço expandido
        self.set_draw_color(200, 200, 200)
        self.set_line_width(0.3)
        self.line(10, 32, 200, 32)
        self.set_y(40)

    def footer(self):
        self.set_y(-25)
        self.set_draw_color(220, 220, 220)
        self.line(10, 270, 200, 270)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C", ln=True)
        self.cell(0, 5, "Fenix Engenharia e Comercio LTDA - Contato: (31) 99539-2027", align="C")
# ==============================================================================
# BLOCO 2: CONECTIVIDADE COM REPOSITÓRIO GITHUB E BANCO DE DATASETS
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

def carregar_dados(nome_arquivo_csv):
    if os.path.exists(nome_arquivo_csv):
        try:
            df = pd.read_csv(nome_arquivo_csv)
            if nome_arquivo_csv == "servicos.csv" and "Serviço" in df.columns:
                df = df.rename(columns={"Serviço": "Descrição", "Preço Base": "Valor Compra Un. (R$)"})
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

# Inicialização de estados
if 'clientes' not in st.session_state: st.session_state.clientes = carregar_dados("clientes.csv")
if 'veiculos' not in st.session_state: st.session_state.veiculos = carregar_dados("veiculos.csv")
if 'materiais' not in st.session_state: st.session_state.materiais = carregar_dados("materiais.csv")
if 'servicos' not in st.session_state: st.session_state.servicos = carregar_dados("servicos.csv")
if 'materiais_orcamento' not in st.session_state: st.session_state.materiais_orcamento = []
if 'logo_bytes' not in st.session_state: st.session_state.logo_bytes = carregar_logo_persistida()

col_topo1, col_topo2 = st.columns(2)
with col_topo1:
    st.title("⚡ Painel de Gestão e Orçamentos Elétricos")
    logo_upload = st.file_uploader("Upload e Salvamento da Logo da Empresa (PNG/JPG):", type=["png", "jpg", "jpeg"])
    if logo_upload:
        bytes_da_logo = logo_upload.getvalue()
        st.session_state.logo_bytes = bytes_da_logo
        with open("logo_local.png", "wb") as f: f.write(bytes_da_logo)
        logo_b64_string = base64.b64encode(bytes_da_logo).decode("utf-8")
        salvar_no_github("logo_persistida.txt", logo_b64_string, sobrescrever=True)
        st.success("Logo salva permanentemente no sistema e no GitHub!")
    if st.session_state.logo_bytes: st.image(st.session_state.logo_bytes, width=200)
with col_topo2:
    st.image(URL_QRCODE, caption="Fale Conosco no WhatsApp")

aba_orc_ponto, aba_calc_preco, aba_clientes, aba_mao_obra, aba_materiais, aba_veiculos = st.tabs([
    "📍 Orçamento por Ponto", "📊 Cálculo de Preço", "👥 Cadastro de Clientes", "⏱️ Mão de Obra & Serviços", "🛒 Cadastro de Materiais", "🚚 Cadastro de Veículos"
])
# ==============================================================================
# BLOCO 3: CLIENTES E FROTA COM CÁLCULO DE DEPRECIAÇÃO LINEAR POR QUILÔMETRO
# ==============================================================================

# ABA - CADASTRO DE CLIENTES
with aba_clientes:
    st.subheader("👥 Cadastro e Modificação de Clientes")
    with st.form("form_cliente", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            c_nome = st.text_input("Nome completo ou Razão Social:")
            c_doc = st.text_input("CPF ou CNPJ:")
        with col_c2:
            c_contato = st.text_input("WhatsApp / Telefone:")
            c_endereco = st.text_input("Endereço da Obra:")
        
        if st.form_submit_button("💾 Salvar Novo Cliente"):
            if c_nome:
                novo_df = pd.DataFrame([{"Nome": c_nome, "Documento": c_doc, "Contato": c_contato, "Endereço": c_endereco}])
                salvar_no_github("clientes.csv", novo_df)
                st.session_state.clientes = carregar_dados("clientes.csv")
                st.success(f"Cliente '{c_nome}' integrado!")
                st.rerun()

    if st.session_state.clientes:
        df_cli = pd.DataFrame(st.session_state.clientes)
        st.dataframe(df_cli, use_container_width=True)
        st.markdown("#### ✏️ Alterar ou Excluir Cliente")
        item_para_gerenciar = st.selectbox("Selecione o Cliente para Modificar:", df_cli["Nome"].tolist(), key="sel_cli")
        idx_cli = df_cli[df_cli["Nome"] == item_para_gerenciar].index
        col_ed1, col_ed2 = st.columns(2)
        with col_ed1:
            novo_contato = st.text_input("Alterar Contato:", value=df_cli.loc[idx_cli, "Contato"].values)
            novo_end = st.text_input("Alterar Endereço:", value=df_cli.loc[idx_cli, "Endereço"].values)
        with col_ed2:
            st.write("")
            if st.button("📝 Confirmar Alteração de Dados", key="btn_edit_cli"):
                df_cli.loc[idx_cli, "Contato"] = novo_contato
                df_cli.loc[idx_cli, "Endereço"] = novo_end
                salvar_no_github("clientes.csv", df_cli, sobrescrever=True)
                st.session_state.clientes = df_cli.to_dict(orient="records")
                st.success("Dados alterados!")
                st.rerun()
            if st.button("🗑️ Excluir Cliente do Sistema", key="btn_del_cli"):
                df_cli = df_cli.drop(idx_cli)
                salvar_no_github("clientes.csv", df_cli, sobrescrever=True)
                st.session_state.clientes = df_cli.to_dict(orient="records")
                st.rerun()

# ABA - GESTÃO DE VEÍCULOS (DEPRECIAÇÃO INCORPORADA)
with aba_veiculos:
    st.subheader("🚚 Frota Corporativa e Métricas de Depreciação Mecânica")
    with st.form("form_veiculo_avancado", clear_on_submit=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v_modelo = st.text_input("Modelo do Veículo:")
            v_placa = st.text_input("Placa do Veículo:")
            v_consumo = st.number_input("Consumo Médio (Km/Litro):", min_value=1.0, value=11.0, step=0.5)
        with col_v2:
            v_compra = st.number_input("Valor de Compra (R$):", min_value=0.0, value=60000.0, step=5000.0)
            v_residual = st.number_input("Valor Residual Estimado (R$):", min_value=0.0, value=20000.0, step=5000.0)
            v_vida_util = st.number_input("Vida Útil Estimada Total (Anos):", min_value=1, value=5, step=1)
            v_km_ano = st.number_input("Média de KM Rodados por Ano:", min_value=1.0, value=15000.0, step=1000.0)
            
        if st.form_submit_button("💾 Salvar Veículo e Métricas"):
            if v_modelo and v_placa:
                depreciacao_anual = (v_compra - v_residual) / v_vida_util
                depreciacao_por_km = depreciacao_anual / v_km_ano
                
                novo_veic_df = pd.DataFrame([{
                    "Modelo": v_modelo,
                    "Placa": v_placa,
                    "Consumo (Km/L)": v_consumo,
                    "Depreciação por KM (R$)": round(depreciacao_por_km, 2),
                    "KM Anual Padrão": v_km_ano
                }])
                salvar_no_github("veiculos.csv", novo_veic_df)
                st.session_state.veiculos = carregar_dados("veiculos.csv")
                st.success("Métricas de desgaste salvas!")
                st.rerun()

    if st.session_state.veiculos:
        df_veic = pd.DataFrame(st.session_state.veiculos)
        st.dataframe(df_veic, use_container_width=True)
        st.markdown("#### 🗑️ Remover Automóvel")
        veic_del = st.selectbox("Escolha pela Placa para Excluir:", df_veic["Placa"].tolist(), key="del_veic_box")
        if st.button("Excluir Veículo Selecionado"):
            df_veic = df_veic[df_veic["Placa"] != veic_del]
            salvar_no_github("veiculos.csv", df_veic, sobrescrever=True)
            st.session_state.veiculos = df_veic.to_dict(orient="records")
            st.rerun()
# ==============================================================================
# BLOCO 4: ALMOXARIFADO E PORTFÓLIO DE SERVIÇOS COM UNIDADE DE MEDIDA CUSTOMIZADA
# ==============================================================================

# ABA - CADASTRO DE MATERIAIS
with aba_materiais:
    st.subheader("🛒 Almoxarifado / Gerenciador de Produtos")
    with st.form("form_catalogo_material", clear_on_submit=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            mat_nome = st.text_input("Nome do Material:")
            mat_marca = st.text_input("Marca / Fabricante:")
        with col_m2:
            mat_unidade = st.text_input("Unidade de Medida livre:", placeholder="UN")
            mat_preco = st.number_input("Preço de Custo Padrão (R$):", min_value=0.0, value=0.0, step=5.0)
            
        if st.form_submit_button("💾 Salvar Material"):
            if mat_nome:
                novo_df = pd.DataFrame([{"Item": mat_nome, "Marca": mat_marca, "Unidade": mat_unidade if mat_unidade else "UN", "Preço Unitário": mat_preco}])
                salvar_no_github("materiais.csv", novo_df)
                st.session_state.materiais = carregar_dados("materiais.csv")
                st.success("Material adicionado!")
                st.rerun()

    if st.session_state.materiais:
        df_mat = pd.DataFrame(st.session_state.materiais)
        st.dataframe(df_mat, use_container_width=True)
        st.markdown("#### 🗑️ Excluir Material")
        mat_del = st.selectbox("Escolha para Remover:", df_mat["Item"].tolist(), key="del_mat_box")
        if st.button("Excluir Item do Estoque"):
            df_mat = df_mat[df_mat["Item"] != mat_del]
            salvar_no_github("materiais.csv", df_mat, sobrescrever=True)
            st.session_state.materiais = df_mat.to_dict(orient="records")
            st.rerun()

# ABA - MÃO DE OBRA E PORTFÓLIO DE SERVIÇOS
with aba_mao_obra:
    st.subheader("🛠️ Portfólio Detalhado de Serviços")
    with st.form("form_novo_servico_detalhado", clear_on_submit=True):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            ts_qtd = st.number_input("Quantidade:", min_value=0.0, value=1.0, step=1.0)
            ts_desc = st.text_input("Descrição do Serviço:")
        with col_s2:
            ts_unidade = st.text_input("Unidade de Medida livre:", placeholder="UN")
            ts_compra = st.number_input("Valor de Compra (Preço Unitário R$):", min_value=0.0, value=0.0, step=50.0)
            
        if st.form_submit_button("💾 Salvar Serviço no GitHub"):
            if ts_desc:
                ts_total_linha = ts_qtd * ts_compra
                novo_serv_df = pd.DataFrame([{
                    "Quantidade": ts_qtd, "Descrição": ts_desc, "Unidade": ts_unidade if ts_unidade else "UN", "Valor Compra Un. (R$)": ts_compra, "Total Bruto (R$)": ts_total_linha
                }])
                salvar_no_github("servicos.csv", novo_serv_df)
                st.session_state.servicos = carregar_dados("servicos.csv")
                st.success("Serviço salvo!")
                st.rerun()

    if st.session_state.servicos:
        df_serv = pd.DataFrame(st.session_state.servicos)
        if "Serviço" in df_serv.columns:
            df_serv = df_serv.rename(columns={"Serviço": "Descrição", "Preço Base": "Valor Compra Un. (R$)"})
        if "Quantidade" not in df_serv.columns: df_serv["Quantidade"] = 1.0
        if "Unidade" not in df_serv.columns: df_serv["Unidade"] = "UN"
        if "Total Bruto (R$)" not in df_serv.columns: df_serv["Total Bruto (R$)"] = df_serv["Quantidade"] * df_serv["Valor Compra Un. (R$)"]
        
        st.dataframe(df_serv, use_container_width=True)
        st.markdown("#### 🗑️ Remover Serviço")
        serv_del = st.selectbox("Escolha para Remover:", df_serv["Descrição"].tolist(), key="del_serv_box")
        if st.button("Excluir Serviço do Portfólio"):
            df_serv = df_serv[df_serv["Descrição"] != serv_del]
            salvar_no_github("servicos.csv", df_serv, sobrescrever=True)
            st.session_state.servicos = df_serv.to_dict(orient="records")
            st.rerun()
# ==============================================================================
# BLOCO 5: CÁLCULOS ANALÍTICOS, LOGÍSTICA DE COMBUSTÍVEL + DEPRECIAÇÃO E PDF
# ==============================================================================

def ler_arquivo_txt(n, d): return open(n, "r", encoding="utf-8").read() if os.path.exists(n) else d
t_pag = ler_arquivo_txt("pagamento.txt", "A combinar.")
t_gar = ler_arquivo_txt("garantia.txt", "90 dias.")
t_obs = ler_arquivo_txt("observacoes.txt", "Sem alteração estrutural.")

# ─── 1. ABA: CÁLCULO DE PREÇO GERAL ───
with aba_calc_preco:
    st.subheader("📊 Painel de Cálculo Analítico de Preços")
    col_cp1, col_cp2 = st.columns(2)
    with col_cp1:
        cp_mao_obra = st.number_input("Custo de Mão de Obra Estimado (R$):", min_value=0.0, value=1000.0, step=100.0)
        cp_custo_mat = st.number_input("Custo de Materiais Diretos (R$):", min_value=0.0, value=500.0, step=50.0)
    with col_cp2:
        cp_margem = st.number_input("Margem de Lucro Desejada (%):", min_value=0.0, value=30.0, step=5.0)
        cp_imposto = st.number_input("Estimativa de Impostos Praticada (%):", min_value=0.0, value=6.0, step=1.0)
        
    custo_total_base = cp_mao_obra + cp_custo_mat
    lucro_calculado = custo_total_base * (cp_margem / 100)
    imposto_calculado = (custo_total_base + lucro_calculado) * (cp_imposto / 100)
    preco_venda_sugerido = custo_total_base + lucro_calculado + imposto_calculado
    
    st.markdown("### 📈 Resultado do Cálculo")
    cpm1, cpm2, cpm3 = st.columns(3)
    cpm1.metric("Custo Total Bruto", f"R$ {custo_total_base:.2f}")
    cpm2.metric("Margem Adicionada", f"R$ {lucro_calculado:.2f}")
    cpm3.metric("PREÇO DE VENDA SUGERIDO", f"R$ {preco_venda_sugerido:.2f}")

# ─── 2. ABA: ORÇAMENTO DETALHADO POR PONTO ───
with aba_orc_ponto:
    st.subheader("📍 Montagem de Orçamento Técnico por Ponto Elétrico")
    col_op1, col_op2 = st.columns(2)
    
    with col_op1:
        st.markdown("### 1. Vínculo de Cliente e Logística")
        if st.session_state.clientes:
            lista_cli = [c["Nome"] for c in st.session_state.clientes]
            cli_sel = st.selectbox("Selecione o Cliente:", lista_cli, key="orc_p_cli")
            dados_cli = next(item for item in st.session_state.clientes if item["Nome"] == cli_sel)
            contato_disp, endereco_disp = dados_cli["Contato"], dados_cli["Endereço"]
        else:
            cli_sel = st.text_input("Nome do Cliente (Manual):", key="man_cli_p")
            contato_disp = st.text_input("Contato (Manual):", key="man_con_p")
            endereco_disp = st.text_input("Endereço (Manual):", key="man_end_p")
            
        orc_descricao = st.text_area("Escopo do serviço por ponto:")
        op_valor_ponto = st.number_input("Valor por Ponto Elétrico (R$):", min_value=0.0, value=120.0, step=10.0)
        op_qtd_pontos = st.number_input("Quantidade de Pontos Totais:", min_value=0.0, value=10.0, step=1.0)
        mo_total_v = op_valor_ponto * op_qtd_pontos
        st.info(f"Subtotal da Mão de Obra: R$ {mo_total_v:.2f}")

        # ─── MÓDULO LOGÍSTICO COMPLETO COM DEPRECIAÇÃO + COMBUSTÍVEL ───
        st.markdown("### 🚘 Engenharia de Deslocamento e Logística")
        if st.session_state.veiculos:
            lista_v = [f"{v['Modelo']} ({v['Placa']})" for v in st.session_state.veiculos]
            v_sel = st.selectbox("Selecione o Veículo para o Serviço:", lista_v, key="orc_p_veic")
            km_r = st.number_input("Distância total (Ida + Volta em KM):", min_value=0.0, value=20.0, key="km_p")
            preco_combustivel = st.number_input("Preço do Litro do Combustível (R$):", min_value=0.0, value=5.90, step=0.10)
            
            idx = lista_v.index(v_sel)
            dados_carro = st.session_state.veiculos[idx]
            
            custo_apenas_combustivel = (km_r / float(dados_carro["Consumo (Km/L)"])) * preco_combustivel
            custo_apenas_depreciacao = km_r * float(dados_carro["Depreciação por KM (R$)"])
            custo_transporte = custo_apenas_combustivel + custo_apenas_depreciacao
            
            st.caption(f"⛽ Combustível: R$ {custo_apenas_combustivel:.2f} | 🛠️ Desgaste/Depreciação: R$ {custo_apenas_depreciacao:.2f}")
        else:
            custo_transporte = st.number_input("Deslocamento Manual Total (R$):", min_value=0.0, value=0.0, key="des_p")

    with col_op2:
        st.markdown("### 2. Materiais Aplicados nos Pontos")
        if st.session_state.materiais:
            lista_m = [m["Item"] for m in st.session_state.materiais]
            m_sel = st.selectbox("Buscar material:", lista_m, key="orc_p_mat")
            dados_m = next(item for item in st.session_state.materiais if item["Item"] == m_sel)
            p_sugerido = dados_m["Preço Unitário"]
        else:
            m_sel = st.text_input("Material Manual:", key="mat_man_p")
            p_sugerido = 0.0
            
        m_qtd = st.number_input("Qtd:", min_value=1, value=1, key="qtd_m_p")
        m_preco = st.number_input("Preço de Custo (R$):", min_value=0.0, value=p_sugerido, key="prc_m_p")
        
        if st.button("➕ Inserir Material na Obra", key="btn_add_mat_p"):
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
            if st.button("🗑️ Limpar Materiais da Obra", key="btn_clear_mat_p"):
                st.session_state.materiais_orcamento = []
                st.rerun()

    st.markdown("---")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        margem_m = st.number_input("Margem sobre materiais (%):", min_value=0.0, value=20.0, key="marg_p")
        total_m_lucro = custo_bruto_m * (1 + (margem_m / 100))
    with col_f2:
        imposto_pc = st.number_input("Impostos / NF (%):", min_value=0.0, value=6.0, key="imp_p")
    with col_f3:
        desc_v = st.number_input("Desconto Especial (R$):", min_value=0.0, value=0.0, key="desc_p")

    subtotal = mo_total_v + total_m_lucro + custo_transporte
    impostos_finais = subtotal * (imposto_pc / 100)
    preco_final = subtotal + impostos_finais - desc_v

    st.markdown("### 📊 Fechamento do Orçamento por Ponto")
    rm1, rm2, rm3, rm4, rm5 = st.columns(5)
    rm1.metric("Mão de Obra", f"R$ {mo_total_v:.2f}")
    rm2.metric("Materiais", f"R$ {total_m_lucro:.2f}")
    rm3.metric("Logística (Total)", f"R$ {custo_transporte:.2f}")
    rm4.metric("Impostos", f"R$ {impostos_finais:.2f}")
    rm5.metric("PREÇO FINAL", f"R$ {preco_final:.2f}", delta=f"- R$ {desc_v:.2f}" if desc_v > 0 else None)

    # ─── GERAÇÃO DO ARQUIVO PDF COM QR CODE ACOPLADO ───
    pdf = PDFOrcamento(logo_bytes=st.session_state.logo_bytes)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 11)
    
    # Seção Cliente
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "DADOS DO CLIENTE", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Cliente: {cli_sel}", ln=True)
    pdf.cell(0, 6, f"Contato: {contato_disp}", ln=True)
    pdf.cell(0, 6, f"Endereco da Obra: {endereco_disp}", ln=True)
    pdf.ln(5)

    # Seção Escopo
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"SERVICO: Orcamento por Ponto Elétrico ({int(op_qtd_pontos)} pontos)", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, f"Escopo Técnico:\n{orc_descricao if orc_descricao else 'Execucao conforme levantamento de pontos.'}")
    pdf.ln(5)

    # Valores
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "RESUMO FINANCEIRO", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"- Mao de Obra calculada por Pontos: R$ {mo_total_v:.2f}", ln=True)
    pdf.cell(0, 6, f"- Fornecimento de Materiais: R$ {total_m_lucro:.2f}", ln=True)
    pdf.cell(0, 6, f"- Logistica Integrada (Desgaste + Combustivel): R$ {custo_transporte:.2f}", ln=True)
    pdf.cell(0, 6, f"- Encargos e Impostos: R$ {impostos_finais:.2f}", ln=True)
    if desc_v > 0: pdf.cell(0, 6, f"- Desconto Concedido: - R$ {desc_v:.2f}", ln=True)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"VALOR TOTAL DO INVESTIMENTO: R$ {preco_final:.2f}", ln=True)
    pdf.ln(5)

    # Termos Comerciais e QR CODE INJETADO LADO A LADO
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "CONDIÇÕES COMERCIAIS", ln=True)
    
    y_condicoes = pdf.get_y()
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(135, 5, f"Formas de Pagamento:\n{t_pag}\n\nGarantia:\n{t_gar}\n\nObservacoes:\n{t_obs}")
    
    try:
        qr_res = requests.get(URL_QRCODE, timeout=5)
        if qr_res.status_code == 200:
            with open("temp_pdf_qr.png", "wb") as f:
                f.write(qr_res.content)
            pdf.image("temp_pdf_qr.png", 160, y_condicoes, 35, 35)
            pdf.set_y(y_condicoes + 36)
            pdf.set_x(160)
            pdf.set_font("Helvetica", "B", 8)
            pdf.cell(35, 4, "Aprovar via WhatsApp", ln=True, align="C")
            if os.path.exists("temp_pdf_qr.png"):
                os.remove("temp_pdf_qr.png")
    except Exception:
        pass
    
    pdf_output = pdf.output()

    st.markdown("### 🖨️ Ações de Envio")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            label="📥 Baixar Orçamento por Ponto em PDF",
            data=bytes(pdf_output),
            file_name=f"Orcamento_Pontos_{cli_sel.replace(' ', '_')}.pdf",
            mime="application/pdf",
            key="btn_down_pdf_p"
        )
    with col_d2:
        st.link_button("💬 Enviar via WhatsApp", LINK_WHATSAPP, key="btn_wa_p")
