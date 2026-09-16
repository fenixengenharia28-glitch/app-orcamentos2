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

# Estado persistente da aplicação
if 'clientes' not in st.session_state: st.session_state.clientes = carregar_dados("clientes.csv")
if 'veiculos' not in st.session_state: st.session_state.veiculos = carregar_dados("veiculos.csv")
if 'materiais' not in st.session_state: st.session_state.materiais = carregar_dados("materiais.csv")
if 'servicos' not in st.session_state: st.session_state.servicos = carregar_dados("servicos.csv")
if 'materiais_orcamento' not in st.session_state: st.session_state.materiais_orcamento = []
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

# Criação das abas navegacionais do painel
aba_orc_ponto, aba_calc_preco, aba_clientes, aba_mao_obra, aba_materiais, aba_veiculos = st.tabs([
    "📍 Orçamento por Ponto", "📊 Cálculo de Preço", "👥 Cadastro de Clientes", "⏱️ Mão de Obra & Serviços", "🛒 Cadastro de Materiais", "🚚 Cadastro de Veículos"
])
# ==============================================================================
# BLOCO 6: GERENCIAMENTO DE CLIENTES E VEÍCULOS COM CALCULADORA INTERNA
# ==============================================================================
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
                st.success("Cliente cadastrado!")
                st.rerun()

    if st.session_state.clientes:
        st.dataframe(pd.DataFrame(st.session_state.clientes), use_container_width=True)

with aba_veiculos:
    st.subheader("🚚 Cadastro de Veículos e Calculadora de Combustível")
    col_v_esq, col_v_dir = st.columns(2)
    
    with col_v_esq:
        st.markdown("#### 🛠️ Cadastrar Novo Veículo")
        with st.form("form_veiculo_simplificado", clear_on_submit=True):
            v_modelo = st.text_input("Modelo do Veículo (Ex: Strada):")
            v_placa = st.text_input("Placa do Veículo:")
            v_compra = st.number_input("Valor de Compra (R$):", min_value=0.0, value=50000.0)
            v_tempo_uso = st.number_input("Tempo de Uso do Veículo (Anos):", min_value=1, value=3, step=1)
            v_consumo = st.number_input("Consumo Médio Praticado (Km/Litro):", min_value=1.0, value=11.0, step=0.5)
            
            if st.form_submit_button("💾 Salvar Veículo no GitHub"):
                if v_modelo and v_placa:
                    depreciacao_anual_simples = v_compra / v_tempo_uso
                    novo_veic_df = pd.DataFrame([{
                        "Modelo": v_modelo, "Placa": v_placa, "Valor Compra": v_compra, "Tempo de Uso (Anos)": v_tempo_uso, "Consumo (Km/L)": v_consumo, "Depreciação Anual Est.": round(depreciacao_anual_simples, 2)
                    }])
                    salvar_no_github("veiculos.csv", novo_veic_df)
                    st.session_state.veiculos = carregar_dados("veiculos.csv")
                    st.success(f"Veículo '{v_modelo}' arquivado!")
                    st.rerun()
# ==============================================================================
# BLOCO 7: CALCULADORA DE COMBUSTÍVEL NA MESMA TAB E LISTAGEM DE FROTA
# ==============================================================================
    with col_v_dir:
        st.markdown("#### 🧮 Calculadora Rápida de Combustível")
        if st.session_state.veiculos:
            df_veic_calc = pd.DataFrame(st.session_state.veiculos)
            lista_placas = df_veic_calc["Placa"].tolist()
            veic_sel_calc = st.selectbox("Selecione o veículo da frota:", lista_placas)
            km_servico = st.number_input("Quilômetros totais estimados (Ida + Volta):", min_value=0.0, value=50.0)
            preco_litro = st.number_input("Preço atual do litro (R$):", min_value=0.0, value=5.90, step=0.10)
            
            consumo_carro = float(df_veic_calc[df_veic_calc["Placa"] == veic_sel_calc]["Consumo (Km/L)"].iloc[0])
            custo_combustivel_calculado = (km_servico / consumo_carro) * preco_litro
            st.metric("Custo Estimado de Combustível", f"R$ {custo_combustivel_calculado:.2f}")
        else:
            st.info("Cadastre um veículo primeiro para liberar a calculadora.")

    if st.session_state.veiculos:
        st.markdown("### Frota Ativa")
        st.dataframe(pd.DataFrame(st.session_state.veiculos), use_container_width=True)
# ==============================================================================
# BLOCO 8: SEÇÕES DE ESTOQUE (ALMOXARIFADO) E PORTFÓLIO DE MÃO DE OBRA
# ==============================================================================
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
        st.dataframe(pd.DataFrame(st.session_state.materiais), use_container_width=True)

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
        st.dataframe(pd.DataFrame(st.session_state.servicos), use_container_width=True)
