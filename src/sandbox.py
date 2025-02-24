import datetime as dt
import pandas as pd
from src.data_processing import prepare_weather_df

# This file contains the functions to build 24h  signals to feed a simulation. 
# The main idea is to enable a user - that fed his data to our modelisation and had his thermal parameters learned - to launch 24h simulations with imagined or forecasted data.
# He could then see how his thermal module would behave thanks to metrics and graphs displayed.

class Simulation:
    def __init__(self, mode="forecasted", parameters=[7.37e-3, 4e6, 71.8, 104, 4]):
        self.mode = mode
        self.parameters = parameters
        self.model = None
        self.radiation_signal = None
        self.temperature_ext_signal = None
        self.switch_signal = None
        self.temperature_int_0 = None

    def load_forecasted_data(self):
        self.forecasted_data_df = (
            pd.read_csv("data/db/weather.csv")
            .pipe(prepare_weather_df)
            .pipe(self.identify_forecast_timeframe)
            )
    
    def create_24h_simulation(self):

        self.model.features_df = self.build_sandbox_features_df()

        return

    @staticmethod
    def identify_forecast_timeframe(df):
        tomorrow = dt.datetime.date.today() + dt.timedelta(days=1)
        return (
            df
            .assign(
                date=lambda df: pd.to_datetime(df['date']),
                day=lambda df: df['date'].dt.date
            )
            .loc[lambda df: df['day'] == tomorrow]
            .drop(columns=['day'])
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
            self.temperature_ext_signal = self.forecasted_data_df[['date', 'direct_radiation']]
        elif self.mode == "past24h":
            pass
        elif self.mode == "custom":
            pass
        else:
            raise ValueError("Invalid mode for external temperature signal")

    def is_heating_signal():
        pass

    def build_sandbox_features_df():
        pass
