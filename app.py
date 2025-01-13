import streamlit as st
import datetime as dt
from utils.get_data import get_history, build_history_df, get_weather
from utils.display import display_time_series


ENTITY_IDS = {
    "capteur_chambre_temperature": "sensor",
    "capteur_salon_temperature": "sensor",
    "paris_17eme_arrondissement_temperature": "sensor",
    "radiateur_bureau_switch": "input_boolean"
}
ENTITY_IDS = [
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
    with st.form("Reload database"):
        days_delta = st.number_input("Delta days for DB history", value=1)
        submitted = st.form_submit_button("Reload DB")
        if submitted:
            for entity_id in ENTITY_IDS:
                if entity_id.split(".")[0]=="sensor":
                    column_names={"state": "temperature", "last_changed": "date"}
                else:
                    column_names={"last_changed": "date"}
                data = get_history(entity_id, days_delta=days_delta)
                df = build_history_df(data, column_names=column_names)
                df.to_csv(f"data/tests_data/{entity_id.split(".")[1]}.csv", index=False)
    
    button = st.button("get weather")
    if button:
        weather_df = get_weather()
        day = dt.datetime.now().strftime('%Y-%m-%d')
        weather_df.to_csv(f"data/meteo_forecast_{day}.csv", index=False)

    # Display time series plots
    display_time_series()


if __name__=="__main__":
    welcome_page()