# ==============================================================================
# BLOCO 1: IMPORTAÇÕES, DEPENDÊNCIAS, FUNÇÃO MONETÁRIA E ESTRUTURA BASE DO PDF
# ==============================================================================
import streamlit as st
import pandas as pd
import requests
import base64
import os
from fpdf import FPDF
from io import StringIO

st.set_page_config(
    page_title="Gestão de Orçamentos Elétricos Integrada", 
    page_icon="⚡", 
    layout="wide"
)

WHATSAPP_NUMERO = "5531995392027"
LINK_WHATSAPP = f"https://wa.me{WHATSAPP_NUMERO}"
URL_QRCODE = f"https://googleapis.com{LINK_WHATSAPP}&choe=UTF-8"

def formatar_real(valor):
    try:
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return f"R$ {valor}"

class PDFOrcamento(FPDF):
    def __init__(self, logo_bytes=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logo_bytes = logo_bytes

    def header(self):
        if self.logo_bytes:
            with open("temp_logo.png", "wb") as f:
                f.write(self.logo_bytes)
            self.image("temp_logo.png", 10, 8, 30)
            if os.path.exists("temp_logo.png"):
                os.remove("temp_logo.png")
        
        self.set_y(8)
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
        
        try:
            qr_res = requests.get(URL_QRCODE, timeout=5)
            if qr_res.status_code == 200:
                with open("temp_header_qr.png", "wb") as f:
                    f.write(qr_res.content)
                self.image("temp_header_qr.png", 172, 6, 28, 28)
                if os.path.exists("temp_header_qr.png"):
                    os.remove("temp_header_qr.png")
        except Exception:
            self.set_y(12); self.set_font("Helvetica", "B", 10); self.set_x(155)
            self.cell(45, 5, "(31) 99539-2027", ln=True, align="R")
        
        self.set_draw_color(200, 200, 200); self.set_line_width(0.3)
        self.line(10, 39, 200, 39); self.set_y(44)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(220, 220, 220)
        self.line(10, 282, 200, 282)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"FENIX ENGENHARIA E COMERCIO LTDA - Página {self.page_no()}/{{nb}}", align="C")
# ==============================================================================
# BLOCO 2: MOTOR DE COMUNICAÇÃO NUVEM E PERSISTÊNCIA VIA GITHUB API
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
            if not sobrescrever:
                conteudo_b64 = response.json().get("content")
                conteudo_txt = base64.b64decode(conteudo_b64).decode("utf-8")
                df_antigo = pd.read_csv(StringIO(conteudo_txt))
                df_final = pd.concat([df_antigo, df_novo]).drop_duplicates().reset_index(drop=True)
            else:
                df_final = df_novo
        else:
            df_final = df_novo

        conteudo_final = df_final.to_csv(index=False, encoding="utf-8")
        conteudo_b64 = base64.b64encode(conteudo_final.encode("utf-8")).decode("utf-8")
        dados_commit = {"message": f"Persistindo dados em: {nome_arquivo_csv}", "content": conteudo_b64}
        if sha: dados_commit["sha"] = sha
        
        requests.put(url, headers=headers, json=dados_commit, timeout=10)
        df_final.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
        return True
    except Exception:
        if isinstance(df_novo, pd.DataFrame):
            df_novo.to_csv(nome_arquivo_csv, index=False, encoding="utf-8")
        return False

def carregar_dados(nome_arquivo_csv):
    try:
        token = st.secrets["GITHUB_TOKEN"].strip()
        repo = st.secrets["GITHUB_REPO"].strip()
        url = f"https://github.com{repo}/contents/{nome_arquivo_csv}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            conteudo_b64 = response.json().get("content")
            conteudo_txt = base64.b64decode(conteudo_b64).decode("utf-8")
            df = pd.read_csv(StringIO(conteudo_txt))
            if "Marca" in df.columns: df = df.drop(columns=["Marca"])
            return df.to_dict(orient="records")
    except Exception: pass
    if os.path.exists(nome_arquivo_csv):
        try:
            df = pd.read_csv(nome_arquivo_csv)
            if "Marca" in df.columns: df = df.drop(columns=["Marca"])
            return df.to_dict(orient="records")
        except Exception: return []
    return []

