import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Radar de Licitações 2026",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Radar de Licitações")
st.markdown("Busque oportunidades a partir de **2026** no Portal Nacional de Contratações Públicas (PNCP).")

# Lista de estados
estados = ["Todos", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
           "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", 
           "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

# Criando as colunas para o design ficar bonito
col1, col2 = st.columns([2, 1])

with col1:
    termo_busca = st.text_input("O que você deseja encontrar?", placeholder="Ex.: computador, cadeira, medalha...")

with col2:
    estado_selecionado = st.selectbox("Estado", estados)

# Função que faz a mágica acontecer
def buscar_licitacoes(termo, uf):
    url_base = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
    
    # Filtro de data exigido: 2026 para frente
    data_inicial = "20260101"
    data_final = "20271231"
    
    todas_licitacoes = []
    
    # Vamos buscar 5 páginas (50 em cada) para ter mais resultados (250 no total)
    for pagina in range(1, 6):
        params = {
            "dataInicial": data_inicial,
            "dataFinal": data_final,
            "pagina": pagina,
            "tamanhoPagina": 50
        }
        
        if uf != "Todos":
            params["uf"] = uf
            
        try:
            response = requests.get(url_base, params=params, timeout=15)
            if response.status_code == 200:
                dados = response.json()
                itens = dados.get('data', [])
                if not itens:
                    break # Se a página vier vazia, para de buscar
                todas_licitacoes.extend(itens)
                time.sleep(0.5) # Pausa de meio segundo para não bloquear nossa conexão
            else:
                st.error(f"Erro na API do PNCP: Status {response.status_code}")
                break
        except Exception as e:
            st.error(f"Erro de conexão: {e}")
            break

    st.info(f"🔎 O PNCP retornou **{len(todas_licitacoes)}** licitações brutas para os filtros de data (2026+) e estado.")
    
    # Se o usuário não digitou nada, retorna tudo
    if not termo.strip():
        return todas_licitacoes
        
    # Filtro inteligente (ignora maiúsculas, minúsculas e espaços)
    termo_limpo = termo.strip().lower()
    filtradas = []
    
    for licitacao in todas_licitacoes:
        # Pega os campos e garante que são texto (str) para não dar erro
        objeto = str(licitacao.get('objetoCompra', '')).lower()
        info_comp = str(licitacao.get('informacaoComplementar', '')).lower()
        orgao = str(licitacao.get('orgaoEntidade', {}).get('razaoSocial', '')).lower()
        
        # Verifica se o termo está em qualquer um dos campos
        if termo_limpo in objeto or termo_limpo in info_comp or termo_limpo in orgao:
            filtradas.append(licitacao)
            
    st.info(f"🎯 Após filtrar por **'{termo.strip()}'**, sobraram **{len(filtradas)}** resultados.")
    return filtradas

# Quando o botão for clicado
if st.button("Pesquisar Licitações", type="primary", use_container_width=True):
    with st.spinner("Buscando no PNCP..."):
        resultados = buscar_licitacoes(termo_busca, estado_selecionado)
        
    if resultados:
        st.success(f"Encontramos {len(resultados)} licitações!")
        
        # Mostrando os resultados em "cartões" bonitos
        for lic in resultados:
            # Tentando pegar o título, se não tiver, coloca um padrão
            titulo = lic.get('objetoCompra', 'Sem Título')
            if len(titulo) > 100:
                titulo = titulo[:100] + "..."
                
            with st.expander(f"📄 {titulo}"):
                st.write(f"**Órgão:** {lic.get('orgaoEntidade', {}).get('razaoSocial', 'Não informado')}")
                st.write(f"**UF:** {lic.get('unidadeOrgao', {}).get('ufSigla', 'Não informado')}")
                st.write(f"**Valor Estimado:** R$ {lic.get('valorTotalEstimado', 'Não informado')}")
                st.write(f"**Data de Abertura:** {lic.get('dataAberturaProposta', 'Não informada')[:10]}")
                
                link = lic.get('linkSistemaOrigem')
                if link:
                    st.markdown(f"[🔗 Acessar Edital]({link})")
                else:
                    st.write("Link do edital não disponível.")
    else:
        st.warning("Nenhuma licitação encontrada com esse termo em 2026/2027. Tente buscar apenas uma palavra (ex: 'papel', 'medalha').")