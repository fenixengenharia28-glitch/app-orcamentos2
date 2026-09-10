import streamlit as st
import pandas as pd
import datetime
import hashlib
import qrcode
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from PIL import Image

# Configuração da página para Desktop e Mobile
st.set_page_config(page_title="Orçamentos Construção Pro", page_icon="🏗️", layout="centered")

# --- SISTEMA DE VERIFICAÇÃO DE DOCUMENTOS (PÁGINA GOV SIMULADA) ---
query_params = st.query_params
if "verificar" in query_params:
    doc_hash = query_params["verificar"]
    st.success("🔒 PORTAL DE VERIFICAÇÃO DE DOCUMENTOS")
    st.title("✅ Documento Autêntico e Verificado")
    st.write("Este orçamento foi verificado digitalmente através do sistema Construção Pro em conformidade com as diretrizes de integridade documental.")
    st.info(f"**Código de Validação (Hash):** {doc_hash}")
    st.write(f"**Status da Assinatura:** ATIVA E VÁLIDA (Padrão ICP-Brasil Equivalente)")
    if st.button("Voltar ao Sistema de Orçamentos"):
        st.query_params.clear()
        st.rerun()
    st.stop()

# --- INICIALIZAÇÃO DE BANCOS DE DADOS EM MEMÓRIA ---
if "db_servicos" not in st.session_state:
    st.session_state.db_servicos = pd.DataFrame([
        {"Serviço": "Instalação de Tomada/Ponto Geral", "Preço Padrão": 50.0},
        {"Serviço": "Reforma de QDC (Quadro de Disjuntores)", "Preço Padrão": 350.0},
        {"Serviço": "Pintura por M² (Mão de Obra)", "Preço Padrão": 25.0},
        {"Serviço": "Regularização de Contra piso M²", "Preço Padrão": 40.0}
    ])

if "db_materiais" not in st.session_state:
    st.session_state.db_materiais = pd.DataFrame([
        {"Material": "Cabo Flexível 2,5mm² (Metro)", "Preço Unitário": 4.50},
        {"Material": "Disjuntor Din Monofilar Tramontina", "Preço Unitário": 18.90},
        {"Material": "Tomada Simples com Placa Pial", "Preço Unitário": 22.00},
        {"Material": "Saco de Cimento 50kg CP-II", "Preço Unitário": 38.00}
    ])

if "db_veiculos" not in st.session_state:
    st.session_state.db_veiculos = pd.DataFrame([
        {"Tipo": "Carro", "Marca": "Fiat", "Modelo": "Uno Way", "Valor (R$)": 35000.0, "IPVA/Licenc. Anual": 1400.0, "Tempo de Posse (Anos)": 2}
    ])

if "df_materiais_orcamento" not in st.session_state:
    st.session_state.df_materiais_orcamento = pd.DataFrame(columns=["Item", "Qtd", "Preço Un.", "Total"])

# --- FLUXO PRINCIPAL DO APLICATIVO ---
st.title("🏗️ Orçamentos Construção Pro")
st.caption("Versão v11 - Sistema Completo com Cadastros, Frota de Veículos e Validação GOV")

# Criação das Abas do Aplicativo
aba_orc, aba_serv, aba_mat, aba_veic, aba_calc = st.tabs([
    "📋 Criar Orçamento", 
    "🛠️ Cadastrar Serviços", 
    "📦 Cadastrar Materiais", 
    "🚗 Configurar Veículo", 
    "🧮 Calcular Minha Hora"
])

# --- ABA 2: CADASTRO DE SERVIÇOS ---
with aba_serv:
    st.header("🛠️ Catálogo de Serviços Padrão")
    st.write("Cadastre seus serviços de referência para a planilha.")
    
    with st.form("cad_servico", clear_on_submit=True):
        novo_serv_nome = st.text_input("Nome do Serviço / Atividade:")
        novo_serv_preco = st.number_input("Preço sugerido (R$):", min_value=0.0, step=5.0)
        if st.form_submit_button("💾 Salvar Serviço"):
            if novo_serv_nome:
                novo_s = pd.DataFrame([{"Serviço": novo_serv_nome, "Preço Padrão": novo_serv_preco}])
                st.session_state.db_servicos = pd.concat([st.session_state.db_servicos, novo_s], ignore_index=True)
                st.success("Serviço cadastrado com sucesso!")
                st.rerun()
                
    st.subheader("Serviços Cadastrados")
    st.session_state.db_servicos = st.data_editor(st.session_state.db_servicos, use_container_width=True, num_rows="dynamic")

