# Entrega individual — Gustavo Henrique

**Indicador demográfico:** 4 — Mulheres
**Projeto Integrador:** Números que Falam — Descobrindo o Brasil (Python & Matemática)
**Grupo:** Lupa Dados — Tema 6, Trabalho e Emprego (Arthur de Souza, Clara Lima e Gustavo Henrique)

## O que está nesta pasta (checklist do entregável individual)

| Item exigido | Arquivo |
|---|---|
| Código Python do módulo: ETL | `etl_mulheres.py` |
| Código Python do módulo: estatísticas | `secao.py` (usa as funções de `core/estatistica.py`) |
| Base IBGE bruta (como publicada) | `dados/brutos/` |
| Base IBGE tratada (CSV/XLSX limpo) | `dados/tratados/` — mulheres_regiao_idade.csv, mulheres_cor_raca.csv, projecao_sexo.csv, indicadores_genero.csv, indicadores_genero_raca.csv e base_mulheres_tratada.xlsx |
| Análise descritiva (interpretação dos dados) | `analise_descritiva.md` |
| Seção do dashboard (Streamlit) | `app.py` (versão individual) e `secao.py` (integrada ao painel do grupo) |

## Como executar

Na **raiz do repositório**:

```bash
pip install -r requirements.txt
python -m individuais.gustavo_henrique_mulheres.etl_mulheres      # (opcional) refaz o ETL: brutos -> tratados
streamlit run individuais/gustavo_henrique_mulheres/app.py
```

## O que o dashboard tem

- **Barra lateral:** filtros (região/UF, sexo, cor ou raça, faixa etária, ano, situação do domicílio — conforme o indicador) e bloco **📤 Upload de dados** (CSV/XLSX) com modelo para download.
- **KPIs** e gráficos interativos (barras comparativas, boxplot, histograma, linhas, mapa por UF).
- **Estatística:** média, mediana, moda, quartis, IQR, amplitude, variância, desvio padrão, coeficiente de variação e outliers (regra 1,5×IQR), com o efeito dos outliers na média × mediana.
- **Respostas** às perguntas de análise ligadas às personas (Ministério do Trabalho, Sebrae e Indústria).
- **Notícias** com links reais e imagens ilustrativas.
