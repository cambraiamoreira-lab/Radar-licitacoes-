import streamlit as st
import requests

# 1. Configuração da página (Layout largo)
st.set_page_config(page_title="Radar de Licitações", page_icon="🔎", layout="wide")

# 2. Banner de topo (Usando uma imagem genérica de negócios/tecnologia)
st.image("https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?q=80&w=1200&auto=format&fit=crop", use_container_width=True)

st.title("🔎 Radar de Licitações")
st.markdown("Encontre as melhores oportunidades de compras públicas de forma simples e rápida.")

# 3. Filtros na Barra Lateral (Sidebar)
with st.sidebar:
    st.header("Filtros de Busca")
    palavra_chave = st.text_input("O que você procura?", placeholder="Ex.: computador, papel...")
    
    estados = ["Todos", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
    uf = st.selectbox("Estado", estados)
    
    st.markdown("---") # Linha divisória
    botao_pesquisar = st.button("🔍 Pesquisar Licitações", use_container_width=True)

# 4. Lógica de Busca (Só roda quando o botão é apertado)
if botao_pesquisar:
    if not palavra_chave:
        st.warning("Por favor, digite uma palavra na barra lateral para pesquisar.")
    else:
        with st.spinner(f"Buscando oportunidades para '{palavra_chave}'..."):
            url = "https://pncp.gov.br/api/search/"
            parametros = {
                "q": palavra_chave,
                "tipos_documento": "edital",
                "ordenacao": "relevancia",
                "pagina": 1
            }
            if uf != "Todos":
                parametros["uf"] = uf
                
            try:
                resposta = requests.get(url, params=parametros, timeout=30)
                resposta.raise_for_status()
                dados = resposta.json()
                
                itens = dados.get('items', [])
                total_resultados = dados.get('total', 0)
                
                if len(itens) == 0:
                    st.warning(f"Nenhuma licitação encontrada para '{palavra_chave}'.")
                else:
                    st.success(f"Encontramos **{total_resultados}** oportunidade(s). Mostrando as mais relevantes:")
                    
                    # 5. Cards Elegantes
                    for item in itens:
                        titulo = item.get('title', 'Sem título')
                        descricao = item.get('description', 'Sem descrição detalhada.')
                        link = item.get('item_url', '#')
                        
                        # Criando o card
                        with st.container(border=True):
                            st.markdown(f"### 📦 {titulo[:100]}...") # Corta títulos muito longos
                            
                            # Usando colunas para separar o texto do botão
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                st.caption(f"📝 {descricao[:200]}...")
                            with col2:
                                if link and link != '#':
                                    st.link_button("📄 Abrir Edital", link, use_container_width=True)
                                    
            except Exception as e:
                st.error(f"Erro ao tentar buscar: {e}")
else:
    # Mensagem inicial na tela principal antes de pesquisar
    st.info("👈 Abra o menu lateral e digite o que você procura para começar.")