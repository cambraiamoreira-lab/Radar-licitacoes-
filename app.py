import streamlit as st
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

st.set_page_config(
    page_title="Radar de Licitações 2026",
    page_icon="🔍",
    layout="wide"
)

# CSS para forçar o botão a ser azul, independentemente do tema
st.markdown("""
    <style>
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #1f77b4 !important;
        color: white !important;
        border: none !important;
    }
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #166a99 !important;
        color: white !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🔍 Radar de Licitações")
st.markdown("Busque oportunidades a partir de **2026** no Portal Nacional de Contratações Públicas (PNCP).")

estados = ["Todos", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", 
           "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", 
           "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

col1, col2 = st.columns([2, 1])

with col1:
    termo_busca = st.text_input("O que você deseja encontrar?", placeholder="Ex.: computador, cadeira, medalha...")

with col2:
    estado_selecionado = st.selectbox("Estado", estados)

def buscar_licitacoes(termo, uf):
    url_base = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
    
    data_inicial = "20260101"
    data_final = "20271231"
    
    todas_licitacoes = []
    
    # Configuração de retentativas para evitar timeout
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session.mount('https://', HTTPAdapter(max_retries=retries))

    # Aumentamos o timeout para 60 segundos
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
            response = session.get(url_base, params=params, timeout=60)
            if response.status_code == 200:
                dados = response.json()
                itens = dados.get('data', [])
                if not itens:
                    break
                todas_licitacoes.extend(itens)
                time.sleep(1) # Pausa maior entre requisições
            else:
                st.error(f"Erro na API do PNCP: Status {response.status_code}")
                break
        except requests.exceptions.Timeout:
            st.error("O servidor do PNCP demorou muito para responder. Tente novamente em alguns instantes.")
            break
        except Exception as e:
            st.error(f"Erro de conexão: {e}")
            break

    st.info(f"🔎 O PNCP retornou **{len(todas_licitacoes)}** licitações brutas para os filtros de data (2026+) e estado.")
    
    if not termo.strip():
        return todas_licitacoes
        
    termo_limpo = termo.strip().lower()
    filtradas = []
    
    for licitacao in todas_licitacoes:
        objeto = str(licitacao.get('objetoCompra', '')).lower()
        info_comp = str(licitacao.get('informacaoComplementar', '')).lower()
        orgao = str(licitacao.get('orgaoEntidade', {}).get('razaoSocial', '')).lower()
        
        if termo_limpo in objeto or termo_limpo in info_comp or termo_limpo in orgao:
            filtradas.append(licitacao)
            
    st.info(f"🎯 Após filtrar por **'{termo.strip()}'**, sobraram **{len(filtradas)}** resultados.")
    return filtradas

if st.button("Pesquisar Licitações", type="primary", use_container_width=True):
    with st.spinner("Buscando no PNCP (isso pode levar até 1 minuto)..."):
        resultados = buscar_licitacoes(termo_busca, estado_selecionado)
        
    if resultados:
        st.success(f"Encontramos {len(resultados)} licitações!")
        
        for lic in resultados:
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
        st.warning("Nenhuma licitação encontrada. Verifique se há resultados para o período de 2026/2027 ou tente buscar por termos mais genéricos (ex: 'papel').")