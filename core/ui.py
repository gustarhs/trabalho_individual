"""
Componentes visuais compartilhados (padronizam o layout de todas as seções).
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import estatistica as est
from core.carregamento import Esquema, higienizar_upload, para_excel_bytes

RAIZ = Path(__file__).resolve().parents[1]
IMG = RAIZ / "assets" / "img"

# Paleta categórica (ordem fixa, validada para daltonismo nos pares adjacentes)
CORES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
AZUL, LARANJA, VERDE_AGUA, AMARELO, MAGENTA, VERDE, VIOLETA, VERMELHO = CORES
CINZA = "#8a8984"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
SEQ_AZUL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
COR_SEXO = {"Homens": AZUL, "Mulheres": LARANJA}
COR_REGIAO = {"Norte": AZUL, "Nordeste": LARANJA, "Sudeste": VERDE_AGUA, "Sul": VIOLETA, "Centro-Oeste": MAGENTA}


# ---------------------------------------------------------------------------
# Formatação
# ---------------------------------------------------------------------------
def fmt(v, casas: int = 1, sufixo: str = "") -> str:
    """Formata número no padrão brasileiro: 1234.5 -> '1.234,5'."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "—"
    s = f"{v:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return s + sufixo


def fmt_mi(v, casas: int = 1) -> str:
    return fmt(v / 1e6, casas, " mi")


