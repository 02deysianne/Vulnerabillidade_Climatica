"""Leitura dos resultados finais; nenhuma estimativa científica é recalculada."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / '03_dados_finais'


def ler(nome):
    df = pd.read_csv(DATA / f'{nome}.csv', dtype={'codigo_municipio': 'string'})
    if 'cultura_dashboard' in df:
        df['cultura'] = df['cultura_dashboard']
    elif 'safra' in df and 'cultura' not in df:
        df['cultura'] = 'Milho ' + df['safra']
    if 'codigo_municipio' in df:
        df['codigo_municipio'] = df['codigo_municipio'].str.strip().str.replace(r'\.0$', '', regex=True)
    return df


def mapa_municipal(base, grupo=None):
    """Uma linha por IBGE; ausência de informação não equivale a zero."""
    municipios = base[['codigo_municipio', 'municipio']].drop_duplicates('codigo_municipio').copy()
    valores = base[['area_colhida', 'quantidade_produzida', 'rendimento_medio']]
    positivos = valores.gt(0).all(axis=1)
    produtores = set(base.loc[positivos, 'codigo_municipio'])
    selecionados = produtores if grupo is None else set(base.loc[positivos & base.cultura.eq(grupo), 'codigo_municipio'])
    incompletos = set(base.loc[valores.isna().any(axis=1), 'codigo_municipio']) - produtores
    def situacao(codigo):
        if codigo in selecionados:
            return 'Com produção' if grupo is None else f'Produziu {grupo}'
        if codigo in produtores:
            return f'Não produziu {grupo}'
        if codigo in incompletos:
            return 'Dados de produção incompletos'
        return 'Sem produção registrada'
    municipios['situacao_mapa'] = municipios.codigo_municipio.map(situacao)
    municipios['codigo_municipio_str'] = municipios.codigo_municipio
    return municipios.sort_values('municipio')


def historico(grupo):
    df = ler('dashboard_serie_anual_cultura')
    df = df.loc[df.cultura.eq(grupo)].sort_values('ano').copy()
    chuva, oni = 'Precipitação anual média (mm)', 'ONI médio anual (°C)'
    if grupo.startswith('Milho '):
        ciclo = ler('dashboard_milho_serie_anual_clima_safras')
        ciclo = ciclo.loc[ciclo.cultura.eq(grupo), ['ano', 'chuva_ciclo_media', 'oni_ciclo_medio']]
        df = df.merge(ciclo, on='ano', how='left', validate='one_to_one')
        df['media_chuva'] = df['chuva_ciclo_media']
        df['media_oni'] = df['oni_ciclo_medio']
        chuva, oni = 'Precipitação média do ciclo (mm)', 'ONI médio aproximado do ciclo (°C)'
    return df, chuva, oni


def geojson_local():
    arquivo = ROOT / 'assets' / 'parana_municipios.geojson'
    if arquivo.exists():
        geo = json.loads(arquivo.read_text(encoding='utf-8'))
        for feature in geo['features']:
            feature['properties']['id'] = str(feature['properties']['id'])
        return geo
    return None
