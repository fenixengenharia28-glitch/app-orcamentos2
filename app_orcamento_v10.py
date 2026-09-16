# ==============================================================================
# BLOCO 1: IMPORTAÇÕES, CONFIGURAÇÃO DA PÁGINA E ESTADOS DE SESSÃO
# ==============================================================================
import streamlit as st
import pandas as pd
import os

# Configuração da página web para o modo amplo (wide)
st.set_page_config(
    page_title="Gestão Integrada de Orçamentos Elétricos", 
    page_icon="⚡", 
    layout="wide"
)

# Função auxiliar para ler os arquivos de texto locais com segurança
def ler_arquivo_txt(nome_arquivo, texto_padrao=""):
    if os.path.exists(nome_arquivo):
        with open(nome_arquivo, "r", encoding="utf-8") as f:
            return f.read()
    return texto_padrao

# Inicialização de tabelas na memória da sessão (evita perder dados ao mudar de aba)
if 'clientes' not in st.session_state:
    st.session_state.clientes = []
if 'materiais' not in st.session_state:
    st.session_state.materiais = []
if 'veiculos' not in st.session_state:
    st.session_state.veiculos = []
if 'materiais_orcamento' not in st.session_state:
    st.session_state.materiais_orcamento = []

# Título Principal do Painel
st.title("⚡ Painel de Gestão e Orçamentos Elétricos")
st.markdown("Gerencie seus clientes, materiais, frotas e crie orçamentos profissionais em um só lugar.")

# Criação das Abas de Navegação
aba_orcamento, aba_clientes, aba_mao_obra, aba_calc_hora, aba_materiais, aba_veiculos = st.tabs([
    "📋 Criar Orçamento", 
    "👥 Cadastro de Clientes", 
    "⏱️ Precificação de Mão de Obra", 
    "🧮 Calculadora de Hora Técnica", 
    "🛒 Cadastro de Materiais", 
    "🚚 Cadastro de Veículos"
])
# ==============================================================================
# BLOCO 2: ABAS DE CADASTROS (CLIENTES, MATERIAIS E VEÍCULOS)
# ==============================================================================

# ABA - CADASTRO DE CLIENTES
with aba_clientes:
    st.subheader("👥 Gerenciamento e Cadastro de Clientes")
    with st.form("form_cliente", clear_on_submit=True):
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            c_nome = st.text_input("Nome completo ou Razão Social:")
            c_doc = st.text_input("CPF ou CNPJ:")
        with col_c2:
            c_contato = st.text_input("WhatsApp / Telefone:")
            c_endereco = st.text_input("Endereço da Obra/Cliente:")
        
        btn_cliente = st.form_submit_button("💾 Salvar Cliente")
        if btn_cliente and c_nome:
            st.session_state.clientes.append({"Nome": c_nome, "Documento": c_doc, "Contato": c_contato, "Endereço": c_endereco})
            st.success(f"Cliente '{c_nome}' cadastrado com sucesso!")

    if st.session_state.clientes:
        st.markdown("### Clientes Cadastrados")
        st.dataframe(pd.DataFrame(st.session_state.clientes), use_container_width=True)
    else:
        st.info("Nenhum cliente cadastrado ainda.")

