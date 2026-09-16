# ==============================================================================
# BLOCO 1: IMPORTAÇÕES, ENGINE DO GITHUB, MOTOR PDF E ESTRUTURA DE ABAS
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
            with open("temp_logo.png", "wb") as f:
                f.write(self.logo_bytes.getbuffer())
            self.image("temp_logo.png", 10, 8, 33)
            if os.path.exists("temp_logo.png"):
                os.remove("temp_logo.png")
        
        self.set_font("Helvetica", "B", 14)
        self.cell(40) 
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

# ─── CONECTIVIDADE E ATUALIZAÇÃO COMPLETA NO GITHUB ───
def salvar_no_github(nome_arquivo_csv, df_novo, sobrescrever=False):
    try:
        token = st.secrets["GITHUB_TOKEN"].strip()
        repo = st.secrets["GITHUB_REPO"].strip()
    except Exception:
        df_novo.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
        return False

    url = f"https://github.com{repo}/contents/{nome_arquivo_csv}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    
    sha = None
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            sha = response.json().get("sha")
            if not sobrescrever:
                conteudo_antigo_b64 = response.json().get("content")
                conteudo_antigo = base64.b64decode(conteudo_antigo_b64).decode("utf-8")
                from io import StringIO
                df_antigo = pd.read_csv(StringIO(conteudo_antigo))
                df_final = pd.concat([df_antigo, df_novo]).drop_duplicates().reset_index(drop=True)
            else:
                df_final = df_novo
        else:
            df_final = df_novo

        csv_conteudo = df_final.to_csv(index=False, encoding="utf-8")
        conteudo_b64 = base64.b64encode(csv_conteudo.encode("utf-8")).decode("utf-8")
        
        dados_commit = {"message": f"Atualizando base de dados: {nome_arquivo_csv}", "content": conteudo_b64}
        if sha: dados_commit["sha"] = sha
        
        requests.put(url, headers=headers, json=dados_commit, timeout=10)
        df_final.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
        return True
        
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        df_novo.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
        st.warning("⚠️ Dados salvos localmente. A sincronização com o GitHub falhou temporariamente.")
        return False

def carregar_dados(nome_arquivo_csv):
    if os.path.exists(nome_arquivo_csv):
        try:
            return pd.read_csv(nome_arquivo_csv).to_dict(orient="records")
        except Exception:
            return []
    return []

# Inicialização de estados
if 'clientes' not in st.session_state: st.session_state.clientes = carregar_dados("clientes.csv")
if 'veiculos' not in st.session_state: st.session_state.veiculos = carregar_dados("veiculos.csv")
if 'materiais' not in st.session_state: st.session_state.materiais = carregar_dados("materiais.csv")
if 'servicos' not in st.session_state: st.session_state.servicos = carregar_dados("servicos.csv")
if 'materiais_orcamento' not in st.session_state: st.session_state.materiais_orcamento = []

col_topo1, col_topo2 = st.columns(2)
with col_topo1:
    st.title("⚡ Painel de Gestão e Orçamentos Elétricos")
    logo_upload = st.file_uploader("Upload da Logo da sua Empresa (PNG/JPG):", type=["png", "jpg", "jpeg"])
    if logo_upload: st.image(logo_upload, width=200)
with col_topo2:
    st.image(URL_QRCODE, caption="Fale Conosco no WhatsApp")

# Criação das Novas Abas Organizadas
aba_orc_ponto, aba_calc_preco, aba_clientes, aba_mao_obra, aba_materiais, aba_veiculos = st.tabs([
    "📍 Orçamento por Ponto", "📊 Cálculo de Preço", "👥 Cadastro de Clientes", "⏱️ Mão de Obra & Serviços", "🛒 Cadastro de Materiais", "🚚 Cadastro de Veículos"
])
# ==============================================================================
# BLOCO 2: SEÇÕES DE CADASTRO PARA CLIENTES E VEÍCULOS (EDIÇÃO E EXCLUSÃO)
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
            novo_contato = st.text_input("Alterar Contato:", value=df_cli.loc[idx_cli, "Contato"].values[0])
            novo_end = st.text_input("Alterar Endereço:", value=df_cli.loc[idx_cli, "Endereço"].values[0])
        with col_ed2:
            st.write("")
            if st.button("📝 Confirmar Alteração de Dados", key="btn_edit_cli"):
                df_cli.loc[idx_cli, "Contato"] = novo_contato
                df_cli.loc[idx_cli, "Endereço"] = novo_end
                salvar_no_github("clientes.csv", df_cli, sobrescrever=True)
                st.session_state.clientes = df_cli.to_dict(orient="records")
                st.success("Dados do cliente alterados com sucesso!")
                st.rerun()
            if st.button("🗑️ Excluir Cliente do Sistema", key="btn_del_cli"):
                df_cli = df_cli.drop(idx_cli)
                salvar_no_github("clientes.csv", df_cli, sobrescrever=True)
                st.session_state.clientes = df_cli.to_dict(orient="records")
                st.error("Cliente removido permanentemente!")
                st.rerun()

