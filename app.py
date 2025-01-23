import streamlit as st
import datetime as dt
import pandas as pd
from utils.get_data import get_history, build_history_df
from utils.display import display_time_series
from utils.forecast import get_weather
from utils.base import HomeModule
from utils.scenario import SimulationHome

ENTITY_IDS = [
    "sensor.capteur_chambre_temperature",
    "sensor.capteur_salon_temperature",
    "sensor.paris_17eme_arrondissement_temperature",
    "input_boolean.radiateur_bureau_switch"
]

st.set_page_config(
    page_title='Homepage', 
    page_icon='😎', 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

def welcome_page():
    st.markdown("Init HomeModule")
    maison_caussa = HomeModule()
    maison_caussa.init(
        name="maison_caussa",
        temperature_interieur_id="sensor.capteur_salon_temperature",
        temperature_exterieur_id="sensor.paris_17eme_arrondissement_temperature",
        switch_id="input_boolean.radiateur_bureau_switch",
        days_delta=10,
        mean_consumption=2500,
        )
    button = st.button("update_db")
    if button:
        maison_caussa.update_db()
    maison_caussa.load_df()

    st.markdown("Compute Tau and C for given HomeModule")
    with st.expander("Tau and C computation"):
        dict_tau = maison_caussa.compute_tau()
        st.markdown(f"tau_mean: {dict_tau['tau_mean']}")
        st.markdown(f"tau_std: {dict_tau['tau_std']}")
        st.markdown(f"tau_values: {dict_tau['tau_values']}")
        st.markdown(f"valid_periods: {dict_tau['valid_periods']}")
        st.markdown(f"total_periods: {dict_tau['total_periods']}")
        st.markdown(maison_caussa.tau)

        dict_C = maison_caussa.compute_C()
        st.markdown(f"C_mean: {dict_C['C_mean']}")
        st.markdown(f"C_std: {dict_C['C_std']}")
        st.markdown(f"C_values: {dict_C['C_values']}")
        st.markdown(f"valid_periods: {dict_C['valid_periods']}")
        st.markdown(f"total_periods: {dict_C['total_periods']}")

    with st.expander("Get daily heating consumption"):
        st.dataframe(maison_caussa.get_daily_consumption())
    
    st.markdown("Ready to launch scenario 1")
    with st.expander("plot scenario 1"):
        simu = SimulationHome()
        simu.init(
            name='scenario1',
            T_0=20,
            T_ext=10,
            mean_consumption=2500,
            tau=maison_caussa.tau,
            C=maison_caussa.C,
            granularity=.25
        )
        data = simu.scenario_1(T_target=20)
        df = pd.DataFrame(data, columns=["time", "temperature", "switch"])
        df = df.drop_duplicates(ignore_index=True)
        st.dataframe(df)
        fig = simu.plot_data(df)
        st.plotly_chart(fig)
        st.markdown("Plot shown")
    
    button = st.button("get weather")
    if button:
        weather_df = get_weather()
        # day = dt.datetime.now().strftime('%Y-%m-%d')
        # weather_df.to_csv(f"data/meteo_forecast_{day}.csv", index=False)
        st.dataframe(weather_df)

    button = st.button("get feature weather")
    if button:
        features = maison_caussa.build_forecast_features()
        st.dataframe(features)
        

    # Display time series plots
    display_time_series()


if __name__=="__main__":
    welcome_page()