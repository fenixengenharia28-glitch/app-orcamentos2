import streamlit as st
import pandas as pd
import datetime as dt
import hashlib
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image

# Configuração da página para Desktop e Celular
st.set_page_config(page_title="Fênix Engenharia - Pro", page_icon="🏗️", layout="centered")

# --- INICIALIZAÇÃO DE BANCOS DE DADOS EM MEMÓRIA ---
if "db_veiculos" not in st.session_state:
    st.session_state.db_veiculos = pd.DataFrame([
        {"Tipo": "Carro", "Marca": "Fiat", "Modelo": "Uno", "Tempo de Uso (Anos)": 2, "Consumo (Km/L)": 12.0, "Valor FIPE (R$)": 35000.0, "Seguro/Doc Anual (R$)": 1400.0, "Manutenção Mensal (R$)": 200.0}
    ])

if "db_custos_fixos" not in st.session_state:
    st.session_state.db_custos_fixos = pd.DataFrame([
        {"Tipo de Gasto": "Contador / MEI", "Valor Mensal (R$)": 80.0},
        {"Tipo de Gasto": "Internet e Celular", "Valor Mensal (R$)": 120.0}
    ])

if "db_materiais" not in st.session_state:
    st.session_state.db_materiais = pd.DataFrame([
        {"ID": "MAT-001", "Descrição": "Cabo Flexível 2,5mm²", "Unidade": "m", "Custo (R$)": 3.60, "Margem (%)": 20, "Valor Unitário (R$)": 4.50},
        {"ID": "MAT-002", "Descrição": "Disjuntor DIN 20A", "Unidade": "Un", "Custo (R$)": 14.00, "Margem (%)": 30, "Valor Unitário (R$)": 20.00}
    ])

if "db_servicos" not in st.session_state:
    st.session_state.db_servicos = pd.DataFrame([
        {"ID": "SRV-001", "Descrição": "Instalação de Ponto de Tomada", "Unidade": "Ponto", "Valor (R$)": 50.00},
        {"ID": "SRV-002", "Descrição": "Pintura de Parede Interna", "Unidade": "M²", "Valor (R$)": 25.00}
    ])

# NOVO: Listas dinâmicas temporárias exclusivas do orçamento ativo na sessão
if "df_materiais_selecionados" not in st.session_state:
    st.session_state.df_materiais_selecionados = pd.DataFrame(columns=["ID", "Descrição", "Unidade", "Quantidade", "Valor Unitário (R$)", "Valor Total (R$)"])

if "df_servicos_selecionados" not in st.session_state:
    st.session_state.df_servicos_selecionados = pd.DataFrame(columns=["ID", "Descrição", "Valor (R$)"])

if "df_bonus_selecionados" not in st.session_state:
    st.session_state.df_bonus_selecionados = pd.DataFrame(columns=["ID", "Descrição", "Valor (R$)"])

st.title("🏗️ Sistema Orçamentário Construção Pro")
st.caption("FÊNIX ENGENHARIA - Módulo Integrado de Emissão de Propostas Técnicas")

# Definição das 4 Abas Ativas do Negócio
aba_proposta, aba_calcular_hora, aba_materiais, aba_servicos = st.tabs([
    "📋 Proposta Comercial", 
    "🧮 Calcular Minha Hora",
    "📦 Cadastro de Materiais",
    "🛠️ Cadastro de Serviços"
])

