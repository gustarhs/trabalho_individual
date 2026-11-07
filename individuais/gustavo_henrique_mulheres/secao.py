"""
Seção individual — Indicador 4: Mulheres.
Responsável: Gustavo Henrique.
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core import estatistica as est
from core import ui
from core.carregamento import REGIOES, Esquema
from individuais.gustavo_henrique_mulheres.etl_mulheres import carregar

AUTOR = "Gustavo Henrique"
RACAS = ["Branca", "Parda", "Preta", "Amarela", "Indígena"]
CORES_RACA = {"Branca": ui.AZUL, "Parda": ui.LARANJA, "Preta": ui.VIOLETA, "Amarela": ui.AMARELO, "Indígena": ui.VERDE_AGUA}

ESQ_IDADE = Esquema("mulheres_regiao_idade", ["regiao", "grupo_idade", "situacao", "homens", "mulheres"],
                    ["homens", "mulheres", "idade_inicio"],
                    {"regiao": ["região", "grandes regioes"], "grupo_idade": ["grupo de idade", "idade", "faixa etaria"]})
ESQ_PROJ = Esquema("projecao_sexo", ["ano", "sexo", "grupo_idade", "populacao"], ["ano", "populacao", "idade_inicio"],
                   {"populacao": ["valor", "pessoas", "população"], "grupo_idade": ["grupo de idade", "idade"]})
ESQ_GEN = Esquema("indicadores_genero", ["indicador", "homens", "mulheres"], ["homens", "mulheres", "ano"],
                  {"dimensao": ["dimensão"]})

NOTICIAS = [
    {"titulo": "Censo 2022: mulheres são maioria em todas as regiões pela primeira vez",
     "fonte": "Brasil de Fato / Agência Brasil", "data": "out/2023",
     "resumo": "São 104,5 milhões de mulheres e 98,5 milhões de homens; razão de sexo de 94,2.",
     "url": "https://www.brasildefato.com.br/2023/10/27/censo-2022-mulheres-sao-maioria-em-todas-as-regioes-pela-primeira-vez/"},
    {"titulo": "Brasil é feminino: mulheres são maioria em todas as regiões pela primeira vez",
     "fonte": "Forbes Brasil", "data": "out/2023",
     "resumo": "Reportagem sobre o resultado do Censo 2022 que mostra maioria feminina em todas as regiões.",
     "url": "https://forbes.com.br/forbes-mulher/2023/10/brasil-e-feminino-mulheres-sao-maioria-em-todas-as-regioes-pela-primeira-vez/"},
    {"titulo": "Taxa de desemprego entre mulheres foi 45,3% maior que entre homens",
     "fonte": "Acionista / Agência Brasil", "data": "2023",
     "resumo": "A desigualdade de gênero no mercado de trabalho persiste mesmo com a queda do desemprego.",
     "url": "https://acionista.com.br/taxa-de-desemprego-entre-mulheres-foi-453-maior-que-entre-homens/"},
    {"titulo": "Veja a desigualdade de gênero no Brasil em sete infográficos",
     "fonte": "Congresso em Foco", "data": "mar/2024",
     "resumo": "Infográficos sobre a desigualdade de gênero no Brasil a partir de dados oficiais.",
     "url": "https://congressoemfoco.com.br/area/pais/veja-a-desigualdade-de-genero-no-brasil-em-sete-infograficos"},
    {"titulo": "Estatísticas de Gênero: indicadores sociais das mulheres no Brasil",
     "fonte": "IBGE", "data": "3ª edição, 2024",
     "resumo": "Página oficial com publicação, tabelas e notas técnicas.",
     "url": "https://www.ibge.gov.br/estatisticas/multidominio/genero/20163"},
    {"titulo": "Estatísticas de Gênero — informativo da 3ª edição (PDF)",
     "fonte": "IBGE", "data": "2024",
     "resumo": "Resumo com trabalho, renda, educação, saúde e vida pública das mulheres.",
     "url": "https://biblioteca.ibge.gov.br/visualizacao/livros/liv102066_informativo.pdf"},
]
IMAGENS = [("mulheres_maioria.png", "Mulheres são 51,5% da população"),
           ("mulheres_renda.png", "Desigualdade de rendimento entre mulheres e homens")]


def render(chave: str = "gustavo"):
    tabelas = carregar()
    bases = ui.painel_upload(chave, {
        "Mulheres e homens por região, idade e situação": (ESQ_IDADE, tabelas["mulheres_regiao_idade"]),
        "Projeção por sexo e idade (2010–2026)": (ESQ_PROJ, tabelas["projecao_sexo"]),
        "Indicadores de gênero (homens × mulheres)": (ESQ_GEN, tabelas["indicadores_genero"]),
    })
    idade = bases["Mulheres e homens por região, idade e situação"].copy()
    proj = bases["Projeção por sexo e idade (2010–2026)"].copy()
    gen = bases["Indicadores de gênero (homens × mulheres)"].copy()
    cor = tabelas["mulheres_cor_raca"]
    gen_raca = tabelas["indicadores_genero_raca"]
    for df in (idade, proj):
        if "idade_inicio" not in df.columns or df["idade_inicio"].isna().all():
            df["idade_inicio"] = df["grupo_idade"].astype(str).str.extract(r"(\d+)")[0].astype(float)
    if "dimensao" not in gen.columns:
        gen["dimensao"] = "Geral"

    # ------------------------------------------------------------------ Filtros
    sb = st.sidebar
    sb.subheader("Filtros — Mulheres")
    regioes = sb.multiselect("Regiões", REGIOES, default=REGIOES, key=f"{chave}_reg")
    situacoes = sb.multiselect("Situação do domicílio", ["Urbana", "Rural"], default=["Urbana", "Rural"], key=f"{chave}_sit")
    inicios = sorted(idade["idade_inicio"].dropna().astype(int).unique().tolist())
    faixa = sb.select_slider("Faixa etária (início do grupo)", inicios, value=(inicios[0], inicios[-1]),
                             format_func=lambda v: f"{v}+" if v == inicios[-1] else f"{v} anos", key=f"{chave}_faixa")
    racas = sb.multiselect("Cor ou raça", RACAS, default=RACAS, key=f"{chave}_raca")
    anos_proj = sorted(proj["ano"].dropna().astype(int).unique().tolist())
    ano = sb.select_slider("Ano (projeção populacional)", anos_proj, value=2022 if 2022 in anos_proj else anos_proj[-1],
                           key=f"{chave}_ano")
    dims = sorted(gen["dimensao"].dropna().unique().tolist())
    dim_sel = sb.multiselect("Dimensões dos indicadores sociais", dims, default=dims, key=f"{chave}_dims")
    if not (regioes and situacoes):
        st.warning("Selecione ao menos uma região e uma situação do domicílio.")
        return

    f = idade[idade["regiao"].isin(regioes) & idade["situacao"].isin(situacoes)
              & idade["idade_inicio"].between(faixa[0], faixa[1])]
    fc = cor[cor["regiao"].isin(regioes) & cor["situacao"].isin(situacoes) & cor["cor_raca"].isin(racas)]
    ui.botao_download_bases({"idade_filtrado": f, "cor_filtrado": fc, "projecao": proj, "indicadores": gen},
                            "mulheres_filtrado", chave)

    ui.cabecalho_secao("Mulheres: quem são, onde estão e como vivem", "Indicador 4 · Censo 2022, Projeções e Estatísticas "
                       "de Gênero (IBGE)", AUTOR, ["Indicador 4", "Censo 2022", "Gênero"])
    ui.caixa_persona(
        "Por que isso importa para o Ministério do Trabalho, o Sebrae e a Indústria?",
        "As mulheres são a maioria da população, mas a minoria na força de trabalho e nos cargos de gestão. Entender "
        "onde elas estão, em que idade e com quais barreiras orienta políticas de emprego, empreendedorismo feminino "
        "(Sebrae Delas) e diversidade na indústria. Perguntas: <b>(a)</b> Onde e em que idades as mulheres são maioria? "
        "<b>(b)</b> Quais recortes são outliers da razão de sexo? <b>(c)</b> Como o número de mulheres idosas evolui até "
        "2026? <b>(d)</b> Quais as principais desigualdades no trabalho, renda e educação?")

    abas = st.tabs(["♀ Perfil territorial", "📐 Estatística e outliers", "🎨 Cor ou raça", "📈 Projeção 2010–2026",
                    "💼 Trabalho, renda e educação", "💡 Respostas", "📰 Notícias"])

    mul, hom = f["mulheres"].sum(), f["homens"].sum()

    # ------------------------------------------------------------------ Aba 1
    with abas[0]:
        c = st.columns(5)
        c[0].metric("Mulheres no recorte", ui.fmt_mi(mul, 2))
        c[1].metric("% de mulheres", ui.fmt(mul / (mul + hom) * 100, 1, "%") if mul + hom else "—")
        c[2].metric("Razão de sexo", ui.fmt(hom / mul * 100, 1) if mul else "—", help="Homens para cada 100 mulheres")
        c[3].metric("Excedente feminino", ui.fmt_mi(mul - hom, 2), help="Mulheres − homens")
        idosas = f[f["idade_inicio"] >= 60]["mulheres"].sum()
        c[4].metric("Mulheres com 60+", ui.fmt(idosas / mul * 100, 1, "%") if mul else "—",
                    help="Parcela das mulheres do recorte com 60 anos ou mais")
        c1, c2 = st.columns(2)
        with c1:
            r = f.groupby(["regiao", "situacao"], as_index=False)[["homens", "mulheres"]].sum()
            r["pct"] = r["mulheres"] / (r["homens"] + r["mulheres"]) * 100
            fig = px.bar(r, x="regiao", y="pct", color="situacao", barmode="group",
                         color_discrete_map={"Urbana": ui.LARANJA, "Rural": ui.AZUL},
                         category_orders={"regiao": REGIOES}, text=r["pct"].map(lambda v: ui.fmt(v, 1)))
            fig.add_hline(y=50, line=dict(color=ui.CINZA, dash="dot"))
            ui.estilizar(fig, "% de mulheres por região e situação (linha = 50%)", "Região", "% de mulheres", altura=420)
            fig.update_yaxes(range=[40, 56])
            st.plotly_chart(fig, key=f"{chave}_pct_reg")
            st.caption("Nas cidades as mulheres são maioria; no campo, os homens — migração feminina para áreas urbanas.")
        with c2:
            rs = f.groupby(["regiao", "grupo_idade", "idade_inicio"], as_index=False)[["homens", "mulheres"]].sum()
            rs["razao"] = rs["homens"] / rs["mulheres"] * 100
            fig = px.line(rs.sort_values("idade_inicio"), x="grupo_idade", y="razao", color="regiao", markers=True,
                          color_discrete_map=ui.COR_REGIAO)
            fig.add_hline(y=100, line=dict(color=ui.CINZA, dash="dot"), annotation_text="equilíbrio (100)",
                          annotation_position="bottom left")
            fig.update_traces(line_width=2, marker_size=7)
            ui.estilizar(fig, "Razão de sexo por idade (homens por 100 mulheres)", "Grupo de idade",
                         "Homens por 100 mulheres", altura=420)
            st.plotly_chart(fig, key=f"{chave}_rs_idade")
            st.caption("Nascem mais meninos, mas a partir dos 25–30 anos as mulheres passam a ser maioria e, entre "
                       "idosos, o excedente feminino dispara (maior mortalidade masculina).")
        ui.fonte("IBGE, Censo Demográfico 2022 — Anuário Estatístico 2024, Tabela 2.1.1.2.")

    # ------------------------------------------------------------------ Aba 2
    with abas[1]:
        st.subheader("Razão de sexo nos recortes região × grupo de idade")
        cel = f.groupby(["regiao", "grupo_idade", "idade_inicio"], as_index=False)[["homens", "mulheres"]].sum()
        cel["razao"] = cel["homens"] / cel["mulheres"] * 100
        cel["pct_mulheres"] = cel["mulheres"] / (cel["homens"] + cel["mulheres"]) * 100
        cel["rotulo"] = cel["regiao"] + " · " + cel["grupo_idade"]
        st.caption(f"Cada ponto é um recorte (região × faixa de idade) — {len(cel)} recortes com os filtros atuais.")
        ui.bloco_estatistico(cel, "razao", "rotulo", "Razão de sexo (homens por 100 mulheres)", "", 1, "recorte",
                             eixo="Homens por 100 mulheres", chave=f"{chave}_est_rs")
        st.plotly_chart(ui.boxplot(cel.sort_values("regiao"), "razao", "grupo_idade", "Razão de sexo por região",
                                   "Homens por 100 mulheres", grupo="regiao", cores=ui.COR_REGIAO), key=f"{chave}_box_reg")
        st.markdown("#### % de mulheres nos recortes região × cor ou raça × situação")
        fc2 = fc.copy()
        fc2["rotulo"] = fc2["regiao"] + " · " + fc2["cor_raca"] + " · " + fc2["situacao"]
        ui.bloco_estatistico(fc2, "pct_mulheres", "rotulo", "% de mulheres por região, cor ou raça e situação", "%", 1,
                             "recorte", eixo="% de mulheres", chave=f"{chave}_est_cor")

    # ------------------------------------------------------------------ Aba 3
    with abas[2]:
        if fc.empty:
            st.warning("Selecione pelo menos uma cor ou raça.")
        else:
            comp = fc.groupby(["regiao", "cor_raca"], as_index=False)["mulheres"].sum()
            comp["pct"] = comp["mulheres"] / comp.groupby("regiao")["mulheres"].transform("sum") * 100
            comp["cor_raca"] = pd.Categorical(comp["cor_raca"], RACAS)
            comp = comp.sort_values("cor_raca")
            fig = px.bar(comp, y="regiao", x="pct", color="cor_raca", orientation="h", color_discrete_map=CORES_RACA,
                         category_orders={"regiao": REGIOES[::-1]}, text=comp["pct"].map(lambda v: ui.fmt(v, 0) if v >= 4 else ""))
            fig.update_traces(marker_line_color="white", marker_line_width=2)
            fig.update_layout(barmode="stack")
            ui.estilizar(fig, "Mulheres por cor ou raça em cada região (% das mulheres)", "% das mulheres", "Região",
                         altura=400)
            st.plotly_chart(fig, key=f"{chave}_cor_comp")
            rs = fc.groupby(["cor_raca", "situacao"], as_index=False)[["homens", "mulheres"]].sum()
            rs["razao"] = rs["homens"] / rs["mulheres"] * 100
            fig = px.bar(rs, x="cor_raca", y="razao", color="situacao", barmode="group",
                         color_discrete_map={"Urbana": ui.LARANJA, "Rural": ui.AZUL}, category_orders={"cor_raca": RACAS},
                         text=rs["razao"].map(lambda v: ui.fmt(v, 1)))
            fig.add_hline(y=100, line=dict(color=ui.CINZA, dash="dot"))
            ui.estilizar(fig, "Razão de sexo por cor ou raça e situação do domicílio", "Cor ou raça",
                         "Homens por 100 mulheres", altura=400)
            st.plotly_chart(fig, key=f"{chave}_cor_rs")
        ui.fonte("IBGE, Censo 2022 — Anuário Estatístico 2024, Tabela 2.1.4.1.")

    # ------------------------------------------------------------------ Aba 4
    with abas[3]:
        tot = proj.groupby(["ano", "sexo"], as_index=False)["populacao"].sum()
        larg = tot.pivot(index="ano", columns="sexo", values="populacao")
        c1, c2 = st.columns(2)
        with c1:
            fig = px.line(tot, x="ano", y=tot["populacao"] / 1e6, color="sexo", markers=True, color_discrete_map=ui.COR_SEXO)
            fig.update_traces(line_width=2, marker_size=8)
            fig.add_vline(x=ano, line=dict(color=ui.CINZA, dash="dot"))
            ui.estilizar(fig, "População projetada por sexo — Brasil (milhões)", "Ano", "Milhões de pessoas", altura=400)
            st.plotly_chart(fig, key=f"{chave}_proj_tot")
        with c2:
            mi = proj[proj["sexo"] == "Mulheres"].copy()
            mi["grupo"] = pd.cut(mi["idade_inicio"], [-1, 14, 29, 59, 200], labels=["0–14", "15–29", "30–59", "60+"])
            gi = mi.groupby(["ano", "grupo"], observed=True, as_index=False)["populacao"].sum()
            gi["pct"] = gi["populacao"] / gi.groupby("ano")["populacao"].transform("sum") * 100
            fig = px.line(gi, x="ano", y="pct", color="grupo", markers=True,
                          color_discrete_sequence=[ui.VERDE_AGUA, ui.AZUL, ui.VIOLETA, ui.LARANJA])
            fig.update_traces(line_width=2, marker_size=7)
            ui.estilizar(fig, "Composição etária das mulheres (% das mulheres)", "Ano", "% das mulheres", altura=400)
            st.plotly_chart(fig, key=f"{chave}_proj_idade")
        pa = proj[proj["ano"] == ano].sort_values("idade_inicio")
        fig = go.Figure()
        for sx in ["Homens", "Mulheres"]:
            d = pa[pa["sexo"] == sx]
            fig.add_bar(y=d["grupo_idade"], x=-d["populacao"] / 1e6 if sx == "Homens" else d["populacao"] / 1e6,
                        orientation="h", name=sx, marker_color=ui.COR_SEXO[sx], customdata=d["populacao"],
                        hovertemplate=sx + " · %{y}: %{customdata:,.0f}<extra></extra>")
        m = (pa["populacao"] / 1e6).max() + 0.5
        fig.update_layout(barmode="relative", bargap=0.08)
        ui.estilizar(fig, f"Pirâmide etária projetada — {ano} (milhões)", "Milhões de pessoas", "Grupo de idade", altura=520)
        fig.update_xaxes(tickvals=[-m, -m / 2, 0, m / 2, m], ticktext=[ui.fmt(abs(v), 1) for v in [-m, -m / 2, 0, m / 2, m]])
        st.plotly_chart(fig, key=f"{chave}_proj_pir")
        if ano in larg.index:
            c = st.columns(3)
            c[0].metric(f"Mulheres em {ano}", ui.fmt_mi(larg.loc[ano, "Mulheres"], 1))
            c[1].metric(f"Excedente feminino em {ano}", ui.fmt_mi(larg.loc[ano, "Mulheres"] - larg.loc[ano, "Homens"], 2))
            m80 = pa[(pa["sexo"] == "Mulheres") & (pa["idade_inicio"] >= 80)]["populacao"].sum()
            h80 = pa[(pa["sexo"] == "Homens") & (pa["idade_inicio"] >= 80)]["populacao"].sum()
            c[2].metric(f"Mulheres por 100 homens (80+) em {ano}", ui.fmt(m80 / h80 * 100, 0) if h80 else "—")
        ui.fonte("IBGE, Projeção da População do Brasil e UFs por sexo e idade 2000-2070 — Revisão 2024 "
                 "(Anuário 2024, Tabela 2.1.1.3).")

    # ------------------------------------------------------------------ Aba 5
    with abas[4]:
        g = gen[gen["dimensao"].isin(dim_sel)].copy()
        pct = g[g["unidade"] == "%"] if "unidade" in g.columns else g
        if not pct.empty:
            lg = pct.melt(id_vars=["indicador"], value_vars=["homens", "mulheres"], var_name="sexo", value_name="valor")
            lg["sexo"] = lg["sexo"].map({"homens": "Homens", "mulheres": "Mulheres"})
            fig = px.bar(lg, y="indicador", x="valor", color="sexo", barmode="group", orientation="h",
                         color_discrete_map=ui.COR_SEXO, text=lg["valor"].map(lambda v: ui.fmt(v, 1)))
            ui.estilizar(fig, "Indicadores sociais (%) — homens × mulheres, 2022", "%", None,
                         altura=max(380, 46 * len(pct) + 120))
            st.plotly_chart(fig, key=f"{chave}_gen_pct")
        outros = g[g["unidade"] != "%"] if "unidade" in g.columns else pd.DataFrame()
        if not outros.empty:
            linhas = list(outros.iterrows())
            for i in range(0, len(linhas), 2):
                cols = st.columns(2)
                for col, (_, row) in zip(cols, linhas[i:i + 2]):
                    un = "R$ " if row["unidade"] == "R$" else ""
                    suf = " h" if row["unidade"] == "horas" else ""
                    casas = 0 if un else 1
                    col.metric(f"{row['indicador']} — mulheres", f"{un}{ui.fmt(row['mulheres'], casas)}{suf}",
                               delta=f"homens: {un}{ui.fmt(row['homens'], casas)}{suf} "
                                     f"(razão M/H = {ui.fmt(row['mulheres'] / row['homens'] * 100, 1)}%)",
                               delta_color="off")
        c1, c2 = st.columns(2)
        for col, ind in zip((c1, c2), ["Taxa de desocupação", "Superior completo (25 anos ou mais)"]):
            d = gen_raca[gen_raca["indicador"] == ind]
            with col:
                fig = go.Figure(go.Bar(x=d["grupo"].str.replace(" ", "<br>", n=1), y=d["valor"],
                                       marker_color=[ui.AZUL if "Homens" in x else ui.LARANJA for x in d["grupo"]],
                                       text=d["valor"].map(lambda v: ui.fmt(v, 1) + "%"), textposition="outside"))
                ui.estilizar(fig, f"{ind} por sexo e cor ou raça — 2022", "Grupo", "%", altura=380, legenda=False)
                st.plotly_chart(fig, key=f"{chave}_raca_{ind[:5]}")
        pol = gen_raca[gen_raca["indicador"] == "Representação política"]
        fig = go.Figure(go.Bar(x=pol["valor"], y=pol["grupo"] + " (" + pol["ano"].astype(str) + ")", orientation="h",
                               marker_color=ui.LARANJA, text=pol["valor"].map(lambda v: ui.fmt(v, 1) + "%"),
                               textposition="outside"))
        fig.add_vline(x=51.5, line=dict(color=ui.CINZA, dash="dot"), annotation_text="mulheres na população: 51,5%",
                      annotation_position="top left")
        ui.estilizar(fig, "Mulheres na vida pública (%)", "% de mulheres", None, altura=320, legenda=False)
        fig.update_xaxes(range=[0, 60])
        st.plotly_chart(fig, key=f"{chave}_politica")
        ui.fonte("IBGE, Estatísticas de Gênero: indicadores sociais das mulheres no Brasil, 3ª ed. (2024); Censo 2022.")

    with abas[5]:
        _respostas(idade, proj, gen, gen_raca)

    with abas[6]:
        st.subheader("Notícias e contexto")
        ui.bloco_noticias(NOTICIAS, IMAGENS, chave)


def _respostas(idade, proj, gen, gen_raca):
    st.caption("Respostas calculadas com o Brasil inteiro (todas as regiões, idades e situações).")
    reg = idade.groupby("regiao")[["homens", "mulheres"]].sum()
    reg["pct"] = reg["mulheres"] / reg.sum(axis=1) * 100
    sit = idade.groupby("situacao")[["homens", "mulheres"]].sum()
    sit["rs"] = sit["homens"] / sit["mulheres"] * 100
    ida = idade.groupby(["grupo_idade", "idade_inicio"], as_index=False)[["homens", "mulheres"]].sum().sort_values("idade_inicio")
    ida["rs"] = ida["homens"] / ida["mulheres"] * 100
    vira = ida[ida["rs"] < 100]["grupo_idade"].iloc[0]
    ui.resposta("(a) Onde e em que idades as mulheres são maioria?",
                "Em todas as regiões: " + "; ".join(f"{r} {ui.fmt(reg.loc[r, 'pct'], 1)}%" for r in REGIOES) + ". "
                f"Nas áreas urbanas há {ui.fmt(sit.loc['Urbana', 'rs'], 1)} homens por 100 mulheres; nas rurais, "
                f"{ui.fmt(sit.loc['Rural', 'rs'], 1)} (maioria masculina). Por idade, os homens são maioria até a "
                f"adolescência e as mulheres passam a ser maioria a partir do grupo de {vira}; aos 70+, a razão cai para "
                f"{ui.fmt(ida.iloc[-1]['rs'], 1)}. <b>Para o Sebrae:</b> o empreendedorismo feminino tem mais público nas "
                "cidades e entre mulheres maduras.")
    cel = idade.groupby(["regiao", "grupo_idade"], as_index=False)[["homens", "mulheres"]].sum()
    cel["rs"] = cel["homens"] / cel["mulheres"] * 100
    rot = (cel["regiao"] + " " + cel["grupo_idade"]).tolist()
    r = est.resumo(cel["rs"].tolist(), rot)
    imp = est.impacto_outliers(cel["rs"].tolist(), rot)
    outs = ", ".join(f"{n} ({ui.fmt(v, 1)})" for n, v, _ in r["outliers"]) or "nenhum"
    ui.resposta("(b) Quais recortes são outliers da razão de sexo?",
                f"Nos {r['n']} recortes região × idade, a razão de sexo tem média {ui.fmt(r['media'], 1)}, mediana "
                f"{ui.fmt(r['mediana'], 1)}, Q1 {ui.fmt(r['q1'], 1)}, Q3 {ui.fmt(r['q3'], 1)} (IQR {ui.fmt(r['iqr'], 1)}) e desvio "
                f"padrão {ui.fmt(r['desvio_pop'], 1)}. Outliers (abaixo de {ui.fmt(r['limite_inferior'], 1)}): {outs}. "
                f"Eles puxam a média para baixo: sem eles, a média sobe para {ui.fmt(imp['media_sem'], 1)}, enquanto a "
                f"mediana quase não muda ({ui.fmt(imp['mediana_sem'], 1)}). São as idosas do Sul e Sudeste, onde a "
                "esperança de vida é maior e a sobremortalidade masculina se acumula.")
    tot = proj.groupby(["ano", "sexo"])["populacao"].sum().unstack()
    m60 = proj[(proj["sexo"] == "Mulheres") & (proj["idade_inicio"] >= 60)].groupby("ano")["populacao"].sum()
    a0, a1 = int(tot.index.min()), int(tot.index.max())
    ui.resposta("(c) Como evolui o número de mulheres idosas?",
                f"Pela projeção do IBGE, as mulheres com 60+ passam de {ui.fmt_mi(m60[a0], 1)} ({a0}) para "
                f"{ui.fmt_mi(m60[a1], 1)} ({a1}), +{ui.fmt((m60[a1] / m60[a0] - 1) * 100, 0)}%, enquanto o total de "
                f"mulheres cresce {ui.fmt((tot.loc[a1, 'Mulheres'] / tot.loc[a0, 'Mulheres'] - 1) * 100, 1)}%. O excedente "
                f"feminino vai de {ui.fmt_mi(tot.loc[a0, 'Mulheres'] - tot.loc[a0, 'Homens'], 1)} para "
                f"{ui.fmt_mi(tot.loc[a1, 'Mulheres'] - tot.loc[a1, 'Homens'], 1)}. <b>Leitura:</b> cresce a demanda por "
                "cuidado — que hoje recai sobre as próprias mulheres e reduz sua participação no trabalho.")
    gi = gen.set_index("indicador")
    def par(ind, casas=1, pre="", suf="%"):
        return f"{pre}{ui.fmt(gi.loc[ind, 'mulheres'], casas)}{suf} × {pre}{ui.fmt(gi.loc[ind, 'homens'], casas)}{suf}"
    try:
        ui.resposta("(d) Quais as principais desigualdades no trabalho, renda e educação?",
                    f"Participação na força de trabalho: {par('Taxa de participação na força de trabalho (15 anos ou mais)')} "
                    f"(mulheres × homens); desocupação: {par('Taxa de desocupação')}; rendimento: "
                    f"{par('Rendimento habitual de todos os trabalhos', 0, 'R$ ', '')} (as mulheres recebem 78,9% do que "
                    f"recebem os homens); cargos gerenciais: {par('Participação em cargos gerenciais')}; horas de cuidados: "
                    f"{par('Horas semanais em cuidados e afazeres domésticos', 1, '', ' h')}. Paradoxo: as mulheres estudam "
                    f"mais (superior completo {par('Superior completo (25 anos ou mais)')}) e ainda assim ganham menos. "
                    "<b>Recomendação às personas:</b> creches e licenças compartilhadas (Ministério), crédito e "
                    "capacitação para empreendedoras (Sebrae) e metas de mulheres em cargos técnicos e de liderança "
                    "(Indústria).")
    except KeyError:
        st.info("A base de indicadores enviada não tem todos os indicadores usados nesta resposta.")