# ABA - CADASTRO DE VEÍCULOS
with aba_veiculos:
    st.subheader("🚚 Gestão, Edição e Remoção de Veículos")
    with st.form("form_veiculo", clear_on_submit=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v_modelo = st.text_input("Modelo do Veículo:")
            v_placa = st.text_input("Placa do Veículo:")
        with col_v2:
            v_km = st.number_input("Custo estimado por Km rodado (R$):", min_value=0.0, value=1.20, step=0.10)
            
        if st.form_submit_button("💾 Salvar Veículo"):
            if v_modelo:
                novo_df = pd.DataFrame([{"Modelo": v_modelo, "Placa": v_placa, "Custo/Km": v_km}])
                salvar_no_github("veiculos.csv", novo_df)
                st.session_state.veiculos = carregar_dados("veiculos.csv")
                st.success(f"Veículo '{v_modelo}' inserido!")
                st.rerun()

    if st.session_state.veiculos:
        df_veic = pd.DataFrame(st.session_state.veiculos)
        st.dataframe(df_veic, use_container_width=True)
        
        st.markdown("#### ✏️ Alterar ou Excluir Veículo")
        veic_para_gerenciar = st.selectbox("Selecione o Veículo pela Placa:", df_veic["Placa"].tolist(), key="sel_veic")
        idx_veic = df_veic[df_veic["Placa"] == veic_para_gerenciar].index
        
        col_ev1, col_ev2 = st.columns(2)
        with col_ev1:
            novo_custo_km = st.number_input("Alterar Custo por KM (R$):", min_value=0.0, value=float(df_veic.loc[idx_veic, "Custo/Km"].values[0]), step=0.10)
        with col_ev2:
            st.write("")
            if st.button("📝 Confirmar Alteração de Valor KM", key="btn_edit_veic"):
                df_veic.loc[idx_veic, "Custo/Km"] = novo_custo_km
                salvar_no_github("veiculos.csv", df_veic, sobrescrever=True)
                st.session_state.veiculos = df_veic.to_dict(orient="records")
                st.success("Valor de KM alterado!")
                st.rerun()
            if st.button("🗑️ Remover Veículo da Frota", key="btn_del_veic"):
                df_veic = df_veic.drop(idx_veic)
                salvar_no_github("veiculos.csv", df_veic, sobrescrever=True)
                st.session_state.veiculos = df_veic.to_dict(orient="records")
                st.error("Veículo excluído!")
                st.rerun()
# ==============================================================================
# BLOCO 3: SEÇÕES DE CONTROLE DE INVENTÁRIO DE MATERIAIS E MODELOS DE PREÇOS
# ==============================================================================

# ABA - CADASTRO DE MATERIAIS
with aba_materiais:
    st.subheader("🛒 Almoxarifado / Gerenciador de Produtos")
    with st.form("form_catalogo_material", clear_on_submit=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            mat_nome = st.text_input("Nome do Material:")
        with col_m2:
            mat_marca = st.text_input("Marca / Fabricante:")
        with col_m3:
            mat_preco = st.number_input("Preço de Custo Padrão (R$):", min_value=0.0, value=0.0, step=5.0)
            
        if st.form_submit_button("💾 Salvar Material"):
            if mat_nome:
                novo_df = pd.DataFrame([{"Item": mat_nome, "Marca": mat_marca, "Preço Unitário": mat_preco}])
                salvar_no_github("materiais.csv", novo_df)
                st.session_state.materiais = carregar_dados("materiais.csv")
                st.success(f"'{mat_nome}' adicionado!")
                st.rerun()

    if st.session_state.materiais:
        df_mat = pd.DataFrame(st.session_state.materiais)
        st.dataframe(df_mat, use_container_width=True)
        
        st.markdown("#### ✏️ Alterar Preço ou Remover Produto")
        mat_para_gerenciar = st.selectbox("Selecione o Material para Modificar:", df_mat["Item"].tolist(), key="sel_mat")
        idx_mat = df_mat[df_mat["Item"] == mat_para_gerenciar].index
        
        col_em1, col_em2 = st.columns(2)
        with col_em1:
            novo_preco_mat = st.number_input("Alterar Preço de Custo Padrão (R$):", min_value=0.0, value=float(df_mat.loc[idx_mat, "Preço Unitário"].values[0]), step=1.0)
        with col_em2:
            st.write("")
            if st.button("📝 Confirmar Alteração de Preço", key="btn_edit_mat"):
                df_mat.loc[idx_mat, "Preço Unitário"] = novo_preco_mat
                salvar_no_github("materiais.csv", df_mat, sobrescrever=True)
                st.session_state.materiais = df_mat.to_dict(orient="records")
                st.success("Preço do produto atualizado com sucesso!")
                st.rerun()
            if st.button("🗑️ Excluir Material do Almoxarifado", key="btn_del_mat"):
                df_mat = df_mat.drop(idx_mat)
                salvar_no_github("materiais.csv", df_mat, sobrescrever=True)
                st.session_state.materiais = df_mat.to_dict(orient="records")
                st.error("Material removido do estoque!")
                st.rerun()

# ABA - MÃO DE OBRA E TIPOS DE SERVIÇOS
with aba_mao_obra:
    st.subheader("🛠️ Tipos de Serviços e Controle de Mão de Obra")
    with st.form("form_tipo_servico", clear_on_submit=True):
        col_ts1, col_ts2, col_ts3 = st.columns(3)
        with col_ts1:
            ts_nome = st.text_input("Nome do Serviço (Ex: Instalação de Padrão):")
        with col_ts2:
            ts_tipo = st.selectbox("Modelo de Cobrança Padrão:", ["Por Ponto Elétrico", "Por Hora Trabalhada", "Valor Fixo"])
        with col_ts3:
            ts_preco = st.number_input("Preço Base Referencial (R$):", min_value=0.0, value=100.0)
            
        if st.form_submit_button("💾 Salvar Tipo de Serviço"):
            if ts_nome:
                novo_df = pd.DataFrame([{"Serviço": ts_nome, "Tipo Cobrança": ts_tipo, "Preço Base": ts_preco}])
                salvar_no_github("servicos.csv", novo_df)
                st.session_state.servicos = carregar_dados("servicos.csv")
                st.success("Serviço registrado!")
                st.rerun()

    if st.session_state.servicos:
        df_serv = pd.DataFrame(st.session_state.servicos)
        st.dataframe(df_serv, use_container_width=True)
        
        st.markdown("#### ✏️ Alterar Valores ou Remover Tipo de Serviço")
        serv_para_gerenciar = st.selectbox("Selecione o Serviço para Modificar:", df_serv["Serviço"].tolist(), key="sel_serv")
        idx_serv = df_serv[df_serv["Serviço"] == serv_para_gerenciar].index
        
        col_es1, col_es2 = st.columns(2)
        with col_es1:
            novo_preco_serv = st.number_input("Alterar Preço Base Referencial (R$):", min_value=0.0, value=float(df_serv.loc[idx_serv, "Preço Base"].values[0]), step=10.0)
        with col_es2:
            st.write("")
            if st.button("📝 Confirmar Alteração de Valor Base", key="btn_edit_serv"):
                df_serv.loc[idx_serv, "Preço Base"] = novo_preco_serv
                salvar_no_github("servicos.csv", df_serv, sobrescrever=True)
                st.session_state.servicos = df_serv.to_dict(orient="records")
                st.success("Valor base do serviço atualizado!")
                st.rerun()
            if st.button("🗑️ Excluir Tipo de Serviço do Portfólio", key="btn_del_serv"):
                df_serv = df_serv.drop(idx_serv)
                salvar_no_github("servicos.csv", df_serv, sobrescrever=True)
                st.session_state.servicos = df_serv.to_dict(orient="records")
                st.error("Serviço removido!")
                st.rerun()
# ==============================================================================
# BLOCO 4: ORÇAMENTO POR PONTO E NOVA ABA DE CÁLCULO DE PREÇO (COM PDF)
# ==============================================================================

# Funções internas para ler arquivos de termos comerciais
def ler_arquivo_txt(n, d): return open(n, "r", encoding="utf-8").read() if os.path.exists(n) else d
t_pag = ler_arquivo_txt("pagamento.txt", "A combinar.")
t_gar = ler_arquivo_txt("garantia.txt", "90 dias.")
t_obs = ler_arquivo_txt("observacoes.txt", "Sem alteração estrutural.")

# ─── 1. NOVA ABA: CÁLCULO DE PREÇO GERAL ───
with aba_calc_preco:
    st.subheader("📊 Painel de Cálculo Analítico de Preços")
    st.markdown("Calcule o preço base do projeto somando custos operacionais de forma rápida.")
    
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
        
        st.markdown("### 🧮 Cálculo da Empreitada por Pontos")
        op_valor_ponto = st.number_input("Valor por Ponto Elétrico (R$):", min_value=0.0, value=120.0, step=10.0)
        op_qtd_pontos = st.number_input("Quantidade de Pontos Totais:", min_value=0.0, value=10.0, step=1.0)
        mo_total_v = op_valor_ponto * op_qtd_pontos
        st.info(f"Subtotal da Mão de Obra ({int(op_qtd_pontos)} pontos): R$ {mo_total_v:.2f}")

        if st.session_state.veiculos:
            lista_v = [f"{v['Modelo']} ({v['Placa']})" for v in st.session_state.veiculos]
            v_sel = st.selectbox("Veículo:", lista_v, key="orc_p_veic")
            km_r = st.number_input("KM Estimado:", min_value=0.0, value=0.0, key="km_p")
            idx = lista_v.index(v_sel)
            custo_transporte = km_r * st.session_state.veiculos[idx]["Custo/Km"]
        else:
            custo_transporte = st.number_input("Deslocamento Manual (R$):", min_value=0.0, value=0.0, key="des_p")

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
    rm1.metric("Mão de Obra (Pontos)", f"R$ {mo_total_v:.2f}")
    rm2.metric("Materiais", f"R$ {total_m_lucro:.2f}")
    rm3.metric("Logística", f"R$ {custo_transporte:.2f}")
    rm4.metric("Impostos", f"R$ {impostos_finais:.2f}")
    rm5.metric("PREÇO FINAL", f"R$ {preco_final:.2f}", delta=f"- R$ {desc_v:.2f}" if desc_v > 0 else None)

    # Conversor FPDF
    pdf = PDFOrcamento(logo_bytes=logo_upload)
    pdf.add_page()
    pdf.set_font("Helvetica", "", 11)
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "DADOS DO CLIENTE", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Cliente: {cli_sel}", ln=True)
    pdf.cell(0, 6, f"Contato: {contato_disp}", ln=True)
    pdf.cell(0, 6, f"Endereco da Obra: {endereco_disp}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"SERVICO: Orcamento por Ponto Elétrico ({int(op_qtd_pontos)} pontos)", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, f"Escopo Tecnico:\n{orc_descricao if orc_descricao else 'Execucao conforme levantamento de pontos.'}")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "RESUMO FINANCEIRO", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"- Mao de Obra calculada por Pontos: R$ {mo_total_v:.2f}", ln=True)
    pdf.cell(0, 6, f"- Fornecimento de Materiais: R$ {total_m_lucro:.2f}", ln=True)
    pdf.cell(0, 6, f"- Logistica/Frota: R$ {custo_transporte:.2f}", ln=True)
    pdf.cell(0, 6, f"- Encargos/Impostos: R$ {impostos_finais:.2f}", ln=True)
    if desc_v > 0: pdf.cell(0, 6, f"- Desconto Concedido: - R$ {desc_v:.2f}", ln=True)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, f"VALOR TOTAL DO INVESTIMENTO: R$ {preco_final:.2f}", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "CONDICOES COMERCIAIS", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, f"Formas de Pagamento:\n{t_pag}\n\nGarantia:\n{t_gar}\n\nObservacoes:\n{t_obs}")
    
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