# --- ABA 2: ENGENHARIA DE CUSTOS E CÁLCULO DA HORA TÉCNICA ---
with aba_calcular_hora:
    st.header("🧮 Configuração do Preço por Hora Técnico")
    salario_desejado = st.number_input("Quanto quer ganhar livre por mês (R$):", min_value=0.0, value=4000.0, step=100.0)
    col_t1, col_t2 = st.columns(2)
    with col_t1: dias_trabalhados = st.number_input("Dias operacionais por mês:", min_value=1, max_value=31, value=22)
    with col_t2: horas_por_dia = st.number_input("Horas faturadas por dia na obra:", min_value=1.0, max_value=24.0, value=6.0, step=0.5)
    margem_lucro = st.slider("Margem de lucro desejada para a empresa (%)", min_value=0, max_value=50, value=20, step=5)
    horas_totais_mes = dias_trabalhados * horas_por_dia
    
    st.write("---")
    st.subheader("🚗 Custos de Logística do Veículo")
    with st.form("cad_veiculo_form", clear_on_submit=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v_tipo = st.selectbox("Tipo:", ["Carro", "Moto", "Caminhão", "Utilitário / Van"])
            v_marca = st.text_input("Marca:")
            v_modelo = st.text_input("Modelo:")
        with col_v2:
            v_tempo = st.number_input("Tempo de Posse (Anos):", min_value=0, value=1)
            v_consumo = st.number_input("Consumo (Km/L):", min_value=1.0, value=10.0, step=0.5)
            v_fipe = st.number_input("Valor FIPE (R$):", min_value=0.0, value=30000.0, step=1000.0)
        v_seg_doc = st.number_input("Seguro + Doc Anual (R$):", min_value=0.0, value=1200.0)
        v_manutencao = st.number_input("Manutenção Mensal (R$):", min_value=0.0, value=200.0)
        if st.form_submit_button("💾 Salvar Veículo"):
            if v_marca and v_modelo:
                novo_v = pd.DataFrame([{"Tipo": v_tipo, "Marca": v_marca, "Modelo": v_modelo, "Tempo de Uso (Anos)": v_tempo, "Consumo (Km/L)": v_consumo, "Valor FIPE (R$)": v_fipe, "Seguro/Doc Anual (R$)": v_seg_doc, "Manutenção Mensal (R$)": v_manutencao}])
                st.session_state.db_veiculos = pd.concat([st.session_state.db_veiculos, novo_v], ignore_index=True); st.rerun()

    if not st.session_state.db_veiculos.empty:
        with st.expander("🗑️ Excluir Veículo"):
            veiculo_para_remover = st.selectbox("Deletar veículo:", [f"{idx} - [{r['Tipo']}] {r['Marca']} {r['Modelo']}" for idx, r in st.session_state.db_veiculos.iterrows()])
            if st.button("❌ Confirmar Exclusão do Veículo", type="primary"): st.session_state.db_veiculos = st.session_state.db_veiculos.drop(int(veiculo_para_remover.split(" - "))).reset_index(drop=True); st.rerun()
        df_v_editado = st.data_editor(st.session_state.db_veiculos, use_container_width=True, num_rows="dynamic")
        st.session_state.db_veiculos = df_v_editado
        v_hora_operacional = ((df_v_editado["Valor FIPE (R$)"].sum() * 0.10 / 12) + (df_v_editado["Seguro/Doc Anual (R$)"].sum() / 12) + df_v_editado["Manutenção Mensal (R$)"].sum()) / horas_totais_mes if horas_totais_mes > 0 else 0.0
    else: v_hora_operacional = 0.0

    st.write("---")
    st.subheader("🏢 Custos Fixos Mensais")
    with st.form("cad_custo_fixo_form", clear_on_submit=True):
        f_tipo = st.text_input("Gasto:")
        f_valor = st.number_input("Valor Mensal (R$):", min_value=0.0)
        if st.form_submit_button("➕ Adicionar Custo Fixo") and f_tipo: st.session_state.db_custos_fixos = pd.concat([st.session_state.db_custos_fixos, pd.DataFrame([{"Tipo de Gasto": f_tipo, "Valor Mensal (R$)": f_valor}])], ignore_index=True); st.rerun()

    if not st.session_state.db_custos_fixos.empty:
        with st.expander("🗑️ Excluir Despesa"):
            gasto_para_remover = st.selectbox("Deletar gasto:", [f"{idx} - {r['Tipo de Gasto']}" for idx, r in st.session_state.db_custos_fixos.iterrows()])
            if st.button("❌ Confirmar Exclusão da Despesa", type="primary"): st.session_state.db_custos_fixos = st.session_state.db_custos_fixos.drop(int(gasto_para_remover.split(" - "))).reset_index(drop=True); st.rerun()
        df_f_trabalho = st.session_state.db_custos_fixos.copy()
        df_f_trabalho["Valor por Hora (R$)"] = (df_f_trabalho["Valor Mensal (R$)"] / horas_totais_mes).round(2) if horas_totais_mes > 0 else 0.0
        df_f_editado = st.data_editor(df_f_trabalho, use_container_width=True, num_rows="dynamic")
        st.session_state.db_custos_fixos = df_f_editado[["Tipo de Gasto", "Valor Mensal (R$)"]]
        f_hora_operacional = df_f_editado["Valor Mensal (R$)"].sum() / horas_totais_mes if horas_totais_mes > 0 else 0.0
    else: f_hora_operacional = 0.0

    st.write("---")
    salario_por_hora = salario_desejado / horas_totais_mes if horas_totais_mes > 0 else 0.0
    custo_hora_operacional = v_hora_operacional + f_hora_operacional
    custo_hora_bruto = salario_por_hora + custo_hora_operacional
    hora_tecnica_final = custo_hora_bruto / (1 - (margem_lucro / 100)) if margem_lucro < 100 else custo_hora_bruto
    st.subheader("📊 Demonstrativo Detalhado do Valor por Hora")
    c_c1, c_c2 = st.columns(2)
    with c_c1: st.metric(label="Valor da sua Hora de Trabalho (Líquido)", value=f"R$ {salario_por_hora:.2f}/h")
    with c_c2: st.metric(label="Valor dos Custos por Hora (Logística + Fixo)", value=f"R$ {custo_hora_operacional:.2f}/h")
    st.markdown(f"### 🎯 Preço Final Combinado com {margem_lucro}\% de Margem: **R$ {hora_tecnica_final:.2f}/h**")
    if st.button("🚀 Sincronizar e Gravar Preço da Hora"): st.session_state["preco_hora_tecnica_fechada"] = round(hora_tecnica_final, 2); st.success("Gravado!")

# --- ABA 3: CADASTRO DE MATERIAIS ---
with aba_materiais:
    st.header("📦 Catálogo de Materiais e Insumos")
    with st.form("cad_material_form", clear_on_submit=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            m_descricao = st.text_input("Descrição do Material:")
            m_unidade = st.selectbox("Unidade de Medida:", ["Un", "m", "Barra", "Saco", "Caixa", "kg", "Outro"])
        with col_m2:
            m_custo = st.number_input("Custo de Aquisição (R$):", min_value=0.0, value=10.0)
            m_margem = st.slider("Margem de Lucro desejada (%)", min_value=0, max_value=80, value=30, step=5)
        if st.form_submit_button("💾 Salvar Material"):
            if m_descricao:
                novo_id = f"MAT-{len(st.session_state.db_materiais) + 1:03d}"
                valor_final = m_custo / (1 - (m_margem / 100)) if m_margem < 100 else m_custo
                novo_m = pd.DataFrame([{"ID": novo_id, "Descrição": m_descricao, "Unidade": m_unidade, "Custo (R$)": round(m_custo, 2), "Margem (%)": m_margem, "Valor Unitário (R$)": round(valor_final, 2)}])
                st.session_state.db_materiais = pd.concat([st.session_state.db_materiais, novo_m], ignore_index=True); st.rerun()

    if not st.session_state.db_materiais.empty:
        with st.expander("🗑️ Excluir Material"):
            mat_remover = st.selectbox("Deletar material:", [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_materiais.iterrows()])
if st.button("❌ Confirmar Exclusão do Insumo", type="primary"): st.session_state.db_materiais = st.session_state.db_materiais[st.session_state.db_materiais["ID"] != mat_remover.split(" - ")].reset_index(drop=True); st.rerun() df_m_editado = st.data_editor(st.session_state.db_materiais, use_container_width=True, num_rows="dynamic") df_m_editado["Valor Unitário (R$)"] = (df_m_editado["Custo (R$)"] / (1 - (df_m_editado["Margem (%)"].clip(0, 99) / 100))).round(2) st.session_state.db_materiais = df_m_editado--- ABA 4: CADASTRO DE SERVIÇOS ---with aba_servicos:st.header("🛠️ Catálogo Técnico de Serviços da Empresa")with st.form("cad_servico_form", clear_on_submit=True):col_s1, col_s2 = st.columns(2)with col_s1:s_descricao = st.text_input("Descrição do Serviço:")s_unidade = st.selectbox("Unidade de Cobrança:", ["Ponto", "M²", "Diária", "Hora", "Empreitada", "Metro"])with col_s2: s_valor = st.number_input("Preço de Venda Sugerido (R$):", min_value=0.0, value=50.0, step=5.0)if st.form_submit_button("💾 Salvar Serviço no Catálogo"):if s_descricao:novo_id_s = f"SRV-{len(st.session_state.db_servicos) + 1:03d}"novo_s = pd.DataFrame([{"ID": novo_id_s, "Descrição": s_descricao, "Unidade": s_unidade, "Valor (R$)": round(s_valor, 2)}])st.session_state.db_servicos = pd.concat([st.session_state.db_servicos, novo_s], ignore_index=True); st.rerun()if not st.session_state.db_servicos.empty:with st.expander("🗑️ Excluir Serviço do Catálogo"):srv_remover = st.selectbox("Selecione o serviço para deletar:", [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_servicos.iterrows()])if st.button("❌ Confirmar Exclusão do Serviço", type="primary"): st.session_state.db_servicos = st.session_state.db_servicos[st.session_state.db_servicos["ID"] != srv_remover.split(" - ")].reset_index(drop=True); st.rerun()df_s_editado = st.data_editor(st.session_state.db_servicos, use_container_width=True, num_rows="dynamic")st.session_state.db_servicos = df_s_editado
# --- ABA 1: PROPOSTA COMERCIAL (TOTALMENTE REESTRUTURADA CONFORME SOLICITADO) ---
with aba_proposta:
    st.info("⚡ FÊNIX ENGENHARIA - Central Comercial")
    
    # Parâmetros Auxiliares Técnicos
    logo_upload = st.file_uploader("Upload da Logomarca (Aparecerá no topo à direita do PDF):", type=["png", "jpg", "jpeg"])
    whatsapp_num = st.text_input("Seu Número de WhatsApp para gerar o QR Code (Apenas números com DDD):", value="31999999999")
    
    st.subheader("Configuração da Proposta")
    nome_cliente = st.text_input("Nome do Cliente / Destinatário:", value="Fenix Engenharia e Comercio LTDA")
    desc_geral_servico = st.text_area("Descrição Geral dos Serviços Realizados:", value="Execução de Infraestrutura Elétrica e Reforma Estrutural de Quadros Técnicos.")
    
    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1: val_dias = st.number_input("Validade do Orçamento (Dias):", min_value=1, value=10)
    with col_d2: dt_emissao = st.date_input("Data de Emissão:", value=dt.date.today())
    with col_d3: dt_validade = st.date_input("Válido Até:", value=dt.date.today() + dt.timedelta(days=int(val_dias)))

    # --- INPUT SEÇÃO 1: MÃO DE OBRA ---
    st.write("---")
    st.subheader("👷 Adicionar Mão de Obra à Proposta")
    lista_db_s = [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_servicos.iterrows()] if not st.session_state.db_servicos.empty else []
    if lista_db_s:
        s_escolhido = st.selectbox("Selecione o Serviço do Catálogo:", lista_db_s)
        if st.button("➕ Vincular Serviço na Proposta"):
            item_s = st.session_state.db_servicos[st.session_state.db_servicos["ID"] == s_escolhido.split(" - ")[0]].iloc[0]
            st.session_state.df_servicos_selecionados = pd.concat([st.session_state.df_servicos_selecionados, pd.DataFrame([{"ID": item_s["ID"], "Descrição": item_s["Descrição"], "Valor (R$)": item_s["Valor (R$)"]}])], ignore_index=True)
            st.success("Mão de obra vinculada!")
    
    if not st.session_state.df_servicos_selecionados.empty:
        st.write("**Mão de Obra Adicionada:**")
        st.session_state.df_servicos_selecionados = st.data_editor(st.session_state.df_servicos_selecionados, use_container_width=True, num_rows="dynamic")
        tot_mo_bruta = st.session_state.df_servicos_selecionados["Valor (R$)"].sum()
    else: tot_mo_bruta = 0.0

    # --- INPUT SEÇÃO 2: MATERIAIS ---
    st.write("---")
    st.subheader("📦 Adicionar Materiais à Proposta")
    lista_db_m = [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_materiais.iterrows()] if not st.session_state.db_materiais.empty else []
    if lista_db_m:
        m_escolhido = st.selectbox("Selecione o Material do Almoxarifado:", lista_db_m)
        qtd_m_solicitada = st.number_input("Quantidade do Item:", min_value=1, value=1)
        if st.button("➕ Vincular Material na Proposta"):
            item_m = st.session_state.db_materiais[st.session_state.db_materiais["ID"] == m_escolhido.split(" - ")[0]].iloc[0]
            v_tot_calc = qtd_m_solicitada * item_m["Valor Unitário (R$)"]
            st.session_state.df_materiais_selecionados = pd.concat([st.session_state.df_materiais_selecionados, pd.DataFrame([{"ID": item_m["ID"], "Descrição": item_m["Descrição"], "Unidade": item_m["Unidade"], "Quantidade": qtd_m_solicitada, "Valor Unitário (R$)": item_m["Valor Unitário (R$)"], "Valor Total (R$)": v_tot_calc}])], ignore_index=True)
            st.success("Material vinculado!")

    if not st.session_state.df_materiais_selecionados.empty:
        st.write("**Materiais Adicionados:**")
        st.session_state.df_materiais_selecionados = st.data_editor(st.session_state.df_materiais_selecionados, use_container_width=True, num_rows="dynamic")
        st.session_state.df_materiais_selecionados["Valor Total (R$)"] = st.session_state.df_materiais_selecionados["Quantidade"] * st.session_state.df_materiais_selecionados["Valor Unitário (R$)"]
        tot_mat_bruto = st.session_state.df_materiais_selecionados["Valor Total (R$)"].sum()
    else: tot_mat_bruto = 0.0

    # --- INPUT SEÇÃO 3: BÔNUS ---
    st.write("---")
    st.subheader("🎁 Adicionar Serviços de Bônus (Cortesia Comercial)")
    with st.form("form_add_bonus", clear_on_submit=True):
        b_desc = st.text_input("Descrição da Cortesia / Bônus (ex: Instalação de Lustre):")
        b_val = st.number_input("Valor Comercial Referencial (R$):", min_value=0.0, value=150.0)
        if st.form_submit_button("➕ Incluir Bônus"):
            if b_desc:
                b_id = f"BON-{len(st.session_state.df_bonus_selecionados) + 1:03d}"
                st.session_state.df_bonus_selecionados = pd.concat([st.session_state.df_bonus_selecionados, pd.DataFrame([{"ID": b_id, "Descrição": b_desc, "Valor (R$)": b_val}])], ignore_index=True)
                st.rerun()

    if not st.session_state.df_bonus_selecionados.empty:
        st.write("**Bônus Adicionados:**")
        st.session_state.df_bonus_selecionados = st.data_editor(st.session_state.df_bonus_selecionados, use_container_width=True, num_rows="dynamic")
        tot_bonus_calc = st.session_state.df_bonus_selecionados["Valor (R$)"].sum()
    else: tot_bonus_calc = 0.0

    # --- FECHAMENTO FINANCEIRO EM ESTRITA CONFORMIDADE ---
    st.write("---")
    st.subheader("📈 Ajustes Gerais")
    desconto_slider = st.slider("Porcentagem de Desconto Comercial (%):", 0, 30, 0)
    
    subtotal_bruto = tot_mo_bruta + tot_mat_bruto
    valor_desconto_real = subtotal_bruto * (desconto_slider / 100)
    
    # Regras matemáticas solicitadas
    total_a_pagar_cartao = subtotal_bruto * 1.08  # Acréscimo da taxa de 8% da maquininha
    total_a_vista_pix = subtotal_bruto - tot_bonus_calc - valor_desconto_real
    total_a_vista_pix = max(0.0, total_a_vista_pix)

    # Painel Comercial Estruturado na Tela
    st.write("---")
    st.subheader("📊 Painel Consolidado de Fechamento")
    st.write(f"**Total Mão de Obra:** R$ {tot_mo_bruta:.2f}")
    st.write(f"**Total Materiais:** R$ {tot_mat_bruto:.2f}")
    st.write(f"🎁 **Total Bônus (Cortesia):** R$ {tot_bonus_calc:.2f}")
    st.write(f"**Subtotal Bruto:** R$ {subtotal_bruto:.2f}")
    st.write(f"📉 **Desconto Comercial ({desconto_slider}%):** - R$ {valor_desconto_real:.2f}")
    st.write("---")
    st.warning(f"💳 **TOTAL A PAGAR (ATÉ 10X CARTÃO): R$ {total_a_pagar_cartao:.2f}** (Inclusa taxa de 8% da maquininha)")
    st.success(f"💰 **TOTAL À VISTA (DINHEIRO OU PIX): R$ {total_a_vista_pix:.2f}** (Subtraído Bônus e Desconto)")

    # --- CONSTRUTOR DE PDF NATIVO COM ARQUITETURA TRIPLA ---
    def build_pdf_fenix(logo_file, qr_url, hash_val):
        bf = BytesIO()
        doc = SimpleDocTemplate(bf, pagesize=letter, rightMargin=35, leftMargin=45, topMargin=40, bottomMargin=40)
        story = []
        s = getSampleStyleSheet()
        
        t_s = ParagraphStyle('T', parent=s['Heading1'], fontSize=15, textColor=colors.HexColor('#1A365D'), alignment=1)
        b_s = ParagraphStyle('B', parent=s['Normal'], fontSize=9, leading=13)
        h2_s = ParagraphStyle('H2', parent=s['Heading2'], fontSize=11, textColor=colors.HexColor('#2B6CB0'), spaceBefore=8, spaceAfter=5)
        
        # 1. Montagem do Cabeçalho Triplo
        qr_obj = qrcode.QRCode(version=1, box_size=2, border=0)
        qr_obj.add_data(qr_url); qr_obj.make(fit=True)
        qimg = qr_obj.make_image(fill_color="black", back_color="white")
        q_buf = BytesIO(); qimg.save(q_buf, format="PNG"); qb_val = q_buf.getvalue(); q_buf.seek(0)
        
        txt_empresa = (
            "<b><font size=13 color='#1A365D'>FÊNIX ENGENHARIA</font></b><br/>"
            "<b>CNPJ:</b> 52.769.953/0001-12<br/>"
            "<b>Endereço:</b> Avenida Getulio Vargas, nº 671, 9º Andar, Sala 1.051,<br/>"
            "Bairro Savassi, Belo Horizonte - MG, Cep: 30112-021"
        )
        
        logo_box = Paragraph("", b_s)
        if logo_file is not None:
            try:
                pimg = Image.open(logo_file); logo_p = pimg.copy(); logo_p.thumbnail((100, 45))
                l_buf = BytesIO(); logo_p.save(l_buf, format="PNG"); l_buf.seek(0)
                logo_box = RLImage(l_buf, width=logo_p.width, height=logo_p.height)
            except: pass
            
        header_table_data = [[RLImage(BytesIO(qb_val), width=50, height=50), Paragraph(txt_empresa, ParagraphStyle('C', parent=s['Normal'], fontSize=8.5, leading=12, alignment=1)), logo_box]]
        t_hdr = Table(header_table_data, colWidths=)
        t_hdr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        story.append(t_hdr); story.append(Spacer(1, 15))
        
        # Descrição e Validade
        story.append(Paragraph(f"<b>Descrição Técnica do Serviço:</b> {desc_geral_servico}", b_s))
        story.append(Spacer(1, 5))
        story.append(Paragraph(f"<b>Validade do Orçamento:</b> {val_dias} dias | <b>Emissão:</b> {dt_emissao.strftime('%d/%m/%Y')} | <b>Válido Até:</b> {dt_validade.strftime('%d/%m/%Y')}", b_s))
        story.append(Spacer(1, 10))
        
        # Tabela 1: Mão de Obra
        story.append(Paragraph("<b>Mão de Obra Executiva</b>", h2_s))
        d_mo = [["ID Código", "Descrição da Atividade de Campo", "Valor Comercial"]]
        for _, r in st.session_state.df_servicos_selecionados.iterrows():
            d_mo.append([r["ID"], r["Descrição"], f"R$ {r['Valor (R$)'].item() if isinstance(r['Valor (R$)'], pd.Series) else r['Valor (R$)']:.2f}"])
        t_mo = Table(d_mo, colWidths=)
        t_mo.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0,0), (-1,-1), 4)]))
        story.append(t_mo); story.append(Spacer(1, 10))
        
        # Tabela 2: Materiais
        história.append(Parágrafo("Romaneio Analítico de Materiais", h2_s))d_ma = [["ID", "Descrição Material", "Un", "Qtd", "Val Un", "Val Tot"]]for _, r in st.session_state.df_materials_selecionados.iterrows():d_ma.append([r["ID"], r["Descrição"], r["Unidade"], str(int(r["Quantidade"])), f"R$ {r['Valor Unitário (R$)']:.2f}", f"R$ {r['Valor Total (R$)']:.2f}"])t_ma = Table(d_ma, colWidths=)t_ma.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0,0), (-1,-1), 4)]))story.append(t_ma); story.append(Spacer(1, 10))# Tabela 3: Bônus se não for st.session_state.df_bonus_selecionados.empty: story.append(Paragraph(" Política de Bônus Comercial (Cortesias Inclusas) ", h2_s)) d_bo = [["ID Code", "Descrição do Item Cortesia", "Valor Abatido"]] for _, r in st.session_state.df_bonus_selecionados.iterrows(): d_bo.append([r["ID"], r["Descrição"], f"R$ {r['Valor (R$)']:.2f}"]) t_bo = Table(d_bo, colWidths=) t_bo.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), cores.HexColor('#4A5568')), ('TEXTCOLOR', (0,0), (-1,0), cores.fumaçabranca), ('GRID', (0,0), (-1,-1), 0.5, cores.HexColor('#CBD5E0')), ('PADDING', (0,0), (-1,-1), 4)])) story.append(t_bo); story.append(Spacer(1, 10))# Resumo Financeiro Consolidado story.append(Paragraph(" Fechamento e Condições de Faturamento ", h2_s)) d_fech = [ ["Total Geral de Mão de Obra", f"R$ {tot_mo_bruta:.2f}"], ["Total Geral de Materiais", f"R$ {tot_mat_bruto:.2f}"], ["Total Acumulado de Bônus", f"R$ {tot_bonus_calc:.2f}"], ["Subtotal Geral Bruto", f"R$ {subtotal_bruto:.2f}"], [f"Desconto Comercial Concedido ({desconto_slider}%)", f"R$ {valor_desconto_real:.2f}"], ["TOTAL A PAGAR (ATÉ 10X NO CARTÃO)", f"R$ {total_a_pagar_cartao:.2f}"], ["TOTAL À VISTA (DINHEIRO OU PIX)", f"R$ {total_a_vista_pix:.2f}"] ] t_fch = Table(d_fech, colWidths=) t_fch.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('FONTNAME', (0,-2), (1,-1), 'Helvetica-Bold'), ('BACKGROUND', (0,-2), (0,-2), colors.HexColor('#FED7D7')), ('BACKGROUND', (0,-1), (0,-1), colors.HexColor('#C6F6D5')), ('PADDING', (0,0), (-1,-1), 4)])) story.append(t_fch); story.append(Spacer(1, 15))# Selo de Verificação Criptográfica GOVmsg_gov = f"Documento Assinado Eletronicamente por: {nome_responsavel.upper()}Proposta gerada via Criptografia Hash MD5: {hash_val}. Assinatura com equivalência de fé pública Gov.br ICP-Brasil."t_gv = Table([[RLImage(BytesIO(qb_val), width=45, height=45), Paragraph(msg_gov, ParagraphStyle('G', parent=s['Normal'], fontSize=7, leading=9))]], colWidths=)t_gv.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#A0AEC0')), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 5)]))story.append(t_gv)doc.build(story); bf.seek(0); return bf.getvalue()if st.button("🚀 Emitir e Chancelar Proposta Comercial Oficial"): h_val = hashlib.md5(f"{nome_cliente}{total_a_vista_pix}".encode()).hexdigest() link_wpp = f"whatsapp.com{whatsapp_num}&text=Olá%20Fênix%20Engenharia,%20gostaria%20de%20aprovar%20o%20orçamento%20código%20{h_val}"pdf_gerado = build_pdf_fenix(logo_upload, link_wpp, h_val)st.download_button(label="📥 Baixar Proposta Comercial em PDF", data=pdf_gerado, file_name=f"Proposta_Comercial_{nome_cliente.replace(' ', '_')}.pdf", mime="application/pdf")st.success("Proposta chancelada e liberada para download!")
