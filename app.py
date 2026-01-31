import streamlit as st
import pandas as pd
import plotly.express as px

# ==============================
# CONFIGURAÇÃO DA PÁGINA
# ==============================
st.set_page_config(
    page_title="Dashboard de Salários na Área de Dados",
    page_icon="📊",
    layout="wide",
)

# ==============================
# CONSTANTES DE SEGURANÇA
# ==============================
DATASET_URL = (
    "https://raw.githubusercontent.com/vqrca/"
    "dashboard_salarios_dados/"
    "main/dados-imersao-final.csv"
)

COLUNAS_ESPERADAS = {
    "ano": "int64",
    "senioridade": "object",
    "contrato": "object",
    "tamanho_empresa": "object",
    "cargo": "object",
    "usd": "float64",
    "remoto": "object",
    "residencia_iso3": "object",
}

MAX_LINHAS_TABELA = 1000


# ==============================
# CARREGAMENTO SEGURO DOS DADOS
# ==============================
@st.cache_data(show_spinner=True)
def carregar_dados():
    try:
        df = pd.read_csv(DATASET_URL)

        # --- Validação de esquema ---
        colunas_faltantes = set(COLUNAS_ESPERADAS) - set(df.columns)
        if colunas_faltantes:
            raise ValueError(f"Colunas ausentes no dataset: {colunas_faltantes}")

        for coluna, tipo in COLUNAS_ESPERADAS.items():
            df[coluna] = df[coluna].astype(tipo, errors="raise")

        # --- Sanitização de texto (anti data poisoning) ---
        colunas_texto = [
            "senioridade", "contrato", "tamanho_empresa",
            "cargo", "remoto", "residencia_iso3"
        ]

        for col in colunas_texto:
            df[col] = (
                df[col]
                .astype(str)
                .str.slice(0, 100)
                .str.replace(r"[<>]", "", regex=True)
                .str.strip()
            )

        return df

    except Exception as e:
        st.error("❌ Erro ao carregar ou validar os dados.")
        st.exception(e)
        st.stop()


df = carregar_dados()

# ==============================
# BARRA LATERAL — FILTROS
# ==============================
st.sidebar.header("🔍 Filtros")

anos = sorted(df["ano"].unique())
anos_sel = st.sidebar.multiselect("Ano", anos, default=anos)

senioridades = sorted(df["senioridade"].unique())
senioridades_sel = st.sidebar.multiselect(
    "Senioridade", senioridades, default=senioridades
)

contratos = sorted(df["contrato"].unique())
contratos_sel = st.sidebar.multiselect(
    "Tipo de Contrato", contratos, default=contratos
)

tamanhos = sorted(df["tamanho_empresa"].unique())
tamanhos_sel = st.sidebar.multiselect(
    "Tamanho da Empresa", tamanhos, default=tamanhos
)

# ==============================
# FILTRAGEM DOS DADOS
# ==============================
df_filtrado = df[
    (df["ano"].isin(anos_sel)) &
    (df["senioridade"].isin(senioridades_sel)) &
    (df["contrato"].isin(contratos_sel)) &
    (df["tamanho_empresa"].isin(tamanhos_sel))
]

# ==============================
# CONTEÚDO PRINCIPAL
# ==============================
st.title("🎲 Dashboard de Análise de Salários na Área de Dados")
st.markdown(
    "Explore os dados salariais na área de dados. "
    "Utilize os filtros à esquerda para refinar sua análise."
)

# ==============================
# KPIs
# ==============================
st.subheader("Métricas gerais (Salário anual em USD)")

if not df_filtrado.empty:
    salario_medio = df_filtrado["usd"].mean()
    salario_max = df_filtrado["usd"].max()
    total = len(df_filtrado)
    cargo_freq = df_filtrado["cargo"].mode().iloc[0]
else:
    salario_medio = salario_max = total = 0
    cargo_freq = "—"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Salário médio", f"${salario_medio:,.0f}")
col2.metric("Salário máximo", f"${salario_max:,.0f}")
col3.metric("Total de registros", f"{total:,}")
col4.metric("Cargo mais frequente", cargo_freq)

st.markdown("---")

# ==============================
# GRÁFICOS
# ==============================
st.subheader("Gráficos")

col_g1, col_g2 = st.columns(2)

with col_g1:
    if not df_filtrado.empty:
        top_cargos = (
            df_filtrado.groupby("cargo")["usd"]
            .mean()
            .nlargest(10)
            .sort_values()
            .reset_index()
        )

        fig = px.bar(
            top_cargos,
            x="usd",
            y="cargo",
            orientation="h",
            title="Top 10 cargos por salário médio",
            labels={"usd": "Média salarial anual (USD)", "cargo": ""}
        )
        st.plotly_chart(fig, use_container_width=True)

with col_g2:
    if not df_filtrado.empty:
        fig = px.histogram(
            df_filtrado,
            x="usd",
            nbins=30,
            title="Distribuição de salários anuais",
            labels={"usd": "Faixa salarial (USD)", "count": ""}
        )
        st.plotly_chart(fig, use_container_width=True)

col_g3, col_g4 = st.columns(2)

with col_g3:
    if not df_filtrado.empty:
        remoto = df_filtrado["remoto"].value_counts().reset_index()
        remoto.columns = ["tipo_trabalho", "quantidade"]

        fig = px.pie(
            remoto,
            names="tipo_trabalho",
            values="quantidade",
            hole=0.5,
            title="Proporção dos tipos de trabalho"
        )
        st.plotly_chart(fig, use_container_width=True)

with col_g4:
    df_ds = df_filtrado[df_filtrado["cargo"] == "Data Scientist"]
    if not df_ds.empty:
        media_pais = (
            df_ds.groupby("residencia_iso3")["usd"]
            .mean()
            .reset_index()
        )

        fig = px.choropleth(
            media_pais,
            locations="residencia_iso3",
            color="usd",
            title="Salário médio de Cientista de Dados por país",
            labels={"usd": "Salário médio (USD)"}
        )
        st.plotly_chart(fig, use_container_width=True)

# ==============================
# TABELA DE DADOS
# ==============================
st.subheader("Dados Detalhados")
st.dataframe(df_filtrado.head(MAX_LINHAS_TABELA))
