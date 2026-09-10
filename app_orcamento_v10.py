import streamlit as st
import pandas as pd

# Configuração da página para Desktop e Celular
st.set_page_config(page_title="Construção Pro - Engenharia de Custos", page_icon="🏗️", layout="centered")

# Inicialização dos bancos de dados internos em memória se não existirem
if "db_veiculos" not in st.session_state:
    st.session_state.db_veiculos = pd.DataFrame([
        {"Tipo": "Carro", "Marca": "Fiat", "Modelo": "Uno", "Tempo de Uso (Anos)": 2, "Consumo (Km/L)": 12.0, "Valor FIPE (R$)": 35000.0, "Seguro/Doc Anual (R$)": 1500.0, "Manutenção Mensal (R$)": 200.0}
    ])

if "db_custos_fixos" not in st.session_state:
    st.session_state.db_custos_fixos = pd.DataFrame([
        {"Tipo de Gasto": "Contador / MEI", "Valor Mensal (R$)": 80.0},
        {"Tipo de Gasto": "Internet e Celular", "Valor Mensal (R$)": 120.0},
        {"Tipo de Gasto": "Ferramentas e Software", "Valor Mensal (R$)": 150.0}
    ])

st.title("🏗️ Sistema Orçamentário Construção Pro")
st.caption("Módulo de Engenharia de Custos e Formação de Preço por Hora Técnica")

# Criação das Abas Principais (Aba de Orçamento no início)
aba_orcamento, aba_calcular_hora = st.tabs(["📋 Gerar Orçamento", "🧮 Calcular Minha Hora"])

# --- ABA 1: RASCUNHO INICIAL DE ORÇAMENTO ---
with aba_orcamento:
    st.header("📋 Novo Orçamento")
    st.write("Esta aba está pronta e será integrada aos custos assim que finalizarmos a calculadora de horas abaixo.")
    st.info("Acesse a aba 'Calcular Minha Hora' ao lado para configurar seus parâmetros de campo.")

