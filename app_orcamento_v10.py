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

st.set_page_config(page_title="Fênix Engenharia", page_icon="🏗️", layout="centered")

if "db_v" not in st.session_state:
    st.session_state.db_v = pd.DataFrame([
        {"Tipo": "Carro", "Marca": "Fiat", "Modelo": "Uno", "Tempo de Uso (Anos)": 2, "Consumo (Km/L)": 12.0, "Valor FIPE (R$)": 35000.0, "IPVA Anual": 1400.0, "Manutenção Mensal": 200.0}
    ])

if "db_c" not in st.session_state:
    st.session_state.db_c = pd.DataFrame([
        {"Tipo de Gasto": "Contador / MEI", "Valor Mensal (R$)": 80.0},
        {"Tipo de Gasto": "Internet e Celular", "Valor Mensal (R$)": 120.0}
    ])

if "db_m" not in st.session_state:
    st.session_state.db_m = pd.DataFrame([
        {"ID": "MAT-001", "Descrição": "Cabo Flexível 2,5mm²", "Unidade": "m", "Custo (R$)": 3.60, "Margem (%)": 20, "Valor Unitário (R$)": 4.50}
    ])

if "db_s" not in st.session_state:
    st.session_state.db_s = pd.DataFrame([
        {"ID": "SRV-001", "Descrição": "Instalação de Tomada", "Unidade": "Ponto", "Valor (R$)": 50.00}
    ])

if "df_m_sel" not in st.session_state:
    st.session_state.df_m_sel = pd.DataFrame(columns=["ID", "Descrição", "Unidade", "Quantidade", "Valor Unitário (R$)", "Valor Total (R$)"])

if "df_s_sel" not in st.session_state:
    st.session_state.df_s_sel = pd.DataFrame(columns=["ID", "Descrição", "Valor (R$)"])

if "df_b_sel" not in st.session_state:
    st.session_state.df_b_sel = pd.DataFrame(columns=["ID", "Descrição", "Valor (R$)"])

