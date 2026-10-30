import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import altair as alt
import urllib.request
import json
from interface_dashboard import aplicar_estilo, grafico_plotly, grafico_altair, tabela, titulo_grafico
from dados_dashboard import ROOT, DATA, ler, mapa_municipal, historico, geojson_local

# 1. Configuração inicial da página
st.set_page_config(
    page_title="Dashboard Análise Climática",
    layout="wide"
)

# Identidade visual compartilhada pelas cinco abas.
aplicar_estilo()

# Função para carregar os polígonos do mapa do Paraná (GeoJSON)
@st.cache_data
def carregar_geojson():
    local = geojson_local()
    if local is not None:
        return local
    url = "https://raw.githubusercontent.com/tbrugz/geodata-br/master/geojson/geojs-41-mun.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            geo = json.loads(response.read().decode('utf-8'))
        for feature in geo['features']:
            feature['properties']['id'] = str(feature['properties']['id'])
        return geo
    except (OSError, ValueError):
        return None


def camada_base_parana(geo):
    """Todos os municípios do Paraná, com borda, para o estado aparecer inteiro."""
    ids, nomes = [], []
    for f in geo['features']:
        p = f['properties']
        ids.append(str(p['id']))
        nomes.append(p.get('name') or p.get('nome') or str(p['id']))
    return go.Choroplethmap(
        geojson=geo,
        locations=ids,
        featureidkey='properties.id',
        z=[0] * len(ids),
        colorscale=[[0, '#EEF0F3'], [1, '#EEF0F3']],
        showscale=False,
        marker=dict(opacity=1, line=dict(color='#8A94A3', width=0.6)),
        text=nomes,
        hovertemplate='%{text}<br>Sem dados de IVC para esta cultura<extra></extra>',
    )


# 4. Função unificada para carregar todos os dados
@st.cache_data
def carregar_dados():

    df_resumo_projeto = ler('dashboard_resumo_projeto')
    df_resumo_geral = ler('dashboard_resumo_geral_cultura')
    df_resumo_enso = ler('dashboard_resumo_enso_cultura')
    df_serie_anual = ler('dashboard_serie_anual_cultura')
    df_val_linear = ler('dashboard_validacao_linear_teste')
    df_val_logistica = ler('dashboard_validacao_logistica_teste')
    df_melhor_linear = ler('dashboard_melhor_modelo_linear')
    df_melhor_logistica = ler('dashboard_melhor_modelo_logistico')
    df_cenarios = ler('dashboard_cenarios_climaticos')
    df_ivc = ler('dashboard_indice_vulnerabilidade')

    return (df_resumo_projeto, df_resumo_geral, df_resumo_enso, df_serie_anual,
            df_val_linear, df_val_logistica, df_melhor_linear, df_melhor_logistica, df_cenarios, df_ivc)

# Unpacking dos dados carregados
(df_projeto, df_geral, df_enso, df_serie_anual,
 df_val_linear, df_val_logistica, df_melhor_linear, df_melhor_logistica, df_cenarios, df_ivc) = carregar_dados()

# CARREGA A VARIÁVEL DO MAPA
geojson_pr = carregar_geojson()

# ========================================================
# ESTRUTURAÇÃO DAS ABAS DO DASHBOARD (Agora com 5 abas)
# ========================================================
aba_geral, aba_historica, aba_modelos, aba_cenarios, aba_ivc = st.tabs([
    "Visão Geral",
    "Análise Histórica",
    "Modelos Estatísticos",
    "Cenários Climáticos",
    "Vulnerabilidade Municipal"
])

