import streamlit as st
from utils.base import HomeModule

st.set_page_config(
    page_title='Data Verification',
    page_icon='🔍',
    layout="wide",
    initial_sidebar_state="collapsed"
)

def verify_data_page():
    st.title("Data Verification")
    st.markdown("""
    This page allows you to verify and clean the switch events data used for thermal modeling.
    You can review each event and decide whether to keep or remove it from the analysis.
    """)

    maison_caussa = HomeModule()
    maison_caussa.init(
        name="maison_caussa",
        temperature_interieur_id="sensor.capteur_salon_temperature",
        temperature_exterieur_id="sensor.paris_17eme_arrondissement_temperature",
        switch_id="input_boolean.radiateur_bureau_switch",
        days_delta=10,
        mean_consumption=2500,
    )
    maison_caussa.load_df()

    st.session_state['verification_mode'] = True

    tab1, tab2 = st.tabs(["Verify Switch-offs", "Verify Switch-ons"])
    
    with tab1:
        st.header("Switch-off Events Verification")
        maison_caussa.identify_switch_offs()
        
    with tab2:
        st.header("Switch-on Events Verification")
        maison_caussa.identify_switch_ons()

if __name__ == "__main__":
    verify_data_page() 