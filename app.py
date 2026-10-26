import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(
    page_title="Consulta de Imóveis",
    page_icon="🏠",
    layout="centered"
)

# -------- CONFIGURAÇÃO --------

ARQUIVO = "prototipo.xlsx"

COLUNA_CODIGO = "BCICADASTRO"
COLUNA_PISO = "ocupacao"
COLUNA_FORRO = "utilizacao"
COLUNA_ESTADO = "zoneamento"

# -------- LEITURA DOS DADOS --------

@st.cache_data
def carregar_dados(arquivo):
    caminho = Path(arquivo)

    if caminho.suffix.lower() == ".csv":
        return pd.read_csv(
            caminho,
            dtype={COLUNA_CODIGO: str},
            sep=None,
            engine="python"
        )

    elif caminho.suffix.lower() in [".xlsx", ".xls"]:
        return pd.read_excel(
            caminho,
            dtype={COLUNA_CODIGO: str}
        )

    else:
        raise ValueError("Formato de arquivo não suportado.")

st.title("Consulta de Cadastro Imobiliário")
st.write("Digite o código do imóvel para consultar suas características.")

try:
    dados = carregar_dados(ARQUIVO)

    # Remove espaços extras dos nomes das colunas
    dados.columns = dados.columns.str.strip()

    colunas_necessarias = [
        COLUNA_CODIGO,
        COLUNA_PISO,
        COLUNA_FORRO,
        COLUNA_ESTADO
    ]

    faltantes = [
        coluna for coluna in colunas_necessarias
        if coluna not in dados.columns
    ]

    if faltantes:
        st.error(
            f"Colunas não encontradas: {', '.join(faltantes)}"
        )
        st.write("Colunas disponíveis:", dados.columns.tolist())

    else:
        with st.form("consulta"):
            codigo = st.text_input(
                "Código do imóvel (bcicodigo)",
                placeholder="Ex.: 1000"
            ).strip()

            consultar = st.form_submit_button("Consultar")

        if consultar:
            if not codigo.strip():
                st.warning("Digite o código do imóvel.")
            else:
                codigo = int(codigo.strip())
        
                resultado = dados[
                    dados[COLUNA_CODIGO] == codigo
                ]
        
                if resultado.empty:
                    st.error("Nenhum imóvel encontrado com esse código.")
                else:
                    imovel = resultado.iloc[0]
                    st.success("Imóvel encontrado!")

                    c1, c2, c3 = st.columns(3)

                    c1.metric("Piso", "—" if pd.isna(imovel[COLUNA_PISO]) else str(imovel[COLUNA_PISO]))
                    c2.metric("Forro", "—" if pd.isna(imovel[COLUNA_FORRO]) else str(imovel[COLUNA_FORRO]))
                    c3.metric("Conservação", "—" if pd.isna(imovel[COLUNA_ESTADO]) else str(imovel[COLUNA_ESTADO]))

                    # Gráfico do valor predito com intervalo de ±30%

                    valor = float(imovel["valor predito"])
                    
                    limite_inferior = valor * 0.70
                    limite_superior = valor * 1.30
                    
                    st.subheader("Valor predito do imóvel")
                    
                    fig = go.Figure()
                    
                    # Barra horizontal representando o intervalo
                    fig.add_trace(go.Bar(
                        x=[limite_superior - limite_inferior],
                        base=[limite_inferior],
                        y=["Valor do imóvel"],
                        orientation="h",
                        marker=dict(color="#BFD7ED"),
                        hovertemplate="Intervalo: R$ %{x:,.2f}<extra></extra>",
                        showlegend=False
                    ))
                    
                    # Marca o valor predito no centro do intervalo
                    fig.add_vline(
                        x=valor,
                        line_color="#145DA0",
                        line_width=4,
                        annotation_text=f"Predito: R$ {valor:,.2f}",
                        annotation_position="top"
                    )
                    
                    # Marca os limites inferior e superior
                    fig.add_vline(
                        x=limite_inferior,
                        line_color="#D9534F",
                        line_dash="dash",
                        annotation_text=f"-30%: R$ {limite_inferior:,.2f}",
                        annotation_position="bottom"
                    )
                    
                    fig.add_vline(
                        x=limite_superior,
                        line_color="#D9534F",
                        line_dash="dash",
                        annotation_text=f"+30%: R$ {limite_superior:,.2f}",
                        annotation_position="bottom"
                    )
                    
                    fig.update_layout(
                        xaxis_title="Valor (R$)",
                        yaxis=dict(visible=False),
                        xaxis=dict(
                            range=[limite_inferior * 0.85, limite_superior * 1.15],
                            tickprefix="R$ ",
                            tickformat=",.2f"
                        ),
                        height=220,
                        margin=dict(l=20, r=20, t=90, b=50)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

                    if len(resultado) > 1:
                        st.warning(
                            f"Foram encontrados {len(resultado)} registros "
                            "com esse código. Exibindo o primeiro."
                        )

except FileNotFoundError:
    st.error(f"Arquivo não encontrado: {ARQUIVO}")

except Exception as erro:
    st.error(f"Erro ao carregar ou consultar os dados: {erro}")
