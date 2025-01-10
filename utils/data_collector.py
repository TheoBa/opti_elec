import time
import pandas as pd
from datetime import datetime
import os
from utils.get_data import get_data, parse_data_string, get_history, build_history_df

ENTITY_IDS = {
    "capteur_chambre_temperature": "sensor",
    "capteur_salon_temperature": "sensor",
    "paris_17eme_arrondissement_temperature": "sensor",
    "radiateur_bureau_switch": "input_boolean"
    }

 
def collect_and_store_history():
    for entity_id, prefix in ENTITY_IDS.items():
        data = get_history(entity_id, is_sensor=(prefix == 'sensor'))
        df = build_history_df(data, is_sensor=(prefix == 'sensor'))
        df.to_csv(f"data/{entity_id}.csv", index=False)



def collect_and_store_data():
    # Create data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')
    
    for entity_id, prefix in ENTITY_IDS.items():
        # Get data for the entity
        data = get_data(entity_id, is_sensor=(prefix == 'sensor'))
        parsed_data = parse_data_string(data)
        
        # Extract relevant information
        state = parsed_data["state"]
        if prefix=='sensor':
            state = float(state)
        timestamp = datetime.fromisoformat(parsed_data["last_changed"])
        
        # Create DataFrame for new row
        new_row = pd.DataFrame({
            'timestamp': [timestamp],
            prefix: [state]
        })
        
        # Define CSV file path
        csv_path = f'data/{entity_id}.csv'
        
        # If file exists, append; if not, create new file
        if os.path.exists(csv_path):
            new_row.to_csv(csv_path, mode='a', header=False, index=False)
        else:
            new_row.to_csv(csv_path, index=False)
