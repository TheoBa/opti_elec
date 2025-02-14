import pandas as pd

def prepare_switch_df(switch_df):
    return (
        switch_df
        .assign(
            date=lambda df: pd.to_datetime(df['date']),
            time_delta_before_switch=lambda df: df['date'].diff(),
            time_delta_after_switch=lambda df: -df['date'].diff(-1),
            day=lambda df: df['date'].dt.date
        )
    )

def prepare_temperature_df(temperature_df):
    return (
        temperature_df
        .assign(
            date=lambda df: pd.to_datetime(df['date']),
            day=lambda df: df['date'].dt.date
        )
    )

def prepare_weather_df(weather_df):
    return (
        weather_df
        .rename(columns={"temperature_2m": "temperature"})
        .assign(
            date=lambda df: pd.to_datetime(df['date']),
            day=lambda df: df['date'].dt.date,
            all_day_temperature=lambda df: df.groupby('day')['temperature'].transform('mean'),
            roll5_avg_temperature=lambda df: df['temperature'].rolling(window=5).mean()
        )
    )