# --------------------------------------------------------
# ABA 1: VISÃO GERAL DO PROJETO
# --------------------------------------------------------
with aba_geral:
    total_registros = df_projeto['registros_modelagem'].iloc[0]
    qtd_municipios = df_projeto['qtd_municipios'].iloc[0]
    qtd_culturas = df_projeto['qtd_culturas'].iloc[0]
    ano_inicial = df_projeto['ano_inicial'].iloc[0]
    ano_final = df_projeto['ano_final'].iloc[0]
    periodo = f"{ano_inicial} - {ano_final}"

    col1, col2, col3, col4 = st.columns(4, border=True, gap="medium", vertical_alignment="bottom")
    with col1:
        st.metric(label="Registros de modelagem", value=f"{total_registros:,}".replace(',', '.'))
    with col2:
        st.metric(label="Municípios analisados", value=qtd_municipios)
    with col3:
        st.metric(label="Grupos agrícolas", value=qtd_culturas)
    with col4:
        st.metric(label="Período analisado", value=periodo)

    st.caption(f"Base municipal: {int(df_projeto.registros_base_original.iloc[0]):,} registros")
    st.markdown("---")

    col_graf1, col_graf2 = st.columns(2, border=True, gap="medium", vertical_alignment="bottom")

    with col_graf1:
        st.html('<h3 class="painel-titulo-grafico">Produtividade média por cultura</h3>')
        fig_geral = px.bar(
            df_geral,
            x='cultura',
            y='media_rendimento',
            color='cultura',
            text_auto='.0f',
            labels={'cultura': 'Cultura', 'media_rendimento': 'Rendimento médio (kg/ha)'},
            template='plotly_white'
        )
        fig_geral.update_traces(textposition='outside')
        fig_geral.update_layout(showlegend=False, height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_geral, width="stretch")

    with col_graf2:
        st.html('<h3 class="painel-titulo-grafico">Rendimento médio por fase climática (ENSO)</h3>')
        fig_enso = px.bar(
            df_enso,
            x='cultura',
            y='media_rendimento',
            color='fase_enso',
            barmode='group',
            text_auto='.0f',
            labels={'cultura': 'Cultura', 'media_rendimento': 'Rendimento médio (kg/ha)', 'fase_enso': 'Fase'},
            template='plotly_white',
            color_discrete_map={'El Nino': '#ef553b', 'La Nina': '#636efa', 'Neutro': '#00cc96'}
        )
        fig_enso.update_traces(textposition='outside')
        fig_enso.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_enso, width="stretch")

    # --------------------------------------------------------
    # MAPA FINAL DA ABA 1: MUNICÍPIOS ANALISADOS E PRODUTORES
    # --------------------------------------------------------
    st.markdown("---")
    st.subheader("Mapa dos municípios analisados e produtores por cultura")
    st.markdown("Verde: produtores do grupo; Azul: produção em outros grupos; Vermelho: sem produção registrada. Situação no período completo, sem somar municípios repetidos.")
    df_base_mapa = ler('dashboard_mapa_municipal')
    grupos_mapa = sorted(df_base_mapa.cultura.unique())
    filtro_mapa = st.radio("Filtro do mapa:", ['Todas as cidades analisadas'] + grupos_mapa,
                          horizontal=True, key='filtro_mapa_aba_geral')
    grupo_mapa = None if filtro_mapa == 'Todas as cidades analisadas' else filtro_mapa
    df_municipios_mapa = mapa_municipal(df_base_mapa, grupo_mapa)
    titulo_mapa = 'Municípios analisados' if grupo_mapa is None else f'Produção de {grupo_mapa}'
    status_produtor = 'Com produção' if grupo_mapa is None else f'Produziu {grupo_mapa}'
    cor_mapa = {status_produtor: '#2e7d32', f'Não produziu {grupo_mapa}': '#1976d2',
                'Sem produção registrada': '#d32f2f', 'Dados de produção incompletos': '#757575'}
    ordem_categorias_mapa = list(cor_mapa)
    contagens = df_municipios_mapa.situacao_mapa.value_counts()
    cards = st.columns(len(contagens) + 1, border=True, gap="medium", vertical_alignment="bottom")
    cards[0].metric('Municípios no mapa', len(df_municipios_mapa))
    for card, (status, quantidade) in zip(cards[1:], contagens.items()):
        card.metric(status, int(quantidade))

    if geojson_pr:
        fig_mapa_aba1 = px.choropleth_map(
            df_municipios_mapa,
            geojson=geojson_pr,
            locations="codigo_municipio_str",
            featureidkey="properties.id",
            color="situacao_mapa",
            color_discrete_map=cor_mapa,
            category_orders={"situacao_mapa": ordem_categorias_mapa},
            map_style="carto-positron",
            zoom=5,
            center={"lat": -24.5, "lon": -51.0},
            opacity=0.85,
            hover_name="municipio",
            hover_data={
                "codigo_municipio_str": False,
                "situacao_mapa": True
            },
            labels={
                "situacao_mapa": "Situação",
                "municipio": "Município"
            }
        )

        fig_mapa_aba1.update_layout(
            title=titulo_mapa,
            height=560,
            margin={"r": 0, "t": 45, "l": 0, "b": 0},
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )

        grafico_plotly(fig_mapa_aba1, width="stretch")

    else:
        st.warning(
            "Não foi possível carregar o GeoJSON dos municípios do Paraná. "
            "Verifique sua conexão com a internet ou a função carregar_geojson()."
        )

    with st.expander("Ver lista de municípios e situação no mapa"):
        df_lista_municipios = (
            df_municipios_mapa[["codigo_municipio", "municipio", "situacao_mapa"]]
            .sort_values(["situacao_mapa", "municipio"])
            .copy()
        )

        df_lista_municipios.columns = [
            "Código do Município",
            "Município",
            "Situação"
        ]

        tabela(
            df_lista_municipios,
            width="stretch",
            hide_index=True
        )


    st.subheader('Comparação das duas safras do milho')
    comparacao = df_geral[df_geral.cultura.str.startswith('Milho ')][['cultura', 'media_rendimento', 'qtd_municipios', 'qtd_registros']]
    tabela(comparacao.rename(columns={'media_rendimento': 'Média municipal (kg/ha)', 'qtd_municipios': 'Municípios produtores', 'qtd_registros': 'Registros de modelagem'}), hide_index=True)
    milho_hist = df_serie_anual[df_serie_anual.cultura.str.startswith('Milho ')]
    grafico_plotly(px.line(milho_hist, x='ano', y='media_rendimento', color='cultura', markers=True,
                            labels={'media_rendimento': 'Média municipal (kg/ha)', 'ano': 'Ano', 'cultura': 'Grupo'}, template='plotly_white'), width='stretch')
    milho_clima = ler('dashboard_milho_serie_anual_clima_safras')
    grafico_plotly(px.line(milho_clima, x='ano', y='chuva_ciclo_media', color='cultura', markers=True,
                            labels={'chuva_ciclo_media': 'Precipitação média do ciclo (mm)', 'ano': 'Ano', 'cultura': 'Grupo'}, template='plotly_white'), width='stretch')
    st.caption('Os ciclos têm janelas distintas; o CSV não contém clima da 1ª safra de 2010. Não se substitui clima do ciclo por clima anual.')
    tabela(ler('dashboard_ivc_resumo_grupos').query("cultura.str.startswith('Milho ')", engine='python'), hide_index=True)
    st.caption('IVCM normalizado por grupo: comparação descritiva das posições relativas, sem equivalência absoluta entre safras.')

