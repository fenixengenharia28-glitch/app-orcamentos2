import streamlit as st
import pandas as pd

# Configuração da página para Desktop e Celular
st.set_page_config(page_title="Construção Pro - Engenharia de Custos", page_icon="🏗️", layout="centered")

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

st.title("🏗️ Sistema Orçamentário Construção Pro")
st.caption("Módulo de Engenharia de Custos e Catálogo Técnico de Itens")

# Criação das Abas Principais
aba_orcamento, aba_calcular_hora, aba_materiais, aba_servicos = st.tabs([
    "📋 Gerar Orçamento", 
    "🧮 Calcular Minha Hora",
    "📦 Cadastro de Materiais",
    "🛠️ Cadastro de Serviços"
])

# --- ABA 1: RASCUNHO INICIAL DE ORÇAMENTO ---
with aba_orcamento:
    st.header("📋 Novo Orçamento")
    st.write("Esta aba será integrada de forma cruzada aos cadastros assim que consolidarmos os módulos de custo.")
    st.info("Utilize as abas superiores para alimentar seus bancos de dados e frotas de campo.")

# --- ABA 2: ENGENHARIA DE CUSTOS E CÁLCULO DA HORA TÉCNICA ---
with aba_calcular_hora:
    st.header("🧮 Configuração do Preço por Hora Técnico")
    salario_desejado = st.number_input("Quanto quer ganhar livre por mês (R$):", min_value=0.0, value=4000.0, step=100.0)
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        dias_trabalhados = st.number_input("Dias operacionais por mês:", min_value=1, max_value=31, value=22)
    with col_t2:
        horas_por_dia = st.number_input("Horas faturadas por dia na obra:", min_value=1.0, max_value=24.0, value=6.0, step=0.5)
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
            if st.button("❌ Confirmar Exclusão do Veículo", type="primary"):
                st.session_state.db_veiculos = st.session_state.db_veiculos.drop(int(veiculo_para_remover.split(" - "))).reset_index(drop=True); st.rerun()
        df_v_editado = st.data_editor(st.session_state.db_veiculos, use_container_width=True, num_rows="dynamic")
        st.session_state.db_veiculos = df_v_editado
        v_hora_operacional = ((df_v_editado["Valor FIPE (R$)"].sum() * 0.10 / 12) + (df_v_editado["Seguro/Doc Anual (R$)"].sum() / 12) + df_v_editado["Manutenção Mensal (R$)"].sum()) / horas_totais_mes if horas_totais_mes > 0 else 0.0
    else: v_hora_operacional = 0.0
    st.write("---")
    st.subheader("🏢 Custos Fixos Mensais")
    with st.form("cad_custo_fixo_form", clear_on_submit=True):
        f_tipo = st.text_input("Gasto:")
        f_valor = st.number_input("Valor Mensal (R$):", min_value=0.0)
        if st.form_submit_button("➕ Adicionar Custo Fixo") and f_tipo:
            st.session_state.db_custos_fixos = pd.concat([st.session_state.db_custos_fixos, pd.DataFrame([{"Tipo de Gasto": f_tipo, "Valor Mensal (R$)": f_valor}])], ignore_index=True); st.rerun()

    if not st.session_state.db_custos_fixos.empty:
        with st.expander("🗑️ Excluir Despesa"):
            gasto_para_remover = st.selectbox("Deletar gasto:", [f"{idx} - {r['Tipo de Gasto']}" for idx, r in st.session_state.db_custos_fixos.iterrows()])
            if st.button("❌ Confirmar Exclusão da Despesa", type="primary"):
                st.session_state.db_custos_fixos = st.session_state.db_custos_fixos.drop(int(gasto_para_remover.split(" - "))).reset_index(drop=True); st.rerun()
        df_f_trabalho = st.session_state.db_custos_fixos.copy()
        df_f_trabalho["Valor por Hora (R$)"] = (df_f_trabalho["Valor Mensal (R$)"] / horas_totais_mes).round(2) if horas_totais_mes > 0 else 0.0
        df_f_editado = st.data_editor(df_f_trabalho, use_container_width=True, num_rows="dynamic")
        st.session_state.db_custos_fixos = df_f_editado[["Tipo de Gasto", "Valor Mensal (R$)"]]
        f_hora_operacional = df_f_editado["Valor Mensal (R$)"].sum() / horas_totais_mes if horas_totais_mes > 0 else 0.0
    else: f_hora_operacional = 0.0

    st.write("---")
    # --- ENGENHARIA DE CUSTOS COM SEPARAÇÃO SOLICITADA ---
    salario_por_hora = salario_desejado / horas_totais_mes if horas_totais_mes > 0 else 0.0
    custo_hora_operacional = v_hora_operacional + f_hora_operacional
    
    # Aplicação do Markup de lucro da empresa somente sobre a parcela de despesas ou sobre o montante bruto
    custo_hora_bruto = salario_por_hora + custo_hora_operacional
    hora_tecnica_final = custo_hora_bruto / (1 - (margem_lucro / 100)) if margem_lucro < 100 else custo_hora_bruto
    
    st.subheader("📊 Demonstrativo Detalhado do Valor por Hora")
    c_c1, c_c2 = st.columns(2)
    with c_c1:
        st.metric(label="Valor da sua Hora de Trabalho (Líquido)", value=f"R$ {salario_por_hora:.2f}/h")
    with c_c2:
        st.metric(label="Valor dos Custos por Hora (Logística + Fixo)", value=f"R$ {custo_hora_operacional:.2f}/h")
        
    st.markdown(f"### 🎯 Preço Final Combinado com {margem_lucro}\% de Margem: **R$ {hora_tecnica_final:.2f}/h**")
    if st.button("🚀 Sincronizar e Gravar Preço da Hora"):
        st.session_state["preco_hora_tecnica_fechada"] = round(hora_tecnica_final, 2); st.success("Gravado!")

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
            if st.button("❌ Confirmar Exclusão do Insumo", type="primary"):
                st.session_state.db_materiais = st.session_state.db_materiais[st.session_state.db_materiais["ID"] != mat_remover.split(" - ")[0]].reset_index(drop=True); st.rerun()
        
        st.write("📝 **Altere preços de custo ou margens diretamente nas células abaixo para atualizar:**")
        df_m_editado = st.data_editor(st.session_state.db_materiais, use_container_width=True, num_rows="dynamic")
        
        # Proteção e recálculo dinâmico quando alterado na planilha
        df_m_editado["Valor Unitário (R$)"] = (df_m_editado["Custo (R$)"] / (1 - (df_m_editado["Margem (%)"].clip(0, 99) / 100))).round(2)
        st.session_state.db_materiais = df_m_editado

