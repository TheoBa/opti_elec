import requests
import streamlit as st
import pandas as pd
import json
import datetime as dt


def get_data(entity_id=""):
    url = "https://17blacroix.duckdns.org:8123/api/states/" + entity_id
    TOKEN = st.secrets["API_TOKEN"]
    headers = {
        "Authorization": f"Bearer " + TOKEN
    }
    response = requests.request("GET", url, headers=headers)
    return response.text

def get_history(entity_id="", days_delta=1):
    start_time = dt.datetime.now() - dt.timedelta(days=days_delta)
    end_time = dt.datetime.now()
    start_date = start_time.strftime("%Y-%m-%dT%H:%M:%S%Z")
    end_date = "?end_time=" + end_time.strftime("%Y-%m-%dT%H:%M:%S%Z")
    entity_id_query = "&filter_entity_id=" + entity_id + "&minimal_response"

    url = f"https://17blacroix.duckdns.org:8123/api/history/period/{start_date}{end_date}{entity_id_query}"

    TOKEN = st.secrets["API_TOKEN"]
    headers = {
        "Authorization": f"Bearer " + TOKEN
    }
    response = requests.request("GET", url, headers=headers)
    return parse_data_string(response.text)[0][1:]

def build_history_df(inputs, column_names):
    df = (
        pd.DataFrame.from_dict(inputs)
        .rename(columns=column_names)
        .assign(date=lambda df: pd.to_datetime(df["date"]))
        )
    return df

def build_df(data, prefix):
    parsed_data = parse_data_string(data)
    data_id = parsed_data["entity_id"]
    data_state = parsed_data["state"]
    
    data_date = dt.datetime.fromisoformat(parsed_data["last_changed"])
    if prefix == 'sensor':
        column_names=["id", "temperature", "date"]
    elif prefix == 'input_boolean':
        column_names=["id", "state", "date"]
    df = pd.DataFrame([[data_id, data_state, data_date]], columns=column_names)
    return df

def init_db(data):
    db_name = data.id
    df = data.df
    db = pd.DataFrame(df)
    db.to_csv(f"data/{db_name}.csv")

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

from pymeteosource.api import Meteosource
from pymeteosource.types import tiers,sections

def get_weather():
    YOUR_API_KEY = st.secrets["API_WEATHER"]
    YOUR_TIER = tiers.FREE
    meteosource = Meteosource(YOUR_API_KEY, YOUR_TIER)

    # Get the forecast for a given point
    forecast = meteosource.get_point_forecast(
        lat=48.864716,  # Latitude of the point
        lon=2.349014,  # Longitude of the point
        place_id=None,  # You can specify place_id instead of lat+lon
        sections=[sections.CURRENT, sections.HOURLY],  # Defaults to '("current", "hourly")'      
    )
    # st.markdown(forecast)
    forecast.hourly[0]['temperature']
    df = forecast.hourly.to_pandas()
    # st.dataframe(df)
    return df
   