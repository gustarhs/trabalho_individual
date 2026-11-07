

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from core.carregamento import REGIOES, ler_ibge, nome_coluna, para_numero

PASTA = Path(__file__).resolve().parent
BRUTOS = PASTA / "dados" / "brutos"
TRATADOS = PASTA / "dados" / "tratados"
SUBGRUPOS = {"15 a 17 anos", "18 e 19 anos"}


def _inicio(grupo: str) -> int:
    return int(re.findall(r"\d+", grupo)[0])


def tratar_regiao_idade() -> pd.DataFrame:
    df = ler_ibge(BRUTOS / "censo2022_pop_regiao_idade_sexo_situacao.csv",
                  ["Grandes Regiões e grupos de idade", "Homens", "Mulheres"])
    df = df.rename(columns={df.columns[0]: "rotulo"})
    df["regiao"] = df["rotulo"].where(df["rotulo"].isin(["Brasil"] + REGIOES)).ffill()
    df = df[~df["rotulo"].isin(["Brasil"] + REGIOES) & ~df["rotulo"].isin(SUBGRUPOS) & (df["regiao"] != "Brasil")]
    linhas = []
    for situacao in ("Urbana", "Rural"):
        p = pd.DataFrame({
            "regiao": df["regiao"], "grupo_idade": df["rotulo"], "situacao": situacao,
            "homens": df[f"{situacao} Homens"].map(para_numero),
            "mulheres": df[f"{situacao} Mulheres"].map(para_numero),
        })
        linhas.append(p)
    out = pd.concat(linhas, ignore_index=True)
    out["idade_inicio"] = out["grupo_idade"].map(_inicio)
    out[["homens", "mulheres"]] = out[["homens", "mulheres"]].astype("int64")
    assert out["mulheres"].sum() == 104_548_325, "Total de mulheres difere do Censo 2022"
    out["razao_sexo"] = (out["homens"] / out["mulheres"] * 100).round(2)
    out["pct_mulheres"] = (out["mulheres"] / (out["homens"] + out["mulheres"]) * 100).round(2)
    return out.sort_values(["regiao", "situacao", "idade_inicio"]).reset_index(drop=True)


def tratar_cor_raca() -> pd.DataFrame:
    df = ler_ibge(BRUTOS / "censo2022_pop_regiao_cor_raca_sexo_situacao.csv",
                  ["Grandes Regiões", "Situação do domicílio", "Sexo", "Branca"])
    df.columns = [nome_coluna(c) for c in df.columns]
    df = df[(df["grandes_regioes"] != "Brasil") & (df["situacao_do_domicilio"] != "Total") & (df["sexo"] != "Total")]
    cores = {"branca": "Branca", "preta": "Preta", "amarela": "Amarela", "parda": "Parda", "indigena": "Indígena"}
    longo = df.melt(id_vars=["grandes_regioes", "situacao_do_domicilio", "sexo"], value_vars=list(cores),
                    var_name="cor_raca", value_name="pop")
    longo["pop"] = longo["pop"].map(para_numero)
    longo["cor_raca"] = longo["cor_raca"].map(cores)
    largo = longo.pivot_table(index=["grandes_regioes", "situacao_do_domicilio", "cor_raca"], columns="sexo",
                              values="pop", aggfunc="sum").reset_index()
    largo.columns = ["regiao", "situacao", "cor_raca", "homens", "mulheres"]
    largo[["homens", "mulheres"]] = largo[["homens", "mulheres"]].astype("int64")
    largo["razao_sexo"] = (largo["homens"] / largo["mulheres"] * 100).round(2)
    largo["pct_mulheres"] = (largo["mulheres"] / (largo["homens"] + largo["mulheres"]) * 100).round(2)
    return largo


def tratar_projecao() -> pd.DataFrame:
    df = ler_ibge(BRUTOS / "projecao_populacao_sexo_idade_2010_2026.csv", ["Sexo e grupos de idade", "2010", "2026"])
    df = df.rename(columns={df.columns[0]: "rotulo"})
    df["sexo"] = df["rotulo"].where(df["rotulo"].isin(["Homens", "Mulheres"])).ffill()
    df = df[~df["rotulo"].isin(["Homens", "Mulheres"])]
    longo = df.melt(id_vars=["sexo", "rotulo"], var_name="ano", value_name="populacao")
    longo["populacao"] = longo["populacao"].map(para_numero).astype("int64")
    longo["ano"] = longo["ano"].astype(int)
    longo = longo.rename(columns={"rotulo": "grupo_idade"})
    longo["idade_inicio"] = longo["grupo_idade"].map(_inicio)
    return longo[["ano", "sexo", "grupo_idade", "idade_inicio", "populacao"]]


def tratar_genero() -> tuple[pd.DataFrame, pd.DataFrame]:
    g = ler_ibge(BRUTOS / "estatisticas_genero_2022.csv", ["Dimensão", "Indicador", "Homens", "Mulheres"])
    g.columns = [nome_coluna(c) for c in g.columns]
    g["homens"] = g["homens"].map(para_numero)
    g["mulheres"] = g["mulheres"].map(para_numero)
    g["diferenca_m_menos_h"] = (g["mulheres"] - g["homens"]).round(2)
    g["razao_m_h_pct"] = (g["mulheres"] / g["homens"] * 100).round(1)
    g["ano"] = g["ano"].astype(int)
    r = ler_ibge(BRUTOS / "estatisticas_genero_raca_2022.csv", ["Indicador", "Grupo", "Valor"])
    r.columns = [nome_coluna(c) for c in r.columns]
    r["valor"] = r["valor"].map(para_numero)
    r["ano"] = r["ano"].astype(int)
    return g, r


def executar() -> dict[str, pd.DataFrame]:
    g, r = tratar_genero()
    tabelas = {
        "mulheres_regiao_idade": tratar_regiao_idade(),
        "mulheres_cor_raca": tratar_cor_raca(),
        "projecao_sexo": tratar_projecao(),
        "indicadores_genero": g,
        "indicadores_genero_raca": r,
    }
    TRATADOS.mkdir(parents=True, exist_ok=True)
    for nome, df in tabelas.items():
        df.to_csv(TRATADOS / f"{nome}.csv", index=False, encoding="utf-8")
    with pd.ExcelWriter(TRATADOS / "base_mulheres_tratada.xlsx") as w:
        for nome, df in tabelas.items():
            df.to_excel(w, sheet_name=nome[:31], index=False)
    return tabelas


def carregar() -> dict[str, pd.DataFrame]:
    nomes = ["mulheres_regiao_idade", "mulheres_cor_raca", "projecao_sexo", "indicadores_genero",
             "indicadores_genero_raca"]
    if not all((TRATADOS / f"{n}.csv").exists() for n in nomes):
        return executar()
    return {n: pd.read_csv(TRATADOS / f"{n}.csv") for n in nomes}


if __name__ == "__main__":
    for nome, df in executar().items():
        print(f"{nome}: {df.shape[0]} linhas x {df.shape[1]} colunas")
