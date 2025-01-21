import os
import pandas as pd
from utils.get_data import get_history, build_history_df
import datetime as dt
import numpy as np
import streamlit as st


def _identify_switch_offs(self):
    self.switch_df['date'] = pd.to_datetime(self.switch_df['date'])
    self.switch_df['time_delta_before_switch'] = self.switch_df['date'].diff()
    self.switch_df["time_delta_after_switch"] = -self.switch_df['date'].diff(-1)
    cdt_off = self.switch_df.state == "off"
    cdt_before = self.switch_df.time_delta_before_switch >= dt.timedelta(minutes=30)
    cdt_after = self.switch_df.time_delta_after_switch >= dt.timedelta(hours=5)
    self.selected_switches_off = self.switch_df[cdt_off & cdt_before & cdt_after]

def _select_temperature_switch_offs(self, switch_event): 
    """
    Select temperature data for 5 hours after a given switch-off event.
    Returns a DataFrame containing temperature measurements during the cooling period.
    """
    self.temperature_int_df['date'] = pd.to_datetime(self.temperature_int_df['date'])

    # Convert temperature to float and remove non-numeric values
    self.temperature_int_df['temperature'] = pd.to_numeric(self.temperature_int_df['temperature'], errors='coerce')
    self.temperature_int_df = self.temperature_int_df.dropna(subset=['temperature'])

    start_time = switch_event['date']
    end_time = start_time + dt.timedelta(hours=5)
    mask = (self.temperature_int_df['date'] >= start_time) & (self.temperature_int_df['date'] <= end_time)
    segment = self.temperature_int_df[mask].copy()
    segment['cooling_period_start'] = start_time
    return segment 

def _identify_min_max(self, segment):
    """
    For a given temperature segment, identify:
    - [T0, t0]: Maximum temperature and its timestamp
    - [T1, t1]: Temperature and timestamp 1 hour after t0
    
    Args:
        segment (pd.DataFrame): DataFrame containing temperature measurements
        
    Returns:
        tuple: Two lists [T0, t0] and [T1, t1]
    """
    segment['date'] = pd.to_datetime(segment['date'])
    max_temp_idx = segment['temperature'].idxmax()
    T0 = segment.loc[max_temp_idx, 'temperature']
    t0 = segment.loc[max_temp_idx, 'date']
    
    # Get the first temperature reading after t1
    t1 = t0 + dt.timedelta(hours=1)
    mask = (segment['date'] >= t1)
    T1 = segment[mask].iloc[0]['temperature']
    t1 = segment[mask].iloc[0]['date']

    return [T0, t0], [T1, t1]

def _get_temperature_ext(self, t0, t1):
    """
    Get mean external temperature between t0 and t1.
    
    Args:
        t0 (datetime): Start timestamp
        t1 (datetime): End timestamp
        
    Returns:
        float: Mean external temperature during the period
    """
    self.temperature_ext_df['date'] = pd.to_datetime(self.temperature_ext_df['date'])
    mask = (self.temperature_ext_df['date'] >= t0) & (self.temperature_ext_df['date'] <= t1)
    temp_slice = self.temperature_ext_df[mask]
    T_ext = temp_slice['temperature'].mean()
    return T_ext

def _compute_tau(self):
    """
    Compute tau values for all cooling periods using the formula:
    tau = (T0 - T_ext)*(t1-t0)/(T0-T1)
    
    Returns:
        dict: Dictionary containing:
            - 'tau_mean': mean tau value
            - 'tau_std': standard deviation of tau values
            - 'tau_values': list of individual tau values
            - 'valid_periods': number of valid cooling periods used
            - 'total_periods': total number of cooling periods found
    """
    self.identify_switch_offs()
    segments = pd.concat([self.select_temperature_switch_offs(switch_event) for _, switch_event in self.selected_switches_off.iterrows()], ignore_index=True)

    tau_values = []
    total_periods = 0
    valid_periods = 0
    
    # Group by cooling period
    for period_start, segment in segments.groupby('cooling_period_start'):
        total_periods += 1
        [T0, t0], [T1, t1] = self.identify_min_max(segment)
        t_margin = dt.timedelta(hours=5)
        T_ext = self.get_temperature_ext(t0 - t_margin, t1 + t_margin)
        delta_t = (t1 - t0).total_seconds() / 3600  # Convert to hours
        tau = (T0 - T_ext) * delta_t / (T0 - T1)
        if tau <= 0:
            print("ERROR ERROR ERROR : Tau is <= 0 !!!")

        tau_values.append(tau)
        valid_periods += 1
    
    return {
        'tau_mean': np.mean(tau_values),
        'tau_std': np.std(tau_values),
        'tau_values': tau_values,
        'valid_periods': valid_periods,
        'total_periods': total_periods
    }

def _get_daily_consumption(self):
    """
    Calculate daily consumption by summing up the time when switches were turned on.
    Returns a DataFrame with:
        - day: date of consumption
        - uptime: total time switches were on (in hours)
        - conso (in kWh): consumption in kWh (uptime * mean_consumption / 1000)
    """
    self.switch_df['date'] = pd.to_datetime(self.switch_df['date'])
    self.switch_df['day'] = self.switch_df['date'].dt.date
    
    self.daily_consumption = (
        self.switch_df[self.switch_df["state"] == "on"]
        .groupby('day')['time_delta_after_switch']
        .sum()
        .reset_index()
        .rename(columns={'time_delta_after_switch': 'uptime'})
        .assign(
            uptime=lambda x: x['uptime'].dt.total_seconds() / 3600,  # Convert to hours
            **{'conso (in kWh)': lambda x: x['uptime'] * self.mean_consumption / 1000}  # Convert to kWh
        )
    )
    return self.daily_consumption
