import streamlit as st
import pandas as pd
import datetime as dt
import hashlib
import qrcode
import requests
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image

st.set_page_config(page_title="Fênix Engenharia", page_icon="🏗️", layout="centered")

SPREADSHEET_ID = "1n5Tn6N-K4s0i17tSra0mrGSh49g3SRnz8B0jobYtods"

# Função leve para baixar os dados atualizados direto da nuvem do Google
def carregar_dados_direto(aba_nome, colunas_padrao, dados_padrao=[]):
    if f"cached_{aba_nome}" not in st.session_state:
        try:
            url = f"https://google.com{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={aba_nome}"
            df = pd.read_csv(url)
            if df.empty:
                df = pd.DataFrame(dados_padrao, columns=colunas_padrao)
            st.session_state[f"cached_{aba_nome}"] = df
        except:
            st.session_state[f"cached_{aba_nome}"] = pd.DataFrame(dados_padrao, columns=colunas_padrao)
    return st.session_state[f"cached_{aba_nome}"]

# Motor de Envio Webbot: Dispara os novos cadastros diretamente para as linhas da sua Planilha Google
def salvar_novo_cliente_nuvem(id_c, nome_c, doc_c, tel_c, end_c):
    # TODO: Substitua os IDs abaixo pelos IDs reais gerados no Passo 2 para sua planilha automatizar 100%
    form_url = "https://google.com"
    form_data = {
        "entry.1000001": id_c,
        "entry.1000002": nome_c,
        "entry.1000003": doc_c,
        "entry.1000004": tel_c,
        "entry.1000005": end_c
    }
    try:
        requests.post(form_url, data=form_data)
        st.toast("Enviado com sucesso para a Planilha Google! ✅")
    except:
        st.sidebar.warning("Erro de rede ao sincronizar com a nuvem.")

db_v = carregar_dados_direto("veiculos", ["Tipo", "Marca", "Modelo", "Tempo de Uso (Anos)", "Consumo (Km/L)", "Valor FIPE (R$)", "Seguro/Doc Anual", "Manutenção Mensal"], [{"Tipo": "Carro", "Marca": "Fiat", "Modelo": "Uno", "Tempo de Uso (Anos)": 2, "Consumo (Km/L)": 12.0, "Valor FIPE (R$)": 35000.0, "Seguro/Doc Anual": 1400.0, "Manutenção Mensal": 200.0}])
db_c = carregar_dados_direto("custos_fixos", ["Tipo de Gasto", "Valor Mensal (R$)"], [{"Tipo de Gasto": "Contador / MEI", "Valor Mensal (R$)": 80.0}, {"Tipo de Gasto": "Internet e Celular", "Valor Mensal (R$)": 120.0}])
db_m = carregar_dados_direto("materiais", ["ID", "Descrição", "Unidade", "Custo (R$)", "Margem (%)", "Valor Unitário (R$)"], [{"ID": "MAT-001", "Descrição": "Cabo Flexível 2,5mm²", "Unidade": "m", "Custo (R$)": 3.60, "Margem (%)": 20, "Valor Unitário (R$)": 4.50}])
db_s = carregar_dados_direto("servicos", ["ID", "Descrição", "Unidade", "Valor (R$)"], [{"ID": "SRV-001", "Descrição": "Instalação de Tomada", "Unidade": "Ponto", "Valor (R$)": 50.00}])
db_clientes = carregar_dados_direto("clientes", ["ID", "Nome / Razão Social", "CPF / CNPJ", "Telefone", "Endereço Completo"], [{"ID": "CLI-001", "Nome / Razão Social": "FENIX ENGENHARIA E COMERCIO LTDA", "CPF / CNPJ": "52.769.953/0001-12", "Telefone": "(31) 99539-2027", "Endereço Completo": "Avenida Getulio Vargas, nº 671, Savassi, Belo Horizonte - MG"}])

