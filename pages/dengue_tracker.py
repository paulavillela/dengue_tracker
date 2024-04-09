import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
import geopandas as gpd
import plotly.express as px
import os

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
        return f'{round(num / 1000, 2)} K'
    if num > 1000000:
        if not num % 1000000:
            return f'{num // 1000000} M'
        return f'{round(num / 1000000, 1)} M'
    else:
        return num

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
        center={"lat": -18.8416, "lon": -44.5550},
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
    # Creates the json file containing the cities coordinates
    shapefile_path = './data/geodata_city_locations/MG_Municipios_2022.shp'
    if os.path.exists(shapefile_path):
        gdf = gpd.read_file(shapefile_path)
        gdf.rename(columns={'CD_MUN': 'geocode'}, inplace=True)
        gdf = gdf[['geocode', 'geometry']]
        gdf.to_file('./data/geodata_city_locations.geojson', driver='GeoJSON')
    else:
        raise NotImplementedError

def get_geodataframe():
    # Gets the geometries of Minas Gerais cities for the map
    create_geodata_json_file()
    gdf = gpd.read_file('./data/geodata_city_locations.geojson')
    gdf.set_index('geocode', inplace=True)
    return gdf

def get_current_map_data(city_geocodes, dengue_data, week, year):
    ''' Merges city geocodes and city data into a single dataframe
    Args:
        city_geocodes (pd.Dataframe): Contains the city names and geocodes
        city_data (pd.Dataframe): Contains the city geocodes and dengue data
    ''' 
    week = datetime.strptime(week, "%Y-%m-%d").date()
    df = dengue_data[(dengue_data['year'] == year) & (dengue_data['epidemiological_week'] == week)]
    city_data_merged = pd.merge(city_geocodes, df, on='geocode')
    return city_data_merged

def get_city_geocodes():
    # Creates the dataframe containing the city codes for the state of Minas Gerais according to IBGE
    path = './data/city_geocodes.csv'
    if os.path.exists(path):
        df = pd.read_csv('./data/city_geocodes.csv')
        df['geocode'] = df['geocode'].astype(str)
    else:
        raise NotImplementedError
    return df

def make_date_slider(dengue_data, year):
    # Makes slider widget for selecting the epidemiological week
    weeks = dengue_data.loc[dengue_data['year'] == year, 'epidemiological_week'].unique()
    if len(weeks) > 1:
        chosen_week = st.sidebar.slider(
            'Week',
            min_value=weeks.min(),
            max_value=weeks.max(),
            step=timedelta(days=7)
        )
    else:
        chosen_week = str(weeks[0])
        st.sidebar.markdown(f'<b>Week: </b>{chosen_week}</font>', unsafe_allow_html=True)
    return chosen_week

def make_year_select_box(dengue_data):
    # Creates a select box widget for selecting the year
    years = dengue_data['year'].unique()
    year_select_box = st.sidebar.selectbox(
        'Year',
        years
    )
    return year_select_box

def load_dengue_data():
    # Loads the downloaded dengue data
    path = './data/dengue_download_data.csv'
    if os.path.exists(path):
        df = pd.read_csv(path)
        df['geocode'] = df['geocode'].astype(str)
        df['epidemiological_week'] = pd.to_datetime(df['epidemiological_week']).dt.date
        df = df.sort_values(by='epidemiological_week')
    else:
        raise NotImplementedError
    return df

def main():
    dengue_data = load_dengue_data()
    chosen_year = make_year_select_box(dengue_data)
    chosen_week = make_date_slider(dengue_data, chosen_year)
    city_geocodes = get_city_geocodes()
    current_map_dict = get_current_map_data(city_geocodes, dengue_data, chosen_week, chosen_year)
    gdf = get_geodataframe()
    plot_map(current_map_dict, gdf)
    write_total_cases(current_map_dict)
    write_about()
    
if __name__ == "__main__":
    main()