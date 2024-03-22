import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
import geopandas as gpd
import xlrd
import plotly.express as px
import zipfile
import requests

def write_about():
    # Writes information about the data source
    with st.expander('About', expanded=True):
        st.write('''
            - Data: [INFO Dengue](<https://info.dengue.mat.br/>).
                    [IBGE](<https://www.ibge.gov.br/>).
            ''')

def format_number(num):
    # Formats large numbers representing dengue cases in Minas Gerais for better readability
    if num > 1000 and num < 1000000:
        if not num % 1000:
            return f'{num // 1000} K'
        return f'{round(num / 1000, 2)} M'
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'

def write_total_cases(df):
    # Writes the total number of dengue cases in Minas Gerais in the sidebar 
    total_cases = df['casos'].sum()
    total_cases = format_number(total_cases)
    st.sidebar.write('Total cases: ', str(total_cases))

def plot_map(df, gdf):
    """ Plots a choropleth map of dengue cases in Minas Gerais

    Args:
        df (pd.DataFrame): DataFrame containing city-level dengue data
        gdf (gpd.GeoDataFrame): GeoDataFrame containing geometries of Minas Gerais cities
    """
    fig = px.choropleth_mapbox(
        df,
        geojson=gdf.geometry,
        locations='geocode',
        color='nivel',
        color_continuous_scale='blackbody_r',
        mapbox_style='carto-positron',
        zoom=5,
        center={"lat": -18.8416, "lon": -46.9810},  # Coordinates for Minas Gerais
        opacity=0.7,
        hover_name='city_name',
        hover_data={'casos': True, 'nivel': False, 'geocode': False}
    )

    fig.update_layout(
        title='Dengue Cases and Risk Levels in Minas Gerais Cities',
        margin={"r": 0, "t": 30, "l": 0, "b": 0}
    )
    st.plotly_chart(fig)

def create_geodata_json_file():
    # Creates the json file containing the 
    shapefile_path = './data/geodata_city_locations/MG_Municipios_2022.shp'
    gdf = gpd.read_file(shapefile_path)
    gdf.rename(columns={'CD_MUN': 'geocode'}, inplace=True)
    gdf = gdf[['geocode', 'geometry']]
    gdf.to_file('./data/geodata_city_locations.geojson', driver='GeoJSON')

@st.cache_data
def get_geodataframe():
    # Gets the geometries of Minas Gerais cities for the map
    create_geodata_json_file()
    gdf = gpd.read_file('./data/geodata_city_locations.geojson')
    gdf.set_index('geocode', inplace=True)
    return gdf

def get_current_map_data(city_geocodes, city_data):
    ''' Merges city geocodes and city data into a single dataframe
    Args:
        city_geocodes (pd.Dataframe): Contains the city names and geocodes
        city_data (pd.Dataframe): Contains the city geocodes and dengue data
    ''' 
    city_data_merged = pd.merge(city_geocodes, city_data, on='geocode')
    return city_data_merged

def load_data(url, geocode):
    '''
    Load and cache data related to the dengue disease for a specific city

    Parameters:
    - url (str): The URL for downloading the data
    - geocode (int): The geocode identifier for the city (source: IBGE)

    Returns:
    pd.DataFrame: A DataFrame containing data on dengue cases and alert levels.
    '''
    df = pd.read_csv(url, index_col='SE')
    df = df[['casos', 'nivel']]
    df['geocode'] = str(geocode)
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
    url = "https://info.dengue.mat.br/api/alertcity"                                                  # BH
    disease = "dengue"
    format = "csv"
    ew_start = epidemiological_week
    ew_end = epidemiological_week
    ey_start = year
    ey_end = year
    return url, geocode, disease, format, ew_start, ew_end, ey_start, ey_end

def get_city_data(city_geocodes, year, week):
    # Creates a data list with data from all Minas Gerais cities in the specified year and epidemiological week
    data_list = list()
    for geocode in city_geocodes['geocode']:
        url = get_data_url(*get_data_parameters(geocode, year, week))
        data = load_data(url, geocode)
        data_list.append(data)
    df = pd.concat(data_list, ignore_index=True)
    return df

def get_city_geocodes():
    # Creates the dataframe containing the city codes for the state of Minas Gerais according to IBGE
    df = pd.read_excel('./data/city_geocodes/RELATORIO_DTB_BRASIL_MUNICIPIO.xls', skiprows=6)
    df = df[df['Nome_UF'] == 'Minas Gerais']
    df = df[['Nome_Município', 'Código Município Completo']]
    df.rename(columns={'Nome_Município': 'city_name', 'Código Município Completo':'geocode'}, inplace=True)
    df['geocode'] = df['geocode'].astype(str)
    return df

def unzip_file(file, extracted_folder):
    # Unzips the file downloaded to be used
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(extracted_folder)

def get_zip_file(zip_url, save_path, extracted_folder):
    # Downloads the zip files used on the application
    response = requests.get(zip_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
    else:
        st.write('Failed to download the file. Status code:', response.status_code)
    unzip_file(save_path, extracted_folder)

def download_additional_data():
    # Downloads additional data required for the application
    city_geocodes_zip_url = 'https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/divisao_territorial/2022/DTB_2022.zip'
    city_geocodes_save_path = './data/city_geocodes.zip'
    city_geocodes_extracted_folder = './data/city_geocodes'
    geodata_zip_url = 'https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2022/UFs/AC/AC_Municipios_2022.zip'
    geodata_save_path = './data/geodata_city_locations.zip'
    geodata_extracted_folder = './data/geodata_city_locations'
    get_zip_file(city_geocodes_zip_url, city_geocodes_save_path, city_geocodes_extracted_folder)
    get_zip_file(geodata_zip_url, geodata_save_path, geodata_extracted_folder)

def make_date_slider(week_list):
    # Makes slider widget for selecting the epidemiological week
    chosen_week = st.sidebar.slider(
        'Week',
        min_value=week_list[0],
        max_value=week_list[-1],
        step=timedelta(days=7)
    )
    chosen_week = week_list.index(chosen_week) + 1
    return chosen_week

def get_sundays_from_year(year):
    # Gets list of every sunday of the year
    current_year = datetime.now().year
    day = date(year, 1, 1)
    day += timedelta(days = 6 - day.weekday())
    sundays = [day]
    if year == current_year:
        today = date.today()
        while sundays[-1] <= today:
            sundays.append(sundays[-1] + timedelta(days=7))
    else:
        while(sundays[-1].year == year):
            sundays.append(sundays[-1] + timedelta(days=7))
    return sundays[:-1]

def make_year_select_box():
    # Creates a select box widget for selecting the year
    current_year = datetime.now().year
    years = list(range(2015, current_year+1))
    year_select_box = st.sidebar.selectbox(
        'Year',
        years
    )
    return year_select_box

def main():
    chosen_year = make_year_select_box()
    weeks_list = get_sundays_from_year(chosen_year)
    chosen_week = make_date_slider(weeks_list)
    download_additional_data()
    city_geocodes = get_city_geocodes()
    city_data = get_city_data(city_geocodes, chosen_year, chosen_week)
    current_map_dict = pd.merge(city_geocodes, city_data, on='geocode')
    gdf = get_geodataframe()
    plot_map(current_map_dict, gdf)
    write_total_cases(current_map_dict)
    write_about()

if __name__ == "__main__":
    main()