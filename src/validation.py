import pandas as pd
from src.model import TemperatureModel
import streamlit as st
import datetime as dt

def validate_model(test_timeframe):
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

    # Optimize the model for the given timeframe
    model.get_optimal_parameters(opti_timeframe=test_timeframe)

    # Test the model on the next 24-hour timeframe
    test_df = model.features_df[model.features_df['date'] > test_timeframe[1]]
    st.markdown(type(test_df.date.loc[11000]))
    day_limit = str((pd.to_datetime(test_timeframe[1]) + pd.Timedelta(days=1)).date())
    test_df = test_df[test_df['date'] <= day_limit]
    prediction_df = model.predict(model.optimal_parameters)

    # Calculate RMSE for the test timeframe
    rmse = model.cost_function(model.optimal_parameters, test_df=test_df)
    print(f"RMSE for the test timeframe: {rmse}")

    return prediction_df, rmse

if __name__ == "__main__":
    test_timeframe = ['2025-01-24', '2025-02-10']
    # [9.23343925e-03 4.25517656e+06 7.63058464e+01 7.75700491e+01 3.00567944e+00]
    prediction_df, rmse = validate_model(test_timeframe)
    print("Validation complete. RMSE:", rmse)
