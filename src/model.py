import numpy as np
import pandas as pd
from src.data_processing import prepare_switch_df, prepare_temperature_df, prepare_weather_df


class TemperatureModel:
    def __init__(self, initial_params):
        self.features_df = None
        self.params = initial_params

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

    def build_features_df(self):
        self.features_df = (
            self.temperature_ext_df.copy()
            .merge(self.temperature_int_df, on='date', how='outer', suffixes=["_ext", "_int"])
            .merge(self.switch_df, on='date', how='outer')
            .merge(self.weather_df, on='date', how='left')
            .loc[:, ['date', 'temperature_ext', 'temperature_ext2', 'all_day_temperature', 'roll5_avg_temperature', 'temperature_int', 'state', 'direct_radiation']]
            .loc[lambda x: x["date"]> '2025-01-04']
        )

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