# --------------------------------------------------------
# ABA 2: ANÁLISE HISTÓRICA POR CULTURA
# --------------------------------------------------------
with aba_historica:
    st.header("Análise histórica e climática anual")
    st.markdown("Acompanhe a evolução da produtividade agrícola e compare com os volumes de chuva e o índice climático (ONI) ao longo do tempo.")

    culturas_disponiveis = df_serie_anual['cultura'].unique().tolist()
    cultura_selecionada = st.selectbox("Selecione a Cultura para análise temporal:", culturas_disponiveis)

    df_filtrado, rotulo_chuva, rotulo_oni = historico(cultura_selecionada)
    st.caption(f"Rendimento: média municipal simples (kg/ha). {rotulo_chuva}; {rotulo_oni}.")
    if df_filtrado[['media_chuva', 'media_oni']].isna().any().any():
        st.warning("Há anos sem clima do ciclo disponível, incluindo a 1ª safra de 2010. As lacunas são preservadas; não são preenchidas com clima anual.")

    st.markdown("---")

    st.subheader(f"Evolução do rendimento médio - {cultura_selecionada}")
    grafico_rendimento = alt.Chart(df_filtrado).mark_line(point=True, color='#2e7b32', strokeWidth=3).encode(
        x=alt.X('ano:O', title='Ano', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('media_rendimento:Q', title='Rendimento Médio (kg/ha)', scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip('ano:O', title='Ano'),
            alt.Tooltip('media_rendimento:Q', title='Rendimento (kg/ha)', format='.2f')
        ]
    ).properties(height=300).interactive()

    grafico_altair(grafico_rendimento, width="stretch")

    st.markdown(" Variáveis climáticas isoladas")
    col1, col2 = st.columns(2, border=True, gap="medium", vertical_alignment="bottom")

    with col1:
        titulo_grafico(rotulo_chuva)
        grafico_chuva = alt.Chart(df_filtrado).mark_line(point=True, color='#0288d1', strokeWidth=2).encode(
            x=alt.X('ano:O', title='Ano'),
            y=alt.Y('media_chuva:Q', title=rotulo_chuva, scale=alt.Scale(zero=False)),
            tooltip=[
                alt.Tooltip('ano:O', title='Ano'),
                alt.Tooltip('media_chuva:Q', title='Chuva (mm)', format='.2f')
            ]
        ).properties(height=200).interactive()
        st.altair_chart(grafico_chuva, width="stretch")

    with col2:
        titulo_grafico(rotulo_oni)
        grafico_oni = alt.Chart(df_filtrado).mark_line(point=True, color='#d32f2f', strokeWidth=2).encode(
            x=alt.X('ano:O', title='Ano'),
            y=alt.Y('media_oni:Q', title=rotulo_oni),
            tooltip=[
                alt.Tooltip('ano:O', title='Ano'),
                alt.Tooltip('media_oni:Q', title='ONI', format='.2f')
            ]
        ).properties(height=200).interactive()
        st.altair_chart(grafico_oni, width="stretch")

    st.markdown("---")
    st.subheader("Análise de sobreposição temporal (escala de tendência relativa)")
    st.markdown(
        "Como as três variáveis possuem unidades distintas, as linhas abaixo foram **normalizadas individualmente de 0 a 1** "
        "para permitir a comparação visual direta de picos e vales e correlação de tendências."
    )

    df_norm = df_filtrado.copy()
    variaveis_alvo = ['media_rendimento', 'media_chuva', 'media_oni']

    for col in variaveis_alvo:
        min_val = df_norm[col].min()
        max_val = df_norm[col].max()
        df_norm[col + '_norm'] = (df_norm[col] - min_val) / (max_val - min_val) if max_val != min_val else 0.5

    df_long = df_norm.melt(
        id_vars=['ano'],
        value_vars=[c + '_norm' for c in variaveis_alvo],
        var_name='Variavel_Original',
        value_name='Valor_Normalizado'
    )

    mapeamento_legendas = {
        'media_rendimento_norm': 'Rendimento Médio',
        'media_chuva_norm': rotulo_chuva,
        'media_oni_norm': rotulo_oni
    }
    df_long['Métrica'] = df_long['Variavel_Original'].map(mapeamento_legendas)

    grafico_sobreposto = alt.Chart(df_long).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X('ano:O', title='Ano'),
        y=alt.Y('Valor_Normalizado:Q', title='Tendência Relativa (0 a 1)', scale=alt.Scale(zero=False)),
        color=alt.Color(
            'Métrica:N',
            scale=alt.Scale(
                domain=['Rendimento Médio', rotulo_chuva, rotulo_oni],
                range=['#2e7b32', '#0288d1', '#d32f2f']
            ),
            title="Métrica Analisada"
        ),
        tooltip=[
            alt.Tooltip('ano:O', title='Ano'),
            alt.Tooltip('Métrica:N', title='Variável'),
            alt.Tooltip('Valor_Normalizado:Q', title='Valor Relativo', format='.2f')
        ]
    ).properties(height=350).interactive()

    grafico_altair(grafico_sobreposto, width="stretch")


