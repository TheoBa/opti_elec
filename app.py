import streamlit as st
import datetime as dt
import pandas as pd
from utils.get_data import get_history, build_history_df
from utils.display import display_time_series, display_simu_vs_truth
from utils.forecast import get_weather, analyze_temperature_correlations, latest_temp_forecast
from utils.base import HomeModule
from utils.scenario import SimulationHome, SCENARIOS

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

    with st.expander("Tau and C computation"):
        st.session_state['verification_mode'] = False
        # Use verified switches if available, otherwise use all switches
        if st.session_state.get('verification_heating_done', False) & st.session_state.get('verification_cooling_done', False):
            st.info("Using verified switch events. To modify selections, visit the Data Verification page.")
        else:
            st.info("Using all switch events. For more accurate results, consider verifying events in the Data Verification page.")
            
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
        col1, col2 = st.columns(2)
        with col1:
            st.dataframe(maison_caussa.get_daily_consumption())
        with col2:
            st.dataframe(maison_caussa.switch_df)            
    
    with st.expander(f"Launch simulations"):
        with st.form("Simulation's parameter's"):
            T_target = st.number_input("Target temperature for your home", min_value=5, max_value=30, value=20)
            T_ext = st.number_input("Outside temperature (mean)", min_value=-30, max_value=40, value=5)
            scenario = st.selectbox("Pick a scenario", options=list(SCENARIOS.keys()))
            launch_btn = st.form_submit_button("Launch simulation")
        if launch_btn:
            simu = SimulationHome()
            simu.init(
                name='scenario1',
                T_0=T_target,
                T_ext=T_ext,
                T_target=T_target,
                mean_consumption=2500,
                tau=maison_caussa.tau,
                C=maison_caussa.C,
                granularity=.25
                )
            data = simu.pick_scenario(scenario)
            df = pd.DataFrame(data, columns=["time", "temperature", "switch"])
            df = df.drop_duplicates(ignore_index=True)
            uptime, conso = simu.get_daily_consumption(df)
            st.markdown(f"tau: {simu.tau} - C: {simu.C} - ratio: {round(100 * simu.tau/simu.C, 2)}%")
            st.markdown(f"Heaters uptime: {round(uptime, 2)} (h) - Conso: {round(conso, 2)} (kWh)")
            fig = simu.plot_data(df)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.plotly_chart(fig)
            with col2:
                delta_T = 6
                st.metric(
                    f"Time to heat {delta_T}°", 
                    value=f"{simu.time_to_target(delta_T=delta_T)} min", 
                    border=True
                    )

    with st.expander(f"Simu vs truth"):
        with st.form("Select day and target"):
            day = st.date_input("Choose a daily comparison", value=dt.datetime(2025, 1, 15))
            launch_btn = st.form_submit_button("Launch simulation")
        if launch_btn:
            switch_df = maison_caussa.switch_df
            temp_df = maison_caussa.temperature_int_df
            conso_df = maison_caussa.get_daily_consumption()
            day = dt.date(day.year, day.month, day.day)
            temp_ext = maison_caussa.get_temperature_ext(
                t0=pd.to_datetime(day).tz_localize('UTC').replace(hour=0, minute=0, second=0),
                t1=pd.to_datetime(day).tz_localize('UTC').replace(hour=23, minute=59, second=59)
            )
            display_simu_vs_truth(
                T_ext=temp_ext, 
                tau=maison_caussa.tau, 
                C=maison_caussa.C,
                daily_switch_inputs_df=switch_df[switch_df.day==day].reset_index(drop=True),
                daily_temp_int=temp_df[temp_df.day==day].reset_index(drop=True),
                daily_conso=conso_df.loc[conso_df.day==day, "conso (in kWh)"].reset_index(drop=True)
                )
    
    button = st.button("get weather")
    if button:
        weather_df = maison_caussa.update_weather_forecast()
        # day = dt.datetime.now().strftime('%Y-%m-%d')
    with st.expander(f"Weather"):
        day = str((dt.datetime.now() + dt.timedelta(days=1)).date())
        temp_forecast = latest_temp_forecast(maison_caussa.weather_forecast_df, day)


    button = st.button("get feature weather")
    if button:
        features = maison_caussa.build_forecast_features()
        st.dataframe(features)
        df = analyze_temperature_correlations(features)
        st.dataframe(df)
        

    # Display time series plots
    with st.expander("Display time series"):
        display_time_series()


if __name__=="__main__":
    welcome_page()