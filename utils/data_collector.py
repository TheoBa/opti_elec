import time
import pandas as pd
from datetime import datetime
import os
from get_data import get_data, parse_data_string

ENTITY_IDS = {
    "capteur_chambre_temperature": "sensor",
    "capteur_salon_temperature": "sensor",
    "paris_17eme_arrondissement_temperature": "sensor",
    "radiateur_bureau_switch": "input_boolean"
    }

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

def main():
    while True:
        try:
            collect_and_store_data()
            print(f"Data collected at {datetime.now()}")
        except Exception as e:
            print(f"Error collecting data: {e}")
        
        # Wait for 10 minutes
        time.sleep(600)

if __name__ == "__main__":
    main() 