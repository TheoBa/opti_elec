import streamlit as st
import datetime as dt
from utils.get_data import get_history, build_history_df, get_weather


ENTITY_IDS = {
    "capteur_chambre_temperature": "sensor",
    "capteur_salon_temperature": "sensor",
    "paris_17eme_arrondissement_temperature": "sensor",
    "radiateur_bureau_switch": "input_boolean"
}

st.set_page_config(
    page_title='Homepage', 
    page_icon='😎', 
    layout="wide", 
    initial_sidebar_state="collapsed"
    )
 
def welcome_page():
    st.markdown("""# PoC OptiElec""")
    button = st.button("get data")
    if button:
        for entity_id, prefix in ENTITY_IDS.items():
            data = get_history(entity_id, is_sensor=(prefix == 'sensor'))
            df = build_history_df(data, is_sensor=(prefix == 'sensor'))
            df.to_csv(f"data/{entity_id}.csv", index=False)
    
    button = st.button("get weather")
    if button:
        weather_df = get_weather()
        day = dt.datetime.now().strftime('%Y-%m-%d')
        weather_df.to_csv(f"data/meteo_forecast_{day}.csv", index=False)


if __name__=="__main__":
    welcome_page()