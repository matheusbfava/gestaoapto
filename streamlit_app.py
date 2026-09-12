"""
==============================================================================
APP: GESTÃO FINANCEIRA E FLUXO DE CAIXA DA REFORMA DO APARTAMENTO
Framework: Streamlit (Python 3.12)
Banco de Dados: Supabase (PostgreSQL via REST API / requests)
==============================================================================
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA STREAMLIT
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão Financeira & Fluxo de Caixa da Reforma",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# 2. CONSTANTES E CONDIÇÕES FIXAS DE PAGAMENTO
# -----------------------------------------------------------------------------
CONDICOES_PAGAMENTO: List[str] = [
    "À vista",
    "7 dias",
    "14 dias",
    "31 dias",
    "2x",
    "3x",
    "4x",
    "5x",
    "6x",
    "7x",
    "8x",
    "9x",
    "10x",
    "12x",
]

CATEGORIAS_LISTA: List[str] = [
    "Demolição/Alvenaria",
    "Mão de Obra",
    "Revestimento",
    "Marmoraria",
    "Marcenaria",
    "Vidraçaria",
    "Gesso/Drywall",
    "Iluminação",
    "Pintura",
    "Louças/Metais",
    "Eletrodomésticos",
    "Ar Condicionado",
    "Decoração",
    "Outros",
]

CATEGORIAS_PADRAO_LISTA: List[Dict[str, Any]] = [
    {"id": 1, "nome": "Revestimento", "descricao": "Porcelanatos, pisos, azulejos e argamassas"},
    {"id": 2, "nome": "Marmoraria", "descricao": "Bancadas, cubas esculpidas, ilhas e soleiras"},
    {"id": 3, "nome": "Mão de Obra", "descricao": "Pedreiro, empreiteiro, gesseiro, encanador e eletricista"},
    {"id": 4, "nome": "Marcenaria", "descricao": "Armários planejados de cozinha, quartos e banheiros"},
    {"id": 5, "nome": "Vidraçaria", "descricao": "Box de banheiro, espelhos e fechamento de sacada"},
    {"id": 6, "nome": "Louças/Metais", "descricao": "Torneiras, misturadores, bacias sanitárias e chuveiros"},
    {"id": 7, "nome": "Iluminação", "descricao": "Perfis de LED, spots, lustres e interruptores"},
    {"id": 8, "nome": "Pintura", "descricao": "Tintas, seladores, massa corrida e fitas"},
    {"id": 9, "nome": "Eletrodomésticos", "descricao": "Cooktop, forno, coifa, geladeira e micro-ondas"},
    {"id": 10, "nome": "Decoração", "descricao": "Cortinas, tapetes, papel de parede e quadros"},
    {"id": 11, "nome": "Outros", "descricao": "Despesas gerais, caçambas, fretes e taxas"},
]

FORNECEDORES_PADRAO_LISTA: List[Dict[str, Any]] = [
    {"id": 1, "nome": "Portobello Shop", "categoria_padrao": "Revestimento", "telefone": "(11) 98888-1111", "observacao": "Pisos e porcelanatos sala e cozinha"},
    {"id": 2, "nome": "Marmoraria Real", "categoria_padrao": "Marmoraria", "telefone": "(11) 97777-2222", "observacao": "Granito Preto São Gabriel e Quartzo"},
    {"id": 3, "nome": "JR Reformas e Construção", "categoria_padrao": "Mão de Obra", "telefone": "(11) 96666-3333", "observacao": "Empreiteiro responsável pela obra"},
    {"id": 4, "nome": "Leroy Merlin", "categoria_padrao": "Louças/Metais", "telefone": "4020-5376", "observacao": "Materiais básicos, tintas e metais"},
    {"id": 5, "nome": "Marcenaria Design Prime", "categoria_padrao": "Marcenaria", "telefone": "(11) 95555-4444", "observacao": "Mobiliário planejado"},
    {"id": 6, "nome": "Vidraçaria Cristal", "categoria_padrao": "Vidraçaria", "telefone": "(11) 94444-5555", "observacao": "Box e envidraçamento de sacada"},
    {"id": 7, "nome": "Lustres & Cia", "categoria_padrao": "Iluminação", "telefone": "(11) 93333-6666", "observacao": "Perfis e luminárias técnicas"},
    {"id": 8, "nome": "Tintas & Cores", "categoria_padrao": "Pintura", "telefone": "(11) 92222-7777", "observacao": "Suvinil e complementos"},
    {"id": 9, "nome": "Fast Shop", "categoria_padrao": "Eletrodomésticos", "telefone": "0800-726-8300", "observacao": "Eletros de embutir"},
]

STATUS_LISTA: List[str] = [
    "Orçado",
    "Negociando",
    "Comprado",
    "Entregue",
    "Instalado",
    "Concluído",
]

# Dados padrão para exibição e demonstração caso a tabela do banco esteja vazia
DADOS_DEMO: List[Dict[str, Any]] = [
    {
        "id": 1,
        "data_compra": "2025-01-10",
        "categoria": "Revestimento",
        "descricao": "Porcelanato Calacatta 90x90 retificado (35m²)",
        "fornecedor": "Portobello Shop",
        "valor_orcado": 4200.0,
        "valor_pago": 3950.0,
        "status": "Entregue",
        "forma_pagamento": "10x",
    },
    {
        "id": 2,
        "data_compra": "2025-01-15",
        "categoria": "Marmoraria",
        "descricao": "Bancada e ilha em Granito Preto São Gabriel escovado",
        "fornecedor": "Marmoraria Real",
        "valor_orcado": 6500.0,
        "valor_pago": 6500.0,
        "status": "Instalado",
        "forma_pagamento": "À vista",
    },
    {
        "id": 3,
        "data_compra": "2025-01-20",
        "categoria": "Mão de Obra",
        "descricao": "Empreiteiro - 1ª parcela de demolição e alvenaria",
        "fornecedor": "JR Reformas e Construção",
        "valor_orcado": 8000.0,
        "valor_pago": 8000.0,
        "status": "Instalado",
        "forma_pagamento": "14 dias",
    },
    {
        "id": 4,
        "data_compra": "2025-01-25",
        "categoria": "Louças/Metais",
        "descricao": "Cuba esculpida e misturador monocomando Docol",
        "fornecedor": "Leroy Merlin",
        "valor_orcado": 1850.0,
        "valor_pago": 1720.0,
        "status": "Comprado",
        "forma_pagamento": "4x",
    },
    {
        "id": 5,
        "data_compra": "2025-02-02",
        "categoria": "Iluminação",
        "descricao": "Perfil de LED embutido 3000K e spots direcionais",
        "fornecedor": "Lustres & Cia",
        "valor_orcado": 2200.0,
        "valor_pago": 2100.0,
        "status": "Comprado",
        "forma_pagamento": "7 dias",
    },
    {
        "id": 6,
        "data_compra": "2025-02-05",
        "categoria": "Marcenaria",
        "descricao": "Armários planejados em MDF naval com amortecedores",
        "fornecedor": "Marcenaria Design Prime",
        "valor_orcado": 14500.0,
        "valor_pago": 12000.0,
        "status": "Orçado",
        "forma_pagamento": "12x",
    },
    {
        "id": 7,
        "data_compra": "2025-02-10",
        "categoria": "Vidraçaria",
        "descricao": "Nivelamento e fechamento de sacada com vidro",
        "fornecedor": "Vidraçaria Cristal",
        "valor_orcado": 5800.0,
        "valor_pago": 5800.0,
        "status": "Instalado",
        "forma_pagamento": "3x",
    },
    {
        "id": 8,
        "data_compra": "2025-02-15",
        "categoria": "Pintura",
        "descricao": "Tinta Suvinil Toque de Seda e massa corrida (kit reforma)",
        "fornecedor": "Tintas & Cores",
        "valor_orcado": 2800.0,
        "valor_pago": 2650.0,
        "status": "Comprado",
        "forma_pagamento": "31 dias",
    },
    {
        "id": 9,
        "data_compra": "2025-02-25",
        "categoria": "Eletrodomésticos",
        "descricao": "Cooktop por indução e forno de embutir elétrico",
        "fornecedor": "Fast Shop",
        "valor_orcado": 3900.0,
        "valor_pago": 3699.0,
        "status": "Entregue",
        "forma_pagamento": "6x",
    },
]

# -----------------------------------------------------------------------------
# 3. MOTOR DE CÁLCULO DE DESEMBOLSO E FLUXO DE CAIXA
# -----------------------------------------------------------------------------
def calcular_cronograma_desembolso(gastos: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Gera a projeção detalhada de cada parcela/desembolso com base na data da compra,
    valor efetivo (ou orçado caso valor_pago seja 0) e condição de pagamento contratada.
    Condições suportadas:
      - 'À vista': Vence na própria data da compra
      - '7 dias': Vence na data + 7 dias
      - '14 dias': Vence na data + 14 dias
      - '31 dias': Vence na data + 31 dias
      - 'Nx' (2x a 12x): N parcelas mensais (a cada 30 dias a partir da data)
    """
    parcelas = []
    
    for g in gastos:
        valor_base = float(g.get("valor_pago") or 0.0)
        if valor_base <= 0:
            valor_base = float(g.get("valor_orcado") or 0.0)
            
        cond = str(g.get("forma_pagamento") or "À vista").strip()
        data_str = str(g.get("data_compra") or date.today().isoformat())
        try:
            dt_compra = datetime.strptime(data_str[:10], "%Y-%m-%d").date()
        except Exception:
            dt_compra = date.today()
            
        desc = g.get("descricao", "Sem descrição")
        cat = g.get("categoria", "Geral")
        forn = g.get("fornecedor", "Não Informado")
        gid = g.get("id")

        if cond == "À vista":
            parcelas.append({
                "gasto_id": gid,
                "descricao": desc,
                "categoria": cat,
                "fornecedor": forn,
                "condicao": cond,
                "parcela_num": 1,
                "total_parcelas": 1,
                "data_vencimento": dt_compra,
                "mes_ano": dt_compra.strftime("%Y-%m"),
                "valor_parcela": valor_base,
            })
        elif cond == "7 dias":
            venc = dt_compra + timedelta(days=7)
            parcelas.append({
                "gasto_id": gid,
                "descricao": desc,
                "categoria": cat,
                "fornecedor": forn,
                "condicao": cond,
                "parcela_num": 1,
                "total_parcelas": 1,
                "data_vencimento": venc,
                "mes_ano": venc.strftime("%Y-%m"),
                "valor_parcela": valor_base,
            })
        elif cond == "14 dias":
            venc = dt_compra + timedelta(days=14)
            parcelas.append({
                "gasto_id": gid,
                "descricao": desc,
                "categoria": cat,
                "fornecedor": forn,
                "condicao": cond,
                "parcela_num": 1,
                "total_parcelas": 1,
                "data_vencimento": venc,
                "mes_ano": venc.strftime("%Y-%m"),
                "valor_parcela": valor_base,
            })
        elif cond == "31 dias":
            venc = dt_compra + timedelta(days=31)
            parcelas.append({
                "gasto_id": gid,
                "descricao": desc,
                "categoria": cat,
                "fornecedor": forn,
                "condicao": cond,
                "parcela_num": 1,
                "total_parcelas": 1,
                "data_vencimento": venc,
                "mes_ano": venc.strftime("%Y-%m"),
                "valor_parcela": valor_base,
            })
        elif "x" in cond.lower():
            # Extrai o número de parcelas (ex: 2x, 10x, 12x)
            try:
                num_vezes = int(cond.lower().replace("x", "").strip())
            except Exception:
                num_vezes = 1

            if num_vezes < 1:
                num_vezes = 1

            valor_parc = round(valor_base / num_vezes, 2)
            sobra = round(valor_base - (valor_parc * num_vezes), 2)

            for i in range(num_vezes):
                # Deslocamento mensal aproximado de 30 dias por parcela
                venc = dt_compra + timedelta(days=30 * i)
                # Ajusta eventuais centavos na 1ª parcela
                val = valor_parc + (sobra if i == 0 else 0.0)
                parcelas.append({
                    "gasto_id": gid,
                    "descricao": desc,
                    "categoria": cat,
                    "fornecedor": forn,
                    "condicao": cond,
                    "parcela_num": i + 1,
                    "total_parcelas": num_vezes,
                    "data_vencimento": venc,
                    "mes_ano": venc.strftime("%Y-%m"),
                    "valor_parcela": val,
                })
        else:
            # Fallback à vista
            parcelas.append({
                "gasto_id": gid,
                "descricao": desc,
                "categoria": cat,
                "fornecedor": forn,
                "condicao": cond,
                "parcela_num": 1,
                "total_parcelas": 1,
                "data_vencimento": dt_compra,
                "mes_ano": dt_compra.strftime("%Y-%m"),
                "valor_parcela": valor_base,
            })

    if not parcelas:
        return pd.DataFrame(columns=[
            "gasto_id", "descricao", "categoria", "fornecedor", "condicao",
            "parcela_num", "total_parcelas", "data_vencimento", "mes_ano", "valor_parcela"
        ])
        
    df = pd.DataFrame(parcelas)
    df["data_vencimento"] = pd.to_datetime(df["data_vencimento"])
    df.sort_values(by="data_vencimento", inplace=True)
    return df

