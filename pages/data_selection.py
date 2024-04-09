import streamlit as st
from datetime import datetime, date, timedelta
from download_dengue_data import download_additional_data, get_city_data

def write_about():
    # Writes information about the data source
    with st.expander("About", expanded=True):
        st.write('''
            - Data: [INFO Dengue](<https://info.dengue.mat.br/>).
            ''')

def download_data(data_dict):
    # Downloads additional data required for the application
    download_additional_data()
    get_city_data(data_dict)

def create_dict_to_download_data(weeks_to_download):
    # Used to download the dengue data
    years = [data.year for data in weeks_to_download]
    years = set(years)
    dict_to_download = {year: [] for year in years}
    weeks_by_year = []
    for year in years:
        weeks = get_sundays_from_year(year)
        weeks_by_year.append(weeks)
    for week in weeks_to_download:
        for year in weeks_by_year:
            if week in year:
                week_index = year.index(week) + 1
                dict_to_download[week.year].append(week_index)
                break
    download_data(dict_to_download)

def display_weeks_to_download():
    # Creates a multiselect box with the chosen weeks to download
    if 'weeks_to_download' in st.session_state:
        st.header("Selected dates to download")
        st.session_state.weeks_to_download = st.multiselect("Epidemiological weeks to download", 
                                                            st.session_state.weeks_to_download, 
                                                            default=st.session_state.weeks_to_download)

def add_weeks_to_download(selected_weeks):
    """
    Appends the selected weeks to the list of weeks to download, dropping duplicates and maintaining 
    sorted order
    """
    if 'weeks_to_download' not in st.session_state:
        st.session_state.weeks_to_download = []
    st.session_state.weeks_to_download.extend(selected_weeks)
    st.session_state.weeks_to_download = sorted(set(st.session_state.weeks_to_download))

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

def get_selected_weeks(year):
    # Creates multiselect box for choosing the weeks to download
    weeks = get_sundays_from_year(year)
    st.header("Epidemiological Week")
    selected_weeks = st.multiselect("**Select the epidemiological weeks to download**", weeks)
    return selected_weeks

def make_year_select_box():
    # Creates a select box widget for selecting the year
    current_year = datetime.now().year
    years = [''] + list(range(2015, current_year+1))
    st.header("Year")
    year_select_box = st.selectbox(
        "**Select the year of the data**",
        years
    )
    return year_select_box

def main():
    st.title("Data Selection")
    st.write("Select the data you want to download from INFO Dengue.")
    st.warning("Note: The more data you choose to download, the longer it will take.")
    
    col1, col2 = st.columns(2)

    with col1:
        selected_year = make_year_select_box()
    with col2:
        if selected_year:
            selected_weeks = get_selected_weeks(selected_year)
            st.write('Choose the weeks from this year to download and press ADD.')
            _, _, _, inside_col = st.columns(4)
            with inside_col:
                add_button = st.button("**Add**")
                if add_button:
                    add_weeks_to_download(selected_weeks)
    display_weeks_to_download()

    _, _, middle_col, _, _= st.columns(5)
    download_button = False
    with middle_col:
        if 'weeks_to_download' in st.session_state:
            download_button = st.button("**DOWNLOAD**", type='primary')
    if download_button:
        create_dict_to_download_data(st.session_state.weeks_to_download)
    write_about()
if __name__ == "__main__":
    main()