# ABA - CADASTRO DE MATERIAIS
with aba_materiais:
    st.subheader("🛒 Almoxarifado / Catálogo Geral de Materiais")
    with st.form("form_catalogo_material", clear_on_submit=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            mat_nome = st.text_input("Nome do Material (Ex: Cabo Flexível 6mm²):")
        with col_m2:
            mat_marca = st.text_input("Marca / Fabricante:")
        with col_m3:
            mat_preco = st.number_input("Preço de Custo Padrão (R$):", min_value=0.0, value=0.0, step=5.0)
            
        btn_material = st.form_submit_button("💾 Cadastrar Material no Estoque")
        if btn_material and mat_nome:
            st.session_state.materiais.append({"Item": mat_nome, "Marca": mat_marca, "Preço Unitário": mat_preco})
            st.success(f"'{mat_nome}' adicionado ao catálogo geral!")

    if st.session_state.materiais:
        st.markdown("### Materiais em Catálogo")
        st.dataframe(pd.DataFrame(st.session_state.materiais), use_container_width=True)
    else:
        st.info("Nenhum material no catálogo padrão.")

# ABA - CADASTRO DE VEÍCULOS
with aba_veiculos:
    st.subheader("🚚 Gestão de Veículos / Frota de Atendimento")
    with st.form("form_veiculo", clear_on_submit=True):
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            v_modelo = st.text_input("Modelo do Veículo (Ex: Fiorino, Strada):")
            v_placa = st.text_input("Placa do Veículo:")
        with col_v2:
            v_km = st.number_input("Custo estimado por Km rodado (Combustível + Desgaste - R$):", min_value=0.0, value=1.20, step=0.10)
            
        btn_veiculo = st.form_submit_button("💾 Salvar Veículo")
        if btn_veiculo and v_modelo:
            st.session_state.veiculos.append({"Modelo": v_modelo, "Placa": v_placa, "Custo/Km": v_km})
            st.success(f"Veículo '{v_modelo}' adicionado à frota!")

    if st.session_state.veiculos:
        st.markdown("### Veículos Disponíveis")
        st.dataframe(pd.DataFrame(st.session_state.veiculos), use_container_width=True)
    else:
        st.info("Nenhum veículo cadastrado na frota.")
# ==============================================================================
# BLOCO 3: ABAS DE PRECIFICAÇÃO DE MÃO DE OBRA E CALCULADORA DE HORA TÉCNICA
# ==============================================================================

# ABA - PRECIFICAÇÃO DE MÃO DE OBRA
with aba_mao_obra:
    st.subheader("🛠️ Modelos de Cobrança da Mão de Obra")
    st.markdown("Configure aqui o valor que será puxado automaticamente para o orçamento final.")
    
    tipo_calculo_mo = st.radio("Selecione o modelo de precificação:", ["Por Hora Trabalhada", "Por Ponto Elétrico / Tarefa Fixa"])
    
    if tipo_calculo_mo == "Por Hora Trabalhada":
        mo_valor_hora = st.number_input("Seu valor da hora técnica (R$):", min_value=0.0, value=80.0, step=5.0)
        mo_horas_estimadas = st.number_input("Horas estimadas de trabalho na obra:", min_value=0.0, value=8.0, step=1.0)
        total_mo_calculado = mo_valor_hora * mo_horas_estimadas
        st.metric("Total Mão de Obra (Horas)", f"R$ {total_mo_calculado:.2f}")
    else:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            mo_valor_ponto = st.number_input("Valor cobrado por Ponto Elétrico (R$):", min_value=0.0, value=120.0, step=10.0)
        with col_p2:
            mo_qtd_pontos = st.number_input("Quantidade total de pontos na obra:", min_value=0.0, value=10.0, step=1.0)
        total_mo_calculado = mo_valor_ponto * mo_qtd_pontos
        st.metric("Total Mão de Obra (Pontos)", f"R$ {total_mo_calculado:.2f}")

# ABA - CALCULADORA DE HORA TÉCNICA
with aba_calc_hora:
    st.subheader("🧮 Calculadora de Custo de Hora Técnica")
    st.markdown("Descubra quanto vale a sua hora com base nos seus custos mensais fixos.")
    
    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        custo_fixo_pessoal = st.number_input("Custos fixos mensais (Aluguel, ferramentas, softwares, etc - R$):", min_value=0.0, value=1500.0, step=100.0)
        salario_desejado = st.number_input("Sua meta de Pro-labore / Salário limpo (R$):", min_value=0.0, value=5000.0, step=500.0)
    with col_ch2:
        dias_trabalhados = st.number_input("Dias trabalhados por mês:", min_value=1, max_value=31, value=22)
        horas_por_dia = st.number_input("Horas produtivas trabalhadas por dia:", min_value=1, max_value=24, value=6)
        
    total_horas_mes = dias_trabalhados * horas_por_dia
    custo_total_operacao = custo_fixo_pessoal + salario_desejado
    
    if total_horas_mes > 0:
        hora_tecnica_sugerida = custo_total_operacao / total_horas_mes
        st.success(f"💡 Sua hora técnica mínima sugerida para cobrir custos e meta é de: **R$ {hora_tecnica_sugerida:.2f} / hora**")
        st.info("Digite este valor obtido na aba 'Precificação de Mão de Obra' para utilizá-lo no orçamento final.")
# ==============================================================================
# BLOCO 4: ABA DE CRIAÇÃO DO ORÇAMENTO, LOGÍSTICA E MONTAGEM DO DOCUMENTO FINAL
# ==============================================================================

# ABA - EMISSÃO DO ORÇAMENTO FINAL
with aba_orcamento:
    st.subheader("📋 Montagem do Orçamento Integrado")
    col_orc1, col_orc2 = st.columns(2)
    
    with col_orc1:
        st.markdown("### 1. Vincular Informações")
        if st.session_state.clientes:
            lista_nomes_clientes = [c["Nome"] for c in st.session_state.clientes]
            cliente_selecionado = st.selectbox("Selecione o Cliente Cadastrado:", lista_nomes_clientes)
            dados_cli = next(item for item in st.session_state.clientes if item["Nome"] == cliente_selecionado)
            contato_display = dados_cli["Contato"]
            endereco_display = dados_cli["Endereço"]
        else:
            cliente_selecionado = st.text_input("Nome do Cliente (Manual):")
            contato_display = st.text_input("Contato (Manual):")
            endereco_display = st.text_input("Endereço da Obra (Manual):")
            
        orc_descricao = st.text_area("Descreva detalhadamente o escopo técnico do serviço:")
        
        st.markdown("### 🚘 Logística de Deslocamento")
        if st.session_state.veiculos:
            lista_veiculos = [f"{v['Modelo']} ({v['Placa']})" for v in st.session_state.veiculos]
            veiculo_sel = st.selectbox("Selecione o Veículo para o serviço:", lista_veiculos)
            km_rodados = st.number_input("Distância total estimada de ida e volta (Km):", min_value=0.0, value=0.0)
            idx_v = lista_veiculos.index(veiculo_sel)
            custo_deslocamento = km_rodados * st.session_state.veiculos[idx_v]["Custo/Km"]
            st.caption(f"Custo de transporte calculado: R$ {custo_deslocamento:.2f}")
        else:
            custo_deslocamento = st.number_input("Custo de Deslocamento/Combustível Manual (R$):", min_value=0.0, value=0.0)

    with col_orc2:
        st.markdown("### 2. Adicionar Materiais ao Orçamento")
        if st.session_state.materiais:
            lista_mat_nomes = [m["Item"] for m in st.session_state.materiais]
            mat_escolhido = st.selectbox("Escolha um material do seu Catálogo:", lista_mat_nomes)
            item_dados = next(item for item in st.session_state.materiais if item["Item"] == mat_escolhido)
            preco_sugerido = item_dados["Preço Unitário"]
        else:
            mat_escolhido = st.text_input("Nome do Material:")
            preco_sugerido = 0.0
            
        mat_qtd = st.number_input("Quantidade para esta obra:", min_value=1, value=1)
        mat_custo_un = st.number_input("Preço de custo unitário praticado (R$):", min_value=0.0, value=preco_sugerido)
        
        if st.button("➕ Inserir Material no Orçamento"):
            if mat_escolhido:
                st.session_state.materiais_orcamento.append({
                    "Material": mat_escolhido, "Qtd": mat_qtd, "Custo Un. (R$)": mat_custo_un, "Total (R$)": mat_qtd * mat_custo_un
                })
                st.rerun()

        custo_bruto_materiais_obra = 0.0
        if st.session_state.materiais_orcamento:
            df_mat_obra = pd.DataFrame(st.session_state.materiais_orcamento)
            st.dataframe(df_mat_obra, use_container_width=True)
            custo_bruto_materiais_obra = df_mat_obra["Total (R$)"].sum()
            if st.button("🗑️ Limpar Lista de Materiais da Obra"):
                st.session_state.materiais_orcamento = []
                st.rerun()

    st.markdown("---")
    st.markdown("### 3. Fechamento de Margens, Impostos e Termos")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        orc_margem_mat = st.number_input("Margem aplicada sobre os materiais (%):", min_value=0.0, value=20.0)
        total_materiais_reajustado = custo_bruto_materiais_obra * (1 + (orc_margem_mat / 100))
    with col_f2:
        orc_imposto = st.number_input("Impostos Incidentes (%):", min_value=0.0, value=6.0)
    with col_f3:
        orc_desconto = st.number_input("Desconto comercial (R$):", min_value=0.0, value=0.0)

    subtotal_valores = total_mo_calculado + total_materiais_reajustado + custo_deslocamento
    calculo_impostos_finais = subtotal_valores * (orc_imposto / 100)
    preco_final_geral = subtotal_valores + calculo_impostos_finais - orc_desconto

    txt_pag = ler_arquivo_txt("pagamento.txt", "Conforme acordado entre as partes.")
    txt_gar = ler_arquivo_txt("garantia.txt", "Garantia legal de 90 dias.")
    txt_obs = ler_arquivo_txt("observacoes.txt", "Não inclui serviços de alvenaria e pintura.")

    st.markdown("### 📊 Resumo Executivo")
    res_m1, res_m2, res_m3, res_m4, res_m5 = st.columns(5)
    res_m1.metric("Mão de Obra", f"R$ {total_mo_calculado:.2f}")
    res_m2.metric("Materiais", f"R$ {total_materiais_reajustado:.2f}")
    res_m3.metric("Logística/Deslocamento", f"R$ {custo_deslocamento:.2f}")
    res_m4.metric("Impostos", f"R$ {calculo_impostos_finais:.2f}")
    res_m5.metric("PREÇO FINAL", f"R$ {preco_final_geral:.2f}", delta=f"- R$ {orc_desconto:.2f}" if orc_desconto > 0 else None)

    texto_final_whatsapp = f"""==================================================
        ORÇAMENTO DE SERVIÇOS ELÉTRICOS
==================================================
CLIENTE: {cliente_selecionado if cliente_selecionado else 'Não Informado'}
CONTATO: {contato_display if contato_display else 'Não Informado'}
ENDEREÇO DA OBRA: {endereco_display if endereco_display else 'Não Informado'}

ESCOPO TÉCNICO DOS SERVIÇOS:
{orc_descricao if orc_descricao else 'Conforme especificações técnicas alinhadas previamente.'}

DETALHAMENTO DE VALORES:
- Mão de Obra Técnica Especializada: R$ {total_mo_calculado:.2f}
- Fornecimento de Materiais e Insumos: R$ {total_materiais_reajustado:.2f}
- Despesas com Transporte/Logística: R$ {custo_deslocamento:.2f}
- Impostos e Encargos Inclusos: R$ {calculo_impostos_finais:.2f}
"""
    if orc_desconto > 0:
        texto_final_whatsapp += f"- Desconto Especial Concedido: - R$ {orc_desconto:.2f}\n"
        
    texto_final_whatsapp += f"""--------------------------------------------------
VALOR TOTAL DO INVESTIMENTO: R$ {preco_final_geral:.2f}
==================================================
CONDIÇÕES COMERCIAIS:

Formas de Pagamento:
{txt_pag}

Garantia dos Serviços:
{txt_gar}

Observações Importantes:
{txt_obs}
==================================================
Validade deste orçamento: 15 dias a partir desta emissão.
"""
    st.markdown("#### 🖨️ Documento Prontinho para Cópia (WhatsApp/E-mail)")
    st.text_area("Copie o texto estruturado abaixo:", value=texto_final_whatsapp, height=450)