# -----------------------------------------------------------------------------
# 4. CLIENTE SUPABASE VIA REST API (requests)
# -----------------------------------------------------------------------------
class SupabaseRestClient:
    def __init__(self, url: str, key: str):
        cleaned_url = url.strip().rstrip("/")
        if cleaned_url.endswith("/rest/v1"):
            cleaned_url = cleaned_url[:-8]
        self.base_url = cleaned_url
        self.key = key.strip()
        self.endpoint = f"{self.base_url}/rest/v1/gastos_reforma"
        self.endpoint_categorias = f"{self.base_url}/rest/v1/categorias_gastos"
        self.endpoint_fornecedores = f"{self.base_url}/rest/v1/fornecedores_reforma"
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def test_connection(self) -> bool:
        try:
            res = requests.get(
                f"{self.endpoint}?select=id&limit=1",
                headers=self.headers,
                timeout=5,
            )
            return res.status_code in [200, 206]
        except Exception:
            return False

    def get_gastos(self) -> List[Dict[str, Any]]:
        try:
            res = requests.get(
                f"{self.endpoint}?select=*&order=data_compra.desc,id.desc",
                headers=self.headers,
                timeout=8,
            )
            if res.status_code in [200, 206]:
                return res.json()
            return []
        except Exception:
            return []

    def create_gasto(self, payload: Dict[str, Any]) -> bool:
        try:
            res = requests.post(
                self.endpoint,
                headers=self.headers,
                json=payload,
                timeout=8,
            )
            return res.status_code in [200, 201]
        except Exception:
            return False

    def update_gasto(self, gasto_id: int, payload: Dict[str, Any]) -> bool:
        try:
            res = requests.patch(
                f"{self.endpoint}?id=eq.{gasto_id}",
                headers=self.headers,
                json=payload,
                timeout=8,
            )
            return res.status_code in [200, 204]
        except Exception:
            return False

    def delete_gasto(self, gasto_id: int) -> bool:
        try:
            res = requests.delete(
                f"{self.endpoint}?id=eq.{gasto_id}",
                headers=self.headers,
                timeout=8,
            )
            return res.status_code in [200, 204]
        except Exception:
            return False

    def delete_all_gastos(self) -> bool:
        try:
            # PostgREST permite deleção em massa com filtro correspondente a todos os registros
            res = requests.delete(
                f"{self.endpoint}?id=gte.0",
                headers=self.headers,
                timeout=8,
            )
            return res.status_code in [200, 204]
        except Exception:
            return False

    # --- CATEGORIAS CRUD ---
    def get_categorias(self) -> List[Dict[str, Any]]:
        try:
            res = requests.get(
                f"{self.endpoint_categorias}?select=*&order=nome.asc",
                headers=self.headers,
                timeout=8,
            )
            if res.status_code in [200, 206]:
                return res.json()
            return []
        except Exception:
            return []

    def create_categoria(self, payload: Dict[str, Any]) -> bool:
        try:
            res = requests.post(
                self.endpoint_categorias,
                headers=self.headers,
                json=payload,
                timeout=8,
            )
            return res.status_code in [200, 201]
        except Exception:
            return False

    def update_categoria(self, cat_id: int, payload: Dict[str, Any]) -> bool:
        try:
            res = requests.patch(
                f"{self.endpoint_categorias}?id=eq.{cat_id}",
                headers=self.headers,
                json=payload,
                timeout=8,
            )
            return res.status_code in [200, 204]
        except Exception:
            return False

    def delete_categoria(self, cat_id: int) -> bool:
        try:
            res = requests.delete(
                f"{self.endpoint_categorias}?id=eq.{cat_id}",
                headers=self.headers,
                timeout=8,
            )
            return res.status_code in [200, 204]
        except Exception:
            return False

    # --- FORNECEDORES CRUD ---
    def get_fornecedores(self) -> List[Dict[str, Any]]:
        try:
            res = requests.get(
                f"{self.endpoint_fornecedores}?select=*&order=nome.asc",
                headers=self.headers,
                timeout=8,
            )
            if res.status_code in [200, 206]:
                return res.json()
            return []
        except Exception:
            return []

    def create_fornecedor(self, payload: Dict[str, Any]) -> bool:
        try:
            res = requests.post(
                self.endpoint_fornecedores,
                headers=self.headers,
                json=payload,
                timeout=8,
            )
            return res.status_code in [200, 201]
        except Exception:
            return False

    def update_fornecedor(self, forn_id: int, payload: Dict[str, Any]) -> bool:
        try:
            res = requests.patch(
                f"{self.endpoint_fornecedores}?id=eq.{forn_id}",
                headers=self.headers,
                json=payload,
                timeout=8,
            )
            return res.status_code in [200, 204]
        except Exception:
            return False

    def delete_fornecedor(self, forn_id: int) -> bool:
        try:
            res = requests.delete(
                f"{self.endpoint_fornecedores}?id=eq.{forn_id}",
                headers=self.headers,
                timeout=8,
            )
            return res.status_code in [200, 204]
        except Exception:
            return False

