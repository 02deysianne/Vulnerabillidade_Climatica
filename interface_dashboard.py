"""Componentes visuais. Não lê dados nem modifica figuras ou resultados."""
import streamlit as st
from html import escape


def aplicar_estilo():
    st.session_state['_cartao_visual'] = 0
    st.html('''
    <style>
      :root { --painel-bg: #F5F6F8; --painel-texto: #151A23; --painel-cinza: #647080; }
      .stApp { background: var(--painel-bg); color: var(--painel-texto);
        font-family: Inter, "Segoe UI", Arial, sans-serif; }
      [data-testid="stHeader"] { background: rgba(245,246,248,.96); }
      .block-container { padding-top: 4.5rem; padding-bottom: 3rem; max-width: 1600px; }
      .painel-cabecalho { margin: 0 0 1.75rem; }
      .painel-cabecalho h1 { font-size: clamp(1.65rem, 2.5vw, 2.3rem); line-height: 1.25;
        font-weight: 750; letter-spacing: -.035em; color: #151A23; margin: 0 0 .6rem; padding: 0; }
      .painel-cabecalho p { font-size: .96rem; line-height: 1.6; color: #647080; margin: 0; }
      [data-testid="stColumn"], [class*="st-key-cartao-visual-"] {
        background: #FFFFFF; border-radius: 14px; border-color: #E5E8ED;
        box-shadow: 0 2px 8px rgba(24,39,58,.035); }
      [data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #E5E8ED;
        border-radius: 12px; padding: 1rem 1.1rem; }
      [data-testid="stColumn"] [data-testid="stMetric"] {
        border: 0; padding: .25rem .1rem; box-shadow: none; }
      [data-testid="stMetricLabel"] { color: #647080; font-size: .82rem; font-weight: 500; }
      [data-testid="stMetricValue"] { color: #111827; font-size: clamp(1.65rem, 2.4vw, 2.1rem);
        line-height: 1.3; font-weight: 750; letter-spacing: -.025em; }
      [data-testid="stCaptionContainer"] { color: #647080; font-size: .82rem; line-height: 1.5; }
      h2 { font-size: 1.5rem; letter-spacing: -.025em; color: #151A23; }
      h3 { font-size: 1.15rem; letter-spacing: -.015em; color: #202938; }
      h2, h3, h4 { padding-top: .3rem; padding-bottom: .4rem; line-height: 1.35; }
      .painel-titulo-grafico { min-height: 3.5rem; display: flex; align-items: flex-start;
        margin: 0; font-size: 1.05rem; line-height: 1.45; font-weight: 650; color: #202938; }
      [data-testid="stTabs"] [role="tablist"] { gap: .5rem; padding: .25rem 0 .7rem;
        margin-bottom: 1.2rem; border-bottom: 1px solid #DFE4EA; }
      [data-testid="stTabs"] [role="tab"] { padding: .6rem .9rem; border-radius: 8px;
        color: #647080; font-weight: 550; height: auto; white-space: nowrap; }
      [data-testid="stTabs"] [role="tab"][aria-selected="true"] { background: #E9EFEB; color: #24553B; }
      [data-testid="stDataFrame"], [data-testid="stPlotlyChart"], [data-testid="stVegaLiteChart"] {
        border-radius: 8px; }
      [data-testid="stExpander"] { background: white; border-radius: 12px; }
      hr { border-color: #E1E5EB; margin: 1.25rem 0; }
      @media (max-width: 900px) {
        .block-container { padding-left: 1.25rem; padding-right: 1.25rem; }
        .painel-titulo-grafico { min-height: 4.6rem; }
        [data-testid="stTabs"] [role="tablist"] { gap: .1rem; }
        [data-testid="stTabs"] [role="tab"] { padding: .5rem .6rem; }
      }
      @media (max-width: 640px) { .painel-titulo-grafico { min-height: unset; margin-bottom: .6rem; } }
    </style>
    ''')
    st.html('''<header class="painel-cabecalho">
      <h1>Análise Climática e Produtividade Agrícola no Paraná</h1>
      <p>Indicadores globais, comportamento histórico, modelagem preditiva, simulação de cenários e vulnerabilidade regional.</p>
    </header>''')


def cartao():
    st.session_state['_cartao_visual'] += 1
    return st.container(border=True, key=f"cartao-visual-{st.session_state['_cartao_visual']}")


def titulo_grafico(texto):
    st.html(f'<h3 class="painel-titulo-grafico">{escape(texto)}</h3>')


def grafico_plotly(*args, **kwargs):
    with cartao():
        return st.plotly_chart(*args, **kwargs)


def grafico_altair(*args, **kwargs):
    with cartao():
        return st.altair_chart(*args, **kwargs)


def tabela(*args, **kwargs):
    with cartao():
        return st.dataframe(*args, **kwargs)
