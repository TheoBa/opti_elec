import requests
import streamlit as st
import pandas as pd
import json
import datetime as dt
import os


def get_data(entity_id=""):
    url = "https://17blacroix.duckdns.org:8123/api/states/" + entity_id
    TOKEN = st.secrets["API_TOKEN"]
    headers = {
        "Authorization": f"Bearer " + TOKEN
    }
    response = requests.request("GET", url, headers=headers)
    return response.text

def get_history(entity_id="", days_delta=1):
    start_time = dt.datetime.now() - dt.timedelta(days=0 + days_delta)
    end_time = dt.datetime.now() - dt.timedelta(days=0)
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

def _update_db(self):
    """A terme cette function sera appellée ponctuellement pour populer la base de donnée avec les données les plus récentes"""
    for entity_id in self.ENTITY_IDS:
        if entity_id.split(".")[0]=="sensor":
            column_names={"state": "temperature", "last_changed": "date"}
        else:
            column_names={"last_changed": "date"}
        data = get_history(entity_id, days_delta=self.days_delta)
        df = build_history_df(data, column_names=column_names)
        self.populate_df(df, f"data/db/{entity_id.split('.')[1]}.csv")

def _populate_df(self, df_new: pd.DataFrame, csv_path: str):
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
        df_combined = df_combined.sort_values('date')
        
        df_combined.to_csv(csv_path, index=False)
    else:
        # If file doesn't exist, save the new DataFrame
        df_new.to_csv(csv_path, index=False)