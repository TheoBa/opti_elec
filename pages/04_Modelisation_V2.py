import streamlit as st
from src.model import TemperatureModel, get_rmse, get_mae
import plotly.graph_objects as go
from src.sandbox import Simulation
from src.data_loader import update_db
import json
import datetime as dt
import pandas as pd
from src.utils import prepare_logs
from src.validation import validate_model

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
    # Update Chauvigny's place
    update_db(config["chauvigny"])
    st.success("Databases updated")

def plot_temperatures(features_df: pd.DataFrame):
    """
    Plot the evolution of different temperature metrics over time.

    Args:
        features_df (pd.DataFrame): DataFrame containing temperature data.
    """
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

def plot_pred(pred_df, parameters):
    """
    Plot the predicted temperatures and other relevant metrics.

    Args:
        pred_df (pd.DataFrame): DataFrame containing prediction data.
        parameters (list): List of parameters used in the prediction model.
    """
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

def get_params_from_model(log_runs, module_name):
    """
    Retrieve the parameters from the most recent model run for a given module.

    Args:
        log_runs (pd.DataFrame): DataFrame containing log runs.
        module_name (str): Name of the module for which to retrieve parameters.

    Returns:
        list: List of parameters from the most recent model run for the specified module.
    """
    df = (
        log_runs[log_runs["module_name"] == module_name].copy()
        .sort_values(by='date', ascending=False)
        .reset_index(drop=True)
    )
    return df.iloc[0]['parameters']

with st.expander("See models performance"):
    with st.form("Model perfo"):
        log_runs = prepare_logs()
        st.markdown("### Models available")
        st.dataframe(log_runs, height=300)
        cols = st.columns([1, 2, 2])
        with cols[1]:
            model_index = st.selectbox("Select model to test", list(log_runs.index), 0)
        btn = st.form_submit_button("Submit")
    if btn:
        module_name = log_runs.loc[model_index, "module_name"]
        model = TemperatureModel(module_config=config[module_name])
        parameters = log_runs.loc[model_index, "parameters"]
        prediction_df = model.predict(parameters)
        model.plot_paintings(parameters)
        plot_pred(prediction_df, parameters)

with st.expander("Train a model - single run"):
    with st.form("Optimal parameters"):
        cols = st.columns([1, 2, 2])
        with cols[0]:
            module_name = st.selectbox("Which model to train", set(config.keys()))
        with cols[1]:
            train_timeframe = st.date_input(
            "Training timeframe",
            value=[dt.date.today() - dt.timedelta(days=20), dt.date.today()],
            format="YYYY-MM-DD"
            )
            all_data = st.toggle("Use all data")
        with cols[2]:
            temp_min = st.slider("Temperature Window min", min_value=-20, max_value=30, value=0)
            temp_max = st.slider("Temperature Window max", min_value=-20, max_value=30, value=0)
            expert_model_temp = st.toggle("Train expert model ? (use temperature window)")
        submitted = st.form_submit_button("Train model")
        if submitted:
            model = TemperatureModel(module_config=config[module_name])
            model.load_data()
            model.preprocess_data()
            model.build_features_df()
            train_timeframe = [str(date) for date in train_timeframe]
            if all_data:
                train_timeframe = None
            if not(expert_model_temp):
                temp_min = None
                temp_max = None
            with st.spinner("Parameters optimisation in progress..."):
                model.get_optimal_parameters(train_timeframe=train_timeframe, temp_min=temp_min, temp_max=temp_max)
            st.success("Done!")

validation_button = st.button("Validate model")
if validation_button:
    with st.spinner("Model validation in progress..."):
        
        train_timeframe = ['2025-01-24', '2025-02-10']
        test_timeframe=['2025-02-11', '2025-02-11']
        prediction_df, rmse = validate_model(
            train_timeframe=train_timeframe, 
            test_timeframe=test_timeframe)
        st.success(f"Validation complete. RMSE: {rmse}")
        st.dataframe(prediction_df)


def plot_simu(simu):
    """
    Plot the simulation results along with relevant metrics.

    Args:
        simu (Simulation): Simulation object related to TemperatureModule object 
        that enables the user to create simulations based on predefined scenarii.
    """
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
        log_runs = prepare_logs()
        st.markdown("### Models available")
        st.dataframe(log_runs, height=300)
        cols = st.columns([1, 2, 2])
        with cols[1]:
            model_index = st.selectbox("Select model to test", list(log_runs.index), 0)
        with cols[2]:
            scenario = st.selectbox("Scenario", ["teletravail", "normal", "off"])
        btn = st.form_submit_button("Submit")
    if btn:
        module_name = log_runs.loc[model_index, "module_name"]
        parameters = log_runs.loc[model_index, "parameters"]
        simu = Simulation(
            module_config=config[module_name],
            mode="forecasted",
            parameters=parameters
        )
        simu.load_forecasted_data()
        simu.create_simulation_features(heating_scenario=scenario)
        simu.compute_temperature_int()
        plot_simu(simu)
