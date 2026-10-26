import streamlit as st
import pandas as pd
from pathlib import Path

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
            if not codigo:
                st.warning("Digite o código do imóvel.")

            else:
                resultado = dados[
                    dados[COLUNA_CODIGO].str.strip() == codigo
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

                    if len(resultado) > 1:
                        st.warning(
                            f"Foram encontrados {len(resultado)} registros "
                            "com esse código. Exibindo o primeiro."
                        )

except FileNotFoundError:
    st.error(f"Arquivo não encontrado: {ARQUIVO}")

except Exception as erro:
    st.error(f"Erro ao carregar ou consultar os dados: {erro}")