# ==============================================================================
# BLOCO 9: ABA DE PRECIFICAÇÃO E ENTRADA DOS DADOS OPERACIONAIS DO ORÇAMENTO
# ==============================================================================
def ler_arquivo_txt(n, d): return open(n, "r", encoding="utf-8").read() if os.path.exists(n) else d
t_pag = ler_arquivo_txt("pagamento.txt", "A combinar.")
t_gar = ler_arquivo_txt("garantia.txt", "90 dias.")
t_obs = ler_arquivo_txt("observacoes.txt", "Sem alteração estrutural.")

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
        st.info(f"Subtotal da Mão de Obra ({int(op_qtd_pontos)} pontos): R$ {mo_total_v:.2f}")

        st.markdown("### 🚘 Logística de Deslocamento do Serviço")
        if st.session_state.veiculos:
            df_v_orc = pd.DataFrame(st.session_state.veiculos)
            lista_v = [f"{v['Modelo']} ({v['Placa']})" for v in st.session_state.veiculos]
            v_sel = st.selectbox("Veículo de Atendimento:", lista_v, key="orc_p_veic")
            km_r = st.number_input("KM Estimado (Ida + Volta):", min_value=0.0, value=20.0, key="km_p")
            preco_combustivel = st.number_input("Preço do Combustível (R$/L):", min_value=0.0, value=5.90, key="prc_comb_p")
            
            idx = lista_v.index(v_sel)
            cons_carro = float(df_v_orc.iloc[idx]["Consumo (Km/L)"])
            custo_transporte = (km_r / cons_carro) * preco_combustivel
            st.caption(f"Custo de Combustível Calculado: R$ {custo_transporte:.2f}")
        else:
            custo_transporte = st.number_input("Custo de Logística Manual (R$):", min_value=0.0, value=0.0, key="des_p")
# ==============================================================================
# BLOCO 10: INCLUSÃO DE INSUMOS E FECHAMENTO DO LAYOUT DO PDF EM FOLHA CHEIA A4
# ==============================================================================
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
    rm3.metric("Logística/Combustível", f"R$ {custo_transporte:.2f}")
    rm4.metric("Impostos", f"R$ {impostos_finais:.2f}")
    rm5.metric("PREÇO FINAL", f"R$ {preco_final:.2f}", delta=f"- R$ {desc_v:.2f}" if desc_v > 0 else None)

    pdf = PDFOrcamento(logo_bytes=st.session_state.logo_bytes)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "DADOS DO CLIENTE E LOCALIDADE", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Cliente / Razao Social: {cli_sel}", ln=True)
    pdf.cell(0, 8, f"Contato Direto: {contato_disp}", ln=True)
    pdf.cell(0, 8, f"Endereco da Execucao: {endereco_disp}", ln=True)
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"ESCOPO TÉCNICO DA PROPOSTA ({int(op_qtd_pontos)} Pontos)", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(0, 8, f"{orc_descricao if orc_descricao else 'Execucao e dimensionamento de infraestrutura conforme levantamento de pontos elétricos corporativos.'}")
    pdf.ln(8)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 10, "DETALHAMENTO ANALÍTICO DE INVESTIMENTO", ln=True)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(130, 9, " Descricao da Despesa do Projeto", border=1, fill=True)
    pdf.cell(60, 9, " Valor do Investimento", border=1, fill=True, ln=True)
    
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(130, 9, f" Mao de Obra Especializada ({int(op_qtd_pontos)} pontos)", border=1)
    pdf.cell(60, 9, f" R$ {mo_total_v:.2f}", border=1, ln=True)
    
    pdf.cell(130, 9, " Fornecimento de Materiais e Insumos Homologados", border=1)
    pdf.cell(60, 9, f" R$ {total_m_lucro:.2f}", border=1, ln=True)
    
    pdf.cell(130, 9, " Despesas com Transporte, Logistica e Mobilizacao de Equipe", border=1)
    pdf.cell(60, 9, f" R$ {custo_transporte:.2f}", border=1, ln=True)
    
    pdf.cell(130, 9, " Encargos, Tributos Incidentes e Emissao de Nota Fiscal", border=1)
    pdf.cell(60, 9, f" R$ {impostos_finais:.2f}", border=1, ln=True)
    
    if desc_v > 0:
        pdf.cell(130, 9, " Desconto Comercial Especial Aplicado", border=1)
        pdf.cell(60, 9, f" - R$ {desc_v:.2f}", border=1, ln=True)
        
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(130, 9, " VALOR TOTAL DO INVESTIMENTO LIQUIDO", border=1, fill=True)
    pdf.cell(60, 9, f" R$ {preco_final:.2f}", border=1, fill=True, ln=True)
    pdf.ln(12)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, "CONDIÇÕES COMERCIAIS E TERMOS", ln=True)
    
    y_condicoes = pdf.get_y()
    pdf.set_font("Helvetica", "", 10.5)
    pdf.multi_cell(135, 6.5, f"Formas de Pagamento:\n{t_pag}\n\nGarantia dos Serviços:\n{t_gar}\n\nObservacoes Importantes:\n{t_obs}")
    
    try:
        qr_res = requests.get(URL_QRCODE, timeout=5)
        if qr_res.status_code == 200:
            with open("temp_pdf_qr.png", "wb") as f:
                f.write(qr_res.content)
            pdf.image("temp_pdf_qr.png", 158, y_condicoes, 38, 38)
            pdf.set_y(y_condicoes + 39)
            pdf.set_x(158)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.cell(38, 4, "Aprovar via WhatsApp", ln=True, align="C")
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