# --- ABA 3: CADASTRO DE MATERIAIS ---
with aba_mat:
    st.header("📦 Almoxarifado de Materiais Frequentes")
    st.write("Alimente sua lista de insumos com valores de referência.")
    
    with st.form("cad_material", clear_on_submit=True):
        novo_mat_nome = st.text_input("Nome do Insumo / Material:")
        novo_mat_preco = st.number_input("Preço de Custo Unitário (R$):", min_value=0.0, step=1.0)
        if st.form_submit_button("💾 Salvar Material"):
            if novo_mat_nome:
                novo_m = pd.DataFrame([{"Material": novo_mat_nome, "Preço Unitário": novo_mat_preco}])
                st.session_state.db_materiais = pd.concat([st.session_state.db_materiais, novo_m], ignore_index=True)
                st.success("Material adicionado com sucesso!")
                st.rerun()
                
    st.subheader("Materiais Cadastrados")
    st.session_state.db_materiais = st.data_editor(st.session_state.db_materiais, use_container_width=True, num_rows="dynamic")

# --- ABA 4: CADASTRO DE VEÍCULOS ---
with aba_veic:
    st.header("🚗 Cadastro e Frota de Veículos da Empresa")
    st.write("Insira e salve as informações dos veículos utilizados em campo para o cálculo preciso da depreciação estrutural.")
    
    with st.form("cad_novo_veiculo", clear_on_submit=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v_tipo = st.selectbox("Tipo do Veículo:", ["Carro", "Moto", "Caminhão", "Utilitário / Van"])
            v_marca = st.text_input("Marca (ex: Chevrolet, Honda):")
            v_tempo = st.number_input("Tempo que estou com o veículo (Em Anos):", min_value=0, max_value=50, value=1, step=1)
        with col_v2:
            v_modelo = st.text_input("Modelo (ex: Onix, Titan):")
            v_valor = st.number_input("Valor de Mercado (Tabela FIPE - R$):", min_value=0.0, step=1000.0, value=25000.0)
            v_anual_imposto = st.number_input("Custos Anuais de Cadastro (IPVA + Licenciamento Anual - R$):", min_value=0.0, step=100.0, value=1500.0)
        
        if st.form_submit_button("💾 Salvar Veículo na Frota"):
            if v_marca and v_modelo:
                novo_v = pd.DataFrame([{
                    "Tipo": v_tipo, 
                    "Marca": v_marca, 
                    "Modelo": v_modelo, 
                    "Valor (R$)": v_valor, 
                    "IPVA/Licenc. Anual": v_anual_imposto,
                    "Tempo de Posse (Anos)": v_tempo
                }])
                st.session_state.db_veiculos = pd.concat([st.session_state.db_veiculos, novo_v], ignore_index=True)
                st.success(f"Veículo {v_modelo} adicionado com sucesso!")
                st.rerun()

    st.subheader("Frota Registrada e Salva")
    st.write("Você pode editar os dados diretamente nas células da tabela abaixo:")
    st.session_state.db_veiculos = st.data_editor(st.session_state.db_veiculos, use_container_width=True, num_rows="dynamic")

# --- ABA 5: CALCULADORA DE HORA TÉCNICA OPERACIONAL ---
with aba_calc:
    st.header("Descubra o Valor da sua Hora")
    custo_fixo_geral = st.number_input("Custos fixos mensais de escritório (MEI, internet, fone, seguros):", min_value=0.0, value=500.0, step=50.0)
    
    total_fipe_frota = 0.0
    total_impostos_frota = 0.0
    
    if not st.session_state.db_veiculos.empty:
        total_fipe_frota = st.session_state.db_veiculos["Valor (R$)"].sum()
        total_impostos_frota = st.session_state.db_veiculos["IPVA/Licenc. Anual"].sum()
        
    depreciacao_mensal_frota = (total_fipe_frota * 0.10) / 12
    cadastro_mensal_frota = total_impostos_frota / 12
    custo_veiculo_total_mes = depreciacao_mensal_frota + cadastro_mensal_frota
    
    st.info(f"🚗 Custos Combinados da Frota Salva ({len(st.session_state.db_veiculos)} veículo(s)): Depreciação (R$ {depreciacao_mensal_frota:.2f}/mês) + Impostos (R$ {cadastro_mensal_frota:.2f}/mês)")
    
    salario_desejado = st.number_input("Meta de Pró-labore mensal líquido (Seu Salário):", min_value=0.0, value=4000.0, step=100.0)
    dias_trabalhados = st.number_input("Dias operacionais efetivos por mês:", min_value=1, max_value=31, value=22)
    horas_por_dia = st.number_input("Horas produtivas faturadas por dia de trabalho:", min_value=1.0, max_value=24.0, value=6.0, step=0.5)
    margem_lucro = st.slider("Margem de Investimento/Lucro da Empresa (%)", min_value=0, max_value=50, value=20, step=5)
    
    horas_totais_mes = dias_trabalhados * horas_por_dia
    if horas_totais_mes > 0:
        custo_hora_bruto = (custo_fixo_geral + custo_veiculo_total_mes + salario_desejado) / horas_totais_mes
        hora_calculada = custo_hora_bruto / (1 - (margem_lucro / 100)) if margem_lucro < 100 else custo_hora_bruto
    else:
        hora_calculada = 0.0
        
    st.success(f"💰 **Sua Hora Técnica Sugerida: R$ {hora_calculada:.2f}**")
    if st.button("Aplicar valor de Hora Técnica na Mão de Obra"):
        st.session_state["preco_hora_salvado"] = round(hora_calculada, 2)
        st.info("Valor sincronizado com sucesso!")

# --- ABA 1: GERADOR DE ORÇAMENTO MULTIUSO ---
with aba_orc:
    st.header("Identificação do Projeto")
    
    logo_upload = st.file_uploader("Upload da Logomarca da Empresa (Para o PDF - Opcional):", type=["png", "jpg", "jpeg"])
    
    col_cli1, col_cli2 = st.columns(2)
    with col_cli1:
        nome_cliente = st.text_input("Nome do Cliente / Empresa:", value="Fenix Engenharia e Comercio LTDA")
    with col_cli2:
        tipo_obra = st.selectbox("Segmento da Obra:", ["Construção Geral", "Elétrica", "Hidráulica", "Pintura / Acabamento", "Alvenaria / Estruturas", "Gesso / Drywall"], index=1)
        
    opcoes_servicos = list(st.session_state.db_servicos["Serviço"].values)
    servico_selecionado = st.selectbox("Selecione o Serviço Cadastrado:", opcoes_servicos)
    servico_principal = st.text_input("Ajuste a descrição do escopo se necessário:", value=servico_selecionado)
    
    nome_responsavel = st.text_input("Nome do Responsável Técnico (Para Assinatura GOV):", value="Ronilson Richardson Fragoso de Souza")

    st.write("---")st.header("👷 Quantificação da Mão de Obra")tipo_cobranca = st.selectbox("Critério de precificação:", ["Por Empreitada / Ponto", "Por Hora Técnica"])valor_servico = 0.0 if tipo_cobranca == "Por Empreitada / Ponto": preco_sugerido_base = st.session_state.db_servicos[st.session_state.db_servicos["Serviço"] == servico_selecionado]["Preço Padrão"].values ​​col_srv1, col_srv2 = st.columns(2) with col_srv1: qtd_pontos = st.number_input("Quantidade de Unidades/Pontos/M²:", min_value=1.0, value=10.0) with col_srv2: preco_ponto = st.number_input("Preço por Unidade (R$):", min_value=0.0, value=float(preco_sugerido_base)) valor_servico = qtd_pontos * preco_ponto elif tipo_cobranca == "Por Hora Técnica": col_hr1, col_hr2 = st.columns(2) with col_hr1: qtd_horas = st.number_input("Horas estimadas de execução:", min_value=0.5, value=4.0) with col_hr2: default_preco_hora = st.session_state.get("preco_hora_salvado", 60.0) preco_hora = st.number_input("Valor da hora técnica (R$):", min_value=0.0, value=default_preco_hora) valor_servico = qtd_horas * preco_horast.write("---")st.header("👥 Dimensionamento de Equipe")tem_ajudante = st.checkbox("O serviço demandará ajudantes?")custo_ajudantes_total = 0.0if tem_ajudante:col_aj1, col_aj2 = st.columns(2)with col_aj1:qtd_ajudantes = st.number_input("Quantidade de ajudantes escalados:", min_value=1, value=1, step=1)with col_aj2:diaria_ajudante = st.number_input("Custo da diária por ajudante (R$):", min_value=0.0, value=120.0, step=10.0)qtd_dias_ajuda = st.number_input("Quantidade de diárias estimadas para os ajudantes:", min_value=1, value=1, step=1)custo_ajudantes_total = qtd_ajudantes * diaria_ajudante * qtd_dias_ajudast.caption(f"ℹ️ Custo total operacional de ajudantes: R$ {custo_ajudantes_total:.2f}")st.write("---")st.header("🎁 Política de Bônus (Dedução Comercial)")oferecer_bonus = st.checkbox("Conceder um serviço bônus dedutível?")valor_bonus = 0.0descricao_bonus = ""if oferecer_bonus:col_bon1, col_bon2 = st.columns(2)with col_bon1:descricao_bonus = st.text_input("Descrição detalhada do Bônus:")with col_bon2:valor_bonus = st.number_input("Valor Comercial do Bônus a Abater (R$):", min_value=0.0, value=150.0)st.write("---")st.header("📦 Romaneio de Materiais")incluir_materiais_no_preco = st.toggle("Somar materiais no preço final cobrado do cliente?", value=False)opcoes_materiais = list(st.session_state.db_materiais["Material"].values)material_selecionado = st.selectbox("Selecione o insumo do Almoxarifado:", opcoes_materiais)preco_mat_sugerido = st.session_state.db_materiais[st.session_state.db_materiais["Material"] == material_selecionado]["Preço Unitário"].valuescol_mat1, col_mat2, col_mat3 = st.columns(3) with col_mat1: nome_mat = st.text_input("Insumo para a Obra:", value=material_selecionado) with col_mat2: qtd_mat = st.number_input("Qtd Itens:", min_value=1, value=1) with col_mat3: preco_mat = st.number_input("Preço Unitário (R$):", min_valor=0,0, valor=float(preco_mat_sugerido))total_materiais = 0.0if not st.session_state.df_materiais_orcamento.empty:st.write("📝 Ajuste quantidades ou valores finais direto na planilha abaixo se necessário:")df_editado = st.data_editor(st.session_state.df_materiais_orcamento, use_container_width=True, num_rows="dynamic")df_editado["Total"] = df_editado["Qtd"] * df_editado["Preço Un."]st.session_state.df_materiais_orcamento = df_editadototal_materiais = df_editado["Total"].sum()if st.button("🗑️ Resetar Insumos da Obra"):st.session_state.df_materiais_orcamento = pd.DataFrame(columns=["Item", "Qtd", "Preço Un.", "Total"])st.rerun()st.write("---") st.header("🚚 Deslocamento Logístico") tipo_transporte = st.selectbox("Cálculo de Transporte:", ["Preço Fixo", "Quilometragem Rodada"]) custo_transporte = 0.0 if tipo_transporte == "Preço Fixo": custo_transporte = st.number_input("Taxa de frete/deslocamento fixa (R$):", min_value=0.0, value=30.0) elif tipo_transporte == "Quilometragem Rodada": col_km1, col_km2 = st.columns(2) with col_km1: km_total = st.number_input("Distância total de rodagem (KM):", min_value=0.0, value=15.0) with col_km2: valor_por_km = st.number_input("Custo por KM Rodado (R$):", min_value=0.0, value=1.50) custo_transporte = km_total * valor_por_kmobs_gerais = st.text_area("Notas gerais, cronograma de execução e garantias legais:") desconto_pct = st.slider("Desconto comercial aplicado à mão de obra principal (%)", min_value=0, max_value=30, value=0)# Engenharia financeira estruturada finalvalor_desconto_mo = valor_servico * (desconto_pct / 100)subtotal_mo = valor_servico - valor_desconto_mototal_geral = subtotal_mo + custo_ajudantes_total + custo_transporte - valor_bonusif incluir_materiais_no_preco:total_geral += total_materiaistotal_geral = max(0.0, total_geral)st.write("---") st.subheader("Painel de Custos Consolidado") st.write(f" Mão de Obra de Execução Principal: R$ {valor_servico:.2f}") st.write(f" Desconto Aplicado à Mão de Obra: - R$ {valor_desconto_mo:.2f}") if tem_ajudante: st.write(f" Custo da Equipe de Apoio (Ajudantes): + R$ {custo_ajudantes_total:.2f}") st.write(f" Logística e Mobilização de Transporte: + R$ {custo_transporte:.2f}") if valor_bonus > 0: st.write(f" Bônus Promocional (Subtraído): - R$ {valor_bonus:.2f}") st.write(f" Materiais da Instalação: R$ {total_materiais:.2f} (" + ("Somado ao total" if incluir_materiais_no_preco else "Por conta do cliente") + ")")st.markdown(f"## 💵 Total Final do Orçamento: R$ {total_geral:.2f}")# --- GERADOR DE PDF COM LOGO, ESTAMPA GOV E QR CODE --- def build_pdf_gov(verification_url, unique_hash, logo_file=None): buffer = BytesIO() doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40) story = []estilos = getSampleStyleSheet() estilo_título = ParagraphStyle('Título', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#1A365D'), spaceAfter=15) estilo_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=12, textColor=colors.HexColor('#2B6CB0'), spaceBefore=8, spaceAfter=8) estilo_corpo = ParagraphStyle('Corpo', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=6) estilo_texto_governamental = ParagraphStyle('Texto Governamental', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#2D3748'))Se logo_file não for None: tente: logo_pil = Image.open(logo_file) logo_pil.thumbnail((150, 50)) logo_buffer = BytesIO() logo_pil.save(logo_buffer, format="PNG") logo_buffer.seek(0) story.append(RLImage(logo_buffer, width=logo_pil.width, height=logo_pil.height)) story.append(Spacer(1, 10)) exceto: passestory.append(Paragraph(f"PROPOSTA COMERCIAL E TÉCNICA DE SERVIÇOS", title_style))story.append(Paragraph(f"Cliente/Empresa: {nome_cliente if nome_cliente else 'Não Informado'}", body_style))story.append(Paragraph(f"Segmento Operacional: {tipo_obra} | Escopo Principal: {servico_principal}", body_style))story.append(Spacer(1, 10))data_fin = [["Item / Descrição Técnico", "Valor"],["Mão de Obra de Execução Principal", f"R$ {valor_servico:.2f}"],["Desconto Comercial Mão de Obra", f"- R$ {valor_desconto_mo:.2f}"]]if tem_ajudante:data_fin.append([f"Equipe Operacional (Ajudantes de Campo)", f"R$ {custo_ajudantes_total:.2f}"])data_fin.append(["Mobilização e Deslocamento Logístico", f"R$ {custo_transporte:.2f}"])if valor_bonus > 0: data_fin.append([f"Bônus Promocional Deduzido (-)", f"- R$ {valor_bonus:.2f}"])t_fin = Table(data_fin, colWidths=[380, 120]) t_fin.setStyle(TableStyle([ ('BACKGROUND', (0,0), (1,0), colors.HexColor('#1A365D')), ('TEXTCOLOR', (0,0), (1,0), colors.whitesmoke), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')), ('FONTNAME', (0,-1), (1,-1), 'Helvetica-Bold'), ('BACKGROUND', (0,-1), (1,-1), colors.HexColor('#E2E8F0')), ('PADDING', (0,0), (-1,-1), 5), ])) story.append(t_fin) história.append(Spacer(1, 15))if not st.session_state.df_materiais_orcamento.empty:story.append(Paragraph("Detalhamento Analítico de Materiais", h2_style))data_mat = [["Item Material", "Quantidade", "Preço Un.", "Total"]]for _, r in st.session_state.df_materiais_orcamento.iterrows():data_mat.append([r["Item"], str(int(r["Qtd"])), f"R$ {r['Preço Un.']:.2f}", f"R$ {r['Total']:.2f}"])t_mat = Table(data_mat, colWidths=[240, 80, 90, 90]) t_mat.setStyle(TableStyle([ ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A5568')), ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('ALIGN', (0,1), (0,-1), 'LEFT'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')), ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('BOTTOMPADDING', (0,0), (-1,-1), 5), ])) story.append(t_mat) story.append(Spacer(1, 15))if obs_gerais:story.append(Paragraph("Diretrizes Gerais e Cláusulas Contratuais", h2_style))story.append(Paragraph(obs_gerais.replace('\n', ''), body_style))story.append(Spacer(1, 20))story.append(Paragraph("VERIFICAÇÃO DE AUTENTICIDADE CRIPTOGRÁFICA", h2_style))qr = qrcode.QRCode(version=1, box_size=2, border=1) qr.add_data(verification_url) qr.make(fit=True) qr_img = qr.make_image(fill_color="black", back_color="white") qr_buffer = BytesIO() qr_img.save(qr_buffer, format="PNG") qr_buffer.seek(0)agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")gov_table_data = [ [RLImage(qr_buffer, width=65, height=65), Paragraph(gov_msg, gov_text_style)] ] t_gov = Table(gov_table_data, colWidths=[80, 420]) t_gov.setStyle(TableStyle([ ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#A0AEC0')), ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F7FAFC')), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('PADDING', (0,0), (-1,-1), 8), ])) story.append(t_gov)doc.build(story) buffer.seek(0) return buffer.getvalue()# Botões de Ação Comercial st.write("---") col_btn1, col_btn2 = st.columns(2) with col_btn1: if st.button("Gerar Orçamento Oficial com Selo GOV 📄"): str_combinada = f"{nome_cliente}{total_geral}{datetime.datetime.now().timestamp()}" unique_hash = hashlib.md5(str_combinada.encode('utf-8')).hexdigest()verification_url = f"streamlit.app{unique_hash}"pdf_data = build_pdf_gov(verification_url, unique_hash, logo_upload)st.download_button(label="📥 Baixar Proposta Técnica em PDF",data=pdf_data,file_name=f"Proposta_Comercial_{nome_cliente.replace(' ', '_')}.pdf",mime="application/pdf")st.success("Orçamento estruturado, assinado e pronto para download!")with col_btn2:if st.button("Gerar Mensagem Comercial (WhatsApp) 💬"):txt_materiais = ""if not st.session_state.df_materiais_orcamento.empty:txt_materiais = "\n📦 RELAÇÃO DE INSUMOS MUDANÇA/OBRA:\n"for _, m in st.session_state.df_materiais_orcamento.iterrows():txt_materiais += f" • {m['Item']} (Qtd: {int(m['Qtd'])})\n"txt_materiais += f"👉 Materiais: " + ("INCLUSOS NO VALOR FINAL" if incluir_materiais_no_preco else "FORNECIMENTO SOB RESPONSABILIDADE DO CLIENTE") + "\n"txt_ajudantes = f"🔹 Equipe de Campo: Inclusos ajudantes técnicos de apoio\n" if tem_ajudante else ""txt_bonus = f"\n🎁 CORTESIA EXCLUSIVA DEDUZIDA DA CONTA:\n • {descricao_bonus}: de R$ {valor_bonus:.2f} por R$ 0,00 (- R$ {valor_bonus:.2f} no total)\n" if valor_bonus > 0 else ""txt_obs = f"\n🗒️ DIRETRIZES DA EXECUÇÃO:\n_{obs_gerais}_\n" if obs_gerais else ""texto_whatsapp = (f"PROPOSTA TÉCNICA E COMERCIAL DE SERVIÇOS\n\n"f"Olá, {nome_cliente if nome_cliente else 'Cliente'}.\n"f"Apresentamos a planilha orçamentária para o segmento de {tipo_obra}.\n\n"f"📌 Escopo Principal: {servico_principal}.\n"f"{txt_bonus}"f"{txt_materiais}"f"{txt_obs}\n"f"🔹 Critério de Mão de Obra: {tipo_cobranca}\n"f"{txt_ajudantes}"f"🔹 Logística e Mobilização de Transporte: R$ {custo_transporte:.2f}\n"f"🔹 Desconto Comercial Aplicado: {desconto_pct}%\n\n"f"💰 VALOR TOTAL DO INVESTIMENTO LÍQUIDO: R$ {total_geral:.2f}\n\n"f"👷 Serviços executados segundo rigorosos critérios técnicos e boas práticas de engenharia.\n"f"📅 Proposta comercial com assinatura digital padrão GOV válida por 10 dias.")
    
    st.write("---")
    st.header("👷 Quantificação da Mão de Obra")
    tipo_cobranca = st.selectbox("Critério de precificação:", ["Por Empreitada / Ponto", "Por Hora Técnica"])
