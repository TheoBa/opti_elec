import datetime as dt
import streamlit as st
import pandas as pd
import json
import os
from retry_requests import retry
import openmeteo_requests
import requests_cache
import requests


ENTITY_IDS_CAUSSA = [
    "sensor.capteur_salon_temperature",
    "sensor.paris_17eme_arrondissement_temperature",
    "input_boolean.radiateur_bureau_switch"
    ]

ENTITY_IDS_NABU = [
    "sensor.sensor.th_03_temperature",
    "weather.forecast_maison",
    "switch.radiateur_bureau"
    ]

def parse_data_string(data_string: str) -> dict:
    """
    Convert a JSON string into a dictionary
    
    Args:
        data_string (str): JSON formatted string containing sensor data
        
    Returns:
        dict: Parsed dictionary containing sensor data
    """
    try:
        return json.loads(data_string)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON string: {e}")

def get_json_data(HA_domain_name="https://17blacroix.duckdns.org:8123", entity_id="", historic_length=10):
    """
    Get data from the Home Assistant API through GET REQUEST
    """
    start_time = dt.datetime.now() - dt.timedelta(days=0 + historic_length)
    end_time = dt.datetime.now() - dt.timedelta(days=0)
    start_date = start_time.strftime("%Y-%m-%dT%H:%M:%S%Z")
    end_date = "?end_time=" + end_time.strftime("%Y-%m-%dT%H:%M:%S%Z")
    entity_id_query = "&filter_entity_id=" + entity_id + "&minimal_response"

    url = f"{HA_domain_name}/api/history/period/{start_date}{end_date}{entity_id_query}"

    TOKEN = st.secrets["API_TOKEN"]
    headers = {
        "Authorization": f"Bearer " + TOKEN
    }
    response = requests.request("GET", url, headers=headers)
    return parse_data_string(response.text)[0][1:]

def json_to_df(inputs, column_names):
    df = (
        pd.DataFrame.from_dict(inputs)
        .rename(columns=column_names)
        .assign(date=lambda df: pd.to_datetime(df["date"]))
        )
    return df

def populate_database(df_new: pd.DataFrame, csv_path: str):
    """
    Populate or update a CSV file with new data, avoiding duplicates.
    
    Args:
        csv_path: Path to the CSV file
        df_new: New DataFrame to add to the existing data
    """
    if os.path.exists(csv_path):
        df_old = pd.read_csv(csv_path, sep=",")
        
        df_old['date'] = pd.to_datetime(df_old['date'])
        df_new['date'] = pd.to_datetime(df_new['date'])
        df_new = df_new[~df_new['date'].isin(df_old['date'])]
        df_combined = pd.concat([df_old, df_new], ignore_index=True)
        for c in df_combined.columns:
            df_combined = df_combined[~df_combined[c].isin(['unknown', 'unavailable'])]
        df_combined = df_combined.sort_values('date')
        
        df_combined.to_csv(csv_path, index=False)
    else:
        # If file doesn't exist, save the new DataFrame
        df_new.to_csv(csv_path, index=False)

def get_past_weather_data2(past_days=5, forecast_days=3):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 48.864716,
        "longitude": 2.349014,
        "hourly": ["temperature_2m", "cloud_cover", "is_day", "direct_radiation"],
	    "timezone": "auto",
        "past_days": past_days,
        "forecast_days": forecast_days
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]
    hourly = response.Hourly()

    hourly_variables = [hourly.Variables(i).ValuesAsNumpy() for i in range(len(params["hourly"]))]

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    for i, var in enumerate(params["hourly"]):
        hourly_data[var] = hourly_variables[i]

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    return hourly_dataframe

def update_db(HA_domain_name, ENTITY_IDS, db_name="db"):
    """
    Request data from Home Assistant and update the database
    """
    for entity_id in ENTITY_IDS:
        if entity_id.split(".")[0]=="sensor":
            column_names={"state": "temperature", "last_changed": "date"}
        else:
            column_names={"last_changed": "date"}
        json_data = get_json_data(HA_domain_name, entity_id, historic_length=10)
        df = json_to_df(json_data, column_names=column_names)
        populate_database(df, f"data/{db_name}/{entity_id.split('.')[1]}.csv")
    
    # weather
    df = get_past_weather_data2(past_days=10, forecast_days=3)
    populate_database(df, f"data/{db_name}/weather.csv")