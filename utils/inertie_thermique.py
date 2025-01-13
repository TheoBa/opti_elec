import pandas as pd
from utils.get_data import get_history, build_history_df

class ClientModule():
    """Object created to monitor each client's Flat properties"""
    
    def init(
            self,
            name: str,
            temperature_interieur_id: str,
            temperature_exterieur_id: str,
            switch_id: str,
            days_delta: int
    ) -> None:
        """Initialize the module"""
        self._name = name
        self.temperature_interieur_id = temperature_interieur_id
        self.temperature_exterieur_id = temperature_exterieur_id
        self.switch_id = switch_id
        self.ENTITY_IDS = [
             "sensor.capteur_salon_temperature",
             "sensor.paris_17eme_arrondissement_temperature",
             "input_boolean.radiateur_bureau_switch"
             ]
        self.days_delta = days_delta

    def update_db(self):
        """A terme cette function sera appellée ponctuellement pour populer la base de donnée avec les données les plus récentes"""
        for entity_id in self.ENTITY_IDS:
            if entity_id.split(".")[0]=="sensor":
                column_names={"state": "temperature", "last_changed": "date"}
            else:
                column_names={"last_changed": "date"}
            data = get_history(entity_id, days_delta=self.days_delta)
            df = build_history_df(data, column_names=column_names)
            df.to_csv(f"data/db/{entity_id.split(".")[1]}.csv", index=False)
    
    def load_df(self):
        self.temperature_ext_df = pd.read_csv("data/db/paris_17eme_arrondissement_temperature.csv", sep=",")
        self.temperature_int_df = pd.read_csv("data/db/capteur_salon_temperature.csv", sep=",")
        self.switch_df = pd.read_csv("data/db/radiateur_bureau_switch.csv", sep=",")

    def identify_switch_offs(self):
        self.switch_df['date'] = pd.to_datetime(self.switch_df['date'])
        self.switch_df['time_delta'] = self.switch_df['date'].diff()
        return self.switch_df