"""
==============================================================================
APLICATIVO STREAMLIT: GESTÃO DE GASTOS DA REFORMA DO APARTAMENTO
==============================================================================
Desenvolvido em Python 3.12 e Streamlit.
Conexão em tempo real com Supabase (PostgreSQL) via REST API com 'requests'.
Arquivo único e autônomo (Single-File).
==============================================================================
"""

from datetime import date, datetime
import json
import os
from typing import Any, Dict, List, Optional
import pandas as pd
import requests
import streamlit as st

# Tentar importar plotly, com fallback elegante
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# ==============================================================================
# CONFIGURAÇÃO GERAL DA PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Gestão de Gastos da Reforma",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# CONSTANTES DE DOMÍNIO
# ==============================================================================
COMODOS_PADRAO = [
    "Cozinha",
    "Banheiro Social",
    "Suíte",
    "Sala",
    "Sacada",
    "Lavabo",
    "Área de Serviço",
    "Quarto 2",
    "Geral",
]

CATEGORIAS_PADRAO = [
    "Revestimento",
    "Marcenaria",
    "Marmoraria",
    "Iluminação",
    "Eletrodomésticos",
    "Mão de Obra",
    "Louças/Metais",
    "Pintura",
    "Elétrica/Hidráulica",
    "Vidraçaria",
    "Decoração",
    "Outros",
]

STATUS_PADRAO = ["Orçado", "Comprado", "Entregue", "Instalado"]

FORMAS_PAGAMENTO_PADRAO = [
    "Pix",
    "Cartão de Crédito 10x",
    "Cartão de Crédito 1x",
    "Boleto",
    "À Vista",
    "Transferência Bancária",
]

