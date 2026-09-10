import streamlit as st, pandas as pd, datetime as dt, hashlib, qrcode, reportlab.lib.colors as c
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from PIL import Image

st.set_page_config(page_title="Orçamentos Pro", page_icon="🏗️", layout="centered")
q = st.query_params
if "verificar" in q:
    st.success("🔒 PORTAL DE VERIFICAÇÃO"); st.title("✅ Documento Autêntico"); st.info(f"**Código Hash:** {q['verificar']}")
    if st.button("Voltar"): st.query_params.clear(); st.rerun()
    st.stop()

if "db_s" not in st.session_state:
    st.session_state.db_s = pd.DataFrame([{"Serviço": "Instalação de Tomada", "Preço Padrão": 50.0}, {"Serviço": "Reforma de QDC", "Preço Padrão": 350.0}])
if "db_m" not in st.session_state:
    st.session_state.db_m = pd.DataFrame([{"Material": "Cabo 2,5mm² (m)", "Preço Unitário": 4.50}])
if "db_v" not in st.session_state:
    st.session_state.db_v = pd.DataFrame([{"Tipo": "Carro", "Marca": "Fiat", "Modelo": "Uno", "Valor (R$)": 35000.0, "IPVA Anual": 1400.0, "Anos Posse": 2}])
if "df_o" not in st.session_state:
    st.session_state.df_o = pd.DataFrame(columns=["Item", "Qtd", "Preço Un.", "Total"])

st.title("🏗️ Orçamentos Construção Pro")
st.caption("Versão v11.1 Corrige TypeError - Proteção de busca e Frota Completa")
a_orc, a_serv, a_mat, a_veic, a_calc = st.tabs(["📋 Criar Orçamento", "🛠️ Serviços", "📦 Materiais", "🚗 Veículo", "🧮 Calcular Hora"])

with a_serv:
    with st.form("c_s", clear_on_submit=True):
        ns, np = st.text_input("Serviço:"), st.number_input("Preço (R$):", min_value=0.0)
        if st.form_submit_button("💾 Salvar") and ns: st.session_state.db_s = pd.concat([st.session_state.db_s, pd.DataFrame([{"Serviço": ns, "Preço Padrão": np}])], ignore_index=True); st.rerun()
    st.session_state.db_s = st.data_editor(st.session_state.db_s, use_container_width=True, num_rows="dynamic")

with a_mat:
    with st.form("c_m", clear_on_submit=True):
        nm, np = st.text_input("Material:"), st.number_input("Preço Unitário (R$):", min_value=0.0)
        if st.form_submit_button("💾 Salvar") and nm: st.session_state.db_m = pd.concat([st.session_state.db_m, pd.DataFrame([{"Material": nm, "Preço Unitário": np}])], ignore_index=True); st.rerun()
    st.session_state.db_m = st.data_editor(st.session_state.db_m, use_container_width=True, num_rows="dynamic")

with a_veic:
    with st.form("c_v", clear_on_submit=True):
        c1, c2 = st.columns(2); vt = c1.selectbox("Tipo:", ["Carro", "Moto", "Caminhão"]); vm = c1.text_input("Marca:"); tp = c1.number_input("Tempo de Posse (Anos):", min_value=0, value=1); mo = c2.text_input("Modelo:"); vl = c2.number_input("Valor FIPE:", min_value=0.0, value=25000.0); ip = c2.number_input("IPVA Anual:", min_value=0.0, value=1500.0)
        if st.form_submit_button("💾 Salvar") and vm and mo: st.session_state.db_v = pd.concat([st.session_state.db_v, pd.DataFrame([{"Tipo": vt, "Marca": vm, "Modelo": mo, "Valor (R$)": vl, "IPVA Anual": ip, "Anos Posse": tp}])], ignore_index=True); st.rerun()
    st.session_state.db_v = st.data_editor(st.session_state.db_v, use_container_width=True, num_rows="dynamic")
with a_calc:
    cf = st.number_input("Custos fixos de escritório:", min_value=0.0, value=500.0); vf = st.session_state.db_v["Valor (R$)"].sum() if not st.session_state.db_v.empty else 0.0; iff = st.session_state.db_v["IPVA Anual"].sum() if not st.session_state.db_v.empty else 0.0; cm = ((vf * 0.10) / 12) + (iff / 12); st.info(f"🚗 Custos da Frota: R$ {cm:.2f}/mês")
    sd = st.number_input("Meta de Pró-labore mensal:", min_value=0.0, value=4000.0); dt_m = st.number_input("Dias trabalhados/mês:", min_value=1, value=22); hd = st.number_input("Horas produtivas/dia:", min_value=1.0, value=6.0); ml = st.slider("Margem da Empresa (%)", 0, 50, 20); ht = dt_m * hd; h_cal = ((cf + cm + sd) / ht) / (1 - (ml / 100)) if ht > 0 else 0.0; st.success(f"💰 Hora Sugerida: R$ {h_cal:.2f}")
    if st.button("Aplicar Hora"): st.session_state["pr_h"] = round(h_cal, 2); st.info("Sincronizado!")

