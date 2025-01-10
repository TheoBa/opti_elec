import streamlit as st
from utils.get_data import get_history, build_history_df
import pandas as pd
import datetime as dt


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
            st.dataframe(build_history_df(data, is_sensor=(prefix == 'sensor')))


if __name__=="__main__":
    welcome_page()