# ==============================================================================
# TEMA E ESTILOS VISUAIS PERSONALIZADOS (MODERNO, LIMPO E ELEGANTE)
# Tons: Azul-escuro #1E293B, Verde-esmeralda #10B981, Cinza claro #F8FAFC
# ==============================================================================
CUSTOM_CSS = """
<style>
    /* Estilos globais */
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Top header bar */
    .main-header {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        padding: 24px 30px;
        border-radius: 14px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 4px 15px rgba(15, 23, 42, 0.08);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .main-header h1 {
        color: #FFFFFF;
        margin: 0;
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .main-header p {
        color: #94A3B8;
        margin: 4px 0 0 0;
        font-size: 0.95rem;
    }

    /* Cards de métricas */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }
    .metric-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(30, 41, 59, 0.06);
    }
    .metric-card .title {
        color: #64748B;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-card .value {
        color: #1E293B;
        font-size: 1.65rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .metric-card .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-positive {
        background-color: #ECFDF5;
        color: #10B981;
    }
    .badge-negative {
        background-color: #FEF2F2;
        color: #EF4444;
    }
    .badge-neutral {
        background-color: #F1F5F9;
        color: #475569;
    }

    /* Badges de Status */
    .status-orcado { background: #FEF3C7; color: #D97706; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .status-comprado { background: #DBEAFE; color: #2563EB; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .status-entregue { background: #E0E7FF; color: #4F46E5; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }
    .status-instalado { background: #D1FAE5; color: #059669; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; }

    /* Custom buttons and tabs styling */
    div.stButton > button {
        border-radius: 8px;
        font-weight: 600;
        border: none;
        transition: all 0.2s;
    }
    div.stButton > button:first-child {
        background-color: #10B981;
        color: white;
    }
    div.stButton > button:first-child:hover {
        background-color: #059669;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.25);
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# CLIENTE SUPABASE REST API (VIA 'requests')
# Conexão em tempo real e sem simulação em memória
# ==============================================================================
class SupabaseRestClient:
    """Cliente REST API robusto para Supabase (PostgreSQL via PostgREST)."""

    def __init__(self, supabase_url: str, supabase_key: str):
        # Normalizar a URL para remover barras finais
        self.base_url = supabase_url.rstrip("/")
        self.api_key = supabase_key.strip()
        self.endpoint = f"{self.base_url}/rest/v1/gastos_reforma"
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def is_configured(self) -> bool:
        return bool(self.base_url and self.api_key)

    def test_connection(self) -> tuple[bool, str]:
        """Testa se a tabela e as credenciais são válidas."""
        if not self.is_configured():
            return False, "URL ou Chave do Supabase não configuradas."
        try:
            url = f"{self.endpoint}?select=count"
            headers = {**self.headers, "Range-Unit": "items", "Range": "0-0"}
            response = requests.get(url, headers=headers, timeout=6)
            if response.status_code in [200, 206]:
                return True, "Conexão com o Supabase estabelecida com sucesso!"
            elif response.status_code == 401:
                return False, "Erro 401: Chave de API do Supabase inválida."
            elif response.status_code == 404:
                return False, "Erro 404: Tabela 'gastos_reforma' não encontrada no banco."
            else:
                return False, f"Erro HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, f"Falha na requisição ao Supabase: {str(e)}"

    def get_gastos(self) -> List[Dict[str, Any]]:
        """Busca todos os registros de gastos ordenados por data decrescente."""
        if not self.is_configured():
            return []
        try:
            url = f"{self.endpoint}?select=*&order=data_compra.desc,id.desc"
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Erro ao buscar dados do Supabase ({response.status_code}): {response.text}")
                return []
        except Exception as ex:
            st.error(f"Erro de comunicação com o Supabase: {ex}")
            return []

    def insert_gasto(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Insere um novo gasto na tabela 'gastos_reforma'."""
        if not self.is_configured():
            return False, "Supabase não configurado."
        try:
            response = requests.post(
                self.endpoint,
                headers=self.headers,
                json=data,
                timeout=10,
            )
            if response.status_code in [200, 201]:
                return True, "Gasto registrado com sucesso!"
            else:
                return False, f"Erro ao inserir no Supabase ({response.status_code}): {response.text}"
        except Exception as ex:
            return False, f"Falha de conexão: {str(ex)}"

    def update_gasto(self, gasto_id: int, data: Dict[str, Any]) -> tuple[bool, str]:
        """Atualiza um gasto existente."""
        if not self.is_configured():
            return False, "Supabase não configurado."
        try:
            url = f"{self.endpoint}?id=eq.{gasto_id}"
            response = requests.patch(
                url,
                headers=self.headers,
                json=data,
                timeout=10,
            )
            if response.status_code in [200, 204]:
                return True, f"Lançamento #{gasto_id} atualizado com sucesso!"
            else:
                return False, f"Erro ao atualizar ({response.status_code}): {response.text}"
        except Exception as ex:
            return False, f"Falha de conexão: {str(ex)}"

    def delete_gasto(self, gasto_id: int) -> tuple[bool, str]:
        """Exclui um gasto pelo ID."""
        if not self.is_configured():
            return False, "Supabase não configurado."
        try:
            url = f"{self.endpoint}?id=eq.{gasto_id}"
            response = requests.delete(url, headers=self.headers, timeout=10)
            if response.status_code in [200, 204]:
                return True, f"Lançamento #{gasto_id} removido com sucesso!"
            else:
                return False, f"Erro ao excluir ({response.status_code}): {response.text}"
        except Exception as ex:
            return False, f"Falha de conexão: {str(ex)}"


# ==============================================================================
# OBTENÇÃO DE CREDENCIAIS (st.secrets OU BARRA LATERAL)
# ==============================================================================
def obter_credenciais() -> tuple[str, str]:
    """Lê automaticamente de st.secrets ou variáveis de ambiente."""
    supabase_url = ""
    supabase_key = ""

    # 1. Tentar ler de st.secrets
    try:
        if "SUPABASE_URL" in st.secrets:
            supabase_url = str(st.secrets["SUPABASE_URL"])
        if "SUPABASE_KEY" in st.secrets:
            supabase_key = str(st.secrets["SUPABASE_KEY"])
        elif "SUPABASE_ANON_KEY" in st.secrets:
            supabase_key = str(st.secrets["SUPABASE_ANON_KEY"])
    except Exception:
        pass

    # 2. Fallback para variáveis de ambiente
    if not supabase_url:
        supabase_url = os.getenv("SUPABASE_URL", "")
    if not supabase_key:
        supabase_key = os.getenv("SUPABASE_KEY", os.getenv("SUPABASE_ANON_KEY", ""))

    return supabase_url, supabase_key


