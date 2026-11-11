import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Radar de Licitações", page_icon="📡", layout="wide")

st.title("📡 Radar de Licitações PNCP")
st.markdown("**Encontre editais públicos abertos em tempo real.**")

# Barra lateral
st.sidebar.header("🔍 Filtros de Busca")
palavra = st.sidebar.text_input("Palavra-chave (separe por vírgula)", value="notebook, computador")
uf = st.sidebar.selectbox("Estado (UF)", ["Todos", "SP", "RJ", "MG", "BA", "PR", "RS", "SC", "DF", "GO", "PE", "CE"])
dias = st.sidebar.slider("Buscar nos últimos X dias", 1, 30, 7)
buscar = st.sidebar.button("🔍 Buscar Editais", use_container_width=True)

# Função de busca
def buscar_editais(palavras, uf, dias):
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    
    # Calcula a data final (hoje) e inicial (há X dias)
    data_final = datetime.now().strftime("%Y%m%d")
    data_inicial = (datetime.now() - timedelta(days=dias)).strftime("%Y%m%d")
    
    resultados = []
    
    # Busca em todas as modalidades principais (6=Concorrência, 8=Pregão, 12=Dispensa)
    for modalidade in [6, 8, 12]:
        params = {
            "dataFinal": data_final,
            "pagina": 1,
            "codigoModalidadeContratacao": modalidade,
            "tamanhoPagina": 10
        }
        
        # Adiciona UF se não for "Todos"
        if uf != "Todos":
            params["uf"] = uf
        
        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                editais = r.json().get('data', [])
                resultados.extend(editais)
        except:
            pass
    
    # Filtra por palavra-chave
    if palavras:
        palavras_lista = [p.strip().lower() for p in palavras.split(",")]
        editais_filtrados = []
        for e in resultados:
            objeto = e.get('objetoCompra', '').lower()
            if any(palavra in objeto for palavra in palavras_lista):
                editais_filtrados.append(e)
        return editais_filtrados
    
    return resultados

# Lógica principal
if buscar:
    with st.spinner(f'Buscando editais dos últimos {dias} dias...'):
        editais = buscar_editais(palavra, uf, dias)
    
    if not editais:
        st.warning("⚠️ Nenhum edital encontrado com esses filtros. Tente outras palavras ou aumente os dias.")
    else:
        st.success(f"✅ Encontrados **{len(editais)} editais**!")
        st.markdown("---")
        
        for i, e in enumerate(editais, 1):
            with st.container():
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(f"📌 Edital #{i}")
                    orgao = e.get('orgaoEntidade', {}).get('razaoSocial', 'N/A')
                    objeto = e.get('objetoCompra', 'N/A')
                    st.write(f"**Órgão:** {orgao}")
                    st.write(f"**Objeto:** {objeto}")
                
                with col2:
                    valor = e.get('valorTotalEstimado', 0)
                    st.metric("Valor", f"R$ {valor:,.2f}")
                    data = e.get('dataAberturaProposta', 'N/A')
                    st.write(f"**Abertura:** {data[:10] if len(str(data)) > 10 else data}")
                
                link = e.get('linkSistemaOrigem', '#')
                st.markdown(f"[🔗 Ver edital completo]({link})")
                st.divider()
else:
    st.info("👈 Use os filtros na barra lateral para começar a busca.")
