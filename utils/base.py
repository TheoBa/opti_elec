import pandas as pd
from utils.get_data import _update_db, _populate_df
from utils.inertie_thermique import _identify_switch_offs, _select_temperature_switch_offs,\
       _identify_min_max, _get_temperature_ext, _compute_tau, _get_daily_consumption
from utils.forecast import _build_forecast_features


class HomeModule():
    """Object created to monitor each client's Flat properties"""
    
    def init(
            self,
            name: str,
            temperature_interieur_id: str,
            temperature_exterieur_id: str,
            switch_id: str,
            days_delta: int,
            mean_consumption: int
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
        self.mean_consumption = mean_consumption

    def update_db(self):
        return _update_db(self)

    def populate_df(self, df_new: pd.DataFrame, csv_path: str):
        return _populate_df(self, df_new, csv_path)

    def load_df(self):
        self.temperature_ext_df = pd.read_csv("data/db/paris_17eme_arrondissement_temperature.csv", sep=",")
        self.temperature_int_df = pd.read_csv("data/db/capteur_salon_temperature.csv", sep=",")
        self.switch_df = pd.read_csv("data/db/radiateur_bureau_switch.csv", sep=",")

    def identify_switch_offs(self):
        return _identify_switch_offs(self)
    
    def select_temperature_switch_offs(self, switch_event): 
        return _select_temperature_switch_offs(self, switch_event)
    
    def identify_min_max(self, segment):
        return _identify_min_max(self, segment)

    def get_temperature_ext(self, t0, t1):
        return _get_temperature_ext(self, t0, t1)

    def compute_tau(self):
        return _compute_tau(self)
    
    def get_daily_consumption(self):
        return _get_daily_consumption(self)

    def build_forecast_features(self):
        return _build_forecast_features(self)