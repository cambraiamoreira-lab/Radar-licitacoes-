import streamlit as st
import requests
from datetime import datetime

# ============================================
# 🎨 DESIGN MODERNO - CSS CUSTOMIZADO
# ============================================
st.markdown("""
<style>
    /* Fundo principal com gradiente */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
    }
    
    /* Container principal */
    .main .block-container {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 20px;
        padding: 2rem;
        margin: 1rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
    }
    
    /* Título principal */
    h1 {
        color: #2d3748;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* Subtítulo */
    .subtitle {
        text-align: center;
        color: #718096;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    
    /* Sidebar moderna */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a202c 0%, #2d3748 100%);
        color: white;
    }
    
    .css-1d391kg h2 {
        color: #63b3ed !important;
    }
    
    /* Botão de busca com gradiente */
    .stButton>button {
        background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.8rem 2rem;
        font-weight: 700;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(72, 187, 120, 0.4);
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(72, 187, 120, 0.6);
    }
    
    /* Cards de edital */
    .editais-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #4299e1;
        transition: transform 0.2s;
    }
    
    .editais-container:hover {
        transform: translateX(5px);
        box-shadow: 0 6px 25px rgba(0,0,0,0.15);
    }
    
    /* Métricas de valor */
    .valor-box {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        padding: 1rem;
        border-radius: 12px;
        text-align: center;
        font-weight: 700;
        font-size: 1.2rem;
        box-shadow: 0 4px 10px rgba(72, 187, 120, 0.3);
    }
    
    /* Links */
    a {
        color: #4299e1;
        text-decoration: none;
        font-weight: 600;
    }
    
    a:hover {
        color: #2b6cb0;
        text-decoration: underline;
    }
    
    /* Alertas coloridos */
    .stAlert {
        border-radius: 12px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# 📱 LAYOUT PRINCIPAL
# ============================================
st.markdown('<h1>📡 Radar de Licitações PNCP</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Encontre editais públicos abertos em tempo real</p>', unsafe_allow_html=True)

# ============================================
# 🔍 BARRA LATERAL - FILTROS
# ============================================
st.sidebar.markdown("## 🔍 Filtros de Busca")
st.sidebar.markdown("---")

palavra = st.sidebar.text_input(
    "💬 Palavra-chave", 
    value="notebook, computador",
    help="Separe múltiplas palavras por vírgula"
)

uf = st.sidebar.selectbox(
    "📍 Estado (UF)", 
    ["Todos", "SP", "RJ", "MG", "BA", "PR", "RS", "SC", "DF", "GO", "PE", "CE", "AM", "PA", "MT", "MS"]
)

modalidade = st.sidebar.selectbox(
    "📋 Modalidade",
    ["Todas", "Pregão Eletrônico", "Concorrência", "Dispensa"]
)

st.sidebar.markdown("---")
buscar = st.sidebar.button("🔍 Buscar Editais")

# ============================================
# ⚙️ FUNÇÃO DE BUSCA
# ============================================
def buscar_editais(palavras, uf, modalidade):
    url = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    data_final = datetime.now().strftime("%Y%m%d")
    
    # Mapeamento de modalidades
    cod_modalidade = {
        "Todas": [6, 8, 12],
        "Pregão Eletrônico": [8],
        "Concorrência": [6],
        "Dispensa": [12]
    }
    
    resultados = []
    
    for cod in cod_modalidade.get(modalidade, [8]):
        params = {
            "dataFinal": data_final,
            "pagina": 1,
            "codigoModalidadeContratacao": cod,
            "tamanhoPagina": 15
        }
        
        if uf != "Todos":
            params["uf"] = uf
        
        try:
            r = requests.get(url, params=params, headers=headers, timeout=15)
            if r.status_code == 200:
                editais = r.json().get('data', [])
                resultados.extend(editais)
        except Exception as e:
            st.sidebar.error(f"Erro na API: {e}")
    
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

# ============================================
# 🚀 LÓGICA PRINCIPAL
# ============================================
if buscar:
    with st.spinner('🔎 Buscando editais abertos...'):
        editais = buscar_editais(palavra, uf, modalidade)
    
    if not editais:
        st.warning("⚠️ Nenhum edital encontrado com esses filtros. Tente outras palavras ou amplie a busca.")
    else:
        st.success(f"✅ **{len(editais)} editais** encontrados!")
        st.markdown("---")
        
        for i, e in enumerate(editais, 1):
            orgao = e.get('orgaoEntidade', {}).get('razaoSocial', 'N/A')
            objeto = e.get('objetoCompra', 'N/A')
            valor = e.get('valorTotalEstimado', 0)
            data = e.get('dataAberturaProposta', 'N/A')
            link = e.get('linkSistemaOrigem', '#')
            
            # Formata data
            if data and len(str(data)) > 10:
                data = str(data)[:10]
            
            # Card do edital
            st.markdown(f"""
            <div class="editais-container">
                <h3>📌 Edital #{i}</h3>
                <p><strong>🏛️ Órgão:</strong> {orgao}</p>
                <p><strong>📝 Objeto:</strong> {objeto}</p>
                <p><strong>📅 Abertura:</strong> {data}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Box de valor e link
            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"""
                <div class="valor-box">
                    💰 R$ {valor:,.2f}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"[🔗 Ver edital completo no PNCP]({link})")
            
            st.markdown("---")
else:
    st.info("👈 Use os filtros na barra lateral para começar a busca.")

# ============================================
# 📊 RODAPÉ
# ============================================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #718096; padding: 1rem;">
    <p>💡 <strong>Dica:</strong> Use palavras-chave específicas do seu nicho para encontrar editais relevantes.</p>
    <p>Desenvolvido com ❤️ usando Python + Streamlit + API PNCP</p>
</div>
""", unsafe_allow_html=True)