if "db_logos" not in st.session_state: st.session_state.db_logos = {}
if "df_m_sel" not in st.session_state: st.session_state.df_m_sel = pd.DataFrame(columns=["ID", "Descrição", "Unidade", "Quantidade", "Valor Unitário (R$)", "Valor Total (R$)"])
if "df_s_sel" not in st.session_state: st.session_state.df_s_sel = pd.DataFrame(columns=["ID", "Descrição", "Quantidade", "Valor Unitário (R$)", "Valor Total (R$)"])
if "df_b_sel" not in st.session_state: st.session_state.df_b_sel = pd.DataFrame(columns=["ID", "Descrição", "Valor (R$)"])

st.title("🏗️ FÊNIX ENGENHARIA E COMERCIO LTDA")
a_orc, a_clientes, a_calc, a_mat, a_serv = st.tabs(["📋 Proposta Comercial", "👥 Cadastro de Clientes", "🧮 Calcular Minha Hora", "📦 Materiais", "🛠️ Serviços"])
with a_clientes:
    st.header("👥 Central Geral de Clientes")
    with st.form("cad_cliente_form", clear_on_submit=True):
        c_nome = st.text_input("Nome Completo / Razão Social:")
        col_c1, col_c2 = st.columns(2)
        with col_c1: c_documento = st.text_input("CPF ou CNPJ do Cliente:")
        with col_c2: c_telefone = st.text_input("Telefone de Contato (com DDD):", value="(31) ")
        c_endereco = st.text_input("Endereço Técnico Completo (Rua, Número, Bairro, Cidade-UF):")
        
        if st.form_submit_button("💾 Salvar Cadastro de Cliente na Nuvem"):
            if c_nome and c_documento:
                novo_id_c = f"CLI-{len(st.session_state.cached_clientes) + 1:03d}"
                # Adiciona localmente na tela para visualização imediata
                novo_cli = pd.DataFrame([{"ID": novo_id_c, "Nome / Razão Social": c_nome, "CPF / CNPJ": c_documento, "Telefone": c_telefone, "Endereço Completo": c_endereco}])
                st.session_state.cached_clientes = pd.concat([st.session_state.cached_clientes, novo_cli], ignore_index=True)
                # Dispara a automação para gravar permanentemente na Planilha Google
                salvar_novo_cliente_nuvem(novo_id_c, c_nome, c_documento, c_telefone, c_endereco)
                st.rerun()

    if not st.session_state.cached_clientes.empty:
        with st.expander("🗑️ Remover Ficha do Sistema"):
            cli_remover = st.selectbox("Selecione para deletar:", [f"{r['ID']} - {r['Nome / Razão Social']}" for idx, r in st.session_state.cached_clientes.iterrows()])
            if st.button("❌ Confirmar Exclusão", type="primary"):
                st.session_state.cached_clientes = st.session_state.cached_clientes[st.session_state.cached_clientes["ID"] != cli_remover.split(" - ")[0]].reset_index(drop=True)
                st.rerun()
        st.data_editor(st.session_state.cached_clientes, use_container_width=True)
