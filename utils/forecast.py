import streamlit as st
import pandas as pd
from pymeteosource.api import Meteosource
from pymeteosource.types import tiers, sections
import datetime as dt


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

def analyze_temperature_correlations(df):
    """
    Displays correlations between temperature features and heater uptime in a simple table.
    
    Args:
        df: DataFrame containing:
            - day: datetime column
            - Tmin, Tmax, Tmean: temperature features
            - uptime: daily heater uptime
    """
    # Select only numerical columns and calculate correlations with uptime
    numerical_cols = ['Tmin', 'Tmax', 'Tmean']
    correlations = df[numerical_cols].corrwith(df['uptime']).sort_values(ascending=False)
    
    # Create a DataFrame for display
    correlation_df = pd.DataFrame({
        'Feature': correlations.index,
        'Correlation with Uptime': correlations.values.round(3)
    })
    
    st.write("### Correlations with Uptime")
    return correlation_df

def get_temp_day(weather_df, day):
    forecast_df = (
        weather_df[["day", "all_day_temperature", "date"]][weather_df["day"] == day]
        .reset_index(drop=True)
        )
    return forecast_df["all_day_temperature"].loc[0]

def get_past_weather_data(
        date_from=dt.datetime(2025, 1, 3),
        date_to=dt.datetime(2025, 2, 6),
        lat=48.864716,
        lon=2.349014
        ):
    YOUR_API_KEY = st.secrets["API_WEATHER"]
    YOUR_TIER = tiers.FREE
    meteosource = Meteosource(YOUR_API_KEY, YOUR_TIER)

def get_past_weather_data2(past_days=5, forecast_days=3):
    import openmeteo_requests

    import requests_cache
    import pandas as pd
    from retry_requests import retry

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 48.864716,
        "longitude": 2.349014,
        "hourly": ["temperature_2m", "cloud_cover", "is_day", "direct_radiation"],
	    "timezone": "auto",
        "past_days": past_days,
        "forecast_days": forecast_days
    }
    responses = openmeteo.weather_api(url, params=params)

    response = responses[0]
    hourly = response.Hourly()

    hourly_variables = [hourly.Variables(i).ValuesAsNumpy() for i in range(len(params["hourly"]))]

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end = pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    for i, var in enumerate(params["hourly"]):
        hourly_data[var] = hourly_variables[i]

    hourly_dataframe = pd.DataFrame(data = hourly_data)
    return hourly_dataframe