def carregar_logo_persistida():
    try:
        token = st.secrets["GITHUB_TOKEN"].strip()
        repo = st.secrets["GITHUB_REPO"].strip()
        url = f"https://github.com{repo}/contents/logo_persistida.txt"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return base64.b64decode(base64.b64decode(res.json().get("content")).decode("utf-8"))
    except Exception: pass
    if os.path.exists("logo_local.png"):
        with open("logo_local.png", "rb") as f: return f.read()
    return None

if 'clientes' not in st.session_state: st.session_state.clientes = carregar_dados("clientes.csv")
if 'veiculos' not in st.session_state: st.session_state.veiculos = carregar_dados("veiculos.csv")
if 'materiais' not in st.session_state: st.session_state.materiais = carregar_dados("materiais.csv")
if 'servicos' not in st.session_state: st.session_state.servicos = carregar_dados("servicos.csv")
if 'materiais_orcamento' not in st.session_state: st.session_state.materiais_orcamento = []
if 'servicos_orcamento' not in st.session_state: st.session_state.servicos_orcamento = []
if 'logo_bytes' not in st.session_state: st.session_state.logo_bytes = carregar_logo_persistida()
# ==============================================================================
# BLOCO 3: CORE DO PAINEL - INTERFACE COMPLETA DA CENTRAL DE EMISSÃO DE ORÇAMENTOS
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
        salvar_no_github("logo_persistida.txt", pd.DataFrame([{"logo": logo_b64_string}]), sobrescrever=True)
        st.success("Logo persistida com sucesso!")
    if st.session_state.logo_bytes: st.image(st.session_state.logo_bytes, width=200)
with col_topo2:
    st.image(URL_QRCODE, caption="Fale Conosco no WhatsApp")

aba_orc_geral, aba_clientes, aba_mao_obra, aba_materiais, aba_veiculos = st.tabs([
    "📋 Orçamento Geral", "👥 Gestão de Clientes", "🛠️ Gestão de Serviços", "🛒 Almoxarifado", "🚚 Frota e Logística"
])

