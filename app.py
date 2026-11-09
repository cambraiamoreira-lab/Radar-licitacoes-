import streamlit as st
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo
from urllib.parse import quote
import re
import html

# =========================================================
# RADAR DE LICITAÇÕES | PNCP
# Busca contratações com recebimento de propostas aberto.
# =========================================================

st.set_page_config(
    page_title="Radar de Licitações",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed"
)

PNCP_API = "https://pncp.gov.br/api/consulta"
TZ = ZoneInfo("America/Sao_Paulo")

# ---------- Identidade visual / UX ----------
st.markdown("""
<style>
:root {
    --navy: #10243A;
    --blue: #2563EB;
    --cyan: #22B8CF;
    --ink: #172B4D;
    --muted: #66758A;
    --line: #E5EAF1;
    --surface: #FFFFFF;
    --bg: #F4F7FB;
    --green: #087E5B;
    --amber: #A65B00;
}
.stApp { background: var(--bg); color: var(--ink); }
.block-container { padding-top: 1.15rem; padding-bottom: 3rem; max-width: 1180px; }
header[data-testid="stHeader"] { background: transparent; }
.hero {
    background: linear-gradient(120deg, #10243A 0%, #173D62 68%, #087E9B 100%);
    padding: 1.5rem 1.6rem; border-radius: 20px; color: white;
    margin-bottom: 1.15rem; box-shadow: 0 12px 30px rgba(16,36,58,.12);
}
.hero-kicker { color: #A8E8F2; font-size: .76rem; letter-spacing: .12em;
    font-weight: 800; text-transform: uppercase; }
.hero h1 { color: white; font-size: clamp(1.65rem, 4vw, 2.35rem);
    margin: .35rem 0 .3rem 0; line-height: 1.12; }
.hero p { color: #DCEAF5; margin: 0; font-size: .98rem; }
.section-title { font-size: 1.08rem; font-weight: 800; color: var(--navy);
    margin: .55rem 0 .75rem 0; }
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: white; border: 1px solid var(--line); border-radius: 16px;
}
div.stButton > button, div.stLinkButton > a {
    border-radius: 10px; font-weight: 750; min-height: 2.7rem;
}
div.stButton > button[kind="primary"] {
    background: var(--blue); border: 1px solid var(--blue);
}
div[data-testid="stTextInput"] input, div[data-testid="stSelectbox"] div[role="combobox"] {
    border-radius: 10px;
}
.metric-label { color: var(--muted); font-size: .78rem; font-weight: 700; }
.metric-value { color: var(--navy); font-size: 1.35rem; font-weight: 850; }
.notice { background: #EAF4FF; border: 1px solid #CFE4FF; padding: .85rem 1rem;
    border-radius: 12px; color: #214B75; font-size: .88rem; }
.result-title { color: var(--navy); font-size: 1.03rem; font-weight: 800; line-height: 1.35; }
.result-meta { color: var(--muted); font-size: .84rem; }
.pill { display: inline-block; padding: .22rem .58rem; border-radius: 99px;
    font-size: .72rem; font-weight: 800; background: #E5F6EF; color: #087E5B; }
.deadline { color: #A65B00; font-weight: 800; }
footer { visibility: hidden; }
@media (max-width: 640px) {
    .block-container { padding: .7rem .8rem 2rem .8rem; }
    .hero { padding: 1.15rem; border-radius: 15px; }
    .hero p { font-size: .9rem; }
}
</style>
""", unsafe_allow_html=True)

# ---------- HTTP ----------
@st.cache_resource
def get_session():
    session = requests.Session()
    retry = Retry(
        total=3, connect=3, read=3, status=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "RadarDeLicitacoes/1.0 (consulta publica PNCP)"
    })
    return session

def parse_date(value):
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, TZ)
        except Exception:
            return None
    raw = str(value).strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=TZ)
        return parsed.astimezone(TZ)
    except Exception:
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"):
        try:
            return datetime.strptime(raw[:10], fmt).replace(tzinfo=TZ)
        except Exception:
            continue
    return None

def first_value(obj, *keys, default=None):
    for key in keys:
        value = obj.get(key) if isinstance(obj, dict) else None
        if value not in (None, ""):
            return value
    return default

def extract_records(payload):
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    for key in ("data", "items", "content", "resultado", "results"):
        value = payload.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = extract_records(value)
            if nested:
                return nested
    return []

