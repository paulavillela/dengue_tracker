import pandas as pd
import geopandas as gpd
import zipfile
import requests
import streamlit as st
import os
from urllib.error import URLError
import time

def create_geodata_json_file():
    geojson_path = './data/geodata_city_locations.geojson'
    if not os.path.exists(geojson_path):
        # Creates the json file containing the 
        shapefile_path = './data/geodata_city_locations/MG_Municipios_2022.shp'
        gdf = gpd.read_file(shapefile_path)
        gdf.rename(columns={'CD_MUN': 'geocode'}, inplace=True)
        gdf = gdf[['geocode', 'geometry']]
        gdf.to_file(geojson_path, driver='GeoJSON')
    else:
        st.write('GDF file already exists. ')

def save_city_data(city_data):
    path = './data/dengue_download_data.csv'
    if not os.path.exists(path):
        city_data.to_csv(path, index=False)
    else:
        old_city_data = pd.read_csv(path)
        updated_city_data = pd.concat([old_city_data, city_data], ignore_index=True)
        updated_city_data.to_csv(path, index=False)

def load_data(url, geocode):
    '''
    Load and cache data related to the dengue disease for a specific city

    Parameters:
    - url (str): The URL for downloading the data
    - geocode (int): The geocode identifier for the city (source: IBGE)

    Returns:
    pd.DataFrame: A DataFrame containing data on dengue cases and alert levels.
    '''
    retry_attempts = 5
    delay_seconds = 20
    attempt = 0
    while attempt < retry_attempts:
        try:
            df = pd.read_csv(url, index_col='SE')
            df = df[['data_iniSE', 'casos', 'nivel']]
            df.rename(columns={'data_iniSE': 'epidemiological_week'}, inplace=True)
            df['geocode'] = str(geocode)
            return df
        except URLError as e:
            attempt += 1
            st.write('attempt: ', attempt)
            if attempt < retry_attempts:
                time.sleep(delay_seconds)
    st.write(f'Unable to load data after {retry_attempts} attempts.')
    return df

def get_data_url(url, geocode, disease, format, ew_start, ew_end, ey_start, ey_end):
    '''
    Generates URL for downloading data related to a specific disease in a given city

    Parameters:
    - url (str): URL base for the data API
    - geocode (int): The geocode identifier for the city. (source: IBGE)
    - disease (str): The type of disease for which data is requested, in this case, dengue
    - format (str): The desired format for the data
    - ew_start (int): The starting epidemiological week
    - ew_end (int): The ending epidemiological week
    - ey_start (int): The starting epidemiological year
    - ey_end (int): The ending epidemiological year

    Returns:
    str: The complete URL for downloading the specified data.
    '''
    params =(
    "&disease="
    + f"{disease}"
    + "&geocode="
    + f"{geocode}"
    + "&disease="
    + f"{disease}"
    + "&format="
    + f"{format}"
    + "&ew_start="
    + f"{ew_start}"
    + "&ew_end="
    + f"{ew_end}"
    + "&ey_start=" 
    + f"{ey_start}"
    + "&ey_end="
    + f"{ey_end}"    
    )
    url_resp = "?".join([url, params])
    return url_resp

def get_data_parameters(geocode, year, epidemiological_week):
    """ Constructs parameters for building the URL to fetch data related to a specific disease in a given city.

    Args:
        geocode (int): The geocode identifier for the city according to IBGE.
        year (int): The year for which data is requested.
        epidemiological_week (int): The week for which data is requested.
    """
    url = "https://info.dengue.mat.br/api/alertcity"
    disease = "dengue"
    format = "csv"
    ew_start = epidemiological_week
    ew_end = epidemiological_week
    ey_start = year
    ey_end = year
    return url, geocode, disease, format, ew_start, ew_end, ey_start, ey_end

def get_city_geocodes():
    # Creates the dataframe containing the city codes for the state of Minas Gerais according to IBGE
    path = './data/city_geocodes.csv'
    if not os.path.exists(path):
        df = pd.read_excel('./data/city_geocodes/RELATORIO_DTB_BRASIL_MUNICIPIO.xls', skiprows=6)
        df = df[df['Nome_UF'] == 'Minas Gerais']
        df = df[['Nome_Município', 'Código Município Completo']]
        df.rename(columns={'Nome_Município': 'city_name', 'Código Município Completo':'geocode'}, inplace=True)
        df['geocode'] = df['geocode'].astype(str)
        df.to_csv('./data/city_geocodes.csv', index=False)
    else:
        df = pd.read_csv(path)
        st.write('city_geocodes.csv already exists.')
    return df

def get_city_data(data_dict):
    # Creates a data list with data from all Minas Gerais cities in the specified year and epidemiological week
    city_geocodes = get_city_geocodes()
    data_list = list()
    total_databases = len(st.session_state.weeks_to_download) * len(city_geocodes)
    processed_databases = 0
    progress_bar = st.progress(0, str(int(processed_databases/total_databases)))
    number_placeholder = st.empty()
    number_placeholder.write("Loading")
    for year, weeks in data_dict.items():
        for week in weeks:
            for geocode in city_geocodes['geocode']:
                url = get_data_url(*get_data_parameters(geocode, year, week))
                data = load_data(url, geocode)
                if not data.empty:
                    data['year'] = year
                    data_list.append(data)
                processed_databases += 1
                progress_bar.progress(processed_databases/total_databases)
                number_placeholder.write(processed_databases)
    df = pd.concat(data_list, ignore_index=True)
    save_city_data(df)
        
def unzip_file(file, extracted_folder):
    # Unzips the file downloaded to be used
    if not os.path.exists(extracted_folder):
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(extracted_folder)
    else:
        st.write(file, ' file already extracted.')

def get_zip_file(zip_url, save_path, extracted_folder):
    # Downloads the zip files used on the application
    if not os.path.exists(save_path):
        response = requests.get(zip_url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
        else:
            st.write("Failed to download the file. Status code:", response.status_code)
        unzip_file(save_path, extracted_folder)
    else:
        st.write(save_path,' zip file already downloaded.')

def create_data_folder():
    data_folder = './data'
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)
    else:
        st.write('Data folder already exists. ')
    return data_folder

def download_additional_data():
    # Downloads additional data required for the application
    data_folder = create_data_folder()
    city_geocodes_zip_url = 'https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2022/DTB_2022.zip'
    city_geocodes_save_path = os.path.join(data_folder, 'city_geocodes.zip')
    city_geocodes_extracted_folder = './data/city_geocodes'
    geodata_zip_url = 'https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2022/UFs/MG/MG_Municipios_2022.zip'
    geodata_save_path = './data/geodata_city_locations.zip'
    geodata_extracted_folder = './data/geodata_city_locations'
    get_zip_file(city_geocodes_zip_url, city_geocodes_save_path, city_geocodes_extracted_folder)
    get_zip_file(geodata_zip_url, geodata_save_path, geodata_extracted_folder)
    create_geodata_json_file()