# --------------------------------------------------------
# ABA 3: DESEMPENHO E VALIDAÇÃO DOS MODELOS
# --------------------------------------------------------
with aba_modelos:
    st.header("Avaliação de modelos estatísticos")
    st.markdown(
        "Esta seção demonstra o comportamento real dos modelos gerados durante a fase de validação temporal "
        "(dados de teste) para entender a precisão das estimativas e a facilidade de antecipar cenários."
    )

    # --------------------------------------------------------
    # FUNÇÕES DE FORMATAÇÃO CONDICIONAL DAS TABELAS
    # --------------------------------------------------------
    def destacar_melhor_pior_coluna(coluna, maior_melhor=True):
        """
        Aplica cores em uma coluna numérica:
        - verde para o melhor valor
        - vermelho para o pior valor
        - amarelo claro para valores intermediários

        maior_melhor=True  -> maior valor é melhor
        maior_melhor=False -> menor valor é melhor
        """
        valores = pd.to_numeric(coluna, errors="coerce")

        estilos = [""] * len(coluna)

        if valores.notna().sum() < 2:
            return estilos

        melhor = valores.max() if maior_melhor else valores.min()
        pior = valores.min() if maior_melhor else valores.max()

        if melhor == pior:
            return estilos

        for i, valor in enumerate(valores):
            if pd.isna(valor):
                estilos[i] = ""
            elif valor == melhor:
                estilos[i] = (
                    "background-color: #c8e6c9; "
                    "color: #1b5e20; "
                    "font-weight: 700;"
                )
            elif valor == pior:
                estilos[i] = (
                    "background-color: #ffcdd2; "
                    "color: #b71c1c; "
                    "font-weight: 700;"
                )
            else:
                estilos[i] = (
                    "background-color: #fff9c4; "
                    "color: #5d4037;"
                )

        return estilos

    # --------------------------------------------------------
    # SEÇÃO 1: RESUMO DIRETO DOS VENCEDORES
    # --------------------------------------------------------
    st.markdown("### Modelos vencedores por cultura")
    st.markdown(
        "Identificação de qual configuração matemática obteve a melhor performance. "
        )

    col_mod1, col_mod2 = st.columns(2, border=True, gap="medium", vertical_alignment="bottom")

    with col_mod1:
        st.subheader("Modelos lineares")
        st.caption(
            "Objetivo: estimar a produtividade em kg/ha com base nas variáveis climáticas. "
            "No MAE, quanto menor o erro, melhor."
        )

        df_lin_resumo = df_melhor_linear[
            ["cultura", "modelo", "r2_treino", "mae_teste"]
        ].copy()

        df_lin_resumo.columns = [
            "Cultura",
            "Abordagem Vencedora",
            "R² (Explicação no Treino)",
            "Erro Médio - MAE (kg/ha)"
        ]

        estilo_lin_resumo = (
            df_lin_resumo
            .style
            .format({
                "R² (Explicação no Treino)": "{:.4f}",
                "Erro Médio - MAE (kg/ha)": "{:,.1f}"
            })

        )

        st.dataframe(
            estilo_lin_resumo,
            width="stretch",
            hide_index=True
        )

    with col_mod2:
        st.subheader("Modelos logísticos")
        st.caption(
            "Objetivo: classificar o ano agrícola entre patamar alto ou baixo de rendimento. "
            "Quanto maiores as taxas, melhor."
        )

        df_log_resumo = df_melhor_logistica[
            ["cultura", "modelo", "taxa_acerto_teste", "sensibilidade_teste"]
        ].copy()

        df_log_resumo.columns = [
            "Cultura",
            "Abordagem Vencedora",
            "Taxa de Acerto",
            "Sensibilidade"
        ]

        estilo_log_resumo = (
            df_log_resumo
            .style
            .format({
                "Taxa de Acerto": "{:.1%}",
                "Sensibilidade": "{:.1%}"
            })

        )

        st.dataframe(
            estilo_log_resumo,
            width="stretch",
            hide_index=True
        )

    st.markdown("---")

    # --------------------------------------------------------
    # SEÇÃO 2: COMPARATIVO VISUAL JÁ EXISTENTE
    # --------------------------------------------------------
    st.markdown("### Qual cultura foi mais fácil ou difícil de classificar?")
    st.markdown(
        "O gráfico abaixo exibe a **taxa de acerto final** de todos os modelos de classificação testados. "
        "Culturas com barras consistentemente mais altas mostram-se mais previsíveis e fáceis de classificar "
        "com variáveis climáticas, enquanto taxas próximas a 50% indicam maior dificuldade de modelagem prática."
    )

    fig_comparativo_acerto = px.bar(
        df_val_logistica,
        x="cultura",
        y="taxa_acerto_teste",
        color="modelo",
        barmode="group",
        text_auto=".1%",
        labels={
            "cultura": "Cultura Agrícola",
            "taxa_acerto_teste": "Taxa de Acerto (Dados de Teste)",
            "modelo": "Estratégia do Modelo"
        },
        template="plotly_white",
        color_discrete_sequence=px.colors.qualitative.Safe
    )

    fig_comparativo_acerto.update_layout(
        height=380,
        margin=dict(l=10, r=10, t=20, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )

    fig_comparativo_acerto.update_yaxes(tickformat=".0%")

    grafico_plotly(fig_comparativo_acerto, width="stretch")

    st.markdown("---")

    # --------------------------------------------------------
    # SEÇÃO 3: DETALHAMENTO DE PERFORMANCE POR CULTURA
    # --------------------------------------------------------
    st.markdown("### Histórico de validação por cultura")
    st.markdown(
        "Selecione uma cultura para abrir a tabela detalhada de erros e acertos de cada algoritmo testado. "
        "As cores destacam automaticamente o melhor e o pior desempenho em cada métrica."
    )

    culturas_disponiveis = sorted(df_val_linear["cultura"].unique().tolist())

    cultura_modelo_sel = st.selectbox(
        "Filtrar auditoria por:",
        culturas_disponiveis,
        key="sb_aba_modelos"
    )

    col_tab1, col_tab2 = st.columns(2, border=True, gap="medium", vertical_alignment="bottom")

    st.caption(
        "Legenda das tabelas: verde = melhor desempenho; vermelho = pior desempenho; "
        "amarelo = desempenho intermediário."
    )

    with col_tab1:
        titulo_grafico(f"Métricas dos Modelos Lineares ({cultura_modelo_sel})")

        df_lin_filtrado = df_val_linear[
            df_val_linear["cultura"] == cultura_modelo_sel
        ][
            ["modelo", "r2_treino", "mae_teste", "rmse_teste"]
        ].copy()

        df_lin_filtrado.columns = [
            "Modelo",
            "R² Treino",
            "Erro MAE (kg/ha)",
            "Erro RMSE (kg/ha)"
        ]

        estilo_lin_filtrado = (
            df_lin_filtrado
            .style
            .format({
                "R² Treino": "{:.4f}",
                "Erro MAE (kg/ha)": "{:,.1f}",
                "Erro RMSE (kg/ha)": "{:,.1f}"
            })
            .apply(
                destacar_melhor_pior_coluna,
                subset=["R² Treino"],
                maior_melhor=True
            )
            .apply(
                destacar_melhor_pior_coluna,
                subset=["Erro MAE (kg/ha)"],
                maior_melhor=False
            )
            .apply(
                destacar_melhor_pior_coluna,
                subset=["Erro RMSE (kg/ha)"],
                maior_melhor=False
            )
        )

        st.dataframe(
            estilo_lin_filtrado,
            width="stretch",
            hide_index=True
        )

    with col_tab2:
        titulo_grafico(f"Métricas dos Modelos Logísticos ({cultura_modelo_sel})")

        df_log_filtrado = df_val_logistica[
            df_val_logistica["cultura"] == cultura_modelo_sel
        ][
            [
                "modelo",
                "taxa_acerto_teste",
                "sensibilidade_teste",
                "especificidade_teste"
            ]
        ].copy()

        df_log_filtrado.columns = [
            "Modelo",
            "Taxa de Acerto",
            "Sensibilidade (Acerto Altas)",
            "Especificidade (Acerto Baixas)"
        ]

        estilo_log_filtrado = (
            df_log_filtrado
            .style
            .format({
                "Taxa de Acerto": "{:.1%}",
                "Sensibilidade (Acerto Altas)": "{:.1%}",
                "Especificidade (Acerto Baixas)": "{:.1%}"
            })
            .apply(
                destacar_melhor_pior_coluna,
                subset=["Taxa de Acerto"],
                maior_melhor=True
            )
            .apply(
                destacar_melhor_pior_coluna,
                subset=["Sensibilidade (Acerto Altas)"],
                maior_melhor=True
            )
            .apply(
                destacar_melhor_pior_coluna,
                subset=["Especificidade (Acerto Baixas)"],
                maior_melhor=True
            )
        )

        st.dataframe(
            estilo_log_filtrado,
            width="stretch",
            hide_index=True
        )

    st.info(
        "  **Guia rápido de interpretação:**\n"
        "- **R²:** indica quanto da variação do rendimento foi explicada no treino. Quanto maior, melhor.\n"
        "- **Erro médio (MAE):** indica, em média, por quantos kg/ha o modelo errou. Quanto menor, melhor.\n"
        "- **RMSE:** também mede erro, mas penaliza mais erros grandes. Quanto menor, melhor.\n"
        "- **Taxa de acerto:** porcentagem geral de acertos do modelo. Quanto maior, melhor.\n"
        "- **Sensibilidade:** mede o acerto em anos de safras altas. Quanto maior, melhor.\n"
        "- **Especificidade:** mede o acerto em anos de safras baixas. Quanto maior, melhor."
    )

# --------------------------------------------------------
# ABA 4: CENÁRIOS CLIMÁTICOS
# --------------------------------------------------------
with aba_cenarios:
    st.header("Simulações condicionais de cenários climáticos")
    st.markdown("Esta seção projeta o desempenho esperado de das culturas com base nas regressões desenvolvidas. Foram cruzados três níveis históricos de preciptação (baixa, média, alta) com três fases do ENSO (La niña/Negativo, Neutro, El Niño/Positivo), estruturando 9 cenários prováveis para a agricultura no Paraná.")

    culturas_cenarios = df_cenarios['cultura'].unique().tolist()
    cultura_cenario_sel = st.selectbox("Selecione a Cultura para simular as projeções:", culturas_cenarios, key="sb_cenarios")

    df_cenario_filtrado = df_cenarios[df_cenarios['cultura'] == cultura_cenario_sel].copy()

    st.markdown("---")
    st.subheader(f"Visão tabular dos 9 Cenários - {cultura_cenario_sel}")
    st.markdown("A tabela apresenta formatação condicional: tons mais intensos indicam valores mais favoráveis ao rendimento agrícola.")

    # Preparação da tabela formatada e ordenada do maior para o menor rendimento
    df_cenario_exibicao = df_cenario_filtrado[['cenario_nome', 'faixa_chuva', 'faixa_oni', 'rendimento_previsto', 'prob_rendimento_alto']].copy()
    df_cenario_exibicao.columns = ['Cenário', 'Nível de Chuva', 'Fase ENSO', 'Rendimento Estimado (kg/ha)', 'Prob. de Safra Alta']
    df_cenario_exibicao = df_cenario_exibicao.sort_values(by='Rendimento Estimado (kg/ha)', ascending=False)

    tabela(
        df_cenario_exibicao.style.format({
            'Rendimento Estimado (kg/ha)': '{:,.1f}',
            'Prob. de Safra Alta': '{:.1%}'
        }).background_gradient(subset=['Rendimento Estimado (kg/ha)'], cmap='Greens')
          .background_gradient(subset=['Prob. de Safra Alta'], cmap='Blues'),
        width="stretch",
        hide_index=True
    )

    st.markdown("---")
    st.subheader("Análise gráfica dos resultados simulados")

    col_cen1, col_cen2 = st.columns(2, border=True, gap="medium", vertical_alignment="bottom")

    with col_cen1:
        titulo_grafico("Rendimento previsto por cenário (modelo linear)")
        # Barras ordenadas do menor para o maior para que o maior valor fique no topo no gráfico horizontal
        fig_rend = px.bar(
            df_cenario_filtrado.sort_values('rendimento_previsto', ascending=True),
            x='rendimento_previsto',
            y='cenario_nome',
            orientation='h',
            text_auto='.0f',
            labels={'rendimento_previsto': 'Rendimento estimado (kg/ha)', 'cenario_nome': 'Cenário Simulado'},
            color='rendimento_previsto',
            color_continuous_scale='Greens'
        )
        fig_rend.update_layout(showlegend=False, height=420, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_rend, width="stretch")

    with col_cen2:
        titulo_grafico("Probabilidade de ocorrência de safra alta (modelo logístico)")
        fig_prob = px.bar(
            df_cenario_filtrado.sort_values('prob_rendimento_alto', ascending=True),
            x='prob_rendimento_alto',
            y='cenario_nome',
            orientation='h',
            text_auto='.1%',
            labels={'prob_rendimento_alto': 'Probabilidade de safra alta', 'cenario_nome': 'Cenário Simulado'},
            color='prob_rendimento_alto',
            color_continuous_scale='Blues'
        )
        fig_prob.update_layout(showlegend=False, height=420, margin=dict(l=10, r=10, t=10, b=10))
        # Formatar a base do eixo x para exibir percentagem corretamente
        fig_prob.layout.xaxis.tickformat = ',.0%'
        st.plotly_chart(fig_prob, width="stretch")

    if cultura_cenario_sel.startswith('Milho '):
        st.info('Os modelos deste CSV de cenários podem diferir dos vencedores do CSV de validação sazonal, especialmente para a 2ª safra. Mantêm-se as previsões e a identificação originais de cada arquivo.')
        st.subheader('Cenários adicionais do milho por ciclo agrícola')
        sazonal = ler('dashboard_milho_cenarios_safras')
        sazonal = sazonal[sazonal.cultura.eq(cultura_cenario_sel)]
        st.caption('Cenários fornecidos separadamente dos modelos anuais. Confira as variáveis e o modelo em cada linha; não se reestimam previsões.')
        tabela(sazonal.style.format(precision=3, na_rep='Não fornecido'), hide_index=True)
        grafico_plotly(px.bar(sazonal, x='cenario_nome', y='rendimento_previsto', labels={'rendimento_previsto': 'Rendimento previsto (kg/ha)', 'cenario_nome': 'Cenário do ciclo'}, template='plotly_white'), width='stretch')
        fig_sazonal = px.bar(sazonal, x='cenario_nome', y='prob_rendimento_alto', labels={'prob_rendimento_alto': 'Probabilidade de rendimento alto', 'cenario_nome': 'Cenário do ciclo'}, template='plotly_white')
        fig_sazonal.update_yaxes(tickformat='.0%')
        grafico_plotly(fig_sazonal, width='stretch')

# --------------------------------------------------------
# ABA 5: VULNERABILIDADE MUNICIPAL (IVC)
# --------------------------------------------------------
with aba_ivc:
    st.header("Índice de vulnerabilidade climática municipal (IVCM)")
    st.markdown(
        "O IVCM é uma métrica de 0 a 100 que resume a vulnerabilidade da produção agrícola às variações climáticas. Sua composição considera quatro pilares: Variabilidade Produtiva, Variabilidade da Chuva, Sensibilidade à Chuva e Sensibilidade ao índice ENSO (ONI)."
    )


    culturas_ivc = df_ivc['cultura'].unique().tolist()
    cultura_ivc_sel = st.selectbox("Selecione a cultura para análise de vulnerabilidade:", culturas_ivc, key="sb_ivc")

    df_ivc_filtrado = df_ivc[df_ivc['cultura'] == cultura_ivc_sel].copy()

    # É preciso converter o código do município para string para o mapa Plotly funcionar com o GeoJSON
    df_ivc_filtrado['codigo_municipio_str'] = df_ivc_filtrado['codigo_municipio'].astype(str)

    # --------------------------------------------------------
    # RESUMO EXECUTIVO DA VULNERABILIDADE - CULTURA SELECIONADA
    # --------------------------------------------------------
    st.markdown("---")
    st.subheader(f"Resumo de vulnerabilidade - {cultura_ivc_sel}")

    ivc_medio = df_ivc_filtrado["ivc"].mean()
    ivc_maximo = df_ivc_filtrado["ivc"].max()
    ivc_minimo = df_ivc_filtrado["ivc"].min()

    municipio_mais_vulneravel = df_ivc_filtrado.loc[
        df_ivc_filtrado["ivc"].idxmax(),
        "municipio"
    ]

    municipio_menos_vulneravel = df_ivc_filtrado.loc[
        df_ivc_filtrado["ivc"].idxmin(),
        "municipio"
    ]

    qtd_municipios_ivc = df_ivc_filtrado["municipio"].nunique()

    qtd_alta_muito_alta = df_ivc_filtrado[
        df_ivc_filtrado["Classe_Vulnerabilidade"].isin(["Alta", "Muito alta"])
    ]["municipio"].nunique()

    perc_alta_muito_alta = (
        qtd_alta_muito_alta / qtd_municipios_ivc * 100
        if qtd_municipios_ivc > 0 else 0
    )

    col_ivc_card1, col_ivc_card2, col_ivc_card3, col_ivc_card4 = st.columns(4, border=True, gap="medium", vertical_alignment="bottom")

    with col_ivc_card1:
        st.metric("IVC médio", f"{ivc_medio:.1f}")

    with col_ivc_card2:
        st.metric("Maior IVC", f"{ivc_maximo:.1f}")
        st.caption(municipio_mais_vulneravel)

    with col_ivc_card3:
        st.metric("Menor IVC", f"{ivc_minimo:.1f}")
        st.caption(municipio_menos_vulneravel)

    with col_ivc_card4:
        st.metric(
            "Alta ou muito alta",
            qtd_alta_muito_alta,

        )
        st.caption(f"{perc_alta_muito_alta:.1f}% dos municípios")

    col_resumo_ivc1, col_resumo_ivc2 = st.columns(2, border=True, gap="medium", vertical_alignment="bottom")

    with col_resumo_ivc1:
        titulo_grafico("Distribuição por classe de vulnerabilidade")

        ordem_classes_ivc = ["Muito baixa", "Baixa", "Média", "Alta", "Muito alta"]

        df_classes_ivc = (
            df_ivc_filtrado
            .groupby("Classe_Vulnerabilidade", as_index=False)
            .agg(qtd_municipios=("municipio", "nunique"))
        )

        df_classes_ivc["Classe_Vulnerabilidade"] = pd.Categorical(
            df_classes_ivc["Classe_Vulnerabilidade"],
            categories=ordem_classes_ivc,
            ordered=True
        )

        df_classes_ivc = df_classes_ivc.sort_values("Classe_Vulnerabilidade")

        fig_classes_ivc = px.bar(
            df_classes_ivc,
            x="Classe_Vulnerabilidade",
            y="qtd_municipios",
            text_auto=True,
            labels={
                "Classe_Vulnerabilidade": "Classe de Vulnerabilidade",
                "qtd_municipios": "Quantidade de Municípios"
            },
            color="Classe_Vulnerabilidade",
            color_discrete_map={
                "Muito baixa": "#2e7d32",
                "Baixa": "#66bb6a",
                "Média": "#fdd835",
                "Alta": "#fb8c00",
                "Muito alta": "#c62828"
            },
            template="plotly_white"
        )

        fig_classes_ivc.update_layout(
            showlegend=False,
            height=330,
            margin=dict(l=10, r=10, t=10, b=10)
        )

        st.plotly_chart(fig_classes_ivc, width="stretch")

    with col_resumo_ivc2:
        titulo_grafico("Componente médio da vulnerabilidade")

        df_componentes_ivc = pd.DataFrame({
            "Componente": [
                "Variação Produtiva",
                "Variação da Chuva",
                "Sensibilidade à Chuva",
                "Sensibilidade ao ENSO"
            ],
            "Score médio": [
                df_ivc_filtrado["score_variabilidade_prod"].mean(),
                df_ivc_filtrado["score_variabilidade_chuva"].mean(),
                df_ivc_filtrado["score_sensibilidade_chuva"].mean(),
                df_ivc_filtrado["score_sensibilidade_enso"].mean()
            ]
        })

        df_componentes_ivc = df_componentes_ivc.sort_values(
            "Score médio",
            ascending=True
        )

        fig_componentes_ivc = px.bar(
            df_componentes_ivc,
            x="Score médio",
            y="Componente",
            orientation="h",
            text_auto=".1f",
            range_x=[0, 100],
            labels={
                "Score médio": "Score Médio de Vulnerabilidade",
                "Componente": "Componente"
            },
            color="Score médio",
            color_continuous_scale="RdYlGn_r",
            range_color=(0, 100),
            template="plotly_white"
        )

        fig_componentes_ivc.update_layout(
            coloraxis_colorbar=dict(title="Score médio<br>(0 a 100)"),
            showlegend=False,
            height=330,
            margin=dict(l=10, r=10, t=10, b=10)
        )

        st.plotly_chart(fig_componentes_ivc, width="stretch")

    st.markdown("---")

    # Mapa de risco (coluna 1) e ranking (coluna 2)
    col_ivc1, col_ivc2 = st.columns(2, border=True, gap="medium", vertical_alignment="bottom")

    with col_ivc1:
        titulo_grafico(f"Mapa de risco climático - {cultura_ivc_sel}")

        if geojson_pr:
            fig_mapa = px.choropleth_map(
                df_ivc_filtrado,
                geojson=geojson_pr,
                locations='codigo_municipio_str',
                featureidkey='properties.id',  # É assim que o GeoJSON armazena o código IBGE
                color='ivc',
                color_continuous_scale='RdYlGn_r',
                range_color=(0, 100),
                map_style="carto-positron",
                zoom=5,
                center={"lat": -24.5, "lon": -51.0},  # Centro do Paraná
                opacity=0.8,
                hover_name='municipio',
                hover_data={'codigo_municipio_str': False, 'Classe_Vulnerabilidade': True, 'ivc': ':.1f'},
                labels={'ivc': 'Score IVC', 'Classe_Vulnerabilidade': 'Classe'}
            )

            # Borda em todos os municípios que têm IVC
            fig_mapa.update_traces(marker_line_color='#6B7380', marker_line_width=0.6)

            # Camada base (estado inteiro) por baixo da camada colorida
            fig_mapa.add_trace(camada_base_parana(geojson_pr))
            fig_mapa.data = (fig_mapa.data[-1],) + fig_mapa.data[:-1]

            fig_mapa.update_layout(height=450, margin={"r": 0, "t": 0, "l": 0, "b": 0})
            st.plotly_chart(fig_mapa, width="stretch")
        else:
            st.warning("Não foi possível carregar as bordas do mapa via internet. Mas os dados seguem abaixo.")

    with col_ivc2:
        titulo_grafico("Top 15 Municípios mais vulneráveis (Maior IVC)")
        df_top15 = df_ivc_filtrado.nlargest(15, 'ivc').sort_values('ivc', ascending=True)

        fig_top_ivc = px.bar(
            df_top15,
            x='ivc',
            y='municipio',
            orientation='h',
            text_auto='.1f',
            labels={
                'ivc': 'Score IVC',
                'municipio': 'Município'
            },
            color='ivc',
            color_continuous_scale='RdYlGn_r',
            range_color=(0, 100)
        )
        fig_top_ivc.update_layout(showlegend=False, height=450, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_top_ivc, width="stretch")

    st.markdown("---")

    # Raio-X Municipal (Drill-down)
    st.subheader("Raio-X Municipal (análise dos scores)")
    st.markdown("Selecione um município específico para examinar os componentes associados à sua vulnerabilidade para a cultura selecionada:")

    municipios_disponiveis = sorted(df_ivc_filtrado['municipio'].unique().tolist())
    municipio_sel = st.selectbox("Selecione o Município:", municipios_disponiveis, key="sb_municipio")

    df_mun = df_ivc_filtrado[df_ivc_filtrado['municipio'] == municipio_sel].iloc[0]
    st.markdown(f"**Classe de vulnerabilidade:** {df_mun['Classe_Vulnerabilidade']} (IVC Geral: **{df_mun['ivc']:.1f}** / 100)")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4, border=True, gap="medium", vertical_alignment="bottom")
    col_m1.metric("Var. Produtiva", f"{df_mun['score_variabilidade_prod']:.1f}")
    col_m2.metric("Var. da Chuva", f"{df_mun['score_variabilidade_chuva']:.1f}")
    col_m3.metric("Sensib. à Chuva", f"{df_mun['score_sensibilidade_chuva']:.1f}")
    col_m4.metric("Sensib. ao ENSO", f"{df_mun['score_sensibilidade_enso']:.1f}")

    df_radar = pd.DataFrame({
        'Métrica': [
            'Variabilidade Produtiva (Inconstância na Colheita)',
            'Variabilidade da Chuva (Instabilidade do Regime)',
            'Sensibilidade à Chuva (Impacto do Volume)',
            'Sensibilidade ao ENSO (Impacto El Niño/La Niña)'
        ],
        'Score': [
            df_mun['score_variabilidade_prod'], df_mun['score_variabilidade_chuva'],
            df_mun['score_sensibilidade_chuva'], df_mun['score_sensibilidade_enso']
        ]
    })

    fig_mun = px.bar(
        df_radar.sort_values('Score', ascending=True),
        x='Score',
        y='Métrica',
        orientation='h',
        text_auto='.1f',
        range_x=[0, 100],
        labels={
            'Score': 'Nota de Vulnerabilidade (0 a 100)',
            'Métrica': 'Componente do Índice'
        },
        color='Score',
        color_continuous_scale='RdYlGn_r',
        range_color=(0, 100)
    )
    fig_mun.update_layout(coloraxis_colorbar=dict(title="Score<br>(0 a 100)"), showlegend=False, height=300, margin=dict(l=10, r=10, t=10, b=10))
    grafico_plotly(fig_mun, width="stretch")

    st.markdown("---")
    st.markdown(" Todos os Municípios")

    df_ivc_exibicao = df_ivc_filtrado[['municipio', 'Classe_Vulnerabilidade', 'ivc',
                                       'score_variabilidade_prod', 'score_variabilidade_chuva',
                                       'score_sensibilidade_chuva', 'score_sensibilidade_enso']].copy()

    df_ivc_exibicao.columns = ['Município', 'Classificação', 'IVC Geral',
                               'Score Variação Produtiva', 'Score Variação Chuva',
                               'Score Impacto Chuva', 'Score Impacto ENSO']

    df_ivc_exibicao = df_ivc_exibicao.sort_values(by='IVC Geral', ascending=False)

    tabela(
        df_ivc_exibicao.style.format({
            'IVC Geral': '{:.1f}', 'Score Variação Produtiva': '{:.1f}',
            'Score Variação Chuva': '{:.1f}', 'Score Impacto Chuva': '{:.1f}', 'Score Impacto ENSO': '{:.1f}'
        }).background_gradient(
            subset=[
                'IVC Geral',
                'Score Variação Produtiva',
                'Score Variação Chuva',
                'Score Impacto Chuva',
                'Score Impacto ENSO'
            ],
            cmap='RdYlGn_r',
            vmin=0,
            vmax=100
        ),
        width="stretch", hide_index=True
    )