import pandas as pd

def prepare_switch_df(switch_df):
    return (
        switch_df
        .assign(date=lambda df: pd.to_datetime(df['date']))
        .set_index('date').resample('5min').ffill().reset_index(drop=False)
    )

def prepare_temperature_df(temperature_df):
    return (
        temperature_df
        .assign(date=lambda df: pd.to_datetime(df['date']))
        .set_index('date').resample('5min').mean().interpolate().reset_index(drop=False)
    )

def prepare_weather_df(weather_df):
    return (
        weather_df
        .rename(columns={"temperature_2m": "temperature_ext"})
        .assign(date=lambda df: pd.to_datetime(df['date']))
        .set_index('date').resample('5min').ffill().reset_index(drop=False)
        .assign(
            day=lambda df: df['date'].dt.date,
            all_day_temperature=lambda df: df.groupby('day')['temperature_ext'].transform('mean'),
            roll5_avg_temperature=lambda df: df['temperature_ext'].rolling(window=5*20).mean(),
            direct_radiation=lambda df: df["direct_radiation"]/20
        )
    )