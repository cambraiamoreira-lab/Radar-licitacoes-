import streamlit as st
import requests

st.set_page_config(page_title="Radar de Licitações", page_icon="🔎", layout="centered")
st.title("🔎 Radar de Licitações")
st.markdown("Encontre oportunidades de compras públicas de forma simples.")

palavra_chave = st.text_input("O que você deseja encontrar?", placeholder="Ex.: computador, troféu, papel...")

estados = ["Todos", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
uf = st.selectbox("Estado", estados)

if st.button("Pesquisar Licitações", use_container_width=True):
    if not palavra_chave:
        st.warning("Por favor, digite uma palavra para pesquisar.")
    else:
        with st.spinner(f"Buscando por '{palavra_chave}'..."):
            
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
                    st.warning(f"Nenhuma licitação encontrada para '{palavra_chave}' no filtro selecionado.")
                else:
                    st.success(f"Encontramos **{total_resultados}** oportunidade(s) no total. Mostrando as {len(itens)} mais relevantes:")
                    
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