st.title("🏗️ Sistema Fênix Engenharia")
st.caption("Versão v11.2 - Edição e Remoção de Itens Vinculados na Proposta")
a_orc, a_calc, a_mat, a_serv = st.tabs(["📋 Proposta Comercial", "🧮 Calcular Minha Hora", "📦 Materiais", "🛠️ Serviços"])
with a_calc:
    st.header("🧮 Preço da Hora Técnica")
    sd = st.number_input("Meta de Pró-labore mensal (R$):", min_value=0.0, value=4000.0)
    col_t1, col_t2 = st.columns(2)
    dt_m = col_t1.number_input("Dias trabalhados/mês:", min_value=1, value=22)
    hd = col_t2.number_input("Horas faturadas/dia:", min_value=1.0, value=6.0)
    ml = st.slider("Margem da empresa (%)", 0, 50, 20)
    ht = dt_m * hd
    
    with st.form("c_v", clear_on_submit=True):
        c1, c2 = st.columns(2)
        vt = c1.selectbox("Tipo:", ["Carro", "Moto", "Caminhão"])
        vm = c1.text_input("Marca:")
        tp = c1.number_input("Tempo de Posse (Anos):", min_value=0, value=1)
        mo = c2.text_input("Modelo:")
        vl = c2.number_input("Valor FIPE:", min_value=0.0, value=30000.0)
        ip = c2.number_input("IPVA Anual:", min_value=0.0, value=1200.0)
        mn = st.number_input("Manutenção Mensal:", min_value=0.0, value=200.0)
        if st.form_submit_button("💾 Salvar Veículo") and vm and mo:
            st.session_state.db_v = pd.concat([st.session_state.db_v, pd.DataFrame([{"Tipo": vt, "Marca": vm, "Modelo": mo, "Tempo de Uso (Anos)": tp, "Consumo (Km/L)": 10.0, "Valor FIPE (R$)": vl, "IPVA Anual": ip, "Manutenção Mensal": mn}])], ignore_index=True)
            st.rerun()
            
    if not st.session_state.db_v.empty:
        if st.checkbox("Excluir Veículo"):
            vr = st.selectbox("Remover veículo:", [f"{idx} - {r['Modelo']}" for idx, r in st.session_state.db_v.iterrows()])
            if st.button("Confirmar Exclusão V"):
                st.session_state.db_v = st.session_state.db_v.drop(int(vr.split(" - "))).reset_index(drop=True); st.rerun()
        st.session_state.db_v = st.data_editor(st.session_state.db_v, use_container_width=True)
        cm = ((st.session_state.db_v["Valor FIPE (R$)"].sum() * 0.10 / 12) + (st.session_state.db_v["IPVA Anual"].sum() / 12) + st.session_state.db_v["Manutenção Mensal"].sum()) / ht if ht > 0 else 0.0
    else: cm = 0.0
    
    with st.form("c_f", clear_on_submit=True):
        ft = st.text_input("Gasto Fixo:")
        fv = st.number_input("Valor Mensal:", min_value=0.0)
        if st.form_submit_button("➕ Adicionar Gasto") and ft:
            st.session_state.db_c = pd.concat([st.session_state.db_c, pd.DataFrame([{"Tipo de Gasto": ft, "Valor Mensal (R$)": fv}])], ignore_index=True); st.rerun()
            
    if not st.session_state.db_c.empty:
        if st.checkbox("Excluir Despesa"):
            gr = st.selectbox("Remover gasto:", [f"{idx} - {r['Tipo de Gasto']}" for idx, r in st.session_state.db_c.iterrows()])
            if st.button("Confirmar Exclusão D"):
                st.session_state.db_c = st.session_state.db_c.drop(int(gr.split(" - "))).reset_index(drop=True); st.rerun()
        df_f = st.session_state.db_c.copy(); df_f["Valor por Hora (R$)"] = (df_f["Valor Mensal (R$)"] / ht).round(2) if ht > 0 else 0.0
        st.session_state.db_c = st.data_editor(df_f, use_container_width=True)[["Tipo de Gasto", "Valor Mensal (R$)"]]
        cf_h = st.session_state.db_c["Valor Mensal (R$)"].sum() / ht if ht > 0 else 0.0
    else: cf_h = 0.0
    
    sl_h = sd / ht if ht > 0 else 0.0; c_op_h = cm + cf_h; h_bruto = sl_h + c_op_h; h_fin = h_bruto / (1 - (ml / 100)) if ml < 100 else h_bruto
    st.subheader("📊 Demonstrativo do Preço por Hora")
    col1, col2 = st.columns(2); col1.metric("Sua Hora de Trabalho Efetivo", f"R$ {sl_h:.2f}/h"); col2.metric("Hora de Custos Operacionais", f"R$ {c_op_h:.2f}/h")
    st.markdown(f"### 🎯 Preço Final Combinado: **R$ {h_fin:.2f}/h**")
    if st.button("🚀 Gravar Preço da Hora"): st.session_state["pr_h_f"] = round(h_fin, 2); st.success("Gravado!")
with a_mat:
    st.header("📦 Catálogo de Materiais")
    with st.form("f_m", clear_on_submit=True):
        c1, c2 = st.columns(2); md = c1.text_input("Descrição:"); mu = c1.selectbox("Unidade:", ["Un", "m", "Barra", "Saco", "Caixa", "kg"]); mc = c2.number_input("Custo:", min_value=0.0); mm = c2.slider("Margem (%):", 0, 80, 30)
        if st.form_submit_button("Salvar Material") and md:
            vf = mc / (1 - (mm / 100)) if mm < 100 else mc
            st.session_state.db_m = pd.concat([st.session_state.db_m, pd.DataFrame([{"ID": f"MAT-{len(st.session_state.db_m)+1:03d}", "Descrição": md, "Unidade": mu, "Custo (R$)": mc, "Margem (%)": mm, "Valor Unitário (R$)": round(vf, 2)}])], ignore_index=True); st.rerun()
    if not st.session_state.db_m.empty:
        if st.checkbox("Remover Material"):
            mr = st.selectbox("Deletar item do catálogo:", [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_m.iterrows()])
            st.session_state.db_m = st.session_state.db_m[st.session_state.db_m["ID"] != mr.split(" - ")].reset_index(drop=True); st.rerun()
        df_me = st.data_editor(st.session_state.db_m, use_container_width=True)
        df_me["Valor Unitário (R$)"] = (df_me["Custo (R$)"] / (1 - (df_me["Margem (%)"].clip(0,99)/100))).round(2); st.session_state.db_m = df_me

