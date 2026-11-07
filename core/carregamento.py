

from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

# Convenções de sinais do IBGE:
#   "-"   = dado numérico igual a zero não resultante de arredondamento -> 0
#   ".."  = não se aplica dado numérico                                  -> ausente (NaN)
#   "..." = dado numérico não disponível                                 -> ausente (NaN)
#   "X"   = dado numérico omitido para evitar identificação              -> ausente (NaN)
SIMBOLOS_ZERO = {"-", "–", "—"}
SIMBOLOS_AUSENTES = {"", "--", "...", "..", "x", "X", "nan", "NaN", "None", "s/d", "S/D"}

UFS = pd.DataFrame(
    [
        ("RO", "Rondônia", "Norte", 11), ("AC", "Acre", "Norte", 12), ("AM", "Amazonas", "Norte", 13),
        ("RR", "Roraima", "Norte", 14), ("PA", "Pará", "Norte", 15), ("AP", "Amapá", "Norte", 16),
        ("TO", "Tocantins", "Norte", 17), ("MA", "Maranhão", "Nordeste", 21), ("PI", "Piauí", "Nordeste", 22),
        ("CE", "Ceará", "Nordeste", 23), ("RN", "Rio Grande do Norte", "Nordeste", 24),
        ("PB", "Paraíba", "Nordeste", 25), ("PE", "Pernambuco", "Nordeste", 26), ("AL", "Alagoas", "Nordeste", 27),
        ("SE", "Sergipe", "Nordeste", 28), ("BA", "Bahia", "Nordeste", 29), ("MG", "Minas Gerais", "Sudeste", 31),
        ("ES", "Espírito Santo", "Sudeste", 32), ("RJ", "Rio de Janeiro", "Sudeste", 33),
        ("SP", "São Paulo", "Sudeste", 35), ("PR", "Paraná", "Sul", 41), ("SC", "Santa Catarina", "Sul", 42),
        ("RS", "Rio Grande do Sul", "Sul", 43), ("MS", "Mato Grosso do Sul", "Centro-Oeste", 50),
        ("MT", "Mato Grosso", "Centro-Oeste", 51), ("GO", "Goiás", "Centro-Oeste", 52),
        ("DF", "Distrito Federal", "Centro-Oeste", 53),
    ],
    columns=["sigla", "uf", "regiao", "codigo_ibge"],
)
REGIOES = ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]


# ---------------------------------------------------------------------------
# Normalização de texto e números
# ---------------------------------------------------------------------------
def sem_acentos(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c))


def nome_coluna(texto: str) -> str:
    t = sem_acentos(texto).strip().lower()
    t = re.sub(r"[^a-z0-9]+", "_", t)
    return t.strip("_")


def para_numero(valor, ponto_decimal: bool = False) -> float:
    if valor is None:
        return np.nan
    if isinstance(valor, (int, float, np.integer, np.floating)):
        return float(valor)
    s = str(valor).strip().replace(" ", " ")
    if s in SIMBOLOS_ZERO:
        return 0.0
    if s in SIMBOLOS_AUSENTES:
        return np.nan
    s = s.replace("%", "").replace("R$", "").strip()
    s = s.replace(" ", "")
    if "," in s:
        # vírgula decimal: pontos são separadores de milhar
        s = s.replace(".", "").replace(",", ".")
    elif not ponto_decimal and re.fullmatch(r"-?\d{1,3}(\.\d{3})+", s):
        # '89.695' ou '1.234.567' -> milhar com ponto
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return np.nan


def _coluna_usa_ponto_decimal(serie: pd.Series) -> bool:
    txt = serie.dropna().astype(str).str.strip()
    if txt.str.contains(",").any():
        return False
    return txt.str.fullmatch(r"-?\d+\.(\d{1,2}|\d{4,})").any()


def converter_colunas_numericas(df: pd.DataFrame, colunas) -> pd.DataFrame:
    df = df.copy()
    for c in colunas:
        if c in df.columns:
            ponto = _coluna_usa_ponto_decimal(df[c]) if df[c].dtype == object else False
            df[c] = df[c].map(lambda v: para_numero(v, ponto)).astype(float)
    return df


# ---------------------------------------------------------------------------
# Leitura de arquivos
# ---------------------------------------------------------------------------
def _ler_bytes(origem) -> tuple[bytes, str]:
    if isinstance(origem, (str, Path)):
        p = Path(origem)
        return p.read_bytes(), p.name
    nome = getattr(origem, "name", "arquivo")
    if hasattr(origem, "getvalue"):
        return origem.getvalue(), nome
    return origem.read(), nome


