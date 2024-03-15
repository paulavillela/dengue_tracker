# https://www.ibge.gov.br/explica/codigos-dos-municipios.php#MG

import pandas as pd

df = pd.read_excel('./dengue_tracker/data/DTB_2022/RELATORIO_DTB_BRASIL_MUNICIPIO.xls', skiprows=6)
df = df[df['Nome_UF'] == 'Minas Gerais']
df = df[['Nome_Município', 'Código Município Completo']]
df.rename(columns={'Nome_Município': 'city_name', 'Código Município Completo':'geocode'}, inplace=True)
df.to_csv('./dengue_tracker/data/mg_city_geocodes.csv', index=False)