# ==============================================================================
# BARRA LATERAL - CONFIGURAÇÕES E PARÂMETROS
# ==============================================================================
with st.sidebar:
    st.image(
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=600&auto=format&fit=crop&q=80",
        caption="Reforma do Apartamento",
        use_container_width=True,
    )
    st.markdown("### ⚙️ Conexão Supabase")

    env_url, env_key = obter_credenciais()

    with st.expander("🔑 Credenciais do Banco", expanded=not (env_url and env_key)):
        input_url = st.text_input(
            "SUPABASE_URL",
            value=env_url,
            placeholder="https://xyzcompany.supabase.co",
            type="default",
            help="Sua Project URL do Supabase encontrada em Settings > API",
        )
        input_key = st.text_input(
            "SUPABASE_KEY (anon/public)",
            value=env_key,
            placeholder="eyJhbGciOiJIUzI1NiIsIn...",
            type="password",
            help="Sua Chave anon/public encontrada em Settings > API",
        )

        st.caption(
            "💡 **Dica de Deploy**: Adicione ao arquivo `.streamlit/secrets.toml`:\n"
            "```toml\nSUPABASE_URL = 'https://...'\nSUPABASE_KEY = 'ey...'\n```"
        )

    url_final = input_url.strip() or env_url.strip()
    key_final = input_key.strip() or env_key.strip()

    client = SupabaseRestClient(url_final, key_final)

    # Teste de conexão
    if url_final and key_final:
        connected, msg = client.test_connection()
        if connected:
            st.success("🟢 Supabase Conectado!")
        else:
            st.error(f"🔴 {msg}")
    else:
        st.warning("⚠️ Insira suas credenciais do Supabase para sincronizar em tempo real.")

    st.markdown("---")
    st.markdown("### 🎯 Teto Orçamentário Global")
    teto_orcamento = st.number_input(
        "Teto da Reforma (R$)",
        min_value=0.0,
        value=80000.0,
        step=5000.0,
        format="%.2f",
        help="Valor máximo estipulado para todo o projeto da reforma.",
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size: 0.8rem; color: #64748B; text-align: center;'>"
        "Gestão de Reforma v2.0 • Python 3.12 & Streamlit<br>"
        "PostgreSQL Supabase em Tempo Real"
        "</div>",
        unsafe_allow_html=True,
    )


# ==============================================================================
# CARREGAMENTO DOS DADOS DO SUPABASE
# ==============================================================================
dados_brutos = []
if client.is_configured():
    dados_brutos = client.get_gastos()

df = pd.DataFrame(dados_brutos)

# Garantir tipos numéricos e colunas corretas caso o dataframe venha vazio
if df.empty:
    df = pd.DataFrame(
        columns=[
            "id",
            "data_compra",
            "comodo",
            "categoria",
            "descricao",
            "fornecedor",
            "valor_orcado",
            "valor_pago",
            "status",
            "forma_pagamento",
        ]
    )
else:
    df["valor_orcado"] = pd.to_numeric(df["valor_orcado"], errors="coerce").fillna(0.0)
    df["valor_pago"] = pd.to_numeric(df["valor_pago"], errors="coerce").fillna(0.0)
    df["diferenca"] = df["valor_pago"] - df["valor_orcado"]


