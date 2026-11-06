import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- CONFIGURAÇÃO DO MECANISMO DE RETENTATIVA ---
def get_session():
    """Cria uma sessão HTTP que tenta reconectar automaticamente em caso de falha."""
    session = requests.Session()
    # Define a política: até 3 tentativas, com pausa crescente entre elas
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Radar de Licitações", page_icon="🔎", layout="wide")
st.image("https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?q=80&w=1200&auto=format&fit=crop", use_container_width=True)
st.title("🔎 Radar de Licitações")
st.markdown("Encontre as melhores oportunidades de compras públicas de forma simples e rápida.")

# --- FILTROS NA BARRA LATERAL ---
with st.sidebar:
    st.header("Filtros de Busca")
    palavra_chave = st.text_input("O que você procura?", placeholder="Ex.: computador, papel...")
    
    estados = ["Todos", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
    uf = st.selectbox("Estado", estados)
    
    st.markdown("---")
    botao_pesquisar = st.button("🔍 Pesquisar Licitações", use_container_width=True)

# --- LÓGICA DE BUSCA ---
if botao_pesquisar:
    if not palavra_chave:
        st.warning("Por favor, digite uma palavra na barra lateral para pesquisar.")
    else:
        with st.spinner(f"Buscando oportunidades para '{palavra_chave}'..."):
            url = "https://pncp.gov.br/api/search/"
            # Headers "disfarçados" para evitar bloqueios do servidor
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Connection": "close" # Evita problemas de conexão "keep-alive"
            }
            
            parametros = {
                "q": palavra_chave,
                "tipos_documento": "edital",
                "ordenacao": "relevancia",
                "pagina": 1
            }
            if uf != "Todos":
                parametros["uf"] = uf
                
            try:
                # Usa a sessão com retentativa
                session = get_session()
                resposta = session.get(url, headers=headers, params=parametros, timeout=45)
                resposta.raise_for_status()
                dados = resposta.json()
                
                itens = dados.get('items', [])
                total_resultados = dados.get('total', 0)
                
                if len(itens) == 0:
                    st.warning(f"Nenhuma licitação encontrada para '{palavra_chave}'.")
                else:
                    st.success(f"Encontramos **{total_resultados}** oportunidade(s). Mostrando as mais relevantes:")
                    for item in itens:
                        titulo = item.get('title', 'Sem título')
                        descricao = item.get('description', 'Sem descrição detalhada.')
                        link = item.get('item_url', '#')
                        
                        with st.container(border=True):
                            st.markdown(f"### 📦 {titulo[:100]}...")
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.caption(f"📝 {descricao[:200]}...")
                            with col2:
                                if link and link != '#':
                                    st.link_button("📄 Abrir Edital", link, use_container_width=True)
                                    
            except requests.exceptions.ConnectionError as e:
                st.error("O servidor do Governo demorou muito para responder ou recusou a conexão. Tente novamente em alguns minutos.")
                st.caption(f"Detalhe técnico: {e}")
            except Exception as e:
                st.error(f"Erro inesperado: {e}")
else:
    st.info("👈 Abra o menu lateral e digite o que você procura para começar.")