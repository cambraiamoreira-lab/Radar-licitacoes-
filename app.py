
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# =====================================
# CONFIGURACAO DA PAGINA
# =====================================

st.set_page_config(
    page_title="Radar de Licitacoes",
    page_icon="🔎",
    layout="wide"
)

st.title("🔎 Radar de Licitacoes")
st.caption("Encontre oportunidades de compras publicas no Brasil")

# =====================================
# CONFIGURACAO DA API PNCP
# =====================================

API_URL = (
    "https://pncp.gov.br/api/consulta"
    "/v1/contratacoes/publicacao"
)

# =====================================
# FILTROS DE PESQUISA
# =====================================

produto = st.text_input(
    "Qual produto ou servico voce procura?",
    placeholder="Ex: cafe, material de limpeza, uniformes"
)

modalidade = st.selectbox(
    "Modalidade de contratacao",
    options={
        "Pregao Eletronico": 6,
        "Concorrencia Eletronica": 4
    }
)

periodo = st.selectbox(
    "Periodo de publicacao",
    options=[7, 15, 30],
    format_func=lambda x: f"Ultimos {x} dias"
)

quantidade = st.selectbox(
    "Quantidade de resultados",
    options=[10, 20, 50]
)

# =====================================
# FUNCAO DE CONSULTA
# =====================================

def buscar_licitacoes(produto, modalidade, periodo, quantidade):

    hoje = datetime.now().date()
    inicio = hoje - timedelta(days=periodo)

    parametros = {
        "dataInicial": inicio.strftime("%Y%m%d"),
        "dataFinal": hoje.strftime("%Y%m%d"),
        "codigoModalidadeContratacao": modalidade,
        "pagina": 1,
        "tamanhoPagina": quantidade
    }

    resposta = requests.get(
        API_URL,
        params=parametros,
        timeout=30
    )

    resposta.raise_for_status()

    dados = resposta.json()

    registros = dados.get("data", [])

    # Filtrar pela palavra pesquisada

    if produto.strip():

        palavra = produto.strip().lower()

        registros = [
            item for item in registros
            if palavra in str(
                item.get("objetoCompra", "")
            ).lower()
        ]

    return registros


# =====================================
# BOTAO DE PESQUISA
# =====================================

if st.button("🔍 Pesquisar licitacoes", type="primary"):

    if not produto.strip():

        st.warning(
            "Digite um produto ou servico para pesquisar."
        )

    else:

        try:

            with st.spinner(
                "Consultando o PNCP..."
            ):

                resultados = buscar_licitacoes(
                    produto,
                    modalidade,
                    periodo,
                    quantidade
                )

            if resultados:

                st.success(
                    f"{len(resultados)} oportunidade(s) encontrada(s)"
                )

                tabela = []

                for item in resultados:

                    orgao = item.get(
                        "orgaoEntidade", {}
                    )

                    tabela.append({

                        "Orgao": orgao.get(
                            "razaoSocial", "Nao informado"
                        ),

                        "Objeto": item.get(
                            "objetoCompra", "Nao informado"
                        ),

                        "Valor estimado": item.get(
                            "valorTotalEstimado", 0
                        ),

                        "UF": item.get(
                            "unidadeOrgao", {}
                        ).get(
                            "ufSigla", "Nao informado"
                        ),

                        "Data de publicacao": item.get(
                            "dataPublicacaoPncp",
                            "Nao informado"
                        ),

                        "Numero PNCP": item.get(
                            "numeroControlePNCP",
                            "Nao informado"
                        )

                    })

                df = pd.DataFrame(tabela)

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                st.download_button(
                    "📥 Baixar resultados CSV",
                    data=df.to_csv(
                        index=False
                    ).encode("utf-8-sig"),
                    file_name="licitacoes.csv",
                    mime="text/csv"
                )

            else:

                st.info(
                    "Nenhuma licitacao encontrada "
                    "com esses filtros."
                )

        except requests.exceptions.Timeout:

            st.error(
                "A consulta demorou demais. "
                "Tente novamente."
            )

        except requests.exceptions.HTTPError as erro:

            st.error(
                f"Erro HTTP na API: {erro}"
            )

        except requests.exceptions.RequestException as erro:

            st.error(
                f"Erro de conexao: {erro}"
            )

        except Exception as erro:

            st.error(
                f"Erro inesperado: {erro}"
            )

# =====================================
# RODAPE
# =====================================

st.divider()

st.caption(
    "Fonte de consulta: Portal Nacional "
    "de Contratacoes Publicas (PNCP)."
)

st.caption(
    "Confira o edital e as condicoes "
    "da contratacao na fonte oficial."
)