with a_serv:
    st.header("🛠️ Catálogo de Serviços")
    with st.form("f_s", clear_on_submit=True):
        c1, c2 = st.columns(2); sd = c1.text_input("Descrição:"); su = c1.selectbox("Unidade Cobrança:", ["Ponto", "M²", "Diária", "Hora", "Empreitada"]); sv = c2.number_input("Preço Sugerido:", min_value=0.0)
        if st.form_submit_button("Salvar Serviço") and sd:
            st.session_state.db_s = pd.concat([st.session_state.db_s, pd.DataFrame([{"ID": f"SRV-{len(st.session_state.db_s)+1:03d}", "Descrição": sd, "Unidade": su, "Valor (R$)": round(sv, 2)}])], ignore_index=True); st.rerun()
    if not st.session_state.db_s.empty:
        if st.checkbox("Remover Serviço"):
            sr = st.selectbox("Deletar serviço do catálogo:", [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_s.iterrows()])
            st.session_state.db_s = st.session_state.db_s[st.session_state.db_s["ID"] != sr.split(" - ")].reset_index(drop=True); st.rerun()
        st.session_state.db_s = st.data_editor(st.session_state.db_s, use_container_width=True)
with a_orc:
    st.subheader("📋 Configuração da Proposta Comercial - Fênix Engenharia")
    logo_upload = st.file_uploader("Upload da Logomarca (Direita do PDF):", type=["png", "jpg", "jpeg"])
    wpp_num = st.text_input("WhatsApp para QR Code (Apenas Números):", value="3152769953")
    nc = st.text_input("Nome do Cliente:", value="Fenix Engenharia e Comercio LTDA")
    ds_serv = st.text_area("Descrição Geral do Serviço Executado:", value="Execução de Infraestrutura e Reforma Técnica.")
    c1, c2, c3 = st.columns(3); val_d = c1.number_input("Validade (Dias):", min_value=1, value=10); dt_e = c2.date_input("Emissão:", value=dt.date.today()); dt_v = c3.date_input("Válido Até:", value=dt.date.today()+dt.timedelta(days=int(val_d)))
    
    st.write("---"); st.subheader("👷 Mão de Obra")
    lista_s = [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_s.iterrows()] if not st.session_state.db_s.empty else []
    if lista_s:
        s_sel = st.selectbox("Vincular Serviço à Proposta:", lista_s)
        if st.button("➕ Vincular Serviço"):
            it_s = st.session_state.db_s[st.session_state.db_s["ID"] == s_sel.split(" - ")].iloc
            st.session_state.df_s_sel = pd.concat([st.session_state.df_s_sel, pd.DataFrame([{"ID": it_s["ID"], "Descrição": it_s["Descrição"], "Valor (R$)": it_s["Valor (R$)"]}])], ignore_index=True)
    if not st.session_state.df_s_sel.empty:
        if st.checkbox("Excluir Serviço Vinculado"):
            s_rem = st.selectbox("Remover serviço da proposta:", [f"{idx} - {r['Descrição']}" for idx, r in st.session_state.df_s_sel.iterrows()])
            if st.button("❌ Confirmar Remoção Serviço"): st.session_state.df_s_sel = st.session_state.df_s_sel.drop(int(s_rem.split(" - "))).reset_index(drop=True); st.rerun()
        st.session_state.df_s_sel = st.data_editor(st.session_state.df_s_sel, use_container_width=True)
        t_mo = st.session_state.df_s_sel["Valor (R$)"].sum()
    else: t_mo = 0.0

    st.write("---"); st.subheader("📦 Materiais")
    lista_m = [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_m.iterrows()] if not st.session_state.db_m.empty else []
    if lista_m:
        m_sel = st.selectbox("Vincular Material à Proposta:", lista_m); q_sol = st.number_input("Quantidade Requerida:", min_value=1, value=1)
        if st.button("➕ Vincular Material"):
            it_m = st.session_state.db_m[st.session_state.db_m["ID"] == m_sel.split(" - ")].iloc
            st.session_state.df_m_sel = pd.concat([st.session_state.df_m_sel, pd.DataFrame([{"ID": it_m["ID"], "Descrição": it_m["Descrição"], "Unidade": it_m["Unidade"], "Quantidade": q_sol, "Valor Unitário (R$)": it_m["Valor Unitário (R$)"], "Valor Total (R$)": q_sol*it_m["Valor Unitário (R$)"]}])], ignore_index=True)
    if not st.session_state.df_m_sel.empty:
        if st.checkbox("Excluir Material Vinculado"):
            m_rem = st.selectbox("Remover produto da proposta:", [f"{idx} - {r['Descrição']}" for idx, r in st.session_state.df_m_sel.iterrows()])
            if st.button("❌ Confirmar Remoção Material"): st.session_state.df_m_sel = st.session_state.df_m_sel.drop(int(m_rem.split(" - "))).reset_index(drop=True); st.rerun()
        df_me_edit = st.data_editor(st.session_state.df_m_sel, use_container_width=True)
        df_me_edit["Valor Total (R$)"] = df_me_edit["Quantidade"] * df_me_edit["Valor Unitário (R$)"]
        st.session_state.df_m_sel = df_me_edit
        t_mat = st.session_state.df_m_sel["Valor Total (R$)"].sum()
    else: t_mat = 0.0

    st.write("---"); st.subheader("🎁 Bônus")
    with st.form("f_b", clear_on_submit=True):
        bd, bv = st.text_input("Cortesia Comercial:"), st.number_input("Valor Cortesia:", min_value=0.0, value=150.0)
        if st.form_submit_button("➕ Vincular Bônus") and bd:
            st.session_state.df_b_sel = pd.concat([st.session_state.df_b_sel, pd.DataFrame([{"ID": f"BON-{len(st.session_state.df_b_sel)+1:03d}", "Descrição": bd, "Valor (R$)": bv}])], ignore_index=True); st.rerun()
    if not st.session_state.df_b_sel.empty:
        if st.checkbox("Excluir Bônus Vinculado"):
            b_rem = st.selectbox("Remover bônus da proposta:", [f"{idx} - {r['Descrição']}" for idx, r in st.session_state.df_b_sel.iterrows()])
            if st.button("❌ Confirmar Remoção Bônus"): st.session_state.df_b_sel = st.session_state.df_b_sel.drop(int(b_rem.split(" - "))).reset_index(drop=True); st.rerun()
        st.session_state.df_b_sel = st.data_editor(st.session_state.df_b_sel, use_container_width=True)
        t_bon = st.session_state.df_b_sel["Valor (R$)"].sum()
    else: t_bon = 0.0

    st.write("---"); st.subheader("📈 Total Bônus / Subtotal / Desconto")
    ds_s = st.slider("Desconto Comercial Aplicado (%):", 0, 30, 0)
    sub_bruto = t_mo + t_mat; v_desc = sub_bruto * (ds_s / 100)
    tot_cartao = sub_bruto * 1.08; tot_vista = max(0.0, sub_bruto - t_bon - v_desc)
    
    st.write(f"**Total Bônus:** R$ {t_bon:.2f} | **Subtotal:** R$ {sub_bruto:.2f} | **Desconto:** R$ {v_desc:.2f}")
    st.warning(f"💳 **TOTAL A PAGAR (ATÉ 10X CARTÃO): R$ {tot_cartao:.2f}**")
    st.success(f"💰 **TOTAL À VISTA (DINHEIRO OU PIX): R$ {tot_vista:.2f}**")

    def build_pdf_fenix(lf, q_url, h_val):
        bf = BytesIO(); doc = SimpleDocTemplate(bf, pagesize=letter, rightMargin=35, leftMargin=45, topMargin=40, bottomMargin=40); sty = []; s = getSampleStyleSheet()
        t_sty = ParagraphStyle('T', parent=s['Heading1'], fontSize=13, textColor=colors.HexColor('#1A365D')); b_sty = ParagraphStyle('B', parent=s['Normal'], fontSize=9, leading=13)
        qr = qrcode.QRCode(version=1, box_size=2, border=0); qr.add_data(q_url); qr.make(fit=True); qb = BytesIO(); qr.make_image(fill_color="black", back_color="white").save(qb, format="PNG"); qb.seek(0)
        tx_emp = "<b>FÊNIX ENGENHARIA</b> - CNPJ: 52.769.953/0001-12<br/>Endereço: Avenida Getulio Vargas, nº 671, 9º Andar, Sala 1.051, Bairro Savassi, Belo Horizonte - MG, Cep: 30112-021"
        l_bx = Paragraph("", b_sty)
        if lf:
            try: pi = Image.open(lf); logo_p = pi.copy(); logo_p.thumbnail((90, 40)); lb = BytesIO(); logo_p.save(lb, format="PNG"); lb.seek(0); l_bx = RLImage(lb, width=logo_p.width, height=logo_p.height)
            except: pass
        t_hdr = Table([[RLImage(BytesIO(qb.getvalue()), width=45, height=45), Paragraph(tx_emp, ParagraphStyle('C', parent=s['Normal'], fontSize=8, leading=11, alignment=1)), l_bx]], colWidths=); t_hdr.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'MIDDLE')])); sty.append(t_hdr); sty.append(Spacer(1, 10))
        sty.append(Paragraph(f"<b>Descrição Técnica do Serviço:</b> {ds_serv}", b_sty)); sty.append(Spacer(1, 4))
        sty.append(Paragraph(f"<b>Validade:</b> {val_d} dias | <b>Emissão:</b> {dt_e.strftime('%d/%m/%Y')} | <b>Válido Até:</b> {dt_v.strftime('%d/%m/%Y')}", b_sty)); sty.append(Spacer(1, 8))
        
        sty.append(Paragraph("<b>Mão de Obra</b>", t_sty))
        d_mo = [["ID", "Descrição Mão de Obra", "Valor"]]
        for _, r in st.session_state.df_s_sel.iterrows(): d_mo.append([r["ID"], r["Descrição"], f"R$ {r['Valor (R$)']:.2f}"])
        t1 = Table(d_mo, colWidths=); t1.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1A365D')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0,0), (-1,-1), 4)])); sty.append(t1); sty.append(Spacer(1, 10))
        
        sty.append(Paragraph("<b>Materiais</b>", t_sty))
        d_ma = [["ID", "Descrição", "Un", "Qtd", "Val Un", "Val Tot"]]
        for _, r in st.session_state.df_m_sel.iterrows(): d_ma.append([r["ID"], r["Descrição"], r["Unidade"], str(int(r["Quantidade"])), f"R$ {r['Valor Unitário (R$)']:.2f}", f"R$ {r['Valor Total (R$)']:.2f}"])
        t2 = Table(d_ma, colWidths=); t2.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2B6CB0')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0,0), (-1,-1), 4)])); sty.append(t2); sty.append(Spacer(1, 10))
        
        if t_bon > 0:
            sty.append(Paragraph("<b>Bônus</b>", t_sty))
            d_bo = [["ID", "Descrição", "Valor"]]
            for _, r in st.session_state.df_b_sel.iterrows(): d_bo.append([r["ID"], r["Descrição"], f"R$ {r['Valor (R$)']:.2f}"])
            t3 = Table(d_bo, colWidths=); t3.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A5568')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('PADDING', (0,0), (-1,-1), 4)])); sty.append(t3); sty.append(Spacer(1, 10))
        
        d_ch = [["Total Bônus", f"R$ {t_bon:.2f}"], ["Subtotal", f"R$ {sub_bruto:.2f}"], [f"Desconto ({ds_s}%)", f"R$ {v_desc:.2f}"], ["TOTAL A PAGAR (ATÉ 10X CARTÃO)", f"R$ {tot_cartao:.2f}"], ["TOTAL À VISTA (DINHEIRO OU PIX)", f"R$ {tot_vista:.2f}"]]
        t4 = Table(d_ch, colWidths=); t4.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('FONTNAME', (0,-2), (1,-1), 'Helvetica-Bold'), ('BACKGROUND', (0,-2), (0,-2), colors.HexColor('#FED7D7')), ('BACKGROUND', (0,-1), (1,-1), colors.HexColor('#C6F6D5')), ('PADDING', (0,0), (-1,-1), 4)])); sty.append(t4); doc.build(sty); bf.seek(0); return bf.getvalue()

    if st.button("🚀 Chancelar Proposta Comercial"):
        hv = hashlib.md5(f"{nc}{tot_vista}".encode()).hexdigest(); l_wp = f"https://whatsapp.com{wpp_num}&text=Aprovar%20Orcamento%20{hv}"
        pdf = build_pdf_fenix(logo_upload, l_wp, hv)
        st.download_button(label="📥 Baixar Proposta Comercial em PDF", data=pdf, file_name=f"Proposta_Fenix_{nc}.pdf", mime="application/pdf")
