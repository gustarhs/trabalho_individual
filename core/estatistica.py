

from __future__ import annotations

import math
from collections import Counter
from typing import Iterable, Sequence


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------
def _limpar(valores: Iterable) -> list[float]:
    """Converte para float e descarta valores ausentes (None/NaN)."""
    limpos = []
    for v in valores:
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isnan(f):
            continue
        limpos.append(f)
    return limpos


# ---------------------------------------------------------------------------
# Tendência central
# ---------------------------------------------------------------------------
def media(valores: Iterable) -> float:
    x = _limpar(valores)
    if not x:
        return float("nan")
    return sum(x) / len(x)


def media_ponderada(valores: Iterable, pesos: Iterable) -> float:
    pares = [(float(v), float(p)) for v, p in zip(valores, pesos)
             if v is not None and p is not None
             and not math.isnan(float(v)) and not math.isnan(float(p))]
    soma_pesos = sum(p for _, p in pares)
    if soma_pesos == 0:
        return float("nan")
    return sum(v * p for v, p in pares) / soma_pesos


def mediana(valores: Iterable) -> float:
    x = sorted(_limpar(valores))
    n = len(x)
    if n == 0:
        return float("nan")
    meio = n // 2
    if n % 2 == 1:
        return x[meio]
    return (x[meio - 1] + x[meio]) / 2


def moda(valores: Iterable, casas: int = 1) -> list[float]:
    x = [round(v, casas) for v in _limpar(valores)]
    if not x:
        return []
    contagem = Counter(x)
    maior = max(contagem.values())
    if maior == 1:
        return []  # amodal
    return sorted(v for v, c in contagem.items() if c == maior)


def percentil(valores: Iterable, p: float) -> float:
    x = sorted(_limpar(valores))
    n = len(x)
    if n == 0:
        return float("nan")
    if n == 1:
        return x[0]
    pos = (n - 1) * p
    baixo = math.floor(pos)
    cima = math.ceil(pos)
    fracao = pos - baixo
    return x[baixo] + (x[cima] - x[baixo]) * fracao


def quartis(valores: Iterable) -> tuple[float, float, float]:
    """Retorna (Q1, Q2, Q3)."""
    x = _limpar(valores)
    return percentil(x, 0.25), percentil(x, 0.50), percentil(x, 0.75)


def amplitude(valores: Iterable) -> float:
    x = _limpar(valores)
    return max(x) - min(x) if x else float("nan")


def variancia(valores: Iterable, amostral: bool = False) -> float:
    x = _limpar(valores)
    n = len(x)
    if n == 0 or (amostral and n < 2):
        return float("nan")
    m = sum(x) / n
    soma_quadrados = sum((v - m) ** 2 for v in x)
    return soma_quadrados / (n - 1 if amostral else n)


def desvio_padrao(valores: Iterable, amostral: bool = False) -> float:
    v = variancia(valores, amostral=amostral)
    return math.sqrt(v) if not math.isnan(v) else float("nan")


def coeficiente_variacao(valores: Iterable) -> float:
    m = media(valores)
    if not m:
        return float("nan")
    return desvio_padrao(valores) / m * 100


def outliers_iqr(valores: Sequence, rotulos: Sequence | None = None, k: float = 1.5) -> dict:
    pares = [(r, float(v)) for r, v in zip(rotulos if rotulos is not None else range(len(valores)), valores)
             if v is not None and not (isinstance(v, float) and math.isnan(v))]
    vals = [v for _, v in pares]
    q1, _, q3 = quartis(vals)
    iqr = q3 - q1
    lim_inf = q1 - k * iqr
    lim_sup = q3 + k * iqr
    lista = []
    for r, v in pares:
        if v < lim_inf:
            lista.append((r, v, "abaixo"))
        elif v > lim_sup:
            lista.append((r, v, "acima"))
    return {"limite_inferior": lim_inf, "limite_superior": lim_sup, "iqr": iqr, "outliers": lista}


