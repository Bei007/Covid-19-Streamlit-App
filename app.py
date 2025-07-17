import streamlit as st
import pydeck as pdk
import pandas as pd
import os
import calendar

st.title("Covid-19 Global Dashboard")
st.subheader("This COVID-19 Dashboard displays a tracker, world map, and time series data on cases, deaths, vaccinations, and recoveries worldwide from 2020 to March 2023.")

tab1, tab2 = st.tabs(["🌍 Global Tracker & World Map", "📊 Country Time Serise"])
with tab1:
    st.subheader("Global Tracker", divider="gray")
    #st.dataframe(df)


    df = pd.read_csv("data/combine_monthly_summary.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.strftime("%B")

    df_vac = pd.read_csv("data/time_series_covid19_vaccine_global.csv")
    df_vac["Date"] = pd.to_datetime(df_vac["Date"])
    df_vac["Year"] = df_vac["Date"].dt.year
    df_vac["Month"] = df_vac["Date"].dt.strftime("%B")

    # -- Selectors Below Tracker --

    # Create ordered list of month names
    month_order = list(calendar.month_name)[1:]  # ['January', 'February', ..., 'December']

    # Sort your unique months based on the correct order
    sorted_months = sorted(df["Month"].unique(), key=lambda m: month_order.index(m))

    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("Select Year", sorted(df["Year"].unique()))
    with col2:
        month = st.selectbox("Select Month", sorted_months)

    # Filter by year and month
    filtered_df = df[(df["Year"] == year) & (df["Month"] == month)]

    # Filter by year and month(vaccination)
    filtered_df_vac = df_vac[(df_vac["Year"] == year) & (df_vac["Month"] == month)]

    # Display numbers
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cases", int(filtered_df["Confirmed"].sum()))
    with col2:
        st.metric("Total Deaths", int(filtered_df["Deaths"].sum()))
    with col3:
        try:
            vacc_count = int(filtered_df_vac[filtered_df_vac.Country_Region=="World"]["Doses_admin"].max())
        except:
            vacc_count = 0
        st.metric("Total Vaccinations", vacc_count)


    st.subheader("World Map", divider="gray")

    #metrics = st.multiselect(
        #"Select Metric(s)",
        #["Confirmed", "Deaths"],
        # default=["Confirmed"]
    #)

    st.markdown("**Select Metric(s)**")
    col1, col2 = st.columns(2)
    metrics = []
    with col1:
        if st.toggle("Confirmed", value=True):
            metrics.append("Confirmed")

    with col2:
        if st.toggle("Deaths"):
            metrics.append("Deaths")

    country_options = df.Country_Region.unique().tolist()


    options = st.multiselect(
            "Select countries",
            sorted(country_options),
            default=["US"],
    )
    if options:
        filtered_df_countries = filtered_df[filtered_df["Country_Region"].isin(options)]
    #st.dataframe(filtered_df)
    else:
        st.write("Please select at least one country to view data.")

    map_df = filtered_df_countries.rename(columns={"Lat": "lat", "Long_": "lon"})
    


    layers = []

    if "Confirmed" in metrics:
        layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[lon, lat]',
            get_radius="Confirmed",
            radius_scale=0.05,
            radius_min_pixels=2,
            radius_max_pixels=15,
            get_fill_color='[0, 100, 200, 160]',  # Blue
            pickable=True,
        ))

    if "Deaths" in metrics:
            layers.append(pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position='[lon, lat]',
            get_radius="Deaths",
            radius_scale=3,
            radius_min_pixels=2,
            radius_max_pixels=30,
            get_fill_color='[200, 0, 50, 160]',  # Red
            pickable=True,
        ))
        
    view_state = pdk.ViewState(latitude=0, longitude=0, zoom=1, pitch=0)

    tooltip_text = "Country: {Country_Region}\nState: {Province_State}"
    if "Deaths" in metrics:
            tooltip_text += "\nDeaths: {Deaths}"
    if "Confirmed" in metrics:
            tooltip_text += "\nCases: {Confirmed}"

    st.pydeck_chart(pdk.Deck(
        #map_style="mapbox://styles/mapbox/light-v9",
        map_style="road",
        initial_view_state=view_state,
        layers=layers,
        tooltip={"text": tooltip_text},
    ))

with tab2:
    tab2.subheader("Global Time Series", divider="gray")
    df=pd.read_csv("data/time_series_covid19_confirmed_global.csv")
    
    country_choices = df["Country/Region"].unique().tolist()
    country_option_tab2 = tab2.selectbox(
    "Select a Country",
    sorted(country_choices)
    )

    df_melt = pd.melt(frame=df,
        id_vars=df.columns[:4],
        value_vars=df.columns[4:],
        var_name="Date",
        value_name="Confirmed"
    )

    df_melt.Date = pd.to_datetime(df_melt.Date)

    df_confirmed = df_melt[df_melt["Country/Region"]==country_option_tab2].groupby(by="Date", as_index=False).agg({"Confirmed": "sum"})
    df_confirmed.sort_values(by="Date", inplace=True)
   

    tab2.line_chart(data=df_confirmed, x="Date", y="Confirmed")

    
    df=pd.read_csv("data/time_series_covid19_deaths_global.csv")

    df_melt = pd.melt(frame=df,
        id_vars=df.columns[:4],
        value_vars=df.columns[4:],
        var_name="Date",
        value_name="Deaths"
    )

    df_melt.Date = pd.to_datetime(df_melt.Date)

    df_deaths = df_melt[df_melt["Country/Region"]==country_option_tab2].groupby(by="Date", as_index=False).agg({"Deaths": "sum"})
    df_deaths.sort_values(by="Date", inplace=True)
    tab2.line_chart(data=df_deaths, x="Date", y="Deaths")

    df=pd.read_csv("data/time_series_covid19_vaccine_doses_admin_global.csv")

    df_melt = pd.melt(frame=df,
        id_vars=df.columns[:12],
        value_vars=df.columns[12:],
        var_name="Date",
        value_name="Vaccinations"
    )

    df_melt.Date = pd.to_datetime(df_melt.Date)

    df_vaccine_admin = df_melt[df_melt["Country_Region"]==country_option_tab2].groupby(by="Date", as_index=False).agg({"Vaccinations": "sum"})
    df_vaccine_admin.sort_values(by="Date", inplace=True)
    tab2.line_chart(data=df_vaccine_admin, x="Date", y="Vaccinations")


    df=pd.read_csv("data/time_series_covid19_recovered_global.csv")

    df_melt = pd.melt(frame=df,
        id_vars=df.columns[:4],
        value_vars=df.columns[4:],
        var_name="Date",
        value_name="Recovered"
    )

    df_melt.Date = pd.to_datetime(df_melt.Date)

    df_recovered = df_melt[df_melt["Country/Region"]==country_option_tab2].groupby(by="Date", as_index=False).agg({"Recovered": "sum"})
    df_recovered.sort_values(by="Date", inplace=True)
    tab2.line_chart(data=df_recovered, x="Date", y="Recovered")

