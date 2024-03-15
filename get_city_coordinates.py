# https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html#:~:text=No%20ano%20de%202022%2C%20a,Distrito%20Federal%20(Bras%C3%ADlia%20%E2%80%93%20DF)%3B

import geopandas as gpd

shapefile_path = './dengue_tracker/data/MG_Municipios_2022/MG_Municipios_2022.shp'

gdf = gpd.read_file(shapefile_path)
gdf.rename(columns={'CD_MUN': 'geocode'}, inplace=True)
gdf = gdf[['geocode', 'geometry']]
gdf.to_file('./dengue_tracker/data/municipios_mg.geojson', driver='GeoJSON')