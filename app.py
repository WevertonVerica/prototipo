
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium

from streamlit_folium import st_folium
from pathlib import Path

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================

st.set_page_config(
    page_title="Consulta de Imóveis",
    page_icon="🏠",
    layout="wide"
)

ARQUIVO = "prototipo.xlsx"

COLUNA_CODIGO = "BCICADASTRO"
COLUNA_PISO = "zoneamento"
COLUNA_FORRO = "ocupacao"
COLUNA_ESTADO = "utilizacao"
COLUNA_VALOR = "valor predito"
COLUNA_LATITUDE = "latitude"
COLUNA_LONGITUDE = "longitude"


# ==========================================
# 2. CARREGAMENTO DOS DADOS
# ==========================================

@st.cache_data
def carregar_dados(arquivo):
    caminho = Path(arquivo)

    if not caminho.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {arquivo}"
        )

    if caminho.suffix.lower() in [".xlsx", ".xls"]:
        dados = pd.read_excel(
            caminho,
            engine="openpyxl"
            if caminho.suffix.lower() == ".xlsx"
            else None
        )

    elif caminho.suffix.lower() == ".csv":
        dados = pd.read_csv(
            caminho,
            sep=None,
            engine="python"
        )

    else:
        raise ValueError(
            "Formato não suportado. Use XLSX ou CSV."
        )

    # Limpa os nomes das colunas
    dados.columns = dados.columns.str.strip()

    # Converte o código para número
    dados[COLUNA_CODIGO] = pd.to_numeric(
        dados[COLUNA_CODIGO],
        errors="coerce"
    )

    return dados


# ==========================================
# 3. FUNÇÕES AUXILIARES
# ==========================================

def mostrar_valor(valor):
    if pd.isna(valor):
        return "Não informado"

    return str(valor)


def moeda_br(valor):
    texto = f"{valor:,.2f}"
    texto = texto.replace(",", "X")
    texto = texto.replace(".", ",")
    texto = texto.replace("X", ".")

    return f"R$ {texto}"


# ==========================================
# 4. TÍTULO
# ==========================================

st.title("Consulta de Cadastro Imobiliário")

st.write(
    "Consulte as características, a localização "
    "e o valor predito de um imóvel."
)


# ==========================================
# 5. CARREGAR E VALIDAR A BASE
# ==========================================