def ler_tabela_bruta(origem) -> pd.DataFrame:
    conteudo, nome = _ler_bytes(origem)
    nome_l = nome.lower()
    if nome_l.endswith((".xlsx", ".xlsm", ".xls")):
        return pd.read_excel(io.BytesIO(conteudo), header=None, dtype=str)

    texto = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            texto = conteudo.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        raise ValueError("Não foi possível decodificar o arquivo (use UTF-8 ou Latin-1).")

    amostra = "\n".join(texto.splitlines()[:30])
    try:
        sep = csv.Sniffer().sniff(amostra, delimiters=";,\t|").delimiter
    except csv.Error:
        sep = ";" if amostra.count(";") >= amostra.count(",") else ","

    linhas = list(csv.reader(io.StringIO(texto), delimiter=sep))
    largura = max((len(l) for l in linhas), default=0)
    linhas = [l + [""] * (largura - len(l)) for l in linhas]
    return pd.DataFrame(linhas, dtype=str)


def localizar_cabecalho(bruto: pd.DataFrame, palavras_chave: list[str], max_linhas: int = 25) -> int:
    chaves = [ch for ch in (nome_coluna(p) for p in palavras_chave) if ch]
    melhor, melhor_pontos = 0, (-1, -1)
    for i in range(min(max_linhas, len(bruto))):
        celulas = [nome_coluna(c) for c in bruto.iloc[i].fillna("") if str(c).strip() not in ("", "nan", "None")]
        # pontua por CÉLULA (um título longo conta só 1) e desempata pelo nº de células preenchidas
        casam = sum(any(ch == c or (len(ch) > 3 and ch in c) for ch in chaves) for c in celulas)
        anos = sum(bool(re.fullmatch(r"(19|20)\d{2}", c)) for c in celulas)
        pontos = (casam + (1 if anos >= 2 else 0), len(celulas))
        if pontos > melhor_pontos:
            melhor, melhor_pontos = i, pontos
    return melhor


def aplicar_cabecalho(bruto: pd.DataFrame, linha: int) -> pd.DataFrame:
    df = bruto.iloc[linha + 1:].copy()
    cab = [str(c).strip() if str(c).strip() not in ("", "nan", "None") else f"col_{i}"
           for i, c in enumerate(bruto.iloc[linha])]
    df.columns = cab
    # remove colunas totalmente vazias
    df = df.loc[:, ~(df.isna() | (df.astype(str).apply(lambda s: s.str.strip()) == "")).all()]
    return df.reset_index(drop=True)


def remover_rodape(df: pd.DataFrame) -> pd.DataFrame:
    primeira = df.columns[0]
    txt = df[primeira].astype(str).str.strip()
    mascara_rodape = txt.str.match(r"^(fonte|nota|notas|obs|elabora|\(\d\))", case=False)
    vazias = df.astype(str).apply(lambda s: s.str.strip().isin(["", "nan", "None"])).all(axis=1)
    return df[~mascara_rodape & ~vazias].reset_index(drop=True)


def anexar_uf(df: pd.DataFrame, coluna: str = "uf") -> pd.DataFrame:
    df = df.copy()
    mapa_nome = {sem_acentos(n).lower(): n for n in UFS["uf"]}
    mapa_sigla = dict(zip(UFS["sigla"], UFS["uf"]))

    def padroniza(v):
        s = str(v).strip()
        if s.upper() in mapa_sigla:
            return mapa_sigla[s.upper()]
        return mapa_nome.get(sem_acentos(s).lower(), s)

    df[coluna] = df[coluna].map(padroniza)
    df = df.drop(columns=[c for c in ("sigla", "regiao") if c in df.columns])
    return df.merge(UFS[["uf", "sigla", "regiao"]], left_on=coluna, right_on="uf", how="left")


@dataclass
class Esquema:
    nome: str
    obrigatorias: list[str]
    numericas: list[str]
    apelidos: dict[str, list[str]] = field(default_factory=dict)
    usa_uf: bool = False
    valor_formato_largo: str | None = None  # coluna que recebe os valores se o arquivo vier com anos nas colunas


@dataclass
class Relatorio:
    ok: bool
    mensagens: list[str]
    linhas_lidas: int = 0
    linhas_finais: int = 0


def _renomear_por_apelidos(df: pd.DataFrame, esquema: Esquema) -> pd.DataFrame:
    df = df.rename(columns={c: nome_coluna(c) for c in df.columns})
    renomear = {}
    for destino, apelidos in esquema.apelidos.items():
        if destino in df.columns:
            continue
        for a in apelidos:
            a_n = nome_coluna(a)
            if a_n in df.columns:
                renomear[a_n] = destino
                break
    return df.rename(columns=renomear)