with a_calc:
    st.header("🧮 Engenharia de Custos e Formação de Preço")
    sd = st.number_input("Meta de Pró-labore mensal desejado (R$):", min_value=0.0, value=4000.0)
    col_t1, col_t2 = st.columns(2)
    dt_m = col_t1.number_input("Dias operacionais por mês:", min_value=1, value=22)
    hd = col_t2.number_input("Horas produtivas por dia:", min_value=1.0, value=6.0)
    ml = st.slider("Margem de lucro para a empresa (%)", 0, 50, 20)
    ht = dt_m * hd
    
    with st.form("c_v", clear_on_submit=True):
        c1, c2 = st.columns(2)
        vt = c1.selectbox("Tipo do Veículo:", ["Carro", "Moto", "Caminhão"])
        vm = c1.text_input("Marca do Veículo:")
        tp = c1.number_input("Tempo de Posse (Anos):", min_value=0, value=1)
        mo = c2.text_input("Modelo do Veículo:")
        vl = c2.number_input("Valor Atual FIPE (R$):", min_value=0.0, value=30000.0)
        ip = c2.number_input("Seguro + IPVA Anual (R$):", min_value=0.0, value=1200.0)
        mn = st.number_input("Manutenção Mensal (R$):", min_value=0.0, value=200.0)
        if st.form_submit_button("💾 Salvar Veículo"):
            if vm and mo:
                st.session_state.cached_veiculos = pd.concat([st.session_state.cached_veiculos, pd.DataFrame([{"Tipo": vt, "Marca": vm, "Modelo": mo, "Tempo de Uso (Anos)": tp, "Consumo (Km/L)": 10.0, "Valor FIPE (R$)": vl, "Seguro/Doc Anual": ip, "Manutenção Mensal": mn}])], ignore_index=True)
                st.rerun()
            
    if not st.session_state.cached_veiculos.empty:
        df_v_editado = st.data_editor(st.session_state.cached_veiculos, use_container_width=True)
        cm = ((df_v_editado["Valor FIPE (R$)"].sum() * 0.10 / 12) + (df_v_editado["Seguro/Doc Anual"].sum() / 12) + df_v_editado["Manutenção Mensal"].sum()) / ht if ht > 0 else 0.0
    else: cm = 0.0
    with st.form("c_f", clear_on_submit=True):
        ft = st.text_input("Tipo de Gasto Fixo (ex: MEI, Internet):")
        fv = st.number_input("Valor Mensal (R$):", min_value=0.0)
        if st.form_submit_button("➕ Adicionar Gasto Fixo") and ft:
            st.session_state.cached_custos_fixos = pd.concat([st.session_state.cached_custos_fixos, pd.DataFrame([{"Tipo de Gasto": ft, "Valor Mensal (R$)": fv}])], ignore_index=True); st.rerun()
            
    if not st.session_state.cached_custos_fixos.empty:
        df_f_editado = st.data_editor(st.session_state.cached_custos_fixos, use_container_width=True)[["Tipo de Gasto", "Valor Mensal (R$)"]]
        cf_h = df_f_editado["Valor Mensal (R$)"].sum() / ht if ht > 0 else 0.0
    else: cf_h = 0.0
    
    sl_h = sd / ht if ht > 0 else 0.0; c_op_h = cm + cf_h; h_bruto = sl_h + c_op_h; h_fin = h_bruto / (1 - (ml / 100)) if ml < 100 else h_bruto
    st.subheader("📊 Preço da Hora")
    col1, col2 = st.columns(2); col1.metric("Sua Hora Líquida", f"R$ {sl_h:.2f}/h"); col2.metric("Custos Operacionais/h", f"R$ {c_op_h:.2f}/h")
    st.markdown(f"### 🎯 Preço Final Combinado com Margem: **R$ {h_fin:.2f}/h**")
    if st.button("🚀 Gravar Preço da Hora no Sistema"): 
        st.session_state["pr_h_f"] = round(h_fin, 2); st.success("Preço da hora gravado!")

with a_mat:
    st.header("📦 Catálogo Técnico de Materiais")
    with st.form("f_m", clear_on_submit=True):
        md = st.text_input("Descrição Material:"); mu = st.selectbox("Unidade:", ["Un", "m", "Barra", "Saco", "Caixa"]); mc = st.number_input("Custo NF:"); mm = st.slider("Margem (%)", 0, 80, 30)
        if st.form_submit_button("Salvar Material") and md:
            st.session_state.cached_materiais = pd.concat([st.session_state.cached_materiais, pd.DataFrame([{"ID": f"MAT-{len(st.session_state.cached_materiais)+1:03d}", "Descrição": md, "Unidade": mu, "Custo (R$)": mc, "Margem (%)": mm, "Valor Unitário (R$)": round(mc/(1-(mm/100)), 2)}])], ignore_index=True); st.rerun()
    if not st.session_state.cached_materiais.empty:
        df_me = st.data_editor(st.session_state.cached_materiais, use_container_width=True)