try:
    dados = carregar_dados(ARQUIVO)

    colunas_necessarias = [
        COLUNA_CODIGO,
        COLUNA_PISO,
        COLUNA_FORRO,
        COLUNA_ESTADO,
        COLUNA_VALOR,
        COLUNA_LATITUDE,
        COLUNA_LONGITUDE
    ]

    faltantes = [
        coluna
        for coluna in colunas_necessarias
        if coluna not in dados.columns
    ]

    if faltantes:
        st.error(
            "As seguintes colunas não foram encontradas: "
            + ", ".join(faltantes)
        )

        st.write(
            "Colunas existentes na planilha:",
            dados.columns.tolist()
        )

        st.stop()

    # ==========================================
    # 6. FORMULÁRIO DE CONSULTA
    # ==========================================

    if "codigo_consultado" not in st.session_state:
        st.session_state.codigo_consultado = None

    with st.form("consulta_imovel"):
        codigo_digitado = st.text_input(
            "Código do imóvel (BCICADASTRO)",
            placeholder="Ex.: 9999999"
        )

        consultar = st.form_submit_button(
            "Consultar imóvel",
            type="primary"
        )

    # Só altera a consulta quando o usuário envia
    # um novo código.
    if consultar:
        codigo_digitado = codigo_digitado.strip()

        if not codigo_digitado:
            st.session_state.codigo_consultado = None
            st.warning("Digite o código do imóvel.")

        elif not codigo_digitado.isdigit():
            st.session_state.codigo_consultado = None
            st.warning(
                "Digite um código numérico inteiro válido."
            )

        else:
            st.session_state.codigo_consultado = int(
                codigo_digitado
            )

    # ==========================================
    # 7. RESULTADO DA CONSULTA
    # ==========================================

    codigo = st.session_state.codigo_consultado

    if codigo is not None:

        resultado = dados[
            dados[COLUNA_CODIGO] == codigo
        ]

        if resultado.empty:
            st.error(
                f"Nenhum imóvel encontrado para o código {codigo}."
            )

        else:
            imovel = resultado.iloc[0]

            if len(resultado) > 1:
                st.warning(
                    "Há mais de um registro com esse código. "
                    "Será exibido o primeiro."
                )

            st.success(f"Imóvel {codigo} encontrado!")

            # ==========================================
            # 8. CARACTERÍSTICAS CADASTRAIS
            # ==========================================

            st.subheader("Características do imóvel")

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Zoneamento",
                mostrar_valor(imovel[COLUNA_PISO])
            )

            col2.metric(
                "Ocupação",
                mostrar_valor(imovel[COLUNA_FORRO])
            )

            col3.metric(
                "Utilização",
                mostrar_valor(imovel[COLUNA_ESTADO])
            )

            # ==========================================
            # 9. VALOR PREDITO E INTERVALO DE ±30%
            # ==========================================

            st.subheader("Valor predito do imóvel")

            valor = pd.to_numeric(
                pd.Series([imovel[COLUNA_VALOR]]),
                errors="coerce"
            ).iloc[0]

            if pd.isna(valor):
                st.warning(
                    "O valor predito não está informado "
                    "ou não é numérico."
                )

            elif valor < 0:
                st.warning(
                    "O valor predito é negativo. "
                    "Verifique o dado antes de exibir o gráfico."
                )

            else:
                inferior = valor * 0.70
                superior = valor * 1.30

                st.metric(
                    "Valor predito",
                    moeda_br(valor)
                )

                st.caption(
                    "A faixa de ±30% é ilustrativa e "
                    "não representa um intervalo de confiança."
                )

                fig = go.Figure()

                # Barra horizontal do limite inferior
                # até o limite superior
                fig.add_trace(
                    go.Bar(
                        x=[superior - inferior],
                        base=[inferior],
                        y=["Faixa de valores"],
                        orientation="h",
                        width=0.30,
                        marker_color="#BFD7ED",
                        name="Intervalo de ±30%",
                        hovertemplate=(
                            "Faixa: "
                            + moeda_br(inferior)
                            + " a "
                            + moeda_br(superior)
                            + "<extra></extra>"
                        )
                    )
                )

                # Marca o valor predito
                fig.add_trace(
                    go.Scatter(
                        x=[valor],
                        y=["Faixa de valores"],
                        mode="markers",
                        marker=dict(
                            color="#145DA0",
                            size=14,
                            symbol="diamond"
                        ),
                        name="Valor predito",
                        hovertemplate=(
                            "Valor predito: R$ %{x:,.2f}"
                            "<extra></extra>"
                        )
                    )
                )

                # Marcas dos limites
                fig.add_trace(
                    go.Scatter(
                        x=[inferior, superior],
                        y=[
                            "Faixa de valores",
                            "Faixa de valores"
                        ],
                        mode="markers",
                        marker=dict(
                            color="#D9534F",
                            size=12,
                            symbol="line-ns-open"
                        ),
                        name="Limites"
                    )
                )

                # Anotações dos três valores
                fig.add_annotation(
                    x=inferior,
                    y="Faixa de valores",
                    text=f"-30%<br>{moeda_br(inferior)}",
                    showarrow=False,
                    yshift=-35
                )

                fig.add_annotation(
                    x=valor,
                    y="Faixa de valores",
                    text=f"Predito<br>{moeda_br(valor)}",
                    showarrow=False,
                    yshift=35
                )

                fig.add_annotation(
                    x=superior,
                    y="Faixa de valores",
                    text=f"+30%<br>{moeda_br(superior)}",
                    showarrow=False,
                    yshift=-35
                )

                amplitude = superior - inferior
                margem = amplitude * 0.20

                fig.update_layout(
                    height=260,
                    margin=dict(
                        l=20,
                        r=20,
                        t=70,
                        b=35
                    ),
                    xaxis=dict(
                        title="Valor do imóvel (R$)",
                        range=[
                            max(0, inferior - margem),
                            superior + margem
                        ],
                        tickformat=",.0f"
                    ),
                    yaxis=dict(visible=False),
                    showlegend=False
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )

            # ==========================================
            # 10. MAPA DO IMÓVEL
            # ==========================================

            st.subheader("Localização do imóvel")

            latitude = pd.to_numeric(
                pd.Series([imovel[COLUNA_LATITUDE]]),
                errors="coerce"
            ).iloc[0]

            longitude = pd.to_numeric(
                pd.Series([imovel[COLUNA_LONGITUDE]]),
                errors="coerce"
            ).iloc[0]

            if pd.isna(latitude) or pd.isna(longitude):
                st.warning(
                    "Este imóvel não possui coordenadas válidas."
                )

            elif not (
                -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                st.warning(
                    "As coordenadas deste imóvel são inválidas."
                )

            else:
                mapa = folium.Map(
                    location=[latitude, longitude],
                    zoom_start=18,
                    tiles="OpenStreetMap"
                )

                folium.Marker(
                    location=[latitude, longitude],
                    tooltip=f"Imóvel {codigo}",
                    popup=f"Cadastro: {codigo}",
                    icon=folium.Icon(
                        color="red",
                        icon="home"
                    )
                ).add_to(mapa)

                # O resultado da consulta fica salvo no
                # session_state, mesmo após interagir com o mapa.
                st_folium(
                    mapa,
                    use_container_width=True,
                    height=450,
                    key=f"mapa_{codigo}",
                    returned_objects=[]
                )

                link_google = (
                    "https://www.google.com/maps/search/?api=1"
                    f"&query={latitude},{longitude}"
                )

                st.link_button(
                    "Abrir no Google Maps",
                    link_google
                )

except FileNotFoundError as erro:
    st.error(str(erro))

except Exception as erro:
    st.error(
        f"Erro ao carregar ou consultar os dados: {erro}"
    )