def aplicar_estilo():
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1250px;}
        [data-testid="stMetric"] {background: #ffffff; border: 1px solid #e6e4df; border-radius: 10px;
            padding: 12px 14px;}
        [data-testid="stMetricLabel"] p {font-size: 0.82rem; color: #52514e;}
        [data-testid="stMetricValue"] {font-size: 1.55rem;}
        .nqf-tag {display:inline-block; padding:2px 10px; border-radius:999px; background:#e8f0fb;
            color:#184f95; font-size:0.78rem; font-weight:600; margin-right:6px;}
        .nqf-persona {border-left: 4px solid #2a78d6; background:#f5f8fd; padding: 12px 16px;
            border-radius: 6px; margin: 6px 0 14px 0;}
        .nqf-resposta {border-left: 4px solid #1baf7a; background:#f3faf7; padding: 12px 16px;
            border-radius: 6px; margin: 4px 0 12px 0;}
        .nqf-fonte {font-size: 0.78rem; color:#6b6a65;}
        .nqf-noticia-titulo {font-weight:600; font-size:0.98rem; line-height:1.3;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def cabecalho_secao(titulo: str, subtitulo: str, autor: str, tags: list[str] | None = None):
    tags_html = "".join(f'<span class="nqf-tag">{t}</span>' for t in (tags or []))
    st.markdown(f"{tags_html}", unsafe_allow_html=True)
    st.title(titulo)
    st.caption(f"{subtitulo} · Responsável: **{autor}**")


def caixa_persona(titulo: str, texto: str):
    st.markdown(f'<div class="nqf-persona"><b>{titulo}</b><br>{texto}</div>', unsafe_allow_html=True)


def resposta(pergunta: str, texto: str):
    st.markdown(f"**{pergunta}**")
    st.markdown(f'<div class="nqf-resposta">{texto}</div>', unsafe_allow_html=True)


def fonte(texto: str):
    st.markdown(f'<div class="nqf-fonte">Fonte: {texto}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Gráficos
# ---------------------------------------------------------------------------
def estilizar(fig: go.Figure, titulo: str | None = None, x: str | None = None, y: str | None = None,
              altura: int = 420, legenda: bool = True) -> go.Figure:
    """Aplica o padrão visual do projeto (eixos rotulados, grade discreta)."""
    fig.update_layout(
        template="plotly_white",
        title=dict(text=titulo, font=dict(size=16, color=TINTA)) if titulo else None,
        height=altura,
        margin=dict(l=10, r=10, t=56 if titulo else 20, b=10),
        font=dict(family="Inter, Segoe UI, Arial, sans-serif", size=13, color=TINTA_2),
        hoverlabel=dict(bgcolor="white", font_size=13),
        showlegend=legenda,
        legend=dict(orientation="h", yanchor="top", y=-0.26 if x else -0.08, xanchor="left", x=0, title=None),
        bargap=0.25,
    )
    fig.update_xaxes(title_text=x, showgrid=False, linecolor="#d6d4ce", ticks="outside", tickcolor="#d6d4ce")
    fig.update_yaxes(title_text=y, gridcolor="#eeede9", zeroline=False, linecolor="#d6d4ce")
    fig.update_traces(cliponaxis=False, selector=dict(type="bar"))  # rótulos de valor não são cortados
    return fig


def boxplot(df: pd.DataFrame, valor: str, rotulo: str, titulo: str, eixo: str,
            grupo: str | None = None, cores: dict | None = None, casas: int = 1) -> go.Figure:
    """Boxplot com todos os pontos visíveis e outliers (1,5×IQR) rotulados."""
    fig = go.Figure()
    grupos = [None] if grupo is None else list(dict.fromkeys(df[grupo]))
    for i, g in enumerate(grupos):
        d = df if g is None else df[df[grupo] == g]
        cor = (cores or {}).get(g, CORES[i % len(CORES)]) if g is not None else AZUL
        fig.add_trace(go.Box(
            y=d[valor], x=[str(g)] * len(d) if g is not None else None, name=str(g) if g is not None else eixo,
            boxpoints="all", jitter=0.35, pointpos=0, marker=dict(size=8, color=cor, opacity=0.75,
                                                                   line=dict(width=1, color="white")),
            line=dict(color=cor, width=2), fillcolor="rgba(0,0,0,0.03)",
            text=d[rotulo], hovertemplate="<b>%{text}</b><br>" + eixo + ": %{y:." + str(casas) + "f}<extra></extra>",
            boxmean=True,
        ))
        r = est.resumo(d[valor].tolist(), d[rotulo].tolist())
        for nome, v, _ in r["outliers"]:
            fig.add_annotation(x=str(g) if g is not None else eixo, y=v, text=f"◀ {nome}", showarrow=False,
                               xanchor="left", xshift=14, font=dict(size=12, color=VERMELHO))
    estilizar(fig, titulo, None, eixo, legenda=False)
    fig.update_layout(boxgap=0.45)
    return fig


def histograma(serie: pd.Series, titulo: str, eixo: str, nbins: int = 8) -> go.Figure:
    fig = go.Figure(go.Histogram(x=serie, nbinsx=nbins, marker=dict(color=AZUL, line=dict(color="white", width=2)),
                                 hovertemplate=eixo + ": %{x}<br>Frequência: %{y}<extra></extra>"))
    m, md = est.media(serie), est.mediana(serie)
    fig.add_vline(x=m, line=dict(color=LARANJA, width=2, dash="dash"))
    fig.add_vline(x=md, line=dict(color=VERDE_AGUA, width=2))
    direita_media = m >= md
    fig.add_annotation(x=m, y=1.0, yref="paper", text=f"Média {fmt(m, 1)}", showarrow=False,
                       xanchor="left" if direita_media else "right", xshift=4 if direita_media else -4,
                       font=dict(color=LARANJA, size=12))
    fig.add_annotation(x=md, y=0.9, yref="paper", text=f"Mediana {fmt(md, 1)}", showarrow=False,
                       xanchor="right" if direita_media else "left", xshift=-4 if direita_media else 4,
                       font=dict(color="#127a55", size=12))
    return estilizar(fig, titulo, eixo, "Frequência (nº de unidades)", legenda=False)


# ---------------------------------------------------------------------------
# Bloco estatístico padrão
# ---------------------------------------------------------------------------
def tabela_medidas(r: dict, casas: int = 1, unidade: str = "") -> pd.DataFrame:
    ud = " p.p." if unidade == "%" else unidade  # diferenças entre taxas são pontos percentuais
    moda_txt = "amodal (nenhum valor se repete)" if not r["moda"] else "; ".join(fmt(m, casas) for m in r["moda"])
    linhas = [
        ("Nº de observações (n)", str(r["n"]), "Quantidade de unidades analisadas após os filtros"),
        ("Média aritmética", fmt(r["media"], casas, unidade), "Soma ÷ n — sensível a valores extremos"),
        ("Mediana (Q2)", fmt(r["mediana"], casas, unidade), "Valor central — robusta a outliers"),
        ("Moda", moda_txt, "Valor mais frequente (arredondado a 1 casa)"),
        ("1º quartil (Q1)", fmt(r["q1"], casas, unidade), "25% das unidades estão abaixo"),
        ("3º quartil (Q3)", fmt(r["q3"], casas, unidade), "75% das unidades estão abaixo"),
        ("Intervalo interquartil (IQR)", fmt(r["iqr"], casas, ud), "Q3 − Q1: dispersão dos 50% centrais"),
        ("Mínimo", fmt(r["minimo"], casas, unidade), ""),
        ("Máximo", fmt(r["maximo"], casas, unidade), ""),
        ("Amplitude", fmt(r["amplitude"], casas, ud), "Máximo − mínimo"),
        ("Variância (populacional)", fmt(r["variancia_pop"], 2), "Média dos desvios ao quadrado (unidade²)"),
        ("Desvio padrão (populacional)", fmt(r["desvio_pop"], 2, ud), "√variância — usado p/ todas as unidades"),
        ("Desvio padrão (amostral, n−1)", fmt(r["desvio_amostral"], 2, ud), "Versão para amostras"),
        ("Coeficiente de variação", fmt(r["cv"], 1, "%"), "Desvio padrão ÷ média × 100"),
        ("Limite inferior (Q1 − 1,5·IQR)", fmt(r["limite_inferior"], casas, unidade), "Abaixo disso = outlier"),
        ("Limite superior (Q3 + 1,5·IQR)", fmt(r["limite_superior"], casas, unidade), "Acima disso = outlier"),
    ]
    return pd.DataFrame(linhas, columns=["Medida", "Valor", "Como ler"])


def texto_outliers(r: dict, imp: dict, unidade: str, casas: int = 1, nome_unidade: str = "UF") -> str:
    ud = " p.p." if unidade == "%" else unidade
    if not r["outliers"]:
        return (f"Nenhum outlier pela regra de 1,5×IQR (todos os valores entre "
                f"{fmt(r['limite_inferior'], casas, unidade)} e {fmt(r['limite_superior'], casas, unidade)}). "
                f"Como não há extremos, média ({fmt(r['media'], casas, unidade)}) e mediana "
                f"({fmt(r['mediana'], casas, unidade)}) ficam próximas e ambas representam bem o centro; "
                f"a distribuição está {est.assimetria_texto(r['media'], r['mediana'])}.")
    nomes = ", ".join(f"**{n}** ({fmt(v, casas, unidade)}, {t} do limite)" for n, v, t in r["outliers"])
    return (f"Outlier(s) pela regra de 1,5×IQR: {nomes}. "
            f"Com eles, a média é {fmt(imp['media_com'], casas, unidade)}; sem eles, passa para "
            f"{fmt(imp['media_sem'], casas, unidade)} (variação de {fmt(imp['variacao_media'], 2, ud)}). "
            f"A mediana praticamente não muda ({fmt(imp['mediana_com'], casas, unidade)} → "
            f"{fmt(imp['mediana_sem'], casas, unidade)}, variação de {fmt(imp['variacao_mediana'], 2, ud)}). "
            f"Por isso, para representar a {nome_unidade} 'típica' neste recorte, a **mediana** é a medida mais "
            f"adequada; a distribuição está {est.assimetria_texto(r['media'], r['mediana'])}.")


def bloco_estatistico(df: pd.DataFrame, valor: str, rotulo: str, titulo: str, unidade: str = "",
                      casas: int = 1, nome_unidade: str = "UF", eixo: str | None = None,
                      chave: str = "est") -> dict:
    """KPIs + tabela de medidas + boxplot + histograma + análise de outliers."""
    d = df.dropna(subset=[valor])
    if len(d) < 3:
        st.warning("Selecione pelo menos 3 unidades nos filtros para calcular quartis e outliers.")
        return {}
    r = est.resumo(d[valor].tolist(), d[rotulo].tolist())
    imp = est.impacto_outliers(d[valor].tolist(), d[rotulo].tolist())
    eixo = eixo or titulo

    ud = " p.p." if unidade == "%" else unidade  # dispersão de taxas em pontos percentuais
    c = st.columns(5)
    c[0].metric("Média", fmt(r["media"], casas, unidade))
    c[1].metric("Mediana", fmt(r["mediana"], casas, unidade))
    c[2].metric("Desvio padrão", fmt(r["desvio_pop"], 2, ud))
    c[3].metric("IQR (Q3 − Q1)", fmt(r["iqr"], casas, ud))
    c[4].metric("Amplitude", fmt(r["amplitude"], casas, ud))

    g1, g2 = st.columns([1.15, 1])
    with g1:
        st.plotly_chart(boxplot(d, valor, rotulo, f"Boxplot — {titulo}", eixo, casas=casas),
                        width="stretch", key=f"{chave}_box")
    with g2:
        st.plotly_chart(histograma(d[valor], f"Distribuição — {titulo}", eixo, nbins=min(10, max(4, len(d) // 3))),
                        width="stretch", key=f"{chave}_hist")

    st.markdown("**Análise de outliers e efeito na média × mediana**")
    st.markdown(texto_outliers(r, imp, unidade, casas, nome_unidade))
    with st.expander("📐 Ver todas as medidas estatísticas (tendência central, quartis e dispersão)"):
        st.dataframe(tabela_medidas(r, casas, unidade), hide_index=True, width="stretch")
        st.caption("Quartis por interpolação linear (mesmo método do Excel QUARTIL.INC e do pandas). "
                   "Desvio padrão populacional porque analisamos todas as unidades do recorte.")
    return r


# ---------------------------------------------------------------------------
# Upload de dados
# ---------------------------------------------------------------------------
def painel_upload(chave: str, bases: dict[str, tuple[Esquema, pd.DataFrame]]) -> dict[str, pd.DataFrame]:
    """
    Bloco de upload na barra lateral. O usuário escolhe qual base quer substituir,
    baixa o modelo, envia CSV/XLSX e o ETL valida e higieniza o arquivo.
    """
    resultado = {nome: df for nome, (_, df) in bases.items()}
    with st.sidebar.expander("📤 Upload de dados (CSV/XLSX)", expanded=False):
        nome = st.selectbox("Base a substituir", list(bases.keys()), key=f"{chave}_base_upload")
        esquema, df_padrao = bases[nome]
        st.download_button(
            "⬇️ Baixar modelo (CSV)", df_padrao.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig"),
            file_name=f"modelo_{chave}_{esquema.nome}.csv", mime="text/csv", key=f"{chave}_modelo",
            width="stretch",
        )
        arquivo = st.file_uploader("Envie a base do IBGE", type=["csv", "xlsx", "xls"], key=f"{chave}_upload",
                                   help="Aceita CSV (; , ou tab) e Excel. Linhas de título, notas de rodapé, "
                                        "vírgula decimal e símbolos do IBGE ('-', '...', 'X') são tratados.")
        st.caption("Colunas obrigatórias: " + ", ".join(f"`{c}`" for c in esquema.obrigatorias))
        if arquivo is not None:
            df_novo, rel = higienizar_upload(arquivo, esquema)
            if rel.ok:
                resultado[nome] = df_novo
                st.success("\n\n".join(rel.mensagens))
            else:
                st.error("\n\n".join(rel.mensagens) + "\n\nUsando a base padrão do IBGE.")
    origem = "arquivo enviado" if (st.session_state.get(f"{chave}_upload") is not None) else "base IBGE padrão"
    st.sidebar.caption(f"Fonte em uso: **{origem}**")
    return resultado


def botao_download_bases(tabelas: dict[str, pd.DataFrame], nome: str, chave: str):
    st.sidebar.download_button("⬇️ Baixar dados filtrados (XLSX)", para_excel_bytes(tabelas), file_name=f"{nome}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               key=f"{chave}_xlsx", width="stretch")


# ---------------------------------------------------------------------------
# Notícias e imagens
# ---------------------------------------------------------------------------
def bloco_noticias(noticias: list[dict], imagens: list[tuple[str, str]], chave: str):
    """Seção de conteúdo adicional: imagens ilustrativas + cards de notícias com link."""
    if imagens:
        cols = st.columns(len(imagens))
        for col, (arq, legenda) in zip(cols, imagens):
            caminho = IMG / arq
            if caminho.exists():
                col.image(str(caminho), caption=legenda, width="stretch")
    st.markdown("")
    for i in range(0, len(noticias), 3):
        cols = st.columns(3)
        for col, n in zip(cols, noticias[i:i + 3]):
            with col.container(border=True):
                st.markdown(f'<div class="nqf-noticia-titulo">{n["titulo"]}</div>', unsafe_allow_html=True)
                st.caption(f'{n["fonte"]} · {n.get("data", "")}')
                st.write(n["resumo"])
                st.link_button("Ler matéria ↗", n["url"], width="stretch")


def tabela_outliers_por_grupo(df: pd.DataFrame, valor: str, rotulo: str, grupo: str, casas: int = 1) -> pd.DataFrame:
    """Aplica a regra 1,5×IQR dentro de cada grupo (ex.: UFs de cada região)."""
    linhas = []
    for g, d in df.dropna(subset=[valor]).groupby(grupo):
        if len(d) < 4:
            continue
        r = est.resumo(d[valor].tolist(), d[rotulo].tolist())
        imp = est.impacto_outliers(d[valor].tolist(), d[rotulo].tolist())
        linhas.append({grupo.capitalize(): g, "n": r["n"], "Média": fmt(r["media"], 2), "Mediana": fmt(r["mediana"], casas),
                       "Limites (inf.; sup.)": f"{fmt(r['limite_inferior'], casas)} ; {fmt(r['limite_superior'], casas)}",
                       "Outliers": ", ".join(f"{n} ({fmt(v, casas)})" for n, v, _ in r["outliers"]) or "—",
                       "Média sem outliers": fmt(imp["media_sem"], 2) if r["outliers"] else "—"})
    return pd.DataFrame(linhas)


# ---------------------------------------------------------------------------
# Mapa coroplético das UFs (desenhado com polígonos, funciona offline)
# ---------------------------------------------------------------------------
_GEO_CACHE: dict = {}


def _poligonos_ufs() -> dict:
    """Lê o GeoJSON simplificado das UFs e devolve {sigla: [(lons, lats), ...]}."""
    if not _GEO_CACHE:
        import json
        with open(RAIZ / "assets" / "geo" / "brasil_ufs.geojson", encoding="utf-8") as f:
            gj = json.load(f)
        for feat in gj["features"]:
            g = feat["geometry"]
            polys = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
            aneis = []
            for poly in polys:
                ext = poly[0]
                aneis.append(([p[0] for p in ext], [p[1] for p in ext]))
            _GEO_CACHE[feat["properties"]["sigla"]] = aneis
    return _GEO_CACHE


def _cor_na_escala(t: float, escala: list[str]) -> str:
    """Interpola linearmente uma cor (hex) na escala para t entre 0 e 1."""
    t = min(max(t, 0.0), 1.0)
    pos = t * (len(escala) - 1)
    i = min(int(pos), len(escala) - 2)
    f = pos - i
    c1 = [int(escala[i][k:k + 2], 16) for k in (1, 3, 5)]
    c2 = [int(escala[i + 1][k:k + 2], 16) for k in (1, 3, 5)]
    return "#" + "".join(f"{round(a + (b - a) * f):02x}" for a, b in zip(c1, c2))


def mapa_ufs(df: pd.DataFrame, valor: str, titulo: str, rotulo_valor: str, escala: list[str] | None = None,
             faixa: tuple[float, float] | None = None, casas: int = 1, altura: int = 440) -> go.Figure:
    """Coroplético por UF sem depender de mapas externos (CDN)."""
    escala = escala or SEQ_AZUL
    poligonos = _poligonos_ufs()
    d = df.dropna(subset=[valor])
    vmin, vmax = faixa if faixa else (d[valor].min(), d[valor].max())
    amp = (vmax - vmin) or 1
    fig = go.Figure()
    valores = dict(zip(d["sigla"], d[valor]))
    nomes = dict(zip(d["sigla"], d["uf"])) if "uf" in d.columns else {}
    for sigla, aneis in poligonos.items():
        v = valores.get(sigla)
        cor = "#e9e8e4" if v is None else _cor_na_escala((v - vmin) / amp, escala)
        texto = f"<b>{nomes.get(sigla, sigla)}</b><br>{rotulo_valor}: " + ("sem dado / fora do filtro" if v is None
                                                                            else fmt(v, casas))
        for j, (lon, lat) in enumerate(aneis):
            fig.add_trace(go.Scatter(x=lon, y=lat, fill="toself", fillcolor=cor, mode="lines",
                                     line=dict(color="white", width=1), hoverinfo="text", text=texto,
                                     hoveron="fills", showlegend=False))
    # traço invisível só para exibir a barra de cores
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", showlegend=False, hoverinfo="skip",
                             marker=dict(colorscale=[[i / (len(escala) - 1), c] for i, c in enumerate(escala)],
                                         cmin=vmin, cmax=vmax, color=[vmin], showscale=True,
                                         colorbar=dict(title=dict(text=rotulo_valor, side="right"), thickness=12))))
    estilizar(fig, titulo, None, None, altura=altura, legenda=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", hovermode="closest")
    return fig