# -----------------------------------------------------------------------------
# 5. GERENCIAMENTO DE CREDENCIAIS (Secrets ou Sidebar)
# -----------------------------------------------------------------------------
def obter_credenciais() -> tuple[Optional[str], Optional[str]]:
    url = None
    key = None
    if "SUPABASE_URL" in st.secrets and "SUPABASE_KEY" in st.secrets:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    return url, key

# -----------------------------------------------------------------------------
# 6. ESTILO CSS REFINADO E COMPACTO
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* Estilo refinado e compacto para cards de indicadores */
    .metric-card-compact {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        margin-bottom: 8px;
    }
    .metric-label-compact {
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b;
        margin-bottom: 2px;
    }
    .metric-value-compact {
        font-size: 20px;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.2;
    }
    .metric-sub-compact {
        font-size: 11px;
        color: #64748b;
        margin-top: 3px;
    }
    .tag-condicao {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        background-color: #f1f5f9;
        color: #334155;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# 7. CARREGAMENTO DOS DADOS
# -----------------------------------------------------------------------------
url_secret, key_secret = obter_credenciais()

with st.sidebar:
    st.markdown("### ⚙️ Conexão Supabase")
    if url_secret and key_secret:
        st.success("✅ Supabase configurado via Secrets!")
        supabase_url = url_secret
        supabase_key = key_secret
    else:
        st.info("Insira suas credenciais abaixo ou adicione em `.streamlit/secrets.toml`:")
        supabase_url = st.text_input("SUPABASE_URL", value="", placeholder="https://xyz.supabase.co")
        supabase_key = st.text_input("SUPABASE_KEY", value="", type="password", placeholder="eyJhbGciOi...")

    st.markdown("---")
    st.markdown("### 🎯 Orçamento Global")
    teto_orcamento = st.number_input(
        "Teto da Reforma (R$)",
        min_value=0.0,
        value=80000.0,
        step=5000.0,
        format="%.2f",
        help="Valor máximo estipulado para a conclusão da obra.",
    )

# Inicializa o cliente do Supabase
client: Optional[SupabaseRestClient] = None
is_connected = False

if supabase_url and supabase_key:
    client = SupabaseRestClient(supabase_url, supabase_key)
    is_connected = client.test_connection()

if is_connected and client:
    raw_gastos = client.get_gastos()
    # Se retornou lista do Supabase (mesmo que vazia []), respeitamos a base do usuário!
    gastos = raw_gastos if raw_gastos is not None else []

    raw_cats = client.get_categorias()
    categorias = raw_cats if (raw_cats is not None and len(raw_cats) > 0) else [dict(c) for c in CATEGORIAS_PADRAO_LISTA]

    raw_forns = client.get_fornecedores()
    fornecedores = raw_forns if (raw_forns is not None and len(raw_forns) > 0) else [dict(f) for f in FORNECEDORES_PADRAO_LISTA]

    fonte_status = "Supabase PostgreSQL (Tempo Real)"
else:
    if "gastos_local" not in st.session_state:
        st.session_state["gastos_local"] = [dict(d) for d in DADOS_DEMO]
    gastos = st.session_state["gastos_local"]

    if "categorias_local" not in st.session_state:
        st.session_state["categorias_local"] = [dict(c) for c in CATEGORIAS_PADRAO_LISTA]
    categorias = st.session_state["categorias_local"]

    if "fornecedores_local" not in st.session_state:
        st.session_state["fornecedores_local"] = [dict(f) for f in FORNECEDORES_PADRAO_LISTA]
    fornecedores = st.session_state["fornecedores_local"]

    fonte_status = "Modo Local Interativo (Demonstração)"

nomes_categorias = [c.get("nome", "") for c in categorias if c.get("nome")]
if not nomes_categorias:
    nomes_categorias = CATEGORIAS_LISTA

nomes_fornecedores = [f.get("nome", "") for f in fornecedores if f.get("nome")]

COLUNAS_GASTOS = [
    "id", "data_compra", "categoria", "descricao", "fornecedor",
    "valor_orcado", "valor_pago", "status", "forma_pagamento"
]
df_gastos = pd.DataFrame(gastos)
for col in COLUNAS_GASTOS:
    if col not in df_gastos.columns:
        df_gastos[col] = pd.Series(dtype="object" if col in ["categoria", "descricao", "fornecedor", "status", "forma_pagamento", "data_compra"] else "float64")

if not df_gastos.empty:
    df_gastos["valor_orcado"] = pd.to_numeric(df_gastos["valor_orcado"], errors="coerce").fillna(0.0)
    df_gastos["valor_pago"] = pd.to_numeric(df_gastos["valor_pago"], errors="coerce").fillna(0.0)


# Motor de Fluxo de Caixa / Cronograma
df_fluxo = calcular_cronograma_desembolso(gastos)

# -----------------------------------------------------------------------------
# 8. CABEÇALHO DO APLICATIVO
# -----------------------------------------------------------------------------
st.title("💸 Gestão Financeira & Fluxo de Caixa da Reforma")
st.caption(f"Status da Base: **{fonte_status}** | Monitoramento de despesas e projeção futura de desembolsos.")

# -----------------------------------------------------------------------------
# 9. CARDS DE INDICADORES (COMPACTOS E SEM CÔMODO)
# -----------------------------------------------------------------------------
total_orcado = df_gastos["valor_orcado"].sum() if not df_gastos.empty else 0.0
total_pago = df_gastos["valor_pago"].sum() if not df_gastos.empty else 0.0
saldo_teto = teto_orcamento - total_pago
percentual_teto = (total_pago / teto_orcamento * 100) if teto_orcamento > 0 else 0.0
dif_orc_pag = total_pago - total_orcado

# Desembolso futuro (parcelas a vencer a partir de hoje)
hoje = pd.to_datetime(date.today())
if not df_fluxo.empty:
    desembolso_futuro = df_fluxo[df_fluxo["data_vencimento"] >= hoje]["valor_parcela"].sum()
    desembolso_30d = df_fluxo[
        (df_fluxo["data_vencimento"] >= hoje) & (df_fluxo["data_vencimento"] <= hoje + timedelta(days=30))
    ]["valor_parcela"].sum()
else:
    desembolso_futuro = 0.0
    desembolso_30d = 0.0

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(
        f"""
        <div class="metric-card-compact">
            <div class="metric-label-compact">Orçamento Total</div>
            <div class="metric-value-compact">R$ {total_orcado:,.2f}</div>
            <div class="metric-sub-compact">Total planejado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""
        <div class="metric-card-compact">
            <div class="metric-label-compact">Total Contratado</div>
            <div class="metric-value-compact" style="color: #0284c7;">R$ {total_pago:,.2f}</div>
            <div class="metric-sub-compact">{percentual_teto:.1f}% do teto consumido</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    cor_saldo = "#16a34a" if saldo_teto >= 0 else "#dc2626"
    status_saldo = "Margem disponível" if saldo_teto >= 0 else "Excesso de orçamento"
    st.markdown(
        f"""
        <div class="metric-card-compact">
            <div class="metric-label-compact">Saldo do Teto</div>
            <div class="metric-value-compact" style="color: {cor_saldo};">R$ {saldo_teto:,.2f}</div>
            <div class="metric-sub-compact">{status_saldo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
        <div class="metric-card-compact">
            <div class="metric-label-compact">A Vencer (Próx. 30 dias)</div>
            <div class="metric-value-compact" style="color: #ea580c;">R$ {desembolso_30d:,.2f}</div>
            <div class="metric-sub-compact">Exigibilidade imediata</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col5:
    st.markdown(
        f"""
        <div class="metric-card-compact">
            <div class="metric-label-compact">Desembolso Futuro</div>
            <div class="metric-value-compact" style="color: #7c3aed;">R$ {desembolso_futuro:,.2f}</div>
            <div class="metric-sub-compact">Parcelas a liquidar</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# -----------------------------------------------------------------------------
# 10. NAVEGAÇÃO EM ABAS
# -----------------------------------------------------------------------------
tab_fluxo, tab_gastos, tab_novo, tab_cadastros, tab_editar = st.tabs([
    "📈 Fluxo de Caixa & Desembolso",
    "📋 Lançamentos e Filtros",
    "➕ Novo Lançamento",
    "🏷️ Categorias & Fornecedores",
    "✏️ Gerenciar & Excluir",
])

# =============================================================================
# ABA 1: FLUXO DE CAIXA E DESEMBOLSO
# =============================================================================
with tab_fluxo:
    st.subheader("📅 Cronograma de Desembolso Financeiro")
    st.caption("Projeção do fluxo de saída de caixa conforme as condições de pagamento (À vista, 7d, 14d, 31d, 2x a 12x).")

    if not df_fluxo.empty:
        # Agrupamento mensal
        df_mensal = df_fluxo.groupby("mes_ano")["valor_parcela"].sum().reset_index()
        df_mensal.sort_values(by="mes_ano", inplace=True)
        df_mensal["acumulado"] = df_mensal["valor_parcela"].cumsum()

        col_g1, col_g2 = st.columns([3, 2])

        with col_g1:
            fig_bar = px.bar(
                df_mensal,
                x="mes_ano",
                y="valor_parcela",
                text="valor_parcela",
                title="Desembolso Previsto por Mês (R$)",
                labels={"mes_ano": "Mês de Vencimento", "valor_parcela": "Valor (R$)"},
                color_discrete_sequence=["#0284c7"],
            )
            fig_bar.update_traces(
                texttemplate="R$ %{text:,.0f}",
                textposition="outside",
            )
            fig_bar.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                height=350,
                xaxis_title="",
                yaxis_title="Total a Pagar (R$)",
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            fig_line = px.line(
                df_mensal,
                x="mes_ano",
                y="acumulado",
                markers=True,
                title="Desembolso Acumulado ao Longo do Tempo (R$)",
                labels={"mes_ano": "Mês", "acumulado": "Acumulado (R$)"},
                color_discrete_sequence=["#16a34a"],
            )
            fig_line.add_hline(
                y=teto_orcamento,
                line_dash="dash",
                line_color="#dc2626",
                annotation_text=f"Teto: R$ {teto_orcamento:,.0f}",
                annotation_position="top left",
            )
            fig_line.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                height=350,
                xaxis_title="",
            )
            st.plotly_chart(fig_line, use_container_width=True)

        st.markdown("### 🔍 Cronograma Detalhado de Parcelas a Vencer")
        
        # Filtros de visualização do fluxo
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            meses_disponiveis = ["Todos"] + sorted(list(df_fluxo["mes_ano"].unique()))
            mes_sel = st.selectbox("Filtrar por Mês de Vencimento:", meses_disponiveis)
        with col_f2:
            status_venc = st.selectbox("Status de Vencimento:", ["Todas as Parcelas", "Apenas Vencimentos Futuros", "Vencidas/Hoje"])

        df_view_fluxo = df_fluxo.copy()
        if mes_sel != "Todos":
            df_view_fluxo = df_view_fluxo[df_view_fluxo["mes_ano"] == mes_sel]

        if status_venc == "Apenas Vencimentos Futuros":
            df_view_fluxo = df_view_fluxo[df_view_fluxo["data_vencimento"] >= hoje]
        elif status_venc == "Vencidas/Hoje":
            df_view_fluxo = df_view_fluxo[df_view_fluxo["data_vencimento"] < hoje]

        df_exibir_fluxo = df_view_fluxo[[
            "data_vencimento", "descricao", "categoria", "fornecedor",
            "condicao", "parcela_num", "total_parcelas", "valor_parcela"
        ]].copy()
        df_exibir_fluxo["data_vencimento"] = df_exibir_fluxo["data_vencimento"].dt.strftime("%d/%m/%Y")
        df_exibir_fluxo["parcela"] = df_exibir_fluxo["parcela_num"].astype(str) + "/" + df_exibir_fluxo["total_parcelas"].astype(str)
        df_exibir_fluxo["valor_parcela"] = df_exibir_fluxo["valor_parcela"].apply(lambda v: f"R$ {v:,.2f}")
        df_exibir_fluxo.drop(columns=["parcela_num", "total_parcelas"], inplace=True)
        df_exibir_fluxo.rename(columns={
            "data_vencimento": "Data Vencimento",
            "descricao": "Item / Serviço",
            "categoria": "Categoria",
            "fornecedor": "Fornecedor",
            "condicao": "Condição",
            "parcela": "Parcela",
            "valor_parcela": "Valor Parcela",
        }, inplace=True)

        st.dataframe(df_exibir_fluxo, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento cadastrado para projetar o fluxo de caixa.")

# =============================================================================
# ABA 2: LANÇAMENTOS E FILTROS
# =============================================================================
with tab_gastos:
    st.subheader("📋 Tabela Consolidada de Lançamentos")
    
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
        filtro_cat = st.multiselect("Filtrar Categoria:", nomes_categorias, default=[])
    with col_s2:
        filtro_status = st.multiselect("Filtrar Status:", STATUS_LISTA, default=[])
    with col_s3:
        filtro_cond = st.multiselect("Filtrar Condição de Pagamento:", CONDICOES_PAGAMENTO, default=[])

    df_filtrado = df_gastos.copy()
    if filtro_cat:
        df_filtrado = df_filtrado[df_filtrado["categoria"].isin(filtro_cat)]
    if filtro_status:
        df_filtrado = df_filtrado[df_filtrado["status"].isin(filtro_status)]
    if filtro_cond:
        df_filtrado = df_filtrado[df_filtrado["forma_pagamento"].isin(filtro_cond)]

    if not df_filtrado.empty:
        df_exibicao = df_filtrado[[
            "id", "data_compra", "categoria", "descricao", "fornecedor",
            "forma_pagamento", "valor_orcado", "valor_pago", "status"
        ]].copy()
        df_exibicao["Diferença"] = df_exibicao["valor_pago"] - df_exibicao["valor_orcado"]

        # Gráfico de gastos por categoria
        col_chart, col_empty = st.columns([2, 1])
        with col_chart:
            fig_cat = px.pie(
                df_filtrado,
                names="categoria",
                values="valor_pago",
                title="Distribuição de Valores por Categoria",
                hole=0.4,
            )
            fig_cat.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300)
            st.plotly_chart(fig_cat, use_container_width=True)

        st.dataframe(
            df_exibicao.style.format({
                "valor_orcado": "R$ {:,.2f}",
                "valor_pago": "R$ {:,.2f}",
                "Diferença": "R$ {:,.2f}",
            }),
            use_container_width=True,
            hide_index=True,
        )

        csv = df_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Baixar Relatório (CSV)",
            data=csv,
            file_name="gastos_reforma_fluxo.csv",
            mime="text/csv",
        )
    else:
        st.warning("Nenhum lançamento corresponde aos filtros selecionados.")

# =============================================================================
# ABA 3: NOVO LANÇAMENTO
# =============================================================================
with tab_novo:
    st.subheader("➕ Registrar Novo Gasto ou Serviço")
    st.caption("Insira os detalhes do item. O fluxo de desembolso futuro é calculado automaticamente a partir da condição de pagamento.")

    with st.form("form_novo_gasto", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            novo_data = st.date_input("Data da Contratação / Compra", value=date.today())
            novo_cat = st.selectbox("Categoria *", nomes_categorias)
            novo_fornecedor = st.text_input("Fornecedor / Prestador de Serviço", placeholder="Ex: Portobello, Vidraçaria Cristal...")
            if nomes_fornecedores:
                st.caption(f"💡 Cadastrados: {', '.join(nomes_fornecedores[:6])}...")
        with c2:
            novo_cond = st.selectbox("Condição de Pagamento (Fixa)", CONDICOES_PAGAMENTO, index=0)
            novo_status = st.selectbox("Status Atual", STATUS_LISTA, index=0)
            novo_desc = st.text_input("Descrição do Item / Serviço", placeholder="Ex: Porcelanato 90x90, Armários embutidos...")

        c3, c4 = st.columns(2)
        with c3:
            novo_orcado = st.number_input("Valor Orçado (R$)", min_value=0.0, step=100.0, format="%.2f")
        with c4:
            novo_pago = st.number_input("Valor Efetivamente Pago / Contratado (R$)", min_value=0.0, step=100.0, format="%.2f")

        # Simulação imediata de desembolso
        if novo_pago > 0:
            if "x" in novo_cond.lower():
                vezes = int(novo_cond.lower().replace("x", "").strip())
                st.info(f"💡 Simulação: {vezes} parcelas mensais de aproximadamente **R$ {novo_pago/vezes:,.2f}**.")
            elif novo_cond in ["7 dias", "14 dias", "31 dias"]:
                dias = int(novo_cond.split()[0])
                st.info(f"💡 Simulação: Vencimento único em {novo_data + timedelta(days=dias)} (daqui a {dias} dias).")
            else:
                st.info(f"💡 Simulação: Desembolso integral à vista na data {novo_data}.")

        submitted = st.form_submit_button("💾 Salvar Gasto no Supabase")
        if submitted:
            if not novo_desc.strip():
                st.error("Por favor, preencha a descrição do item.")
            else:
                payload = {
                    "data_compra": novo_data.isoformat(),
                    "categoria": novo_cat,
                    "descricao": novo_desc.strip(),
                    "fornecedor": novo_fornecedor.strip() or "Não Informado",
                    "valor_orcado": float(novo_orcado),
                    "valor_pago": float(novo_pago),
                    "status": novo_status,
                    "forma_pagamento": novo_cond,
                }
                if is_connected and client:
                    ok = client.create_gasto(payload)
                    if ok:
                        st.success("✅ Gasto registrado com sucesso no Supabase!")
                        st.rerun()
                    else:
                        st.error("❌ Erro ao salvar no Supabase. Verifique as credenciais.")
                else:
                    payload["id"] = max([g.get("id", 0) for g in gastos] + [0]) + 1
                    if "gastos_local" in st.session_state:
                        st.session_state["gastos_local"].insert(0, payload)
                    st.success("✅ Gasto adicionado no modo de demonstração!")
                    st.rerun()

# =============================================================================
# ABA 4: GERENCIAR CATEGORIAS E FORNECEDORES
# =============================================================================
with tab_cadastros:
    st.subheader("🏷️ Gestão de Categorias e Fornecedores")
    st.caption("Gerencie as tabelas auxiliares para padronizar despesas e manter o cadastro organizado no Supabase.")

    sub_c1, sub_c2 = st.tabs(["🏷️ Categorias de Gastos", "🏢 Fornecedores & Prestadores"])

    with sub_c1:
        st.markdown("#### Categorias Cadastradas")
        cats_table = []
        for c in categorias:
            c_nome = c.get("nome", "")
            c_gastos = [g for g in gastos if g.get("categoria") == c_nome]
            total_cat = sum(float(g.get("valor_pago") or 0) for g in c_gastos)
            cats_table.append({
                "ID": c.get("id"),
                "Nome": c_nome,
                "Descrição": c.get("descricao", "") or "-",
                "Lançamentos Vinculados": len(c_gastos),
                "Total Pago": f"R$ {total_cat:,.2f}",
            })
        if cats_table:
            st.dataframe(pd.DataFrame(cats_table), use_container_width=True, hide_index=True)

        col_c_nova, col_c_alterar = st.columns(2)
        with col_c_nova:
            st.markdown("##### ➕ Nova Categoria")
            with st.form("form_nova_categoria", clear_on_submit=True):
                n_cat_nome = st.text_input("Nome da Categoria *", placeholder="Ex: Automação Residencial")
                n_cat_desc = st.text_input("Descrição / Finalidade", placeholder="Ex: Equipamentos de domótica e sonorização")
                sub_n_cat = st.form_submit_button("Salvar Categoria")
                if sub_n_cat:
                    if not n_cat_nome.strip():
                        st.error("O nome da categoria é obrigatório.")
                    else:
                        cat_payload = {"nome": n_cat_nome.strip(), "descricao": n_cat_desc.strip()}
                        if is_connected and client:
                            if client.create_categoria(cat_payload):
                                st.success(f"Categoria '{n_cat_nome}' salva no Supabase!")
                                st.rerun()
                            else:
                                st.error("Erro ao salvar categoria no Supabase.")
                        else:
                            next_cid = max([c.get("id", 0) for c in categorias] + [0]) + 1
                            cat_payload["id"] = next_cid
                            st.session_state["categorias_local"].append(cat_payload)
                            st.success(f"Categoria '{n_cat_nome}' adicionada localmente!")
                            st.rerun()

        with col_c_alterar:
            st.markdown("##### ✏️ Editar / Excluir Categoria")
            if categorias:
                c_sel = st.selectbox("Selecione a categoria:", [c.get("nome") for c in categorias], key="sb_edit_cat")
                c_selecionada = next((c for c in categorias if c.get("nome") == c_sel), None)
                if c_selecionada:
                    with st.form("form_edit_cat_detalhe"):
                        e_c_nome = st.text_input("Nome", value=c_selecionada.get("nome", ""))
                        e_c_desc = st.text_input("Descrição", value=c_selecionada.get("descricao", "") or "")
                        salvar_c = st.form_submit_button("💾 Salvar Alterações")
                        if salvar_c:
                            up_cat = {"nome": e_c_nome.strip(), "descricao": e_c_desc.strip()}
                            if is_connected and client:
                                if client.update_categoria(c_selecionada["id"], up_cat):
                                    st.success("Categoria atualizada no Supabase!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar categoria.")
                            else:
                                c_selecionada.update(up_cat)
                                st.success("Categoria atualizada localmente!")
                                st.rerun()

                    if st.button(f"🗑️ Excluir Categoria '{c_sel}'", key="btn_del_cat_final"):
                        if is_connected and client:
                            if client.delete_categoria(c_selecionada["id"]):
                                st.success("Categoria excluída do Supabase!")
                                st.rerun()
                            else:
                                st.error("Erro ao excluir categoria do Supabase.")
                        else:
                            st.session_state["categorias_local"] = [c for c in st.session_state["categorias_local"] if c.get("id") != c_selecionada.get("id")]
                            st.success("Categoria excluída localmente!")
                            st.rerun()

    with sub_c2:
        st.markdown("#### Fornecedores e Prestadores Cadastrados")
        forns_table = []
        for f in fornecedores:
            f_nome = f.get("nome", "")
            f_gastos = [g for g in gastos if g.get("fornecedor") == f_nome]
            total_forn = sum(float(g.get("valor_pago") or 0) for g in f_gastos)
            forns_table.append({
                "ID": f.get("id"),
                "Nome": f_nome,
                "Categoria Padrão": f.get("categoria_padrao", "") or "-",
                "Telefone": f.get("telefone", "") or "-",
                "Observação": f.get("observacao", "") or "-",
                "Compras": len(f_gastos),
                "Total Contratado": f"R$ {total_forn:,.2f}",
            })
        if forns_table:
            st.dataframe(pd.DataFrame(forns_table), use_container_width=True, hide_index=True)

        col_f_nova, col_f_alterar = st.columns(2)
        with col_f_nova:
            st.markdown("##### ➕ Novo Fornecedor")
            with st.form("form_novo_fornecedor", clear_on_submit=True):
                n_f_nome = st.text_input("Nome do Fornecedor / Empresa *", placeholder="Ex: Marmoraria Real")
                n_f_cat = st.selectbox("Categoria Principal", nomes_categorias, key="novo_forn_cat_select")
                n_f_tel = st.text_input("Telefone / WhatsApp", placeholder="(11) 98888-7777")
                n_f_obs = st.text_input("Observações", placeholder="Ex: Contato Carlos, desconto no PIX")
                sub_n_forn = st.form_submit_button("Salvar Fornecedor")
                if sub_n_forn:
                    if not n_f_nome.strip():
                        st.error("O nome do fornecedor é obrigatório.")
                    else:
                        forn_payload = {
                            "nome": n_f_nome.strip(),
                            "categoria_padrao": n_f_cat,
                            "telefone": n_f_tel.strip(),
                            "observacao": n_f_obs.strip(),
                        }
                        if is_connected and client:
                            if client.create_fornecedor(forn_payload):
                                st.success(f"Fornecedor '{n_f_nome}' salvo no Supabase!")
                                st.rerun()
                            else:
                                st.error("Erro ao salvar fornecedor no Supabase.")
                        else:
                            next_fid = max([f.get("id", 0) for f in fornecedores] + [0]) + 1
                            forn_payload["id"] = next_fid
                            st.session_state["fornecedores_local"].append(forn_payload)
                            st.success(f"Fornecedor '{n_f_nome}' cadastrado localmente!")
                            st.rerun()

        with col_f_alterar:
            st.markdown("##### ✏️ Editar / Excluir Fornecedor")
            if fornecedores:
                f_sel = st.selectbox("Selecione o fornecedor:", [f.get("nome") for f in fornecedores], key="sb_edit_forn")
                f_selecionado = next((f for f in fornecedores if f.get("nome") == f_sel), None)
                if f_selecionado:
                    with st.form("form_edit_forn_detalhe"):
                        e_f_nome = st.text_input("Nome", value=f_selecionado.get("nome", ""))
                        cat_idx = nomes_categorias.index(f_selecionado.get("categoria_padrao", nomes_categorias[0])) if f_selecionado.get("categoria_padrao") in nomes_categorias else 0
                        e_f_cat = st.selectbox("Categoria Principal", nomes_categorias, index=cat_idx, key="edit_forn_cat_select")
                        e_f_tel = st.text_input("Telefone", value=f_selecionado.get("telefone", "") or "")
                        e_f_obs = st.text_input("Observações", value=f_selecionado.get("observacao", "") or "")
                        salvar_f = st.form_submit_button("💾 Salvar Alterações")
                        if salvar_f:
                            up_forn = {
                                "nome": e_f_nome.strip(),
                                "categoria_padrao": e_f_cat,
                                "telefone": e_f_tel.strip(),
                                "observacao": e_f_obs.strip(),
                            }
                            if is_connected and client:
                                if client.update_fornecedor(f_selecionado["id"], up_forn):
                                    st.success("Fornecedor atualizado no Supabase!")
                                    st.rerun()
                                else:
                                    st.error("Erro ao atualizar fornecedor.")
                            else:
                                f_selecionado.update(up_forn)
                                st.success("Fornecedor atualizado localmente!")
                                st.rerun()

                    if st.button(f"🗑️ Excluir Fornecedor '{f_sel}'", key="btn_del_forn_final"):
                        if is_connected and client:
                            if client.delete_fornecedor(f_selecionado["id"]):
                                st.success("Fornecedor excluído do Supabase!")
                                st.rerun()
                            else:
                                st.error("Erro ao excluir fornecedor do Supabase.")
                        else:
                            st.session_state["fornecedores_local"] = [f for f in st.session_state["fornecedores_local"] if f.get("id") != f_selecionado.get("id")]
                            st.success("Fornecedor excluído localmente!")
                            st.rerun()

# =============================================================================
# ABA 5: GERENCIAR E EXCLUIR
# =============================================================================
with tab_editar:
    st.subheader("✏️ Atualizar ou Excluir Lançamentos")
    st.caption("Selecione um lançamento existente para alterar o status, ajustar valores ou remover da base de dados.")

    if gastos:
        opcoes_gastos = {
            f"#{g.get('id')} - {g.get('descricao')} (R$ {float(g.get('valor_pago') or 0):,.2f} | {g.get('forma_pagamento')})": g.get("id")
            for g in gastos
        }
        item_escolhido = st.selectbox("Selecione o Lançamento:", list(opcoes_gastos.keys()))
        id_selecionado = opcoes_gastos[item_escolhido]
        gasto_atual = next((g for g in gastos if g.get("id") == id_selecionado), None)

        if gasto_atual:
            with st.form("form_editar_gasto"):
                e1, e2 = st.columns(2)
                with e1:
                    cat_idx_ed = nomes_categorias.index(gasto_atual.get("categoria", nomes_categorias[0])) if gasto_atual.get("categoria") in nomes_categorias else 0
                    ed_cat = st.selectbox("Categoria", nomes_categorias, index=cat_idx_ed)
                    ed_desc = st.text_input("Descrição", value=gasto_atual.get("descricao", ""))
                    ed_forn = st.text_input("Fornecedor", value=gasto_atual.get("fornecedor", ""))
                with e2:
                    cond_idx = CONDICOES_PAGAMENTO.index(gasto_atual.get("forma_pagamento", CONDICOES_PAGAMENTO[0])) if gasto_atual.get("forma_pagamento") in CONDICOES_PAGAMENTO else 0
                    ed_cond = st.selectbox("Condição de Pagamento", CONDICOES_PAGAMENTO, index=cond_idx)
                    status_idx = STATUS_LISTA.index(gasto_atual.get("status", STATUS_LISTA[0])) if gasto_atual.get("status") in STATUS_LISTA else 0
                    ed_status = st.selectbox("Status", STATUS_LISTA, index=status_idx)

                e3, e4 = st.columns(2)
                with e3:
                    ed_orc = st.number_input("Valor Orçado (R$)", value=float(gasto_atual.get("valor_orcado") or 0.0), step=100.0, format="%.2f")
                with e4:
                    ed_pag = st.number_input("Valor Pago (R$)", value=float(gasto_atual.get("valor_pago") or 0.0), step=100.0, format="%.2f")

                salvar_edicao = st.form_submit_button("💾 Salvar Alterações")
                if salvar_edicao:
                    update_payload = {
                        "categoria": ed_cat,
                        "descricao": ed_desc.strip(),
                        "fornecedor": ed_forn.strip() or "Não Informado",
                        "forma_pagamento": ed_cond,
                        "status": ed_status,
                        "valor_orcado": float(ed_orc),
                        "valor_pago": float(ed_pag),
                    }
                    if is_connected and client:
                        if client.update_gasto(id_selecionado, update_payload):
                            st.success(f"✅ Lançamento #{id_selecionado} atualizado no Supabase!")
                            st.rerun()
                        else:
                            st.error("Erro ao atualizar no banco de dados.")
                    else:
                        gasto_atual.update(update_payload)
                        if "gastos_local" in st.session_state:
                            for idx, item in enumerate(st.session_state["gastos_local"]):
                                if item.get("id") == id_selecionado:
                                    st.session_state["gastos_local"][idx].update(update_payload)
                                    break
                        st.success("Atualizado localmente!")
                        st.rerun()

            # Área de exclusão individual
            st.markdown("---")
            st.markdown("#### 🗑️ Excluir Registro Individual")
            col_d1, col_d2 = st.columns([3, 1])
            with col_d1:
                confirma = st.checkbox(f"Confirmo que desejo apagar permanentemente o lançamento #{id_selecionado}")
            with col_d2:
                if st.button("Excluir Definitivamente", type="primary", disabled=not confirma):
                    if is_connected and client:
                        if client.delete_gasto(id_selecionado):
                            st.success(f"Lançamento #{id_selecionado} excluído do Supabase!")
                            st.rerun()
                        else:
                            st.error("Erro ao excluir do Supabase.")
                    else:
                        if "gastos_local" in st.session_state:
                            st.session_state["gastos_local"] = [
                                g for g in st.session_state["gastos_local"] if g.get("id") != id_selecionado
                            ]
                        st.success("Excluído localmente!")
                        st.rerun()

        # Área de Zerar Base Completa
        st.markdown("---")
        st.markdown("#### 🧨 Zerar Toda a Base de Dados (Começar do Zero)")
        st.caption("Remove permanentemente **TODOS** os lançamentos para que você possa cadastrar suas despesas reais do zero.")
        col_z1, col_z2 = st.columns([3, 1])
        with col_z1:
            confirma_tudo = st.checkbox(f"Confirmo que desejo apagar TODOS os {len(gastos)} lançamentos e começar do zero")
        with col_z2:
            if st.button("Zerar Todos os Gastos", type="secondary", disabled=not confirma_tudo):
                if is_connected and client:
                    if client.delete_all_gastos():
                        st.success("Base de dados do Supabase limpa com sucesso (0 registros)!")
                        st.rerun()
                    else:
                        st.error("Erro ao limpar dados do Supabase. Você também pode rodar `TRUNCATE TABLE public.gastos_reforma;` no SQL Editor do Supabase.")
                else:
                    st.session_state["gastos_local"] = []
                    st.success("Base local limpa com sucesso (0 registros)!")
                    st.rerun()
    else:
        st.info("ℹ️ Nenhum lançamento cadastrado no momento. A base está completamente limpa (0 registros) e pronta para receber seus gastos reais!")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.markdown("👉 Acesse a aba **➕ Novo Lançamento** para cadastrar seu primeiro gasto da reforma.")
        with col_v2:
            if not is_connected:
                if st.button("Restaurar Dados de Exemplo (Demonstração)"):
                    st.session_state["gastos_local"] = [dict(d) for d in DADOS_DEMO]
                    st.rerun()

