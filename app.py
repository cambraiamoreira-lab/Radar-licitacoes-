import streamlit as st
import requests
from datetime import datetime

st.set_page_config(page_title="Radar de Licitações", page_icon="📡")

st.title("📡 Radar de Licitações PNCP")
st.markdown("Editais abertos em tempo real.")

st.sidebar.header("Filtros")
palavra = st.sidebar.text_input("Palavra-chave", value="notebook")
uf = st.sidebar.text_input("UF", value="SP")
buscar = st.sidebar.button("🔍 Buscar")

if buscar:
    with st.spinner('Buscando...'):
        url = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
        data_final = datetime.now().strftime("%Y%m%d")
        params = {
            "dataFinal": data_final,
            "pagina": 1,
            "codigoModalidadeContratacao": 8,
            "uf": uf.upper(),
            "tamanhoPagina": 5
        }
        r = requests.get(url, params=params, timeout=15)
        editais = r.json().get('data', []) if r.status_code == 200 else []
    
    if not editais:
        st.warning("Nenhum edital encontrado.")
    else:
        st.success(f"{len(editais)} editais encontrados!")
        for i, e in enumerate(editais, 1):
            st.subheader(f"📌 Edital #{i}")
            st.write(f"**Órgão:** {e.get('orgaoEntidade', {}).get('razaoSocial', 'N/A')}")
            st.write(f"**Objeto:** {e.get('objetoCompra', 'N/A')}")
            st.write(f"**Valor:** R$ {e.get('valorTotalEstimado', 0):,.2f}")
            st.markdown(f"[🔗 Ver edital]({e.get('linkSistemaOrigem', '#')})")
            st.divider()