def normalize_item(item):
    org = item.get("orgaoEntidade") or {}
    unidade = item.get("unidadeOrgao") or {}
    encerramento = first_value(
        item, "dataEncerramentoProposta", "dataFimRecebimentoPropostas",
        "dataFinalProposta", "dataEncerramento"
    )
    fim = parse_date(encerramento)
    agora = datetime.now(TZ)

    # O endpoint /proposta já consulta propostas abertas. Esta segunda
    # checagem evita exibir registros cujo prazo já venceu no momento da busca.
    if fim and fim <= agora:
        return None

    cnpj = str(first_value(org, "cnpj", default="")).strip()
    ano = first_value(item, "anoCompra", "ano")
    sequencial = first_value(item, "sequencialCompra", "sequencial")
    link = first_value(item, "linkSistemaOrigem", "linkProcessoEletronico")
    if not link and cnpj and ano and sequencial:
        link = f"https://pncp.gov.br/app/editais/{cnpj}/{ano}/{sequencial}"
    if not link:
        link = "https://pncp.gov.br/app/"

    objeto = first_value(item, "objetoCompra", "objeto", "title", default="Objeto não informado")
    orgao = first_value(org, "razaoSocial", "nome", default="Órgão não informado")
    municipio = first_value(unidade, "municipioNome", "nomeMunicipio", default="")
    uf = first_value(unidade, "ufSigla", "uf", default=item.get("uf", ""))
    modalidade = first_value(item, " modalidadeNome", "modalidadeNome", "nomeModalidade", default="")
    valor = first_value(item, "valorTotalEstimado", "valorEstimado", "valorTotalHomologado")
    numero = first_value(item, "numeroCompra", "numero", default="")
    controle = first_value(item, "numeroControlePNCP", default="")
    data_publicacao = first_value(item, "dataPublicacaoPncp", "dataPublicacao")
    return {
        "objeto": str(objeto),
        "orgao": str(orgao),
        "municipio": str(municipio),
        "uf": str(uf),
        "modalidade": str(modalidade),
        "valor": valor,
        "fim": fim,
        "data_publicacao": parse_date(data_publicacao),
        "numero": str(numero),
        "controle": str(controle),
        "link": str(link)
    }

def money_br(value):
    try:
        number = float(value)
        formatted = f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except (TypeError, ValueError):
        return "Não informado"

def search_pncp(keyword, uf, modality, pages):
    # A API oficial de propostas abertas exige dataFinal e pagina.
    # A janela de 12 meses permite consultar prazos futuros sem depender
    # de uma busca textual não documentada no endpoint.
    date_final = (date.today() + timedelta(days=365)).strftime("%Y%m%d")
    found = []
    total_api = None
    session = get_session()

    for page in range(1, pages + 1):
        params = {
            "dataFinal": date_final,
            "pagina": page,
            "tamanhoPagina": 50
        }
        if uf != "Todos":
            params["uf"] = uf
        if modality != "Todas":
            params["codigoModalidadeContratacao"] = int(modality)

        response = session.get(
            f"{PNCP_API}/v1/contratacoes/proposta",
            params=params,
            timeout=(15, 45)
        )
        response.raise_for_status()
        payload = response.json()
        if total_api is None and isinstance(payload, dict):
            total_api = first_value(payload, "totalRegistros", "total", "totalElements")
        records = extract_records(payload)
        if not records:
            break

        term = keyword.casefold().strip()
        for raw in records:
            normalized = normalize_item(raw)
            if not normalized:
                continue
            searchable = " ".join([
                normalized["objeto"], normalized["orgao"],
                normalized["municipio"], normalized["modalidade"],
                normalized["controle"]
            ]).casefold()
            if not term or term in searchable:
                found.append(normalized)

        if len(records) < 50:
            break

    # Remove duplicados pelo número de controle ou pelo conjunto órgão/objeto.
    unique = {}
    for item in found:
        key = item["controle"] or (item["orgao"] + item["objeto"])
        unique[key] = item
    results = list(unique.values())
    results.sort(key=lambda x: x["fim"] or datetime.max.replace(tzinfo=TZ))
    return results, total_api

# ---------- Cabeçalho ----------
st.markdown("""
<div class="hero">
  <div class="hero-kicker">Radar de oportunidades públicas</div>
  <h1>Encontre licitações. Chegue antes.</h1>
  <p>Pesquise oportunidades com recebimento de propostas aberto no PNCP.</p>
</div>
""", unsafe_allow_html=True)