# ==============================================================================
# CABEÇALHO PRINCIPAL
# ==============================================================================
st.markdown(
    """
    <div class="main-header">
        <div>
            <h1>🏗️ Gestão de Gastos da Reforma</h1>
            <p>Controle financeiro em tempo real com Supabase (PostgreSQL)</p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(16, 185, 129, 0.2); color: #10B981; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 0.85rem; border: 1px solid rgba(16, 185, 129, 0.4);">
                ● Supabase Online
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==============================================================================
# ABAS DE NAVEGAÇÃO
# ==============================================================================
aba1, aba2, aba3, aba4 = st.tabs([
    "📊 Dashboard & Indicadores",
    "🔍 Filtros & Lançamentos",
    "➕ Lançar Novo Gasto",
    "✏️ Gerenciar & Editar",
])


# ==============================================================================
# ABA 1: DASHBOARD DE INDICADORES (VISÃO GERAL)
# ==============================================================================
with aba1:
    # 1. Cálculos consolidados
    total_orcado = float(df["valor_orcado"].sum()) if not df.empty else 0.0
    total_pago = float(df["valor_pago"].sum()) if not df.empty else 0.0
    saldo_teto = teto_orcamento - total_pago
    economia_geral = total_orcado - total_pago

    pct_utilizado = (total_pago / teto_orcamento * 100) if teto_orcamento > 0 else 0.0

    # 2. Cards com Métricas Principais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="title">Orçamento Planejado</div>
                <div class="value">R$ {total_orcado:,.2f}</div>
                <span class="badge badge-neutral">Soma de todos orçamentos</span>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="title">Efetivamente Pago</div>
                <div class="value" style="color: #10B981;">R$ {total_pago:,.2f}</div>
                <span class="badge badge-positive">{pct_utilizado:.1f}% do teto consumido</span>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."),
            unsafe_allow_html=True,
        )

    with col3:
        cor_saldo = "#10B981" if saldo_teto >= 0 else "#EF4444"
        badge_class = "badge-positive" if saldo_teto >= 0 else "badge-negative"
        status_saldo = "Dentro do teto" if saldo_teto >= 0 else "Teto Ultrapassado"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="title">Saldo do Teto Orçado</div>
                <div class="value" style="color: {cor_saldo};">R$ {saldo_teto:,.2f}</div>
                <span class="badge {badge_class}">{status_saldo} (Teto: R$ {teto_orcamento:,.2f})</span>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."),
            unsafe_allow_html=True,
        )

    with col4:
        cor_econ = "#10B981" if economia_geral >= 0 else "#EF4444"
        badge_econ = "badge-positive" if economia_geral >= 0 else "badge-negative"
        desc_econ = "Economizado vs Orçado" if economia_geral >= 0 else "Sobrecusto vs Orçado"
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="title">Economia / Variação</div>
                <div class="value" style="color: {cor_econ};">R$ {abs(economia_geral):,.2f}</div>
                <span class="badge {badge_econ}">{desc_econ}</span>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."),
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 3. Gráficos de barras e pizza
    if not df.empty:
        c_graf1, c_graf2 = st.columns(2)

        # Gráfico por Cômodo (Orçado vs Pago)
        with c_graf1:
            st.markdown("##### 🏡 Gastos por Cômodo (Orçado vs. Pago)")
            df_comodo = df.groupby("comodo")[["valor_orcado", "valor_pago"]].sum().reset_index()

            if HAS_PLOTLY:
                fig_comodo = go.Figure(data=[
                    go.Bar(
                        name="Orçado",
                        x=df_comodo["comodo"],
                        y=df_comodo["valor_orcado"],
                        marker_color="#94A3B8",
                    ),
                    go.Bar(
                        name="Pago",
                        x=df_comodo["comodo"],
                        y=df_comodo["valor_pago"],
                        marker_color="#10B981",
                    ),
                ])
                fig_comodo.update_layout(
                    barmode="group",
                    margin=dict(l=20, r=20, t=30, b=20),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    font=dict(color="#1E293B"),
                    yaxis=dict(gridcolor="#E2E8F0"),
                )
                st.plotly_chart(fig_comodo, use_container_width=True)
            else:
                st.bar_chart(df_comodo.set_index("comodo"))

        # Gráfico por Categoria (Distribuição / Pizza)
        with c_graf2:
            st.markdown("##### 🏷️ Distribuição por Categoria (Valor Pago)")
            df_cat = df.groupby("categoria")["valor_pago"].sum().reset_index()
            df_cat = df_cat[df_cat["valor_pago"] > 0]

            if HAS_PLOTLY and not df_cat.empty:
                cores_personalizadas = [
                    "#10B981", "#3B82F6", "#F59E0B", "#8B5CF6", "#EC4899",
                    "#14B8A6", "#F97316", "#6366F1", "#84CC16", "#06B6D4"
                ]
                fig_cat = px.pie(
                    df_cat,
                    names="categoria",
                    values="valor_pago",
                    hole=0.45,
                    color_discrete_sequence=cores_personalizadas,
                )
                fig_cat.update_layout(
                    margin=dict(l=20, r=20, t=30, b=20),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#1E293B"),
                )
                st.plotly_chart(fig_cat, use_container_width=True)
            elif not df_cat.empty:
                st.bar_chart(df_cat.set_index("categoria"))
            else:
                st.info("Nenhum valor pago registrado até o momento.")

        # 4. Tabela consolidada com rolagem
        st.markdown("##### 📋 Últimos Lançamentos Registrados")
        df_display = df[[
            "id", "data_compra", "comodo", "categoria", "descricao",
            "fornecedor", "valor_orcado", "valor_pago", "status", "forma_pagamento"
        ]].copy()

        st.dataframe(
            df_display.style.format({
                "valor_orcado": "R$ {:,.2f}",
                "valor_pago": "R$ {:,.2f}",
            }),
            use_container_width=True,
            height=320,
        )
    else:
        st.info("💡 Nenhum lançamento encontrado no Supabase. Use a aba '➕ Lançar Novo Gasto' para começar!")


# ==============================================================================
# ABA 2: 🔍 FILTROS PESQUISÁVEIS E CONSULTAS
# ==============================================================================
with aba2:
    st.markdown("### 🔍 Pesquisa e Filtros Avançados")

    with st.expander("🔎 Painel de Filtros Detalhados", expanded=True):
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)

        with f_col1:
            comodos_disponiveis = ["Todos"] + sorted(df["comodo"].dropna().unique().tolist()) if not df.empty else ["Todos"]
            sel_comodo = st.selectbox("Cômodo", comodos_disponiveis)

        with f_col2:
            cat_disponiveis = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist()) if not df.empty else ["Todas"]
            sel_categoria = st.selectbox("Categoria", cat_disponiveis)

        with f_col3:
            status_disponiveis = ["Todos"] + STATUS_PADRAO
            sel_status = st.selectbox("Status", status_disponiveis)

        with f_col4:
            fornecedores = ["Todos"] + sorted([f for f in df["fornecedor"].dropna().unique().tolist() if f]) if not df.empty else ["Todos"]
            sel_fornecedor = st.selectbox("Fornecedor", fornecedores)

        busca_texto = st.text_input(
            "Buscar por palavra-chave na descrição ou fornecedor",
            placeholder="Ex: Porcelanato, Marmoraria, Leroy...",
        )

    # Aplicação dos filtros
    df_filtrado = df.copy()

    if not df_filtrado.empty:
        if sel_comodo != "Todos":
            df_filtrado = df_filtrado[df_filtrado["comodo"] == sel_comodo]
        if sel_categoria != "Todas":
            df_filtrado = df_filtrado[df_filtrado["categoria"] == sel_categoria]
        if sel_status != "Todos":
            df_filtrado = df_filtrado[df_filtrado["status"] == sel_status]
        if sel_fornecedor != "Todos":
            df_filtrado = df_filtrado[df_filtrado["fornecedor"] == sel_fornecedor]
        if busca_texto:
            termo = busca_texto.lower()
            df_filtrado = df_filtrado[
                df_filtrado["descricao"].astype(str).str.lower().str.contains(termo)
                | df_filtrado["fornecedor"].astype(str).str.lower().str.contains(termo)
            ]

        # Resumo dos filtrados
        qtd_itens = len(df_filtrado)
        sub_orcado = df_filtrado["valor_orcado"].sum()
        sub_pago = df_filtrado["valor_pago"].sum()

        st.markdown(
            f"""
            <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 12px 18px; border-radius: 8px; margin-bottom: 16px; display: flex; gap: 24px; align-items: center;">
                <span><strong>Encontrados:</strong> {qtd_itens} itens</span>
                <span><strong>Subtotal Orçado:</strong> R$ {sub_orcado:,.2f}</span>
                <span><strong>Subtotal Pago:</strong> R$ {sub_pago:,.2f}</span>
                <span><strong>Diferença:</strong> R$ {(sub_pago - sub_orcado):,.2f}</span>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."),
            unsafe_allow_html=True,
        )

        st.dataframe(
            df_filtrado[[
                "id", "data_compra", "comodo", "categoria", "descricao",
                "fornecedor", "valor_orcado", "valor_pago", "status", "forma_pagamento"
            ]].style.format({
                "valor_orcado": "R$ {:,.2f}",
                "valor_pago": "R$ {:,.2f}",
            }),
            use_container_width=True,
            height=400,
        )

        # Botão para exportação em CSV
        csv_data = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Exportar Lista Filtrada (CSV)",
            data=csv_data,
            file_name=f"gastos_reforma_{date.today()}.csv",
            mime="text/csv",
        )
    else:
        st.info("Nenhum registro para exibir.")