# --- ABA 4: CADASTRO DE SERVIÇOS ---
with aba_servicos:
    st.header("🛠️ Catálogo Técnico de Serviços da Empresa")
    with st.form("cad_servico_form", clear_on_submit=True):
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            s_descricao = st.text_input("Descrição do Serviço:")
            s_unidade = st.selectbox("Unidade de Cobrança:", ["Ponto", "M²", "Diária", "Hora", "Empreitada", "Metro"])
        with col_s2:
            s_valor = st.number_input("Preço de Venda Sugerido (R$):", min_value=0.0, value=50.0, step=5.0)
            
        if st.form_submit_button("💾 Salvar Serviço no Catálogo"):
            if s_descricao:
                novo_id_s = f"SRV-{len(st.session_state.db_servicos) + 1:03d}"
                novo_s = pd.DataFrame([{"ID": novo_id_s, "Descrição": s_descricao, "Unidade": s_unidade, "Valor (R$)": round(s_valor, 2)}])
                st.session_state.db_servicos = pd.concat([st.session_state.db_servicos, novo_s], ignore_index=True); st.rerun()

    if not st.session_state.db_servicos.empty:
        with st.expander("🗑️ Excluir Serviço do Catálogo"):
            srv_remover = st.selectbox("Selecione o serviço para deletar:", [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_servicos.iterrows()])
            if st.button("❌ Confirmar Exclusão do Serviço", type="primary"):
                st.session_state.db_servicos = st.session_state.db_servicos[st.session_state.db_servicos["ID"] != srv_remover.split(" - ")[0]].reset_index(drop=True); st.rerun()

        st.write("📝 **Altere descrições, unidades ou valores diretamente nas células abaixo:**")
        df_s_editado = st.data_editor(st.session_state.db_servicos, use_container_width=True, num_rows="dynamic")
        st.session_state.db_servicos = df_s_editado
