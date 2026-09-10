import streamlit as st
import pandas as pd

# Configuração da página para Desktop e Celular
st.set_page_config(page_title="Construção Pro - Engenharia de Custos", page_icon="🏗️", layout="centered")

# --- INICIALIZAÇÃO DE BANCOS DE DADOS EM MEMÓRIA ---
if "db_veiculos" not in st.session_state:
    st.session_state.db_veiculos = pd.DataFrame([
        {"Tipo": "Carro", "Marca": "Fiat", "Modelo": "Uno", "Tempo de Uso (Anos)": 2, "Consumo (Km/L)": 12.0, "Valor FIPE (R$)": 35000.0, "Seguro/Doc Anual (R$)": 1500.0, "Manutenção Mensal (R$)": 200.0}
    ])

if "db_custos_fixos" not in st.session_state:
    st.session_state.db_custos_fixos = pd.DataFrame([
        {"Tipo de Gasto": "Contador / MEI", "Valor Mensal (R$)": 80.0},
        {"Tipo de Gasto": "Internet e Celular", "Valor Mensal (R$)": 120.0}
    ])

# NOVO: Banco de dados estruturado para a Aba 3 - Cadastro de Materiais
if "db_materiais" not in st.session_state:
    st.session_state.db_materiais = pd.DataFrame([
        {"ID": "MAT-001", "Descrição": "Cabo Flexível 2,5mm²", "Unidade": "m", "Custo (R$)": 3.60, "Margem (%)": 20, "Valor Unitário (R$)": 4.50},
        {"ID": "MAT-002", "Descrição": "Disjuntor DIN 20A", "Unidade": "Un", "Custo (R$)": 14.00, "Margem (%)": 30, "Valor Unitário (R$)": 20.00}
    ])

st.title("🏗️ Sistema Orçamentário Construção Pro")
st.caption("Módulo de Engenharia de Custos e Catálogo de Materiais Comercial")

# Criação das Abas Principais (Orçamento, Hora e Materiais na sequência lógica)
aba_orcamento, aba_calcular_hora, aba_materiais = st.tabs([
    "📋 Gerar Orçamento", 
    "🧮 Calcular Minha Hora",
    "📦 Cadastro de Materiais"
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
    custo_hora_bruto = (salario_desejado / horas_totais_mes if horas_totais_mes > 0 else 0.0) + v_hora_operacional + f_hora_operacional
    hora_tecnica_final = custo_hora_bruto / (1 - (margem_lucro / 100)) if margem_lucro < 100 else custo_hora_bruto
    st.markdown(f"### 🎯 Preço da sua Hora Técnica Sugerida: **R$ {hora_tecnica_final:.2f}/h**")
    if st.button("🚀 Sincronizar e Gravar Preço da Hora"):
        st.session_state["preco_hora_tecnica_fechada"] = round(hora_tecnica_final, 2); st.success("Gravado!")
# --- ABA 3: CADASTRO DE MATERIAIS E ROMANEIO (NOVA) ---
with aba_materials:
    st.header("📦 Catálogo de Materiais e Insumos")
    st.write("Registre os materiais de estoque ou de fornecedores para calcular o preço final de venda com margem de lucro líquida.")
    
    # Formulário de entrada para novos insumos
    with st.form("cad_material_form", clear_on_submit=True):
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            m_descricao = st.text_input("Descrição do Material (ex: Cabo Flexível 4mm²):")
            m_unidade = st.selectbox("Unidade de Medida:", ["Un", "m", "Barra", "Saco", "Caixa", "kg", "Par", "Outro"])
        with col_v2: # Reutiliza referências de layout estáveis
            m_custo = st.number_input("Custo de Aquisição / Nota Fiscal (R$):", min_value=0.0, value=10.0, step=1.0)
            m_margem = st.slider("Margem de Lucro desejada sobre o item (%)", min_value=0, max_value=80, value=30, step=5)
            
        if st.form_submit_button("💾 Salvar Material no Almoxarifado"):
            if m_descricao:
                # Gerador sequencial de ID inteligente baseado no tamanho do banco de dados
                novo_id = f"MAT-{len(st.session_state.db_materiais) + 1:03d}"
                
                # Fórmula de Markup sobre preço de venda (Garante lucro real sobre insumos)
                valor_final_com_margem = m_custo / (1 - (m_margem / 100)) if m_margem < 100 else m_custo
                
                novo_m = pd.DataFrame([{
                    "ID": novo_id,
                    "Descrição": m_descricao,
                    "Unidade": m_unidade,
                    "Custo (R$)": round(m_custo, 2),
                    "Margem (%)": m_margem,
                    "Valor Unitário (R$)": round(valor_final_com_margem, 2)
                }])
                st.session_state.db_materiais = pd.concat([st.session_state.db_materiais, novo_m], ignore_index=True)
                st.success(f"Material {m_descricao} registrado com sucesso!")
                st.rerun()

    # Painel analítico de gestão de insumos ativos
    if not st.session_state.db_materiais.empty:
        # Seção Avançada: Remoção de Insumos obsoletos
        with st.expander("🗑️ Excluir Insumo / Material do Almoxarifado"):
            lista_materiais_remover = [f"{r['ID']} - {r['Descrição']}" for idx, r in st.session_state.db_materiais.iterrows()]
            material_para_remover = st.selectbox("Selecione o insumo para deletar definitivamente:", lista_materiais_remover)
            if st.button("❌ Confirmar Exclusão do Insumo", type="primary"):
                # Captura o ID exato para realizar o drop limpo
                id_alvo = material_para_remover.split(" - ")[0]
                st.session_state.db_materiais = st.session_state.db_materiais[st.session_state.db_materiais["ID"] != id_alvo].reset_index(drop=True)
                st.success("Material removido do catálogo com sucesso!")
                st.rerun()

        st.write("📝 **Relação de Materiais Cadastrados (Ajuste preços ou margens direto na tabela):**")
        
        # Data editor responsivo
        df_m_editado = st.data_editor(st.session_state.db_materiais, use_container_width=True, num_rows="dynamic")
        
        # Recálculo automático das colunas de preço caso o usuário altere o custo ou a margem direto nas células
        df_m_editado["Valor Unitário (R$)"] = (df_m_editado["Custo (R$)"] / (1 - (df_m_editado["Margem (%)"] / 100))).round(2)
        st.session_state.db_materiais = df_m_editado
        
        # Métricas de resumo do catálogo
        st.caption(f"ℹ️ Total de itens cadastrados no catálogo técnico: **{len(df_m_editado)} insumos ativos**.")
    else:
        st.info("Nenhum material cadastrado até o momento. Utilize o formulário acima para registrar seus insumos de obra.")
