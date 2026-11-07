
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import streamlit as st  # noqa: E402

from core import ui  # noqa: E402
from individuais.gustavo_henrique_mulheres.secao import render  # noqa: E402

st.set_page_config(page_title="4 · Mulheres · Gustavo Henrique", page_icon="♀️", layout="wide")
ui.aplicar_estilo()
st.sidebar.title("♀️ Lupa Dados")
st.sidebar.caption("Entrega individual · **Gustavo Henrique**\n\nProjeto Integrador — Números que Falam")
render("gustavo")
