import datetime as dt
import pandas as pd
from src.data_processing import prepare_weather_df
from src.model import compute_temperature_int
import streamlit as st

# This file contains the functions to build 24h  signals to feed a simulation. 
# The main idea is to enable a user - that fed his data to our modelisation and had his thermal parameters learned - to launch 24h simulations with imagined or forecasted data.
# He could then see how his thermal module would behave thanks to metrics and graphs displayed.

class Simulation:
    def __init__(self, module_config, mode="forecasted", parameters=[7.37e-3, 4e6, 71.8, 104, 4]):
        self.mode = mode
        self.parameters = parameters
        self.P_consigne = 2500
        self.temperature_int_0 = 15
        self.target_temperature = 19
        self.hysteresis = 0.5
        self.simulation_df = None
        self.module_config = module_config

    def load_forecasted_data(self):
        self.forecasted_data_df = (
            pd.read_csv(f"data/{self.module_config["db_name"]}/weather.csv")
            .pipe(prepare_weather_df)
            .pipe(self.filter_forecast_timeframe)
            .assign(
                hour=lambda df: df['date'].dt.hour,
                minute=lambda df: df['date'].dt.minute
            )
            .rename(columns={"temperature": "temperature_ext"})
            .loc[:,["date", "hour", "minute", "temperature_ext", "direct_radiation"]]
            )

    @staticmethod
    def filter_forecast_timeframe(df):
        tomorrow = dt.date.today() + dt.timedelta(days=1)
        return (
            df
            .assign(
                date=lambda df: pd.to_datetime(df['date']),
                day=lambda df: df['date'].dt.date,
                hour=lambda df: df['date'].dt.hour,
                minute=lambda df: df['date'].dt.minute
            )
            .loc[lambda df: df['day'] == tomorrow]
        )

    def build_radiation_signal(self):
        if self.mode == "forecasted":
            self.radiation_signal = self.forecasted_data_df[['date', 'direct_radiation']]
        elif self.mode == "past24h":
            pass
        elif self.mode == "custom":
            pass
        else:
            raise ValueError("Invalid mode for external temperature signal")
        pass

    def build_temp_ext_signal(self):
        if self.mode == "forecasted":
            self.temperature_ext_signal = self.forecasted_data_df[['date', 'temperature_2m']].rename(columns={'temperature_2m': 'temperature_ext'})
        elif self.mode == "past24h":
            pass
        elif self.mode == "custom":
            pass
        else:
            raise ValueError("Invalid mode for external temperature signal")

    def create_simulation_features(self, heating_scenario):
        """
        This function builds the switch signal from heating_scenario provided by the user.
        The switch signal is a binary signal that indicates whether the thermostat is on or off.
        It follows the proposed modelisation (currently 2.0.0 or V2)
        :param:
        heating_scenario: pd.DataFrame
        :return:
        switch_df: pd.DataFrame
        """
        features_df = (
            self.forecasted_data_df.copy()
            .merge(self.build_scenario(heating_scenario), how='left', on=["hour", "minute"])
            .sort_values(by=['date'])
            .fillna(method='ffill')
            .fillna({'thermostat_state': "off"})
            .reset_index(drop=True)
            .assign(
                shape_t_ext=lambda df: 15-df["temperature_ext"],
                P_consigne=self.P_consigne
                )
            )
        self.features_df = features_df

    @staticmethod
    def compute_Tlim(features_row, parameters, is_heating):
        return (
            features_row["temperature_ext"] + parameters[0] * (
                features_row["P_consigne"] * is_heating +
                parameters[2] * features_row["direct_radiation"] +
                parameters[3] * features_row["shape_t_ext"]
            )
        )

    def compute_temperature_int(self):
        parameters = self.parameters
        is_heating = [0]
        Tlim = [0] # Any init would work as Tlim[0] is not used
        T_int_pred = [self.temperature_int_0]
        for i in range(1, int(parameters[4])):
            is_heating += [0]
            Tlim += [self.compute_Tlim(self.features_df.iloc[i], parameters, is_heating[-1])]
            T_int_pred.append(compute_temperature_int(t=300, T0=T_int_pred[-1], Tlim=Tlim[-1], R=parameters[0], C=parameters[1]))
        
        for i in range(int(parameters[4]), len(self.features_df)):
            if self.features_df['thermostat_state'].iloc[i] == "on":
                # BLOC FONCTIONNEL DE THERMOSTAT A ISOLER ET FONCTIONNALISER A TERME
                if is_heating[-1] == 0:
                    if (T_int_pred[-int(parameters[4])] > self.target_temperature - self.hysteresis):
                        is_heating += [0]
                    else:
                        is_heating += [1]
                else:
                    if (T_int_pred[-int(parameters[4])] < self.target_temperature + self.hysteresis):
                        is_heating += [1]
                    else:
                        is_heating += [0]
                # FIN BLOC
            else:
                is_heating += [0]
            Tlim += [self.compute_Tlim(self.features_df.iloc[i], parameters, is_heating[-1])]
            T_int_pred.append(compute_temperature_int(t=300, T0=T_int_pred[-1], Tlim=Tlim[-1], R=parameters[0], C=parameters[1]))
        
        self.simulation_df = self.features_df.copy()
        self.simulation_df["is_heating"] = pd.Series(is_heating)
        self.simulation_df["Tlim"] = pd.Series(Tlim)
        self.simulation_df["T_int_pred"] = pd.Series(T_int_pred)

    def build_scenario(self, heating_scenario: str):
        if heating_scenario == "teletravail":
            scenario_df = pd.DataFrame([
                [9, 0, "on"],
                [22, 0, "off"]
                ],
                columns=['hour', 'minute', 'thermostat_state']
            )
        elif heating_scenario == "normal":
            scenario_df = pd.DataFrame([
                [7, 0, "on"],
                [9, 0, "off"],
                [18, 0, "on"], 
                [22, 0, "off"]
                ],
                columns=['hour', 'minute', 'thermostat_state']
            )
        elif heating_scenario == "off":
            scenario_df = pd.DataFrame([
                [0, 0, "off"],
                ],
                columns=['hour', 'minute', 'thermostat_state']
            )
        return scenario_df
    
    def compute_scenarios_consumption(self):
        """
        Calculate consumption associated to studied scenario.
        Compute uptime: total time heaters were on (in hours)
        Returns conso (in kWh): consumption in kWh (uptime * P_consigne / 1000)
        """
        uptime = self.simulation_df.is_heating.sum() * 300 / 3600 # Convert to hours
        conso = uptime * self.P_consigne / 1000 # Convert to kWh
        return round(conso, 2)
