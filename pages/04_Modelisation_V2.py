import streamlit as st
from src.model import TemperatureModel
import plotly.graph_objects as go
from src.sandbox import Simulation
from src.data_loader import update_db, ENTITY_IDS_CAUSSA, ENTITY_IDS_NABU
import json

st.set_page_config(
    page_title='Modelisation V2', 
    page_icon='🕵️‍♂️', 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

config = json.load(open("config.json", "r"))
if st.button("update databases"):
    # Update Caussa's place
    update_db(config["caussa"])
    st.success("Databases updated")
    # Update Nabu's place
    update_db(config["nabu"])
    st.success("Databases updated")

def plot_temperatures(features_df):
        fig = go.Figure()
        for c in ['temperature_int', 'temperature_ext', 'all_day_temperature', 'roll5_avg_temperature']:
            fig.add_trace(
                go.Scatter(
                    x=features_df['date'],
                    y=features_df[c],
                    name=c,
                )
            )
            fig.update_layout(
                title='Temp evolution',
                xaxis_title='Date',
                yaxis_title='Temperature (°C)',
                legend_title='Legend',
            )
        st.plotly_chart(fig)
   
def get_rmse(pred_df):
        squared_errors = (pred_df["temperature_int"] - pred_df["T_int_pred"]) ** 2
        mse = squared_errors.mean()
        rmse = mse ** 0.5
        return rmse

def plot_pred(pred_df, parameters):
    col1, col2 = st.columns([1, 6])
    with col1:
        st.metric("R", "{:.1e}".format(parameters[0]), border=True)
        st.metric("C", "{:.1e}".format(parameters[1]), border=True)
        st.metric("alpha", parameters[2], border=True)
        st.metric("Pvoisin", parameters[3], border=True)
        st.metric("delta_t", parameters[4], border=True)
    with col2:
        fig = go.Figure()
        for c in ['temperature_int', 'T_int_pred', 'direct_radiation', 'temperature_ext', 'all_day_temperature']:
            fig.add_trace(
                go.Scatter(
                    x=pred_df['date'],
                    y=pred_df[c],
                    name=c,
                )
            )
        is_heating_df = pred_df[pred_df.state=='on']
        fig.add_trace(
            go.Scatter(
                x=is_heating_df['date'],
                y=is_heating_df['is_heating'],
                name="is_heating",
                mode='markers'
            )
        )
        st.metric("RMSE", round(get_rmse(pred_df), 2), border=True)
        st.plotly_chart(fig)

with st.expander("See models performance"):
    with st.form("Model perfo"):
        cols = st.columns([1,5])
        with cols[0]:
            module_name = st.selectbox("Select module", ["caussa", "nabu"], )
        model = TemperatureModel(module_config=config[module_name])
        model.load_data()
        model.preprocess_data()
        model.build_features_df()
        btn = st.form_submit_button("Submit")
    if btn:
        plot_temperatures(features_df=model.features_df)

        if module_name=="caussa":
            st.markdown("### Doigt mouillé")
            parameters=[8e-3, 2.5e6, 80, 100, 5]
            prediction_df = model.predict(parameters)
            plot_pred(prediction_df, parameters)

            st.markdown("### Powell >24th Jan 25")
            parameters=[7.37e-3, 4e6, 71.8, 104, 4]
            prediction_df = model.predict(parameters)
            plot_pred(prediction_df, parameters)

            st.markdown("### Powell all data")
            parameters=[1.02e-2, 4.28e6, 87, 65.5, 2]
            prediction_df = model.predict(parameters)
            plot_pred(prediction_df, parameters)
        elif module_name=="nabu":
            st.markdown("### Nabu opti 10 days")
            parameters=[5.20e-3, 1.07e6, -1.45e1, 1.45e2, 2]
            prediction_df = model.predict(parameters)
            plot_pred(prediction_df, parameters)


button = st.button("Find optimal parameters ?")
if button:
    with st.spinner("Parameters optimisation in progress..."):
        model.debug_pred_df=False
        model.get_optimal_parameters(
            # train_timeframe=['2025-01-24', '2025-02-20']
            )
    st.success("Done!")

validation_button = st.button("Validate model")
if validation_button:
    with st.spinner("Model validation in progress..."):
        from src.validation import validate_model
        train_timeframe = ['2025-01-24', '2025-02-10']
        test_timeframe=['2025-02-11', '2025-02-11']
        prediction_df, rmse = validate_model(
            train_timeframe=train_timeframe, 
            test_timeframe=test_timeframe)
        st.success(f"Validation complete. RMSE: {rmse}")
        st.dataframe(prediction_df)


def plot_simu(simu):
    pred_df = simu.simulation_df
    parameters = simu.parameters
    
    col1, col2 = st.columns([1, 6])
    with col1:
        st.metric("R", "{:.1e}".format(parameters[0]), border=True)
        st.metric("C", "{:.1e}".format(parameters[1]), border=True)
        st.metric("alpha", parameters[2], border=True)
        st.metric("Pvoisin", parameters[3], border=True)
        st.metric("delta_t", parameters[4], border=True)
    with col2:
        fig = go.Figure()
        for c in ['T_int_pred', 'direct_radiation', 'temperature_ext']:
            fig.add_trace(
                go.Scatter(
                    x=pred_df['date'],
                    y=pred_df[c],
                    name=c,
                )
            )
        for c in ["thermostat_state", "is_heating"]:
            fig.add_trace(
                go.Scatter(
                    x=pred_df['date'],
                    y=pred_df[c],
                    name=c,
                    mode='markers'
                )
            )
        st.metric("Conso (in kWh)", value=simu.compute_scenarios_consumption(), border=True)
        st.plotly_chart(fig)


with st.expander("See scenario output"):
    with st.form("Scenario input"):
        scenario = st.selectbox("Scenario", ["teletravail", "normal"])
        btn = st.form_submit_button("Submit")
    if btn:
        simu = Simulation(
            module_config=config[module_name],
            mode="forecasted",
            parameters=[1.11e-02, 4.26e+06, 6.32e+01, 6.34e+01, 2.0e+00]
        )
        simu.load_forecasted_data()
        simu.create_simulation_features(heating_scenario=scenario)
        simu.compute_temperature_int()
        plot_simu(simu)
