import streamlit as st
import pandas as pd
from pymeteosource.api import Meteosource
from pymeteosource.types import tiers,sections


def get_weather():
    YOUR_API_KEY = st.secrets["API_WEATHER"]
    YOUR_TIER = tiers.FREE
    meteosource = Meteosource(YOUR_API_KEY, YOUR_TIER)

    # Get the forecast for a given point
    forecast = meteosource.get_point_forecast(
        lat=48.864716,  # Latitude of the point
        lon=2.349014,  # Longitude of the point
        place_id=None,  # You can specify place_id instead of lat+lon
        sections=[sections.DAILY],  # Defaults to '("current", "hourly")'      
    )
    # forecast.daily[0]['temperature']
    st.markdown(forecast.daily[0]["afternoon"])
    df = forecast.daily.to_pandas()
    
    return df

def _build_forecast_features(self):
    """
    Creates a daily summary DataFrame from the external temperature measurements.
    
    Uses self.temperature_ext_df which must contain:
        - 'date': timestamp of the temperature measurement
        - 'temperature': temperature value
    
    Returns:
        pandas.DataFrame: A DataFrame with one row per day containing:
            - 'day': the date (without time)
            - 'Tmin': minimum temperature of the day
            - 'Tmax': maximum temperature of the day
            - 'Tmean': mean temperature of the day
    """
    self.forecast_features = (
        self.temperature_ext_df.copy()
        .assign(
            date=lambda df: pd.to_datetime(df['date']),
            day=lambda df: df['date'].dt.date,
        )
        .groupby('day')
        .agg(
            Tmin=('temperature', 'min'),
            Tmax=('temperature', 'max'),
            Tmean=('temperature', 'mean')
        )
        .reset_index()
        .merge(self.daily_consumption, on="day", how='inner')
    )

    return self.forecast_features
