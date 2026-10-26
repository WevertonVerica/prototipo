
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

# ==========================================
# 1. CONFIGURAÇÕES
# ==========================================

st.set_page_config(
    page_title="Consulta de Cadastro Imobiliário",
    page_icon="🏠",
    layout="centered"
)

ARQUIVO = "prototipo.xlsx"

COLUNA_CODIGO = "BCICADASTRO"
COLUNA_PISO = "zoneamento"
COLUNA_FORRO = "ocupacao"
COLUNA_ESTADO = "utilizacao"
COLUNA_VALOR = "valor predito"

# ==========================================
# 2. CARREGAMENTO DOS DADOS
# ==========================================

@st.cache_data
def carregar_dados(arquivo):
    caminho = Path(arquivo)

    if caminho.suffix.lower() == ".csv":
        dados = pd.read_csv(
            caminho,
            sep=None,
            engine="python"
        )
    elif caminho.suffix.lower() in [".xlsx", ".xls"]:
        dados = pd.read_excel(caminho)
    else:
        raise ValueError("Formato de arquivo não suportado.")

    # Remove espaços extras dos nomes das colunas
    dados.columns = dados.columns.str.strip()

    # Padroniza o código para comparação numérica
    dados[COLUNA_CODIGO] = pd.to_numeric(
        dados[COLUNA_CODIGO],
        errors="coerce"
    )

    return dados


# ==========================================
# 3. TÍTULO DA APLICAÇÃO
# ==========================================

st.title("🏠 Consulta de Cadastro Imobiliário")
st.write(
    "Digite o código do imóvel para consultar "
    "suas características e o valor predito."
)

# ==========================================
# 4. CONSULTA DO IMÓVEL
# ==========================================

try:
    dados = carregar_dados(ARQUIVO)

    colunas_necessarias = [
        COLUNA_CODIGO,
        COLUNA_PISO,
        COLUNA_FORRO,
        COLUNA_ESTADO,
        COLUNA_VALOR
    ]

    faltantes = [
        coluna for coluna in colunas_necessarias
        if coluna not in dados.columns
    ]

    if faltantes:
        st.error(
            "Não encontrei estas colunas no arquivo: "
            + ", ".join(faltantes)
        )

        st.write(
            "Colunas disponíveis:",
            dados.columns.tolist()
        )

    else:
        with st.form("consulta_imovel"):
            codigo_digitado = st.text_input(
                "Código do imóvel (bcicodigo)",
                placeholder="Ex.: 9999999"
            )

            consultar = st.form_submit_button("Consultar")

        if consultar:
            codigo_digitado = codigo_digitado.strip()

            if not codigo_digitado:
                st.warning("Digite o código do imóvel.")

            elif not codigo_digitado.isdigit():
                st.warning(
                    "Digite um código numérico inteiro válido."
                )

            else:
                codigo = int(codigo_digitado)

                resultado = dados[
                    dados[COLUNA_CODIGO] == codigo
                ]

                if resultado.empty:
                    st.error("Imóvel não encontrado.")

                else:
                    imovel = resultado.iloc[0]

                    if len(resultado) > 1:
                        st.warning(
                            "Existem vários registros com esse código. "
                            "Será exibido o primeiro."
                        )

                    st.success(
                        f"Imóvel {codigo} encontrado!"
                    )

                    # ==========================================
                    # 5. CARACTERÍSTICAS DO IMÓVEL
                    # ==========================================

                    st.subheader("Características do imóvel")

                    def mostrar_valor(valor):
                        if pd.isna(valor):
                            return "Não informado"
                        return str(valor)

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Piso",
                        mostrar_valor(imovel[COLUNA_PISO])
                    )

                    col2.metric(
                        "Forro",
                        mostrar_valor(imovel[COLUNA_FORRO])
                    )

                    col3.metric(
                        "Estado de conservação",
                        mostrar_valor(imovel[COLUNA_ESTADO])
                    )

                    # ==========================================
                    # 6. GRÁFICO DO VALOR PREDITO
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
                            "Verifique o dado antes de gerar o gráfico."
                        )

                    else:
                        limite_inferior = valor * 0.70
                        limite_superior = valor * 1.30

                        def moeda_br(valor):
                            texto = f"{valor:,.2f}"
                            texto = texto.replace(",", "X")
                            texto = texto.replace(".", ",")
                            texto = texto.replace("X", ".")
                            return f"R$ {texto}"

                        st.metric(
                            "Valor predito",
                            moeda_br(valor)
                        )

                        st.caption(
                            "Faixa ilustrativa de ±30% "
                            "em torno do valor predito."
                        )

                        # Barra horizontal do intervalo
                        fig = go.Figure()

                        fig.add_trace(
                            go.Bar(
                                x=[
                                    limite_superior
                                    - limite_inferior
                                ],
                                base=[limite_inferior],
                                y=["Faixa de valores"],
                                orientation="h",
                                marker_color="#BFD7ED",
                                width=0.35,
                                hovertemplate=(
                                    "Intervalo: %{base:,.2f} "
                                    "a %{customdata:,.2f}"
                                    "<extra></extra>"
                                ),
                                customdata=[limite_superior],
                                showlegend=False
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
                                    "Predito: %{x:,.2f}"
                                    "<extra></extra>"
                                )
                            )
                        )

                        # Marca os limites do intervalo
                        fig.add_trace(
                            go.Scatter(
                                x=[
                                    limite_inferior,
                                    limite_superior
                                ],
                                y=[
                                    "Faixa de valores",
                                    "Faixa de valores"
                                ],
                                mode="markers",
                                marker=dict(
                                    color="#D9534F",
                                    size=10,
                                    symbol="line-ns-open"
                                ),
                                name="Limites ±30%",
                                hovertemplate=(
                                    "%{x:,.2f}<extra></extra>"
                                )
                            )
                        )

                        # Anotações dos valores
                        fig.add_annotation(
                            x=limite_inferior,
                            y="Faixa de valores",
                            text=f"-30%<br>{moeda_br(limite_inferior)}",
                            showarrow=False,
                            yshift=-35,
                            font=dict(color="#D9534F")
                        )

                        fig.add_annotation(
                            x=valor,
                            y="Faixa de valores",
                            text=f"Predito<br>{moeda_br(valor)}",
                            showarrow=False,
                            yshift=35,
                            font=dict(color="#145DA0")
                        )

                        fig.add_annotation(
                            x=limite_superior,
                            y="Faixa de valores",
                            text=f"+30%<br>{moeda_br(limite_superior)}",
                            showarrow=False,
                            yshift=-35,
                            font=dict(color="#D9534F")
                        )

                        # Ajustes visuais
                        amplitude = (
                            limite_superior - limite_inferior
                        )

                        margem = amplitude * 0.20

                        fig.update_layout(
                            height=260,
                            margin=dict(
                                l=20,
                                r=20,
                                t=60,
                                b=30
                            ),
                            xaxis=dict(
                                title="Valor do imóvel (R$)",
                                range=[
                                    max(0, limite_inferior - margem),
                                    limite_superior + margem
                                ],
                                tickformat=",.0f",
                                separatethousands=True
                            ),
                            yaxis=dict(
                                visible=False
                            ),
                            showlegend=False,
                            plot_bgcolor="white",
                            paper_bgcolor="white"
                        )

                        st.plotly_chart(
                            fig,
                            use_container_width=True
                        )

except FileNotFoundError:
    st.error(
        f"Arquivo '{ARQUIVO}' não encontrado. "
        "Verifique se ele está no repositório."
    )

except Exception as erro:
    st.error(
        f"Erro ao carregar ou consultar os dados: {erro}"
    )
