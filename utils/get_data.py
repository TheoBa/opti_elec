import requests
import streamlit as st
import pandas as pd
import json
import datetime as dt


def get_data(entity_id="", is_sensor=True):
    if is_sensor:
        url = "https://17blacroix.duckdns.org:8123/api/states/sensor." + entity_id
    else:
        url = "https://17blacroix.duckdns.org:8123/api/states/input_boolean." + entity_id
    TOKEN = st.secrets["API_TOKEN"]
    headers = {
        "Authorization": f"Bearer " + TOKEN
    }
    response = requests.request("GET", url, headers=headers)
    return response.text

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