with aba_orc_geral:
    st.subheader("📋 Central Única de Emissão de Orçamentos")
    col_o1, col_o2 = st.columns(2)
    with col_o1:
        st.markdown("#### 1. Identificação Corporativa")
        if st.session_state.clientes:
            lista_cli = [c["Nome"] for c in st.session_state.clientes]
            cli_sel = st.selectbox("Selecione o Cliente Cadastrado:", lista_cli)
            dados_cli = next(item for item in st.session_state.clientes if item["Nome"] == cli_sel)
            contato_disp = dados_cli["Contato"]
            endereco_disp = dados_cli["Endereço"]
            doc_disp = dados_cli.get("Documento", "Não Cadastrado")
        else:
            cli_sel = st.text_input("Nome do Cliente (Manual):")
            doc_disp = st.text_input("CPF ou CNPJ do Cliente (Manual):")
            contato_disp = st.text_input("Contato (Manual):")
            endereco_disp = st.text_input("Endereço (Manual):")

        orc_descricao = st.text_area("Memorial Descritivo / Resumo do Escopo:")
        st.markdown("#### 🛠️ Inserir Mão de Obra do Catálogo")
        if st.session_state.servicos:
            df_serv_disp = pd.DataFrame(st.session_state.servicos)
            lista_servicos_nomes = df_serv_disp["Descrição"].dropna().tolist()
            servico_escolhido = st.selectbox("Escolha qual tipo de serviço será prestado:", lista_servicos_nomes)
            linha_filtrada = df_serv_disp[df_serv_disp["Descrição"] == servico_escolhido]
            
            unidade_medida_servico = str(linha_filtrada["Unidade"].values[0]) if "Unidade" in linha_filtrada.columns and len(linha_filtrada) > 0 else "UN"
            qtd_servico_solicitado = st.number_input(f"Especifique a quantidade ({unidade_medida_servico}):", min_value=1.0, value=1.0, step=1.0)
            servico_bonus = st.checkbox("Definir esta atividade como BÔNUS do orçamento")
            
            if st.button("➕ Adicionar Serviço ao Escopo"):
                preco_unitario_servico = float(linha_filtrada["Valor Compra Un. (R$)"].values[0])
                preco_calculado_linha = preco_unitario_servico * qtd_servico_solicitado
                st.session_state.servicos_orcamento.append({
                    "Descrição": servico_escolhido, "Quantidade": int(qtd_servico_solicitado),
                    "Unidade": unidade_medida_servico, "Total": preco_calculado_linha,
                    "Bônus": servico_bonus, "Preço Original": preco_calculado_linha
                })
                st.rerun()
        else: st.warning("Cadastre os serviços na aba correspondente primeiro.")
        if st.session_state.servicos_orcamento:
            st.dataframe(pd.DataFrame(st.session_state.servicos_orcamento), use_container_width=True)
            if st.button("🗑️ Limpar Lista de Serviços"): st.session_state.servicos_orcamento = []; st.rerun()

    with col_o2:
        st.markdown("#### 🛒 Inserir Materiais Necessários")
        if st.session_state.materiais:
            lista_m = [m["Item"] for m in st.session_state.materiais]
            m_sel = st.selectbox("Buscar material no Almoxarifado:", lista_m)
            dados_m = next(item for item in st.session_state.materiais if item["Item"] == m_sel)
            p_sugerido = dados_m.get("Preço Unitário", 0.0)
        else:
            m_sel = st.text_input("Material (Manual):")
            p_sugerido = 0.0
            
        col_mq1, col_mq2 = st.columns(2)
        m_qtd = col_mq1.number_input("Qtd Requerida:", min_value=1, value=1)
        m_preco = col_mq2.number_input("Preço Unitário de Venda (R$):", min_value=0.0, value=float(p_sugerido))
        if st.button("➕ Adicionar Material à Obra"):
            if m_sel:
                st.session_state.materiais_orcamento.append({"Material": m_sel, "Qtd": m_qtd, "Preço": m_preco, "Total": m_qtd * m_preco})
                st.rerun()
        if st.session_state.materiais_orcamento:
            st.dataframe(pd.DataFrame(st.session_state.materiais_orcamento), use_container_width=True)
            if st.button("🗑️ Limpar Lista de Materiais"): st.session_state.materiais_orcamento = []; st.rerun()

        st.markdown("#### 🚚 Logística Automotiva de Atendimento")
        custo_transporte, depreciacao_veiculo_proporcional, margem_manutencao_veiculo = 0.0, 0.0, 0.0
        if st.session_state.veiculos:
            df_v_orc = pd.DataFrame(st.session_state.veiculos)
            lista_v = [f"{v['Modelo']} ({v['Placa']})" for v in st.session_state.veiculos]
            v_sel = st.selectbox("Selecione o Veículo Alocado para a Obra:", lista_v)
            km_r = st.number_input("Distância em KM (Ida + Volta):", min_value=0.0, value=20.0)
            preco_combustivel = st.number_input("Preço do Combustível (R$/L):", min_value=0.0, value=5.90)
            margem_manutencao_veiculo = st.number_input("Margem de Custo para Manutenção de Frota (R$):", min_value=0.0, value=50.0)
            idx = lista_v.index(v_sel)
            cons_carro = float(df_v_orc.iloc[idx]["Consumo (Km/L)"])
            dep_anual = float(df_v_orc.iloc[idx]["Depreciação Anual Est."])
            custo_transporte = (km_r / cons_carro) * preco_combustivel
            depreciacao_veiculo_proporcional = (dep_anual / 365)
