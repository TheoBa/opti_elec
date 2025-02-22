import pandas as pd
from src.model import TemperatureModel
import streamlit as st
import datetime as dt

def validate_model(train_timeframe, test_timeframe):
    # Initialize the model
    PATH_FILES = {
        "temperature_ext_csv": "data/db/paris_17eme_arrondissement_temperature.csv",
        "temperature_int_csv": "data/db/capteur_salon_temperature.csv",
        "switch_csv": "data/db/radiateur_bureau_switch.csv",
        "weather_csv": "data/db/weather.csv",
    }
    model = TemperatureModel(P_consigne=2500)
    model.load_data(PATH_FILES)
    model.preprocess_data() 
    model.build_features_df()

    # Optimize the model for the given train_timeframe
    model.get_optimal_parameters(train_timeframe=train_timeframe)

    # Test the model on the given test_timeframe
    test_df, rmse = model.test_model(
        test_timeframe=test_timeframe,
        test_parameters=model.optimal_parameters
        )

    return test_df, rmse

