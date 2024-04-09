import streamlit as st

def show_home():
    st.title("Welcome to the Dengue Tracker App!")

    st.write("This app allows you to visualize dengue data for cities in Minas Gerais, Brazil.")
    st.write("To get started, follow these steps:")

    st.header("Step 1: Data Selection")
    st.write("Navigate to the 'data selection' page by clicking on the sidebar.")
    st.write("In the 'data selection' page, choose the epidemiological weeks you wish to download data for.")

    st.warning("Note: The more data you choose to download, the longer it will take.")
    st.write("Please be patient, especially if you are selecting a large number of weeks.")

    st.header("Step 2: Running the Dengue Tracker")
    st.write("Once you've downloaded the necessary data, click on the 'dengue tracker' page in the sidebar.")
    st.write("In the 'dengue tracker' page, select a year and epidemiological week from the downloaded data.")
    st.write("A map of Minas Gerais will be generated, showing the alert level of each city based on the dengue data.")
    st.write("The alert level is calculated using the number of current cases and the population of the city.")
    st.write("This helps in understanding the severity of the dengue outbreak in different areas.")

show_home()