# ==============================================================================
# BLOCO 4: MOTOR FINANCEIRO DE CÁLCULO E CORREÇÃO DE MARGEM DE QUEBRA DO PDF (MULTI_CELL FIXED)
# ==============================================================================
        st.markdown("#### 📊 Configurações Comerciais")
        imposto_pc = st.number_input("Porcentagem de Imposto para Diluir na Mão de Obra (%):", min_value=0.0, value=6.0)
        desconto_comercial_pc = st.number_input("Desconto Comercial Concedido (%):", min_value=0.0, value=0.0, step=1.0)
        # CORREÇÃO CRUCIAL SANEADA: Atribuição limpa removendo de vez o termo corrompido que causava quebra de sintaxe
        desconto_avista_pc = st.number_input("Desconto Adicional para Pagamento À VISTA (%):", min_value=0.0, value=10.0, step=1.0)

    custo_bruto_materials = sum([item["Total"] for item in st.session_state.materiais_orcamento])
    custo_bruto_servicos_total = sum([item["Total"] for item in st.session_state.servicos_orcamento])
    total_custos_frota_diluiveis = custo_transporte + depreciacao_veiculo_proporcional + margem_manutencao_veiculo
    valor_imposto_real = (custo_bruto_servicos_total + custo_bruto_materials + custo_transporte) * (imposto_pc / 100)
    total_mao_obra_com_encargos = custo_bruto_servicos_total + valor_imposto_real + total_custos_frota_diluiveis
    fator_proporcional = total_mao_obra_com_encargos / custo_bruto_servicos_total if custo_bruto_servicos_total > 0 else 1.0
    
    custo_final_servicos_normais_com_imposto = sum([item["Total"] for item in st.session_state.servicos_orcamento if not item["Bônus"]]) * fator_proporcional
    valor_total_bonus_exibicao = sum([item["Total"] for item in st.session_state.servicos_orcamento if item["Bônus"]]) * fator_proporcional
    valor_composto_mao_de_obra_total = custo_final_servicos_normais_com_imposto + valor_total_bonus_exibicao
    
    subtotal_faturavel_base = custo_final_servicos_normais_com_imposto + custo_bruto_materials
    valor_desconto_dinheiro = subtotal_faturavel_base * (desconto_comercial_pc / 100)
    preco_final_cheio = subtotal_faturavel_base - valor_desconto_dinheiro
    if preco_final_cheio < 0: preco_final_cheio = 0.0
    
    preco_final_avista = preco_final_cheio * (1 - (desconto_avista_pc / 100))
    preco_final_parcelado_com_taxa = preco_final_cheio * 1.08
    valor_parcela_10x = preco_final_parcelado_com_taxa / 10

    st.markdown("---"); st.markdown("### 📊 Painel Geral de Resumo")
    rm1, rm2, rm3 = st.columns(3)
    rm1.metric("Mão de Obra Unificada (Normais + Bônus)", formatar_real(valor_composto_mao_de_obra_total))
    rm2.metric("Materiais Coletados", formatar_real(custo_bruto_materials))
    rm3.metric("VALOR TOTAL FINAL COBRADO", formatar_real(preco_final_cheio), delta=f"- {formatar_real(valor_desconto_dinheiro)}" if valor_desconto_dinheiro > 0 else None)

    pdf = PDFOrcamento(logo_bytes=st.session_state.logo_bytes)
    pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 12); pdf.cell(0, 10, "DADOS DO CLIENTE E LOCALIDADE", ln=True); pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Cliente / Razao Social: {cli_sel}", ln=True); pdf.cell(0, 8, f"CPF / CNPJ: {doc_disp}", ln=True)
    pdf.cell(0, 8, f"Contato Direto: {contato_disp}", ln=True); pdf.cell(0, 8, f"Endereco da Execucao: {endereco_disp}", ln=True); pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12); pdf.cell(0, 10, "ESCOPO TÉCNICO DA PROPOSTA", ln=True); pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(190, 8.5, f"{orc_descricao if orc_descricao else 'Execucao conforme escopo acordado.'}"); pdf.ln(8)

    pdf.set_font("Helvetica", "B", 12); pdf.cell(0, 10, "DETALHAMENTO NOMINAL DOS ITENS DO PROJETO", ln=True)
    pdf.set_font("Helvetica", "B", 11); pdf.cell(0, 8, "SERVIÇOS DE MÃO DE OBRA CONTRATADOS:", ln=True); pdf.set_font("Helvetica", "", 11)
    for serv in st.session_state.servicos_orcamento:
        if not serv["Bônus"]:
            valor_serv_com_todos_custos = serv["Total"] * fator_proporcional
            # CORREÇÃO DA MARGEM: Ajustado de cell para multi_cell com largura máxima fixa de 190 para forçar quebra de linha nos serviços longos
            pdf.multi_cell(190, 7, f"-> {serv['Descrição']} | Qtd: {serv['Quantidade']} {serv.get('Unidade', 'UN')} | Investimento: {formatar_real(valor_serv_com_todos_custos)}")
    
    pdf.ln(4); pdf.set_font("Helvetica", "B", 11); pdf.cell(0, 8, "ATIVIDADES CONCEDIDAS COMO BÔNUS (CORTESIA):", ln=True); pdf.set_font("Helvetica", "", 11)
    if valor_total_bonus_exibicao > 0:
        for serv in st.session_state.servicos_orcamento:
            if serv["Bônus"]:
                valor_bonus_inflado_linha = serv["Total"] * fator_proporcional
                pdf.multi_cell(190, 7, f"-> {serv['Descrição']} | Qtd: {serv['Quantidade']} {serv.get('Unidade', 'UN')} | Valor Real com Diluicao: {formatar_real(valor_bonus_inflado_linha)}")
    else: pdf.cell(0, 8, "Nenhuma atividade de bonus registrada para este projeto.", ln=True)
    
    pdf.ln(4); pdf.set_font("Helvetica", "B", 11); pdf.cell(0, 8, "MATERIAIS E INSUMOS COMPLEMENTARES:", ln=True); pdf.set_font("Helvetica", "", 11)
    for mat in st.session_state.materiais_orcamento:
        # CORREÇÃO DA MARGEM: Alterado para multi_cell com tamanho 190 fixo eliminando o corte na borda direita das tabelas de insumos
        pdf.multi_cell(190, 7, f"-> {mat['Material']} | Qtd: {mat['Qtd']} UN | Preco Unitario: {formatar_real(mat['Preço'])} | Total: {formatar_real(mat['Total'])}")
    
    pdf.ln(8); pdf.set_font("Helvetica", "B", 12); pdf.cell(0, 10, "COMPOSIÇÃO FINANCEIRA DO PROJETO", ln=True); pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Mao de Obra: {formatar_real(valor_composto_mao_de_obra_total)}", ln=True); pdf.cell(0, 8, f"Material: {formatar_real(custo_bruto_materials)}", ln=True)
    pdf.cell(0, 8, f"Bonus: - {formatar_real(valor_total_bonus_exibicao)}", ln=True); pdf.cell(0, 8, f"Desconto: - {formatar_real(valor_desconto_dinheiro)}", ln=True)
    pdf.cell(0, 8, f"Valor Total: {formatar_real(preco_final_cheio)}", ln=True)

    pdf.ln(4); pdf.set_font("Helvetica", "B", 12); pdf.cell(0, 10, f"valor total do investimento: {formatar_real(preco_final_cheio)}", ln=True); pdf.ln(10)
    pdf.cell(0, 10, "CONDIÇÕES DE PAGAMENTO", ln=True); y_condicoes = pdf.get_y(); pdf.set_font("Helvetica", "B", 10.5); pdf.cell(135, 7, "Formas de Pagamento:", ln=True); pdf.set_font("Helvetica", "", 10.5)
    pdf.multi_cell(135, 7, f"OPCAO 01 - A VISTA COM DESCONTO ESPECIAL:\nValor total com desconto aplicado: {formatar_real(preco_final_avista)}\n\nOPCAO 02 - PARCELAMENTO FACILITADO CORPORATIVO:\nPagamento em ate 10x mensais fixas de {formatar_real(valor_parcela_10x)}\nValor total final parcelado: {formatar_real(preco_final_parcelado_com_taxa)}")
    
    def ler_arquivo_txt(n, d): return open(n, "r", encoding="utf-8").read() if os.path.exists(n) else d
    t_gar = ler_arquivo_txt("garantia.txt", "90 dias."); t_obs = ler_arquivo_txt("observacoes.txt", "Sem alteração estrutural.")
    pdf.ln(4); pdf.set_font("Helvetica", "B", 10.5); pdf.cell(135, 7, "Garantia dos Servicos:", ln=True); pdf.set_font("Helvetica", "", 10.5); pdf.multi_cell(135, 7, f"{t_gar}")
    pdf.ln(4); pdf.set_font("Helvetica", "B", 10.5); pdf.cell(135, 7, "Observacoes Importantes:", ln=True); pdf.set_font("Helvetica", "", 10.5); pdf.multi_cell(135, 7, f"{t_obs}")
    
    try:
        qr_res = requests.get(URL_QRCODE, timeout=5)
        if qr_res.status_code == 200:
            with open("temp_pdf_qr.png", "wb") as f: f.write(qr_res.content)
            pdf.image("temp_pdf_qr.png", 158, y_condicoes, 38, 38); pdf.set_y(y_condicoes + 39); pdf.set_x(158); pdf.set_font("Helvetica", "B", 8.5); pdf.cell(38, 5, "Aprovar via WhatsApp", ln=True, align="C")
            if os.path.exists("temp_pdf_qr.png"): os.remove("temp_pdf_qr.png")
    except Exception: pass
    
    pdf_output = pdf.output(); st.markdown("### 🖨️ Ações de Envio"); col_d1, col_d2 = st.columns(2)
    with col_d1: st.download_button(label="📥 Baixar Orçamento Customizado em PDF", data=bytes(pdf_output), file_name=f"Orcamento_Fenix_{cli_sel.replace(' ', '_')}.pdf", mime="application/pdf")
    with col_d2: st.link_button("💬 Enviar via WhatsApp", LINK_WHATSAPP)
