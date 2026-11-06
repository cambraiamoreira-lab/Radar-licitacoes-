import streamlit as st
import requests
from datetime import date, timedelta

st.set_page_config(page_title="Radar de Licitações", page_icon="🔎", layout="centered")
st.title("🔎 Radar de Licitações")

palavra_chave = st.text_input("O que você deseja encontrar?", placeholder="Ex.: computador, merenda, pneu...")
estados = ["Todos", "RS", "SP", "RJ", "MG", "PR", "SC", "BA"]
uf = st.selectbox("Estado", estados)

if st.button("Pesquisar Licitações", use_container_width=True):
    with st.spinner("Buscando oportunidades no PNCP..."):
        
        # O código agora descobre a data real do servidor sozinho
        hoje = date.today()
        futuro = hoje + timedelta(days=365) # Busca oportunidades para os próximos 365 dias
        
        data_inicial = hoje.strftime("%Y%m%d")
        data_final = futuro.strftime("%Y%m%d")
        
        url = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
        headers = {"User-Agent": "RadarLicitacoes/1.0"}
        
        resultados_brutos = []
        
        try:
            # Buscando 3 páginas (150 licitações)
            for pagina in range(1, 4):
                parametros = {
                    "dataInicial": data_inicial, # A API exige data inicial e final
                    "dataFinal": data_final,
                    "pagina": pagina,
                    "tamanhoPagina": 50
                }
                if uf != "Todos":
                    parametros["uf"] = uf
                    
                resposta = requests.get(url, headers=headers, params=parametros, timeout=30)
                resposta.raise_for_status()
                dados = resposta.json()
                
                if 'data' in dados and len(dados['data']) > 0:
                    resultados_brutos.extend(dados['data'])
                else:
                    break
            
            total_bruto = len(resultados_brutos)
            st.info(f"🔍 O PNCP retornou **{total_bruto}** licitações brutas (prazos até {futuro.strftime('%d/%m/%Y')}).")
            
            if total_bruto > 0:
                if palavra_chave:
                    resultados_filtrados = [lic for lic in resultados_brutos if palavra_chave.lower() in str(lic.get('objetoCompra', '')).lower()]
                    st.info(f"🔍 Após filtrar por '{palavra_chave}', sobraram **{len(resultados_filtrados)}**.")
                else:
                    resultados_filtrados = resultados_brutos
                
                if len(resultados_filtrados) == 0:
                    st.warning(f"Nenhuma licitação com a palavra '{palavra_chave}' nas {total_bruto} baixadas.")
                    
                    # Mostrando os exemplos para você ver a linguagem que o governo usa
                    st.markdown("### 👀 Veja o que o Governo enviou (Exemplos reais):")
                    for i, lic in enumerate(resultados_brutos[:10]):
                        obj = lic.get('objetoCompra', 'Vazio')
                        st.write(f"**{i+1}.** {obj[:150]}...")
                        
                else:
                    st.success(f"Encontramos {len(resultados_filtrados)} oportunidade(s)!")
                    for lic in resultados_filtrados:
                        objeto = lic.get('objetoCompra', 'Objeto não informado')
                        orgao = lic.get('orgaoEntidade', {}).get('razaoSocial', 'Órgão não informado')
                        with st.container(border=True):
                            st.subheader(objeto)
                            st.write(f"🏢 **Órgão:** {orgao}")
            else:
                st.warning("A API não retornou nenhuma licitação.")
                
        except requests.exceptions.HTTPError as erro:
            st.error(f"Erro no PNCP: {erro.response.status_code}. Detalhes: {erro.response.text}")
        except Exception as e:
            st.error(f"Erro: {e}")