# --- ABA 2: ENGENHARIA DE CUSTOS E CÁLCULO DA HORA TÉCNICA ---
with aba_calcular_hora:
    st.header("🧮 Configuração do Preço por Hora Técnico")
    st.write("Preencha suas metas de ganho e tempo disponível para o sistema estruturar o seu preço de mercado.")
    
    # 1. Parâmetros Individuais Principais
    st.subheader("1. Metas Financeiras e Tempo")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        salario_desejado = st.number_input("Quanto quer ganhar livre por mês (Seu Pró-labore - R$):", min_value=0.0, value=4000.0, step=100.0)
        dias_trabalhados = st.number_input("Dias operacionais trabalhados por mês:", min_value=1, max_value=31, value=22)
    with col_t2:
        horas_por_dia = st.number_input("Horas produtivas faturadas por dia (Trabalho na obra):", min_value=1.0, max_value=24.0, value=6.0, step=0.5)
        margem_lucro = st.slider("Margem de lucro desejada para a empresa (%)", min_value=0, max_value=50, value=20, step=5)
        
    horas_totais_mes = dias_trabalhados * horas_por_dia
    st.caption(f"ℹ️ Seu tempo de trabalho faturável total no mês é de **{horas_totais_mes:.1f} horas**.")
    
    st.write("---")
    # 2. Cadastro e Gerenciamento Veicular
    st.subheader("2. Parâmetros e Custos de Logística do Veículo")
    
    with st.form("cad_veiculo_form", clear_on_submit=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v_tipo = st.selectbox("Tipo do Veículo:", ["Carro", "Moto", "Caminhão", "Utilitário / Van"])
            v_marca = st.text_input("Marca do Veículo:")
            v_modelo = st.text_input("Modelo do Veículo:")
        with col_v2:
            v_tempo = st.number_input("Tempo que tenho o veículo (Anos):", min_value=0, value=1)
            v_consumo = st.number_input("Consumo Médio de Combustível (Km/L):", min_value=1.0, value=10.0, step=0.5)
            v_fipe = st.number_input("Valor Atual de Mercado (Tabela FIPE - R$):", min_value=0.0, value=30000.0, step=1000.0)
            
        v_seg_doc = st.number_input("Seguro + Documentação Anual total (R$):", min_value=0.0, value=1200.0, step=100.0)
        v_manutencao = st.number_input("Gasto de Manutenção Mensal estimado (R$):", min_value=0.0, value=200.0, step=50.0)
            
        if st.form_submit_button("💾 Salvar Veículo na Frota"):
            if v_marca and v_modelo:
                novo_v = pd.DataFrame([{
                    "Tipo": v_tipo, "Marca": v_marca, "Modelo": v_modelo, "Tempo de Uso (Anos)": v_tempo,
                    "Consumo (Km/L)": v_consumo, "Valor FIPE (R$)": v_fipe, 
                    "Seguro/Doc Anual (R$)": v_seg_doc, "Manutenção Mensal (R$)": v_manutencao
                }])
                st.session_state.db_veiculos = pd.concat([st.session_state.db_veiculos, novo_v], ignore_index=True)
                st.success(f"Veículo {v_modelo} cadastrado com sucesso!")
                st.rerun()
    # Renderização da Planilha Dinâmica do Veículo e Remoção
    if not st.session_state.db_veiculos.empty:
        with st.expander("🗑️ Excluir Veículo Cadastrado"):
            lista_veiculos = [f"{idx} - [{r['Tipo']}] {r['Marca']} {r['Modelo']}" for idx, r in st.session_state.db_veiculos.iterrows()]
            veiculo_para_remover = st.selectbox("Selecione o veículo para deletar:", lista_veiculos)
            if st.button("❌ Confirmar Exclusão do Veículo", type="primary"):
                idx_remover = int(veiculo_para_remover.split(" - ")[0])
                st.session_state.db_veiculos = st.session_state.db_veiculos.drop(idx_remover).reset_index(drop=True)
                st.success("Veículo removido com sucesso!")
                st.rerun()

        df_v_editado = st.data_editor(st.session_state.db_veiculos, use_container_width=True, num_rows="dynamic")
        st.session_state.db_veiculos = df_v_editado
        
        tot_fipe = df_v_editado["Valor FIPE (R$)"].sum()
        tot_seg_anual = df_v_editado["Seguro/Doc Anual (R$)"].sum()
        tot_man_mensal = df_v_editado["Manutenção Mensal (R$)"].sum()
        
        depreciacao_mensal = (tot_fipe * 0.10) / 12
        seg_doc_mensal = tot_seg_anual / 12
        custo_veicular_mensal_total = depreciacao_mensal + seg_doc_mensal + tot_man_mensal
        
        v_hora_operacional = custo_veicular_mensal_total / horas_totais_mes if horas_totais_mes > 0 else 0.0
        st.metric(label="Total de Custo Veicular por Hora Trabalhada", value=f"R$ {v_hora_operacional:.2f}/h", delta=f"R$ {custo_veicular_mensal_total:.2f}/mês total")
    else:
        v_hora_operacional = 0.0

    st.write("---")
    # 3. Módulo de Custos Fixos de Operação
    st.subheader("3. Gestão e Cadastro de Custos Fixos Mensais")
    
    with st.form("cad_custo_fixo_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            f_tipo = st.text_input("Tipo de Gasto (ex: Aluguel, MEI, Software):")
        with col_f2:
            f_valor = st.number_input("Valor Mensal do Gasto (R$):", min_value=0.0, step=10.0)
            
        if st.form_submit_button("➕ Adicionar Custo Fixo"):
            if f_tipo:
                novo_f = pd.DataFrame([{"Tipo de Gasto": f_tipo, "Valor Mensal (R$)": f_valor}])
                st.session_state.db_custos_fixos = pd.concat([st.session_state.db_custos_fixos, novo_f], ignore_index=True)
                st.success("Custo fixo adicionado!")
                st.rerun()

    if not st.session_state.db_custos_fixos.empty:
        with st.expander("🗑️ Excluir Despesa / Gasto Fixo"):
            lista_gastos = [f"{idx} - {r['Tipo de Gasto']}" for idx, r in st.session_state.db_custos_fixos.iterrows()]
            gasto_para_remover = st.selectbox("Selecione a despesa para deletar:", lista_gastos)
            if st.button("❌ Confirmar Exclusão da Despesa", type="primary"):
                idx_gasto_remover = int(gasto_para_remover.split(" - ")[0])
                st.session_state.db_custos_fixos = st.session_state.db_custos_fixos.drop(idx_gasto_remover).reset_index(drop=True)
                st.success("Despesa removida com sucesso!")
                st.rerun()

        df_f_trabalho = st.session_state.db_custos_fixos.copy()
        df_f_trabalho["Valor por Hora (R$)"] = df_f_trabalho["Valor Mensal (R$)"] / (horas_totais_mes if horas_totais_mes > 0 else 1)
        df_f_trabalho["Valor por Hora (R$)"] = df_f_trabalho["Valor por Hora (R$)"].round(2)
        
        st.write("📝 **Planilha de Custos Fixos Ativos (Editável):**")
        df_f_editado = st.data_editor(df_f_trabalho, use_container_width=True, num_rows="dynamic")
        
        st.session_state.db_custos_fixos = df_f_editado[["Tipo de Gasto", "Valor Mensal (R$)"]]
        
        total_fixo_mensal = df_f_editado["Valor Mensal (R$)"].sum()
        f_hora_operacional = total_fixo_mensal / horas_totais_mes if horas_totais_mes > 0 else 0.0
        st.metric(label="Total de Custo Fixo por Hora Trabalhada", value=f"R$ {f_hora_operacional:.2f}/h", delta=f"R$ {total_fixo_mensal:.2f}/mês total")
    else:
        f_hora_operacional = 0.0

    st.write("---")
    # 4. Cálculo de Fechamento da Hora Técnica Sugerida
    st.subheader("📊 Engenharia Final de Preço")
    
    salario_por_hora = salario_desejado / horas_totais_mes if horas_totais_mes > 0 else 0.0
    custo_hora_bruto = salario_por_hora + v_hora_operacional + f_hora_operacional
    
    if margem_lucro < 100:
        hora_tecnica_final = custo_hora_bruto / (1 - (margem_lucro / 100))
    else:
        hora_tecnica_final = custo_hora_bruto
        
    st.write(f"• **Seu salário limpo por hora trabalhada:** R$ {salario_por_hora:.2f}/h")
    st.write(f"• **Custo operacional bruto total por hora:** R$ {custo_hora_bruto:.2f}/h")
    st.markdown(f"### 🎯 Preço da sua Hora Técnica Sugerida (Com {margem_lucro}\% de Margem): **R$ {hora_tecnica_final:.2f}/h**")
    
    if st.button("🚀 Sincronizar e Gravar Preço da Hora no Sistema"):
        st.session_state["preco_hora_tecnica_fechada"] = round(hora_tecnica_final, 2)
        st.success("Preço da hora gravado com sucesso! Pronto para ser puxado no fechamento dos orçamentos.")