# ==============================================================================
# ABA 3: ➕ LANÇAR NOVO GASTO
# ==============================================================================
with aba3:
    st.markdown("### ➕ Lançamento de Novo Gasto da Reforma")
    st.caption("Cadastre despesas orçadas ou pagas diretamente no banco de dados Supabase.")

    with st.form("form_novo_gasto", clear_on_submit=True):
        col_f1, col_f2, col_f3 = st.columns(3)

        with col_f1:
            novo_comodo = st.selectbox("Cômodo *", COMODOS_PADRAO)
            nova_categoria = st.selectbox("Categoria *", CATEGORIAS_PADRAO)
            nova_data = st.date_input("Data da Compra / Contratação *", value=date.today())

        with col_f2:
            novo_status = st.selectbox("Status Atual *", STATUS_PADRAO, index=0)
            nova_forma_pag = st.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO_PADRAO)
            novo_fornecedor = st.text_input("Fornecedor / Prestador", placeholder="Ex: Portobello, Eletricista João...")

        with col_f3:
            novo_orcado = st.number_input("Valor Orçado (R$) *", min_value=0.0, value=0.0, step=50.0, format="%.2f")
            novo_pago = st.number_input("Valor Efetivamente Pago (R$)", min_value=0.0, value=0.0, step=50.0, format="%.2f")

            # Cálculo automático em tempo real da economia/sobrecusto
            dif_calculada = novo_pago - novo_orcado
            if novo_orcado > 0 or novo_pago > 0:
                if dif_calculada <= 0:
                    st.success(f"Economia prevista: R$ {abs(dif_calculada):,.2f}")
                else:
                    st.error(f"Sobrecusto previsto: R$ {dif_calculada:,.2f}")

        nova_descricao = st.text_area(
            "Descrição do Item ou Serviço *",
            placeholder="Ex: Porcelanato Portinari 120x120 para o piso da sala e cozinha...",
            help="Descreva detalhadamente o item, medidas ou escopo contratado.",
        )

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("💾 Salvar Gasto no Supabase", use_container_width=True)

        if submitted:
            # Validação dos campos obrigatórios
            erros = []
            if not nova_descricao.strip():
                erros.append("A descrição do item/serviço é obrigatória.")
            if novo_orcado <= 0 and novo_pago <= 0:
                erros.append("Informe um valor orçado ou valor pago maior que zero.")

            if erros:
                for erro in erros:
                    st.error(f"⚠️ {erro}")
            else:
                novo_registro = {
                    "data_compra": nova_data.strftime("%Y-%m-%d"),
                    "comodo": novo_comodo,
                    "categoria": nova_categoria,
                    "descricao": nova_descricao.strip(),
                    "fornecedor": novo_fornecedor.strip() or "Não Informado",
                    "valor_orcado": float(novo_orcado),
                    "valor_pago": float(novo_pago),
                    "status": novo_status,
                    "forma_pagamento": nova_forma_pag,
                }

                with st.spinner("Salvando no Supabase..."):
                    sucesso, msg_retorno = client.insert_gasto(novo_registro)

                if sucesso:
                    st.success(f"✅ {msg_retorno}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {msg_retorno}")


