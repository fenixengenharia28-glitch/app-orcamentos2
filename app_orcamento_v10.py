# ==========================================
# BLOCO 1: IMPORTAÇÕES E CONFIGURAÇÃO DA PÁGINA
# ==========================================
import streamlit as st
import pandas as pd
import os

# Configura o layout da página web
st.set_page_config(
    page_title="Orçamentos Elétricos Pro", 
    page_icon="⚡", 
    layout="wide"
)

# Função auxiliar para ler os arquivos de texto com segurança
def ler_arquivo_txt(nome_arquivo, texto_padrao=""):
    if os.path.exists(nome_arquivo):
        with open(nome_arquivo, "r", encoding="utf-8") as f:
            return f.read()
    return texto_padrao

# Título Principal do Sistema
st.title("⚡ Sistema de Orçamento de Serviços Elétricos")
st.markdown("Preencha as informações abaixo para gerar o seu orçamento integrado.")
st.markdown("---")

# ==========================================
# BLOCO 2: DADOS DO CLIENTE E DO PROJETO
# ==========================================
col_cli1, col_cli2 = st.columns(2)

with col_cli1:
    st.subheader("📋 Dados do Cliente & Contato")
    nome_cliente = st.text_input("Nome do Cliente ou Razão Social:")
    contato_cliente = st.text_input("Telefone, WhatsApp ou E-mail:")

with col_cli2:
    st.subheader("📝 Detalhes da Execução")
    descricao_servico = st.text_area(
        "Descrição Geral do Serviço Elétrico:",
        placeholder="Ex: Reforma de QDC residencial, balanceamento de fases e instalação de DPS."
    )

st.markdown("---")

# ==========================================
# BLOCO 3: CÁLCULO DE MÃO DE OBRA
# ==========================================
st.subheader("⏱️ Precificação da Mão de Obra")
col_mo1, col_mo2 = st.columns(2)

with col_mo1:
    tipo_cobranca = st.radio(
        "Como você deseja cobrar pela sua mão de obra?", 
        ["Por Hora Trabalhada", "Valor Fixo / Empreitada"]
    )

with col_mo2:
    if tipo_cobranca == "Por Hora Trabalhada":
        valor_hora = st.number_input("Valor da sua hora técnica (R$):", min_value=0.0, value=80.0, step=5.0)
        horas_estimadas = st.number_input("Quantidade de horas estimadas:", min_value=0.0, value=8.0, step=1.0)
        valor_mao_de_obra = valor_hora * horas_estimadas
        st.info(f"Subtotal da Mão de Obra: R$ {valor_mao_de_obra:.2f}")
    else:
        valor_mao_de_obra = st.number_input("Valor fixo fechado para o serviço (R$):", min_value=0.0, value=500.0, step=50.0)

st.markdown("---")

# ==========================================
# BLOCO 4: LEVANTAMENTO E GERENCIAMENTO DE MATERIAIS
# ==========================================
st.subheader("🛒 Lista de Materiais e Insumos")

if 'materiais_lista' not in st.session_state:
    st.session_state.materiais_lista = []

with st.form("form_novo_material", clear_on_submit=True):
    col_mat1, col_mat2, col_mat3 = st.columns()
    with col_mat1:
        item_nome = st.text_input("Nome do Material / Equipamento:", placeholder="Ex: Disjuntor DIN Bifásico 32A")
    with col_mat2:
        item_qtd = st.number_input("Quantidade:", min_value=1, value=1, step=1)
    with col_mat3:
        item_preco = st.number_input("Preço de Custo Unitário (R$):", min_value=0.0, value=0.0, step=1.0)
    
    btn_adicionar = st.form_submit_button("➕ Adicionar Material")
    
    if btn_adicionar and item_nome:
        st.session_state.materiais_lista.append({
            "Item/Material": item_nome,
            "Quantidade": item_qtd,
            "Preço Custo Un. (R$)": item_preco,
            "Total Custo (R$)": item_qtd * item_preco
        })

custo_total_materiais = 0.0

if st.session_state.materiais_lista:
    df_materiais = pd.DataFrame(st.session_state.materiais_lista)
    st.table(df_materiais)
    
    custo_total_materiais = df_materiais["Total Custo (R$)"].sum()
    st.write(f"**Custo Bruto Total dos Materiais:** R$ {custo_total_materials:.2f}")
    
    if st.button("🗑️ Limpar Lista de Materiais"):
        st.session_state.materiais_lista = []
        st.rerun()