def higienizar_upload(origem, esquema: Esquema) -> tuple[pd.DataFrame | None, Relatorio]:
    msgs: list[str] = []
    try:
        bruto = ler_tabela_bruta(origem)
    except Exception as e:  # noqa: BLE001
        return None, Relatorio(False, [f"Não foi possível ler o arquivo: {e}"])

    chaves = esquema.obrigatorias + [a for lst in esquema.apelidos.values() for a in lst]
    linha_cab = localizar_cabecalho(bruto, chaves)
    if linha_cab > 0:
        msgs.append(f"Cabeçalho encontrado na linha {linha_cab + 1} (linhas de título ignoradas).")
    df = aplicar_cabecalho(bruto, linha_cab)
    df = remover_rodape(df)
    lidas = len(df)
    df = _renomear_por_apelidos(df, esquema)

    # Formato largo (SIDRA costuma exportar UF nas linhas e ANOS nas colunas): converte para longo
    colunas_ano = [c for c in df.columns if re.fullmatch(r"(19|20)\d{2}", str(c))]
    if ("ano" in esquema.obrigatorias and "ano" not in df.columns and colunas_ano
            and esquema.valor_formato_largo):
        ids = [c for c in df.columns if c not in colunas_ano]
        df = df.melt(id_vars=ids, value_vars=colunas_ano, var_name="ano", value_name=esquema.valor_formato_largo)
        msgs.append(f"Arquivo em formato largo ({len(colunas_ano)} colunas de ano) convertido para formato longo.")

    # Colunas do tipo "populacao_2010", "populacao_2022": separa o ano do nome da variável
    com_ano = {c: re.search(r"_((19|20)\d{2})(?=_|$)", str(c)) for c in df.columns}
    com_ano = {c: m for c, m in com_ano.items() if m}
    if "ano" in esquema.obrigatorias and "ano" not in df.columns and com_ano:
        ids = [c for c in df.columns if c not in com_ano]
        partes = []
        for c, m in com_ano.items():
            var = (str(c)[:m.start()] + str(c)[m.end():]).strip("_")
            var = var if var in esquema.numericas else next((n for n in esquema.numericas if var.startswith(n)), var)
            partes.append(df[ids + [c]].rename(columns={c: var}).assign(ano=m.group(1)))
        df = pd.concat(partes).groupby(ids + ["ano"], as_index=False, sort=False).first()
        msgs.append(f"Colunas com o ano no nome ({', '.join(list(com_ano)[:4])}...) convertidas para formato longo.")

    faltando = [c for c in esquema.obrigatorias if c not in df.columns]
    if faltando:
        return None, Relatorio(
            False,
            msgs + [f"Colunas obrigatórias ausentes: {', '.join(faltando)}. "
                    f"Colunas encontradas: {', '.join(map(str, df.columns))}. "
                    "Baixe o modelo para ver o formato esperado."],
            lidas, 0,
        )

    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.strip()
    df = converter_colunas_numericas(df, esquema.numericas)

    if esquema.usa_uf and "uf" in df.columns:
        df = df[~df["uf"].str.lower().isin(["brasil", "total"])]
        df = anexar_uf(df, "uf")
        invalidas = df[df["sigla"].isna()]["uf"].unique().tolist()
        if invalidas:
            msgs.append(f"Linhas com UF não reconhecida foram descartadas: {', '.join(map(str, invalidas[:8]))}.")
            df = df[df["sigla"].notna()]

    antes = len(df)
    colunas_valor = [c for c in esquema.numericas if c in esquema.obrigatorias and c != "ano"]
    if colunas_valor:
        df = df.dropna(subset=colunas_valor, how="all")
    if len(df) < antes:
        msgs.append(f"{antes - len(df)} linha(s) sem valor numérico removida(s).")
    antes = len(df)
    df = df.drop_duplicates()
    if len(df) < antes:
        msgs.append(f"{antes - len(df)} linha(s) duplicada(s) removida(s).")

    if df.empty:
        return None, Relatorio(False, msgs + ["Após a limpeza, a base ficou vazia."], lidas, 0)

    if "ano" in df.columns:
        df["ano"] = df["ano"].astype(float).round().astype("Int64")

    msgs.append(f"Base '{esquema.nome}' carregada: {len(df)} linhas válidas (arquivo com {lidas} linhas de dados).")
    return df.reset_index(drop=True), Relatorio(True, msgs, lidas, len(df))


def para_excel_bytes(tabelas: dict[str, pd.DataFrame]) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as w:
        for nome, df in tabelas.items():
            df.to_excel(w, sheet_name=nome[:31], index=False)
    return buffer.getvalue()


def ler_ibge(origem, palavras_chave: list[str]) -> pd.DataFrame:
    bruto = ler_tabela_bruta(origem)
    linha = localizar_cabecalho(bruto, palavras_chave)
    return remover_rodape(aplicar_cabecalho(bruto, linha))


def wide_para_long(df: pd.DataFrame, id_cols: list[str], nome_var: str, nome_valor: str) -> pd.DataFrame:
    longo = df.melt(id_vars=id_cols, var_name=nome_var, value_name=nome_valor)
    longo[nome_valor] = longo[nome_valor].map(para_numero)
    return longo