# ---------- Busca ----------
st.markdown('<div class="section-title">Sua próxima oportunidade começa aqui</div>', unsafe_allow_html=True)
with st.container(border=True):
    with st.form("form_busca", clear_on_submit=False):
        keyword = st.text_input(
            "Palavra-chave",
            placeholder="Ex.: material de escritório, computadores, limpeza..."
        )
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            estados = ["Todos", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
                       "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ",
                       "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
            uf = st.selectbox("Estado", estados, index=estados.index("RS"))
        with c2:
            modalidades = [
                ("Todas", "Todas"),
                ("Pregão - Eletrônico", "6"),
                ("Concorrência - Eletrônica", "4"),
                ("Dispensa", "8"),
                ("Inexigibilidade", "9"),
                ("Leilão - Eletrônico", "7"),
                ("Concurso", "5"),
                ("Diálogo Competitivo", "12")
            ]
            modalidade_label = st.selectbox("Modalidade", [x[0] for x in modalidades])
            modalidade = dict(modalidades)[modalidade_label]
        with c3:
            pages = st.selectbox("Profundidade da busca", [1, 2, 3, 5, 10], index=2,
                                 help="Cada página consulta até 50 registros do PNCP. Mais páginas podem levar mais tempo.")
        submitted = st.form_submit_button("🔎  Buscar oportunidades", type="primary", use_container_width=True)

st.markdown(
    '<div class="notice"> <b>Como funciona:</b> a busca consulta o endpoint oficial de contratações com propostas abertas. '
    'A palavra-chave é aplicada aos registros recebidos nas páginas consultadas. Aumente a profundidade para ampliar a varredura.</div>',
    unsafe_allow_html=True
)

if submitted:
    if not keyword.strip():
        st.warning("Digite uma palavra-chave para iniciar a pesquisa.")
    else:
        try:
            with st.spinner("Consultando o PNCP e verificando os prazos..."):
                results, total_api = search_pncp(keyword, uf, modalidade, pages)
            st.session_state["radar_results"] = results
            st.session_state["radar_keyword"] = keyword.strip()
            st.session_state["radar_pages"] = pages
            st.session_state["radar_total_api"] = total_api
        except requests.exceptions.Timeout:
            st.error("O PNCP demorou para responder. Tente novamente em alguns instantes ou reduza a profundidade da busca.")
        except requests.exceptions.HTTPError as exc:
            st.error(f"O PNCP retornou um erro HTTP: {exc}. Confira os filtros e tente novamente.")
            if getattr(exc, "response", None) is not None:
                st.caption(f"Código HTTP: {exc.response.status_code}")
        except requests.exceptions.RequestException as exc:
            st.error("Não foi possível conectar ao PNCP. Verifique sua internet e tente novamente.")
            st.caption(f"Detalhe técnico: {exc}")
        except (ValueError, TypeError) as exc:
            st.error("A resposta recebida do PNCP não veio no formato esperado. Tente novamente mais tarde.")
            st.caption(f"Detalhe técnico: {exc}")

# ---------- Resultados ----------
results = st.session_state.get("radar_results")
if results is not None:
    term = st.session_state.get("radar_keyword", "")
    st.markdown('<div class="section-title">Resultados da pesquisa</div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    with m1:
        st.metric("Oportunidades encontradas", len(results))
    with m2:
        st.metric("Páginas consultadas", st.session_state.get("radar_pages", 0))
    if not results:
        st.info(f"Nenhuma oportunidade aberta com o termo “{term}” foi encontrada nas páginas consultadas. Tente outro termo, estado ou aumente a profundidade.")
    else:
        st.success(f"{len(results)} oportunidade(s) compatível(is) com “{term}”.")
        for item in results:
            fim = item["fim"]
            prazo = fim.strftime("%d/%m/%Y às %H:%M") if fim else "Prazo não informado pela API"
            local = " / ".join(x for x in [item["municipio"], item["uf"]] if x) or "Local não informado"
            titulo = html.escape(item["objeto"])
            orgao = html.escape(item["orgao"])
            modalidade_txt = html.escape(item["modalidade"] or "Modalidade não informada")
            with st.container(border=True):
                st.markdown(f'<div class="result-title">{titulo}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="result-meta">🏛️ {orgao}</div>', unsafe_allow_html=True)
                a, b = st.columns(2)
                with a:
                    st.markdown(f"**📍 Local**  \n{html.escape(local)}")
                    st.markdown(f"**📑 Modalidade**  \n{modalidade_txt}")
                with b:
                    st.markdown(f"**💰 Valor estimado**  \n{money_br(item['valor'])}")
                    st.markdown(f"**⏳ Encerramento das propostas**  \n<span class='deadline'>{html.escape(prazo)}</span>", unsafe_allow_html=True)
                st.link_button("Abrir oportunidade no PNCP ↗", item["link"], use_container_width=True)
                if item["controle"]:
                    st.caption(f"Controle PNCP: {html.escape(item['controle'])}")

    st.caption("Os dados são consultados diretamente no PNCP no momento da pesquisa. Confirme edital, anexos, condições e prazo no portal oficial antes de tomar qualquer decisão.")
else:
    st.markdown('<div class="section-title">Uma pesquisa mais objetiva</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("**01 · Pesquise pelo que você fornece**")
            st.caption("Use termos específicos: produto, serviço, equipamento ou categoria.")
    with right:
        with st.container(border=True):
            st.markdown("**02 · Refine por localização**")
            st.caption("Escolha o estado e a modalidade para reduzir o ruído.")

st.divider()
st.caption("Radar de Licitações • Fonte: Portal Nacional de Contratações Públicas (PNCP) • Ferramenta independente, sem vínculo com o Governo Federal.")
