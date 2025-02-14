import numpy as np
import pandas as pd
from src.data_processing import prepare_switch_df, prepare_temperature_df, prepare_weather_df


PATH_FILES = {
    "temperature_ext_csv": "data/db/paris_17eme_arrondissement_temperature.csv",
    "temperature_int_csv": "data/db/capteur_salon_temperature.csv",
    "switch_csv": "data/db/radiateur_bureau_switch.csv",
    "weather_csv": "data/db/weather.csv",
}


class TemperatureModel:
    def __init__(self, data, initial_params):
        self.data = data
        self.params = initial_params
        self.estimated_params = None

    def load_data(self, PATH_FILES):
        self.temperature_ext_df = pd.read_csv(PATH_FILES["temperature_ext_csv"], sep=",")
        self.temperature_int_df = pd.read_csv(PATH_FILES["temperature_int_csv"], sep=",")
        self.switch_df = pd.read_csv(PATH_FILES["switch_csv"], sep=",")
        self.weather_df = pd.read_csv(PATH_FILES["weather_csv"], sep=",")

    def preprocess_data(self):
        self.temperature_ext_df = prepare_temperature_df(self.temperature_ext_df)
        self.temperature_int_df = prepare_temperature_df(self.temperature_int_df)
        self.switch_df = prepare_switch_df(self.switch_df)
        self.weather_df = prepare_weather_df(self.weather_df)
        pass

    def estimate_parameters(self, t_data, Tint_data, Text_data, P_radiateur, is_switch_on, P_ensoleillement, alpha_initial):

        def cost_function(params):
            Tlim = Text_data + params[0] * (P_radiateur * is_switch_on + P_ensoleillement * params[1])
            T0 = Tint_data[0]
            T_pred = self.temperature_model(t_data, T0, Tlim, params[2], params[3])
            return np.sum((Tint_data - T_pred) ** 2)
        
        self.estimated_params = ...  # Résultat de l'estimation

    def predict(self, t):
        # Méthode pour prédire la température à un instant t
        Tlim = self.data['Text'] + self.estimated_params[0] * (
            self.data['P_radiateur'] * self.data['is_switch_on'] +
            self.data['P_ensoleillement'] * self.estimated_params[1]
        )
        T0 = self.data['Tint'][0]
        return self.temperature_model(t, T0, Tlim, self.estimated_params[2], self.estimated_params[3])

    @staticmethod
    def temperature_model(t, T0, Tlim, R, C):
        return Tlim + (T0 - Tlim) * np.exp(-t / (R * C))