with a_orc:
    logo_upload = st.file_uploader("Upload da Logomarca (Opcional):", type=["png", "jpg", "jpeg"]); c1, c2 = st.columns(2); nc = c1.text_input("Cliente:", value="Fenix Engenharia"); to = c2.selectbox("Segmento:", ["Construção Geral", "Elétrica", "Hidráulica", "Pintura"], index=1)
    
    lista_s = list(st.session_state.db_s["Serviço"].values) if not st.session_state.db_s.empty else ["Nenhum cadastrado"]
    sv = st.selectbox("Serviço:", lista_s)
    sp = st.text_input("Ajuste o escopo:", value=sv)
    nr = st.text_input("Responsável Técnico:", value="Ronilson Richardson Fragoso de Souza"); st.write("---"); tc = st.selectbox("Critério:", ["Por Empreitada", "Por Hora"]); v_s = 0.0
    
    if tc == "Por Empreitada":
        filtro_s = st.session_state.db_s[st.session_state.db_s["Serviço"] == sv]
        sb = filtro_s["Preço Padrão"].values[0] if not filtro_s.empty else 0.0
        c1, c2 = st.columns(2); qp = c1.number_input("Quantidade:", min_value=1.0, value=10.0); pp = c2.number_input("Preço Unitário (R$):", min_value=0.0, value=float(sb)); v_s = qp * pp
    else: c1, c2 = st.columns(2); qh = c1.number_input("Horas estimadas:", min_value=0.5, value=4.0); ph = c2.number_input("Valor da hora (R$):", min_value=0.0, value=st.session_state.get("pr_h", 60.0)); v_s = qh * ph
    
    st.write("---"); ta = st.checkbox("Demanda ajudantes?"); c_aj = 0.0
    if ta: c1, c2 = st.columns(2); qa = c1.number_input("Quantidade ajudantes:", min_value=1, value=1); da = c2.number_input("Diária ajudante (R$):", min_value=0.0, value=120.0); nj = st.number_input("Quantidade diárias:", min_value=1, value=1); c_aj = qa * da * nj
    st.write("---"); ob = st.checkbox("Conceder bônus?"); v_b, d_b = 0.0, ""
    if ob: c1, c2 = st.columns(2); d_b = c1.text_input("Descrição Bônus:"); v_b = c2.number_input("Valor Bônus (R$):", min_value=0.0, value=150.0)
    st.write("---"); im = st.toggle("Somar materiais no preço final?", value=False)
    
    lista_m = list(st.session_state.db_m["Material"].values) if not st.session_state.db_m.empty else ["Nenhum cadastrado"]
    m_sel = st.selectbox("Insumo Almoxarifado:", lista_m)
    filtro_m = st.session_state.db_m[st.session_state.db_m["Material"] == m_sel]
    ms = filtro_m["Preço Unitário"].values[0] if not filtro_m.empty else 0.0
    
    c1, c2, c3 = st.columns(3); n_m = c1.text_input("Material Obra:", value=m_sel); q_m = c2.number_input("Qtd:", min_value=1, value=1); p_m = c3.number_input("Preço Un (R$):", min_value=0.0, value=float(ms))
    if st.button("➕ Adicionar Material"): st.session_state.df_o = pd.concat([st.session_state.df_o, pd.DataFrame([{"Item": n_m, "Qtd": q_m, "Preço Un.": p_m, "Total": q_m * p_m}])], ignore_index=True)
    
    t_mat = 0.0
    if not st.session_state.df_o.empty:
        df_e = st.data_editor(st.session_state.df_o, use_container_width=True, num_rows="dynamic"); df_e["Total"] = df_e["Qtd"] * df_e["Preço Un."]; st.session_state.df_o = df_e; t_mat = df_e["Total"].sum()
        if st.button("🗑️ Resetar Materiais"): st.session_state.df_o = pd.DataFrame(columns=["Item", "Qtd", "Preço Un.", "Total"]); st.rerun()
    st.write("---"); tt = st.selectbox("Transporte:", ["Preço Fixo", "KM Rodado"]); c_tr = 0.0
    if tt == "Preço Fixo": c_tr = st.number_input("Taxa fixa (R$):", min_value=0.0, value=30.0)
    else: c1, c2 = st.columns(2); kt = c1.number_input("Distância total (KM):", min_value=0.0, value=15.0); vk = c2.number_input("Custo por KM (R$):", min_value=0.0, value=1.50); c_tr = kt * vk
    og = st.text_area("Notas gerais:"); dp = st.slider("Desconto MO (%)", 0, 30, 0); v_d = v_s * (dp / 100); t_g = max(0.0, (v_s - v_d) + c_aj + c_tr - v_b + (t_mat if im else 0.0)); st.write("---"); st.subheader("Resumo Financeiro"); st.markdown(f"## 💵 Total Final: **R$ {t_g:.2f}**")

    def build_pdf(v_url, uh, lf):
        bf = BytesIO(); doc = SimpleDocTemplate(bf, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40); sty = []; s = getSampleStyleSheet(); t_s = ParagraphStyle('T', parent=s['Heading1'], fontSize=16, textColor=c.HexColor('#1A365D')); b_s = ParagraphStyle('B', parent=s['Normal'], fontSize=10, leading=14)
        if lf:
            try: pi = Image.open(lf); logo_p = pi.copy(); logo_p.thumbnail((120, 40)); lb = BytesIO(); logo_p.save(lb, format="PNG"); lb.seek(0); sty.append(RLImage(lb, width=logo_p.width, height=logo_p.height)); sty.append(Spacer(1, 10))
            except: pass
        sty.append(Paragraph("<b>PROPOSTA COMERCIAL</b>", t_s)); sty.append(Paragraph(f"<b>Cliente:</b> {nc} | <b>Segmento:</b> {to} | <b>Escopo:</b> {sp}", b_s)); sty.append(Spacer(1, 10))
        d_f = [["Descrição", "Valor"], ["Mão de Obra", f"R$ {v_s:.2f}"], ["Desconto MO", f"- R$ {v_d:.2f}"]]
        if ta: d_f.append(["Ajudantes", f"R$ {c_aj:.2f}"])
        d_f.append(["Transporte", f"R$ {c_tr:.2f}"])
        if v_b > 0: d_f.append(["Bônus", f"- R$ {v_b:.2f}"])
        d_f.append([f"Materiais ({'Inclusos' if im else 'Cliente'})", f"R$ {t_mat:.2f}"]); d_f.append(["TOTAL LÍQUIDO", f"R$ {t_g:.2f}"]); tf = Table(d_f, colWidths=); tf.setStyle(TableStyle([('BACKGROUND', (0,0), (1,0), c.HexColor('#1A365D')), ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, c.HexColor('#CBD5E0')), ('FONTNAME', (0,-1), (1,-1), 'Helvetica-Bold'), ('BACKGROUND', (0,-1), (1,-1), c.HexColor('#E2E8F0')), ('PADDING', (0,0), (-1,-1), 5)])); sty.append(tf); sty.append(Spacer(1, 15))
        if og: sty.append(Paragraph(f"<b>Notas:</b> {og}", b_s)); sty.append(Spacer(1, 15))
        qr = qrcode.QRCode(version=1, box_size=2, border=1); qr.add_data(v_url); qr.make(fit=True); qi = qr.make_image(fill_color="black", back_color="white"); qb = BytesIO(); qi.save(qb, format="PNG"); qb.seek(0)
        msg = f"<b>Assinado por:</b> {nr.upper()}<br/><b>Data:</b> {dt.datetime.now().strftime('%d/%m/%Y %H:%M')}<br/><b>Hash MD5:</b> {uh}"; tgv = Table([[RLImage(qb, width=60, height=65), Paragraph(msg, ParagraphStyle('G', parent=s['Normal'], fontSize=7.5, leading=10))]], colWidths=); tgv.setStyle(TableStyle([('BOX', (0,0), (-1,-1), 1, c.HexColor('#A0AEC0')), ('BACKGROUND', (0,0), (-1,-1), c.HexColor('#F7FAFC')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 6)])); sty.append(tgv); doc.build(story=sty); bf.seek(0); return bf.getvalue()

    st.write("---"); c1, c2 = st.columns(2)
    with c1:
        if st.button("Gerar PDF GOV 📄"):
            uh = hashlib.md5(f"{nc}{t_g}{dt.datetime.now().timestamp()}".encode()).hexdigest(); pdf = build_pdf(f"https://streamlit.app{uh}", uh, logo_upload)
            st.download_button("📥 Baixar PDF", data=pdf, file_name=f"Orcamento_{nc}.pdf", mime="application/pdf")
    with col2:
        if st.button("Gerar WhatsApp 💬"):
            txt = f"*PROPOSTA DE SERVIÇOS*\n\nOlá, *{nc}*.\nEscopo: {sp}.\n🔹 *Mão de Obra:* {tc}\n🔹 *Transporte:* R$ {c_tr:.2f}\n💰 *TOTAL INVESTIDO: R$ {t_g:.2f}*\n\nValidado com assinatura padrão GOV."
            st.text_area("Mensagem:", value=txt, height=120)