# ==============================================================================
# BLOCO 5: RETAGUARDA OPERACIONAL - CADASTROS CRUD COM IDENTIFICAÇÃO STR COMPATÍVEL
# ==============================================================================
def renderizar_crud(nome_aba, s_key, nome_arquivo_csv, campos_lista, dict_vazio):
    with nome_aba:
        st.subheader(f"⚙️ Gerenciador de Banco de Dados: {nome_arquivo_csv}")
        dados_atuais = carregar_dados(nome_arquivo_csv)
        df_crud = pd.DataFrame(dados_atuais) if dados_atuais else pd.DataFrame(columns=campos_lista)
        chave_busca = campos_lista[0] if isinstance(campos_lista, list) else campos_lista
        st.markdown("#### ➕ Adicionar / Modificar Registro")
        
        if nome_arquivo_csv == "materiais.csv":
            with st.form("form_material_custom_lucro", clear_on_submit=True):
                m_item = st.text_input("Item (Nome do Material):")
                m_unidade = st.text_input("Unidade de Medida:", value="UN")
                m_custo = st.number_input("Preço de Custo (R$):", min_value=0.0, value=0.0)
                m_lucro_pc = st.number_input("Margem de Lucro Desejada (%):", min_value=0.0, value=30.0)
                if st.form_submit_button("💾 Catalogar Produto com Lucro"):
                    if m_item:
                        preco_venda_calculado = m_custo * (1 + (m_lucro_pc / 100))
                        novo_reg_mat = {"Item": m_item, "Unidade": m_unidade, "Preço de Custo": m_custo, "Margem de Lucro (%)": m_lucro_pc, "Preço Unitário": round(preco_venda_calculado, 2)}
                        df_novo_registro = pd.DataFrame([novo_reg_mat])
                        if not df_crud.empty and "Item" in df_crud.columns: df_crud = df_crud[df_crud["Item"] != m_item]
                        df_final_salvar = pd.concat([df_crud, df_novo_registro]).reset_index(drop=True)
                        salvar_no_github("materiais.csv", df_final_salvar, sobrescrever=True)
                        st.success(f"Produto salvo! Preço de venda gerado: {formatar_real(preco_venda_calculado)}")
                        st.session_state[s_key] = carregar_dados(nome_arquivo_csv); st.rerun()
        else:
            with st.form(f"form_crud_{s_key}", clear_on_submit=True):
                inputs_coletados = {}
                for campo in campos_lista:
                    if "Valor" in campo or "Preço" in campo or "Consumo" in campo or "Depreciação" in campo:
                        inputs_coletados[campo] = st.number_input(f"{campo}:", min_value=0.0, value=0.0, key=f"in_{s_key}_{campo}")
                    else: inputs_coletados[campo] = st.text_input(f"{campo}:", key=f"in_{s_key}_{campo}")
                if st.form_submit_button("💾 Arquivar Registro no GitHub"):
                    if inputs_coletados[chave_busca]:
                        df_novo_registro = pd.DataFrame([inputs_coletados])
                        if not df_crud.empty and chave_busca in df_crud.columns: df_crud = df_crud[df_crud[df_crud[chave_busca] != inputs_coletados[chave_busca]]]
                        df_final_salvar = pd.concat([df_crud, df_novo_registro]).reset_index(drop=True)
                        salvar_no_github(nome_arquivo_csv, df_final_salvar, sobrescrever=True)
                        st.success("Dados processados e salvos com sucesso!")
                        st.session_state[s_key] = carregar_dados(nome_arquivo_csv); st.rerun()

        if dados_atuais:
            st.markdown("#### 📋 Registros Armazenados")
            for i, reg in enumerate(dados_atuais):
                col_reg, col_btn = st.columns(2)
                col_reg.write(f"🔹 **{reg[chave_busca]}** - { {k:v for k,v in reg.items() if k != chave_busca} }")
                if col_btn.button("🗑️ Excluir", key=f"del_{s_key}_{i}"):
                    df_filtrado_exclusao = pd.DataFrame(dados_atuais).drop(i).reset_index(drop=True)
                    salvar_no_github(nome_arquivo_csv, df_filtrado_exclusao, sobrescrever=True)
                    st.success("Registro removido do repositório!")
                    st.session_state[s_key] = carregar_dados(nome_arquivo_csv); st.rerun()

renderizar_crud(aba_clientes, "clientes", "clientes.csv", ["Nome", "Documento", "Contato", "Endereço"], {})
renderizar_crud(aba_mao_obra, "servicos", "servicos.csv", ["Descrição", "Unidade", "Valor Compra Un. (R$)"], {})
renderizar_crud(aba_materiais, "materiais", "materiais.csv", ["Item", "Unidade", "Preço Unitário"], {})
renderizar_crud(aba_veiculos, "veiculos", "veiculos.csv", ["Modelo", "Placa", "Consumo (Km/L)", "Depreciação Anual Est."], {})
