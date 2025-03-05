import streamlit as st
from src.utils import prepare_logs
from src.model import TemperatureModel, get_mae, get_rmse, select_features_from_temperature_window
import json

config = json.load(open("config.json", "r"))

st.set_page_config(
    page_title='Model analysis & testing', 
    page_icon='🔬', 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

st.title("Test Models")

with st.expander("Model test"):
    with st.form("Model test"):
        log_runs = prepare_logs()
        st.dataframe(log_runs)
        cols = st.columns([1,5])
        with cols[0]:
            model_index = st.selectbox("Select model to test", list(log_runs.index), 0)

        btn = st.form_submit_button("Submit test")
    if btn:
        with st.spinner("Model validation in progress..."):
            module_name = log_runs.loc[model_index, "module_name"]
            model = TemperatureModel(module_config=config[module_name])
            pred_df = model.predict(log_runs.loc[model_index, "parameters"])
            st.dataframe(model.features_df)
            st.dataframe(pred_df)

def build_residuals(pred_df):
    pred_df = (
        pred_df
        .assign(
            residuals=lambda df: df["temperature_int"] - df["T_int_pred"],
            hours_minute=lambda df: df["date"].dt.hour*100 + df["date"].dt.minute,
        )
    )
    # Compute correlation of 'residuals' with other columns
    correlation = pred_df[["date", "hours_minute", "temperature_ext", "all_day_temperature", "residuals", "shape_t_ext", "is_heating"]].corr()['residuals'].drop('residuals')
    return pred_df, correlation

with st.expander("Residuals analysis"):
    with st.form("Residuals  analysis"):
        log_runs = prepare_logs()
        st.dataframe(log_runs)
        cols = st.columns([1,5])
        with cols[0]:
            model_index = st.selectbox("Select model to test", list(log_runs.index), 0)
        btn = st.form_submit_button("Submit Residuals Analysis")
    if btn:
        with st.spinner("Model validation in progress..."):
            module_name = log_runs.loc[model_index, "module_name"]
            model = TemperatureModel(module_config=config[module_name])
            pred_df = model.predict(log_runs.loc[model_index, "parameters"])
            pred_df, correlation = build_residuals(pred_df)
            st.dataframe(pred_df)
            st.write(correlation)
            