def correlacao_pearson(x: Sequence, y: Sequence) -> float:
    pares = [(float(a), float(b)) for a, b in zip(x, y)
             if a is not None and b is not None
             and not math.isnan(float(a)) and not math.isnan(float(b))]
    n = len(pares)
    if n < 3:
        return float("nan")
    mx = sum(a for a, _ in pares) / n
    my = sum(b for _, b in pares) / n
    sxy = sum((a - mx) * (b - my) for a, b in pares)
    sxx = sum((a - mx) ** 2 for a, _ in pares)
    syy = sum((b - my) ** 2 for _, b in pares)
    if sxx == 0 or syy == 0:
        return float("nan")
    return sxy / math.sqrt(sxx * syy)

def media_agrupada(pontos_medios: Sequence[float], frequencias: Sequence[float]) -> float:
    return media_ponderada(pontos_medios, frequencias)


def mediana_agrupada(limites_inferiores: Sequence[float], amplitudes: Sequence[float],
                     frequencias: Sequence[float]) -> float:
    n = sum(frequencias)
    metade = n / 2
    acumulada = 0.0
    for L, h, f in zip(limites_inferiores, amplitudes, frequencias):
        if acumulada + f >= metade:
            return L + ((metade - acumulada) / f) * h
        acumulada += f
    return float("nan")


def quartil_agrupado(limites_inferiores, amplitudes, frequencias, p: float) -> float:
    n = sum(frequencias)
    alvo = n * p
    acumulada = 0.0
    for L, h, f in zip(limites_inferiores, amplitudes, frequencias):
        if acumulada + f >= alvo:
            return L + ((alvo - acumulada) / f) * h
        acumulada += f
    return float("nan")

def resumo(valores: Sequence, rotulos: Sequence | None = None, casas_moda: int = 1) -> dict:
    x = _limpar(valores)
    q1, q2, q3 = quartis(x)
    out = outliers_iqr(list(valores), rotulos, 1.5)
    return {
        "n": len(x),
        "media": media(x),
        "mediana": mediana(x),
        "moda": moda(x, casas_moda),
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "iqr": q3 - q1,
        "minimo": min(x) if x else float("nan"),
        "maximo": max(x) if x else float("nan"),
        "amplitude": amplitude(x),
        "variancia_pop": variancia(x),
        "desvio_pop": desvio_padrao(x),
        "variancia_amostral": variancia(x, amostral=True),
        "desvio_amostral": desvio_padrao(x, amostral=True),
        "cv": coeficiente_variacao(x),
        "limite_inferior": out["limite_inferior"],
        "limite_superior": out["limite_superior"],
        "outliers": out["outliers"],
    }


def impacto_outliers(valores: Sequence, rotulos: Sequence | None = None) -> dict:
    r = resumo(valores, rotulos)
    nomes_out = {o[0] for o in r["outliers"]}
    rot = list(rotulos) if rotulos is not None else list(range(len(valores)))
    sem = [v for nome, v in zip(rot, valores) if nome not in nomes_out]
    return {
        "media_com": r["media"],
        "media_sem": media(sem),
        "mediana_com": r["mediana"],
        "mediana_sem": mediana(sem),
        "variacao_media": r["media"] - media(sem) if sem else float("nan"),
        "variacao_mediana": r["mediana"] - mediana(sem) if sem else float("nan"),
        "n_outliers": len(nomes_out),
    }


def assimetria_texto(media_v: float, mediana_v: float, tolerancia: float = 0.01) -> str:
    if any(math.isnan(v) for v in (media_v, mediana_v)) or mediana_v == 0:
        return "indefinida"
    dif = (media_v - mediana_v) / abs(mediana_v)
    if dif > tolerancia:
        return "assimétrica à direita (média > mediana: valores altos puxam a média para cima)"
    if dif < -tolerancia:
        return "assimétrica à esquerda (média < mediana: valores baixos puxam a média para baixo)"
    return "aproximadamente simétrica (média ≈ mediana)"


def desvio_padrao_agrupado(pontos_medios: Sequence[float], frequencias: Sequence[float]) -> float:
    m = media_agrupada(pontos_medios, frequencias)
    n = sum(frequencias)
    return math.sqrt(sum(f * (x - m) ** 2 for x, f in zip(pontos_medios, frequencias)) / n)


def classe_modal(rotulos: Sequence[str], amplitudes: Sequence[float], frequencias: Sequence[float]) -> str:
    dens = [f / h for f, h in zip(frequencias, amplitudes)]
    return rotulos[dens.index(max(dens))]