else:
    st.caption("Nenhum material adicionado até o momento.")

st.markdown("---")

# ==========================================
# BLOCO 5: FECHAMENTO FINANCEIRO E TEXTOS EXCLUSIVOS
# ==========================================
st.subheader("📊 Ajustes Financeiros Finais")
col_fin1, col_fin2, col_fin3 = st.columns(3)

with col_fin1:
    margem_material = st.number_input("Margem de Lucro sobre Materiais (%):", min_value=0.0, value=20.0, step=5.0)
    total_materiais_com_lucro = custo_total_materiais * (1 + (margem_material / 100))

with col_fin2:
    imposto_porcentagem = st.number_input("Alíquota de Impostos / Nota Fiscal (%):", min_value=0.0, value=6.0, step=0.5)

with col_fin3:
    desconto_especial = st.number_input("Desconto em Reais (R$):", min_value=0.0, value=0.0, step=10.0)

# Fórmulas de cálculo do fechamento
subtotal_geral = valor_mao_de_obra + total_materiais_com_lucro
valor_imposto = subtotal_geral * (imposto_porcentagem / 100)
preco_final_total = subtotal_geral + valor_imposto - desconto_especial

# Importando os textos dos seus arquivos locais .txt
texto_pagamento = ler_arquivo_txt("pagamento.txt", "À vista ou condições a combinar.")
texto_garantia = ler_arquivo_txt("garantia.txt", "90 dias conforme código de defesa do consumidor.")
texto_observacoes = ler_arquivo_txt("observacoes.txt", "Orçamento sujeito a alterações caso haja mudança no escopo.")

# Exibição dos termos na interface
with st.expander("📄 Visualizar Termos Importados (.txt)"):
    st.markdown(f"**Formas de Pagamento:**\n{texto_pagamento}")
    st.markdown(f"**Termos de Garantia:**\n{texto_garantia}")
    st.markdown(f"**Observações Gerais:**\n{texto_observacoes}")

st.markdown("---")

# ==========================================
# BLOCO 6: VISUALIZAÇÃO DO ORÇAMENTO E CÓPIA RÁPIDA
# ==========================================
st.subheader("📝 Resumo Final do Orçamento")

res_col1, res_col2, res_col3, res_col4 = st.columns(4)
res_col1.metric("Mão de Obra", f"R$ {valor_mao_de_obra:.2f}")
res_col2.metric("Materiais (c/ Lucro)", f"R$ {total_materiais_com_lucro:.2f}")
res_col3.metric("Impostos", f"R$ {valor_imposto:.2f}")
res_col4.metric(
    "PREÇO FINAL", 
    f"R$ {preco_final_total:.2f}", 
    delta=f"- R$ {desconto_especial:.2f} desc." if desconto_especial > 0 else None
)

st.markdown("#### 🖨️ Documento de Envio Rápido")

# Montagem do template final injetando as variáveis e os textos dos arquivos .txt
texto_orcamento = f"""==================================================
        ORÇAMENTO DE SERVIÇOS ELÉTRICOS
==================================================
CLIENTE: {nome_cliente if nome_cliente else 'Não Informado'}
CONTATO: {contato_cliente if contato_cliente else 'Não Informado'}

DESCRIÇÃO DO SERVIÇO:
{descricao_servico if descricao_servico else 'Conforme especificações técnicas alinhadas previamente.'}

DETALHAMENTO DE VALORES:
- Mão de Obra Técnica Especializada: R$ {valor_mao_de_obra:.2f}
- Fornecimento de Materiais/Insumos: R$ {total_materiais_com_lucro:.2f}
- Encargos/Impostos Inclusos: R$ {valor_imposto:.2f}
"""

if desconto_especial > 0:
    texto_orcamento += f"- Desconto Especial Concedido: - R$ {desconto_especial:.2f}\n"

texto_orcamento += f"""--------------------------------------------------
VALOR TOTAL DO INVESTIMENTO: R$ {preco_final_total:.2f}
==================================================
CONDIÇÕES COMERCIAIS:

Formas de Pagamento:
{texto_pagamento}

Garantia:
{texto_garantia}

Observações Importantes:
{texto_observacoes}
==================================================
Validade deste orçamento: 15 dias.
"""

st.text_area("Texto formatado para WhatsApp ou E-mail (Copie abaixo):", value=texto_orcamento, height=400)
