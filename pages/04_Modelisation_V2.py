import streamlit as st
from src.model import TemperatureModel


st.set_page_config(
    page_title='Modelisation V2', 
    page_icon='🕵️‍♂️', 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

PATH_FILES = {
    "temperature_ext_csv": "data/db/paris_17eme_arrondissement_temperature.csv",
    "temperature_int_csv": "data/db/capteur_salon_temperature.csv",
    "switch_csv": "data/db/radiateur_bureau_switch.csv",
    "weather_csv": "data/db/weather.csv",
}

model = TemperatureModel(
    initial_params=[0.01, 1000, 1, 100], 
    P_consigne=2500
)
model.load_data(PATH_FILES)
model.preprocess_data()
model.build_features_df()

st.dataframe(model.features_df.head())

def plot_temperatures(features_df):
    import plotly.graph_objects as go
    fig = go.Figure()
    for c in ['temperature_ext', 'temperature_ext2', 'all_day_temperature', 'roll5_avg_temperature']:
        fig.add_trace(
            go.Scatter(
                x=features_df['date'],
                y=features_df[c],
                name=c,
            )
        )
    st.plotly_chart(fig)

plot_temperatures(features_df=model.features_df)

def plot_pred(pred_df):
    import plotly.graph_objects as go
    fig = go.Figure()
    for c in ['temperature_int', 'T_int_pred']:
        fig.add_trace(
            go.Scatter(
                x=pred_df['date'],
                y=pred_df[c],
                name=c,
            )
        )
    st.plotly_chart(fig)

st.markdown("### Doigt mouillé")
prediction_df = model.predict(parameters=[.005, 5e6, 0.1, 500, 5])
plot_pred(prediction_df)

st.markdown("### Powell all data")
prediction_df = model.predict(parameters=[1.61e-02, 1.38e+07, 1.37e+02, 2.61e+02, -7.96])
plot_pred(prediction_df)

st.markdown("### Differential all data")
prediction_df = model.predict(parameters=[2.35e-02, 9.47e+08, 1.62e+01, 7.56e+00, 7.25])
plot_pred(prediction_df)


button = st.button("Find optimal parameters ?")
if button:
    with st.spinner("Parameters optimisation in progress..."):
        model.get_optimal_parameters()
    st.success("Done!")