# ==============================================================================
# ABA 4: ✏️ GERENCIAR E EDITAR GASTOS
# ==============================================================================
with aba4:
    st.markdown("### ✏️ Edição e Atualização de Status")
    st.caption("Altere status de entrega/instalação, ajuste valores ou exclua registros com segurança.")

    if df.empty:
        st.info("Nenhum lançamento disponível para gerenciar.")
    else:
        # Opções para selecionar o gasto existente
        opcoes_gastos = {
            f"#{row['id']} - [{row['comodo']}] {row['descricao'][:45]}... (R$ {row['valor_pago']:,.2f})": row['id']
            for _, row in df.iterrows()
        }

        escolha_texto = st.selectbox("Selecione o Lançamento para Editar", list(opcoes_gastos.keys()))
        id_selecionado = opcoes_gastos[escolha_texto]

        # Obter registro selecionado
        registro_sel = df[df["id"] == id_selecionado].iloc[0]

        st.markdown(f"**Editando Lançamento ID:** `#{id_selecionado}`")

        with st.form("form_editar_gasto"):
            ecol1, ecol2, ecol3 = st.columns(3)

            with ecol1:
                # Tratar índice do selectbox
                idx_comodo = COMODOS_PADRAO.index(registro_sel["comodo"]) if registro_sel["comodo"] in COMODOS_PADRAO else 0
                edit_comodo = st.selectbox("Cômodo", COMODOS_PADRAO, index=idx_comodo)

                idx_cat = CATEGORIAS_PADRAO.index(registro_sel["categoria"]) if registro_sel["categoria"] in CATEGORIAS_PADRAO else 0
                edit_categoria = st.selectbox("Categoria", CATEGORIAS_PADRAO, index=idx_cat)

                try:
                    data_parsed = datetime.strptime(str(registro_sel["data_compra"]), "%Y-%m-%d").date()
                except Exception:
                    data_parsed = date.today()
                edit_data = st.date_input("Data da Compra", value=data_parsed)

            with ecol2:
                idx_status = STATUS_PADRAO.index(registro_sel["status"]) if registro_sel["status"] in STATUS_PADRAO else 0
                edit_status = st.selectbox("Status", STATUS_PADRAO, index=idx_status)

                idx_fp = FORMAS_PAGAMENTO_PADRAO.index(registro_sel["forma_pagamento"]) if registro_sel["forma_pagamento"] in FORMAS_PAGAMENTO_PADRAO else 0
                edit_forma_pag = st.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO_PADRAO, index=idx_fp)

                edit_fornecedor = st.text_input("Fornecedor / Prestador", value=str(registro_sel["fornecedor"] or ""))

            with ecol3:
                edit_orcado = st.number_input(
                    "Valor Orçado (R$)",
                    min_value=0.0,
                    value=float(registro_sel["valor_orcado"]),
                    step=50.0,
                    format="%.2f",
                )
                edit_pago = st.number_input(
                    "Valor Pago (R$)",
                    min_value=0.0,
                    value=float(registro_sel["valor_pago"]),
                    step=50.0,
                    format="%.2f",
                )
                edit_dif = edit_pago - edit_orcado
                st.caption(f"Variação calculada: R$ {edit_dif:,.2f}")

            edit_descricao = st.text_area("Descrição", value=str(registro_sel["descricao"]))

            salvar_alteracoes = st.form_submit_button("🔄 Atualizar no Supabase", use_container_width=True)

            if salvar_alteracoes:
                dados_atualizados = {
                    "data_compra": edit_data.strftime("%Y-%m-%d"),
                    "comodo": edit_comodo,
                    "categoria": edit_categoria,
                    "descricao": edit_descricao.strip(),
                    "fornecedor": edit_fornecedor.strip(),
                    "valor_orcado": float(edit_orcado),
                    "valor_pago": float(edit_pago),
                    "status": edit_status,
                    "forma_pagamento": edit_forma_pag,
                }
                with st.spinner("Atualizando no Supabase..."):
                    sucesso, msg = client.update_gasto(id_selecionado, dados_atualizados)

                if sucesso:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")

        # Seção de exclusão segura
        st.markdown("---")
        with st.expander("🗑️ Área de Exclusão de Lançamento", expanded=False):
            st.warning(f"Atenção: A exclusão do lançamento #{id_selecionado} é irreversível.")
            confirma_exclusao = st.checkbox(f"Confirmo que desejo apagar permanentemente o registro #{id_selecionado}")
            if st.button("🚨 Excluir Registro Definitivamente", type="secondary"):
                if confirma_exclusao:
                    with st.spinner("Excluindo do banco..."):
                        sucesso, msg = client.delete_gasto(id_selecionado)
                    if sucesso:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.error("Marque a caixa de confirmação para autorizar a exclusão.")