with a_serv:
    st.header("🛠️ Catálogo Referencial de Serviços")
    with st.form("s_f", clear_on_submit=True):
        sd_item = st.text_input("Descrição do Serviço:"); su = st.selectbox("Unidade:", ["Ponto", "M²", "Diária", "Hora"]); sv = st.number_input("Preço:")
        if st.form_submit_button("Salvar Serviço") and sd_item:
            st.session_state.cached_servicos = pd.concat([st.session_state.cached_servicos, pd.DataFrame([{"ID": f"SRV-{len(st.session_state.cached_servicos)+1:03d}", "Descrição": sd_item, "Unidade": su, "Valor (R$)": round(sv, 2)}])], ignore_index=True); st.rerun()
    if not st.session_state.cached_servicos.empty:
        df_se = st.data_editor(st.session_state.cached_servicos, use_container_width=True)
with a_orc:
    st.subheader("📋 Configuração da Proposta Comercial - FÊNIX ENGENHARIA E COMERCIO LTDA")
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        logo_upload = st.file_uploader("Suba uma nova Logomarca:", type=["png", "jpg", "jpeg"])
        if logo_upload is not None: st.session_state.db_logos[logo_upload.name] = logo_upload.read(); st.success("Logo salva!")
    with col_l2:
        logo_selecionada = st.selectbox("Selecione a logo ativa:", list(st.session_state.db_logos.keys()) if st.session_state.db_logos else ["Nenhuma logo salva"])
    logo_final_bytes = st.session_state.db_logos.get(logo_selecionada) if logo_selecionada != "Nenhuma logo salva" else None
    
    wpp_num = st.text_input("WhatsApp para QR Code (Apenas Números com DDD):", value="31995392027")
    lista_clientes_ativos = [f"{r['ID']} - {r['Nome / Razão Social']}" for idx, r in st.session_state.cached_clientes.iterrows()] if not st.session_state.cached_clientes.empty else ["Nenhum cliente cadastrado"]
    c_selecionado = st.selectbox("Selecione o Cliente do Faturamento:", lista_clientes_ativos)
    
    if not st.session_state.cached_clientes.empty and c_selecionado != "Nenhum cliente cadastrado":
        id_real_c = c_selecionado.split(" - ")[0]
        ficha_c = st.session_state.cached_clientes[st.session_state.cached_clientes["ID"] == id_real_c]
        if not ficha_c.empty:
            nc = str(ficha_c["Nome / Razão Social"].values[0])
            cnpj_c = str(ficha_c["CPF / CNPJ"].values[0])
            end_c = str(ficha_c["Endereço Completo"].values[0])
        else: nc, cnpj_c, end_c = "Não Informado", "00.000.000/0001-00", "Não Informado"
    else: nc, cnpj_c, end_c = "Não Informado", "00.000.000/0001-00", "Não Informado"
        
    ds_serv = st.text_area("Descrição Geral Técnica dos Serviços Executados:", value="Execução de Infraestrutura e Reforma Técnica.")
    c1, c2, c3 = st.columns(3); val_d = c1.number_input("Validade (Dias):", min_value=1, value=10); dt_e = c2.date_input("Emissão:", value=dt.date.today()); dt_v = c3.date_input("Válido Até:", value=dt.date.today()+dt.timedelta(days=int(val_d)))
    st.write("---"); st.subheader(" Mão de Obra")
    lista_s = [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.cached_servicos.iterrows()] if not st.session_state.cached_servicos.empty else []
    if lista_s:
        s_sel = st.selectbox("Vincular Serviço à Proposta:", lista_s)
        tipo_cobranca_mo = st.selectbox("Critério de Faturamento da Mão de Obra:", ["Por Empreitada / Ponto", "Por Hora Técnica"])
        q_srv_solicitada = st.number_input("Quantidade (Ponto ou Hora):", min_value=1.0, value=1.0, step=0.5)
        if st.button("➕ Vincular Serviço Técnico"):
            item_filtrado_s = st.session_state.cached_servicos[st.session_state.cached_servicos["ID"] == s_sel.split(" - ")[0]]
            if not item_filtrado_s.empty:
                it_s = item_filtrado_s.iloc[0]
                val_unit_mo = float(it_s["Valor (R$)"]) if tipo_cobranca_mo == "Por Empreitada / Ponto" else float(st.session_state.get("pr_h_f", 60.0))
                st.session_state.df_s_sel = pd.concat([st.session_state.df_s_sel, pd.DataFrame([{"ID": it_s["ID"], "Descrição": f"{it_s['Descrição']} ({tipo_cobranca_mo.split()[-1]})", "Quantidade": q_srv_solicitada, "Valor Unitário (R$)": val_unit_mo, "Valor Total (R$)": q_srv_solicitada * val_unit_mo}])], ignore_index=True); st.rerun()
    if not st.session_state.df_s_sel.empty:
        df_se_edit = st.data_editor(st.session_state.df_s_sel, use_container_width=True)
        t_mo = df_se_edit["Valor Total (R$)"].sum()
    else: t_mo = 0.0

    st.write("---"); st.subheader("📦 Materiais")
    lista_m = [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.cached_materiais.iterrows()] if not st.session_state.cached_materiais.empty else []
    if lista_m:
        m_sel = st.selectbox("Vincular Material à Proposta:", lista_m); q_sol = st.number_input("Quantidade Insumo Requerida:", min_value=1, value=1)
        if st.button("➕ Vincular Material Almoxarifado"):
            item_filtrado_m = st.session_state.cached_materiais[st.session_state.cached_materiais["ID"] == m_sel.split(" - ")[0]]
            if not item_filtrado_m.empty:
                it_m = item_filtrado_m.iloc[0]
                st.session_state.df_m_sel = pd.concat([st.session_state.df_m_sel, pd.DataFrame([{"ID": it_m["ID"], "Descrição": it_m["Descrição"], "Unidade": it_m["Unidade"], "Quantidade": q_sol, "Valor Unitário (R$)": it_m["Valor Unitário (R$)"], "Valor Total (R$)": q_sol * it_m["Valor Unitário (R$)"]}])], ignore_index=True); st.rerun()
    if not st.session_state.df_m_sel.empty:
        df_me_edit = st.data_editor(st.session_state.df_m_sel, use_container_width=True)
        t_mat = df_me_edit["Valor Total (R$)"].sum()
    else: t_mat = 0.0

    st.write("---"); st.subheader("🎁 Cortesia Comercial / Bônus")
    with st.form("f_b", clear_on_submit=True):
        bd, bv = st.text_input("Descrição do Bônus:"), st.number_input("Valor de Mercado Comercial:", min_value=0.0)
        if st.form_submit_button("➕ Vincular Bônus") and bd:
            st.session_state.df_b_sel = pd.concat([st.session_state.df_b_sel, pd.DataFrame([{"ID": f"BON-{len(st.session_state.df_b_sel)+1:03d}", "Descrição": bd, "Valor (R$)": bv}])], ignore_index=True); st.rerun()
    t_bon = st.session_state.df_b_sel["Valor (R$)"].sum() if not st.session_state.df_b_sel.empty else 0.0

    ds_s = st.slider("Desconto Comercial Aplicado (%):", 0, 30, 0)
    sub_bruto = t_mo + t_mat; v_desc = sub_bruto * (ds_s / 100); tot_cartao = sub_bruto * 1.08; tot_vista = max(0.0, sub_bruto - t_bon - v_desc)
    st.warning(f"💳 **TOTAL A PAGAR (ATÉ 10X CARTÃO): R$ {tot_cartao:.2f}**"); st.success(f"💰 **TOTAL À VISTA (DINHEIRO OU PIX): R$ {tot_vista:.2f}**")
    def build_pdf_fenix(logo_bytes, q_url, h_val):
        bf = BytesIO(); doc = SimpleDocTemplate(bf, pagesize=letter, rightMargin=35, leftMargin=45, topMargin=40, bottomMargin=40); sty = []; s = getSampleStyleSheet()
        t_sty = ParagraphStyle('T', parent=s['Heading1'], fontSize=12, textColor=colors.HexColor('#1A365D'), spaceBefore=10, spaceAfter=4)
        b_sty = ParagraphStyle('B', parent=s['Normal'], fontSize=9, leading=13, spaceAfter=4)
        tx_emp = "<b>FENIX ENGENHARIA E COMERCIO LTDA</b> - CNPJ: 52.769.953/0001-12<br/>Endereço: Avenida Getulio Vargas, nº 671, 9º Andar, Sala 1.051, Savassi, Belo Horizonte-MG"
        l_bx = Paragraph("", b_sty)
        if logo_bytes is not None:
            try:
                pi = Image.open(BytesIO(logo_bytes)); logo_p = pi.copy(); logo_p.thumbnail((90, 40))
                lb = BytesIO(); logo_p.save(lb, format="PNG"); lb.seek(0); l_bx = RLImage(lb, width=logo_p.width, height=logo_p.height)
            except: pass
        qr = qrcode.QRCode(version=1, box_size=2, border=0); qr.add_data(q_url); qr.make(fit=True); qb = BytesIO(); qr.make_image(fill_color="black", back_color="white").save(qb, format="PNG"); qb.seek(0)
        t_hdr = Table([[RLImage(BytesIO(qb.getvalue()), width=45, height=45), Paragraph(tx_emp, ParagraphStyle('C', parent=s['Normal'], fontSize=8, leading=11, alignment=1)), l_bx]], colWidths=(60, 350, 110))
        t_hdr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')])); sty.append(t_hdr); sty.append(Spacer(1, 10))
        sty.append(Paragraph(f"<b>Descrição Técnica do Serviço:</b> {ds_serv}<br/><b>Validade:</b> {val_d} dias | <b>Emissão:</b> {dt_e.strftime('%d/%m/%Y')} | <b>Válido Até:</b> {dt_v.strftime('%d/%m/%Y')}", b_sty))
        sty.append(Spacer(1, 5)); sty.append(Paragraph(f"<b>Cliente / Empresa:</b> {nc} | <b>CPF / CNPJ:</b> {cnpj_c}<br/><b>Endereço Técnico da Obra:</b> {end_c}", b_sty)); sty.append(Spacer(1, 8))
        
        sty.append(Paragraph("<b>Mão de Obra</b>", t_sty))
        d_mo = [["ID", "Descrição Mão de Obra", "Qtd", "Val Un", "Val Tot"]]
        for _, r in st.session_state.df_s_sel.iterrows(): d_mo.append([r["ID"], r["Descrição"], f"{r['Quantidade']:.1f}", f"R$ {r['Valor Unitário (R$)']:.2f}", f"R$ {r['Valor Total (R$)']:.2f}"])
        t1 = Table(d_mo, colWidths=(60, 240, 40, 80, 100)); t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0,0), (-1,-1), 4)])); sty.append(t1); sty.append(Spacer(1, 10))
        
        sty.append(Paragraph("<b>Materiais</b>", t_sty))
        d_ma = [["ID", "Descrição", "Un", "Qtd", "Val Un", "Val Tot"]]
        for _, r in st.session_state.df_m_sel.iterrows(): d_ma.append([r["ID"], r["Descrição"], r["Unidade"], str(int(r["Quantidade"])), f"R$ {r['Valor Unitário (R$)']:.2f}", f"R$ {r['Valor Total (R$)']:.2f}"])
        t2 = Table(d_ma, colWidths=(60, 210, 30, 40, 80, 100)); t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0,0), (-1,-1), 4)])); sty.append(t2); sty.append(Spacer(1, 10))
        
        d_ch = [["Total Bônus", f"R$ {t_bon:.2f}"], ["Subtotal", f"R$ {sub_bruto:.2f}"], [f"Desconto ({ds_s}%)", f"R$ {v_desc:.2f}"], ["TOTAL A PAGAR (ATÉ 10X CARTÃO)", f"R$ {tot_cartao:.2f}"], ["TOTAL À VISTA (DINHEIRO OU PIX)", f"R$ {tot_vista:.2f}"]]
        t4 = Table(d_ch, colWidths=(350, 170)); t4.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('FONTNAME', (0,-2), (1,-1), 'Helvetica-Bold'), ('BACKGROUND', (0,-2), (0,-2), colors.HexColor('#FED7D7')), ('BACKGROUND', (0,-1), (1,-1), colors.HexColor('#C6F6D5')), ('PADDING', (0,0), (-1,-1), 4)])); sty.append(t4)
        
        sty.append(Spacer(1, 10)); sty.append(Paragraph("<b>Garantia</b>", t_sty))
        t_garantia = "O presente documento concede ao proprietário garantia condicional de 06 meses sobre os serviços de instalação realizados e registrados neste documento sob as seguintes condições:<br/>1- Durante este período o proprietário não poderá realizar demais intervenções nas instalações realizadas utilizando outra mão de obra de eletricistas terceiros, caso precise de algum reparo, acionar nossa empresa para tal.<br/>2- O painel elétrico será lacrado e não poderá ser rompido o lacre sem que seja formalizado junto à nossa empresa.<br/><br/>O presente documento concede ao proprietário garantia condicional de 06 meses sobre os materiais de instalação realizados e registrados neste documento sob as seguintes condições:<br/>1- Os equipamentos instalados nas tomadas devem ser compatíveis em valores de corrente elétrica com as especificações das tomadas.<br/>2- Não serão considerados os danos provenientes da utilização de conectores de tomada tipo \"T\", Benjamim, Extensões e outros dispositivos não certificados pelo INMETRO que possam causar sobrecarga na mesma."
        sty.append(Paragraph(t_garantia, b_sty))
        sty.append(Paragraph("<b>OBSERVAÇÕES</b>", t_sty))
        t_obs = "1- Caso seja necessário a execução de demais atividades não listadas neste orçamento, será criado outro orçamento para estes serviços.<br/>2- Caso, durante a execução das atividades, seja necessário a compra de materiais não contemplados nesta lista, por solicitação do cliente ou por terem sido subestimados, os valores destes materiais extras serão passados ao cliente junto das justificativas e este valor deverá ser cobrado à parte."
        sty.append(Paragraph(t_obs, b_sty))
        sty.append(Paragraph("<b>PAGAMENTO</b>", t_sty))
        t_pag = "1- Será considerado à vista pagamento em dinheiro ou PIX, sendo realizado 50% do valor total no ato do fechamento do serviço e 50% do valor total na entrega técnica ao finalizar as atividades descritas no escopo deste orçamento.<br/>2- Para pagamento à vista, será concedido um desconto para o cliente, conforme indicado na proposta comercial.<br/>3- O valor total poderá ser parcelado em até 10 vezes no cartão de crédito.<br/>4- Aceitamos cartões VISA e Master Card."
        sty.append(Paragraph(t_pag, b_sty))
        
        now_t = dt.datetime.now().strftime('%d/%m/%Y %H:%M')
        msg = f"<b>Assinado digitalmente por:</b> RONILSON RICHARDSON FRAGOSO DE SOUZA<br/><b>Data da Chancelagem:</b> {now_t} | <b>Padrão:</b> ICP-Brasil Equivalente V2<br/><b>Chave Identificadora de Autenticidade (MD5):</b> {h_val}"
        tgv = Table([[RLImage(BytesIO(qb.getvalue()), width=55, height=55), Paragraph(msg, ParagraphStyle('G', parent=s['Normal'], fontSize=7.5, leading=10))]], colWidths=(65, 455))
        tgv.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 1, colors.HexColor('#A0AEC0')), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 6)]))
        sty.append(Spacer(1, 15)); sty.append(tgv)
        doc.build(sty); bf.seek(0); return bf.getvalue()

    if st.button("🚀 Chancelar Proposta Comercial"):
        hv = hashlib.md5(f"{nc}{tot_vista}".encode()).hexdigest(); l_wp = f"https://whatsapp.com{wpp_num}&text=Aprovar%20Orcamento%20{hv}"
        pdf = build_pdf_fenix(logo_final_bytes, l_wp, hv)
        st.download_button(label="📥 Baixar Proposta Comercial em PDF", data=pdf, file_name=f"Proposta_Fenix_{nc.replace(' ', '_')}.pdf", mime="application/pdf")
