import streamlit as st
import requests

st.set_page_config(page_title="Radar de Licitações", page_icon="🔎", layout="centered")
st.title("🔎 Radar de Licitações")
st.markdown("Encontre oportunidades de compras públicas de forma simples.")

palavra_chave = st.text_input("O que você deseja encontrar?", placeholder="Ex.: computador, merenda, uniforme...")

if st.button("Pesquisar Licitações", use_container_width=True):
    if not palavra_chave:
        st.warning("Por favor, digite uma palavra para pesquisar.")
    else:
        with st.spinner(f"Buscando por '{palavra_chave}' nos cofres do Governo..."):
            
            # Essa é a API de BUSCA do governo. Ela funciona como o Google.
            url = "https://pncp.gov.br/api/search/"
            
            parametros = {
                "q": palavra_chave,               # A palavra que o usuário digitou
                "tipos_documento": "edital",      # Queremos apenas editais
                "ordenacao": "relevancia",        # Trazer os mais relevantes primeiro
                "pagina": 1
            }
            
            try:
                resposta = requests.get(url, params=parametros, timeout=30)
                resposta.raise_for_status()
                dados = resposta.json()
                
                itens = dados.get('items', [])
                
                if len(itens) == 0:
                    st.warning(f"Nenhuma licitação encontrada com a palavra '{palavra_chave}'. Tente outro termo.")
                else:
                    st.success(f"Encontramos oportunidades para '{palavra_chave}'!")
                    
                    for item in itens:
                        titulo = item.get('title', 'Sem título')
                        descricao = item.get('description', 'Sem descrição')
                        link = item.get('item_url', '#')
                        
                        with st.container(border=True):
                            st.subheader(titulo)
                            st.write(descricao)
                            
                            if link and link != '#':
                                st.markdown(f"[🔗 Abrir edital oficial]({link})")
                        
            except Exception as e:
                st.error(f"Erro ao tentar buscar: {e}")