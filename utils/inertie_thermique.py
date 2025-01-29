import os
import pandas as pd
from utils.get_data import get_history, build_history_df
import datetime as dt
import numpy as np
import streamlit as st
import plotly.graph_objects as go


def _identify_switch_offs(self):
    cdt_off = self.switch_df.state == "off"
    cdt_before = self.switch_df.time_delta_before_switch >= dt.timedelta(minutes=30)
    cdt_after = self.switch_df.time_delta_after_switch >= dt.timedelta(hours=5)
    potential_switches = self.switch_df[cdt_off & cdt_before & cdt_after]
    
    # Check if we're in verification mode (on the verification page)
    if st.session_state.get('verification_mode', False):
        self.selected_switches_off = self.verify_switches(potential_switches, is_cooling=True)
    else:
        # Original behavior - use all potential switches
        self.selected_switches_off = potential_switches
        
    return self.selected_switches_off

def _identify_switch_ons(self):
    cdt_on = self.switch_df.state == "on"
    cdt_before = self.switch_df.time_delta_before_switch >= dt.timedelta(hours=5)
    cdt_after = self.switch_df.time_delta_after_switch >= dt.timedelta(hours=1)
    potential_switches = self.switch_df[cdt_on & cdt_before & cdt_after]
    
    # Check if we're in verification mode (on the verification page)
    if st.session_state.get('verification_mode', False):
        self.selected_switches_on = self.verify_switches(potential_switches, is_cooling=False)
    else:
        # Original behavior - use all potential switches
        self.selected_switches_on = potential_switches
        
    return self.selected_switches_on

def _select_temperature_after_switch(self, switch_event, time_delta: int = 5): 
    """
    Select temperature data for 5 hours after a given switch-off event.
    Returns a DataFrame containing temperature measurements during the cooling period.
    """
    self.temperature_int_df['date'] = pd.to_datetime(self.temperature_int_df['date'])

    # Convert temperature to float and remove non-numeric values
    self.temperature_int_df['temperature'] = pd.to_numeric(self.temperature_int_df['temperature'], errors='coerce')
    self.temperature_int_df = self.temperature_int_df.dropna(subset=['temperature'])

    start_time = switch_event['date']
    end_time = start_time + dt.timedelta(hours=time_delta)
    mask = (self.temperature_int_df['date'] >= start_time) & (self.temperature_int_df['date'] <= end_time)
    segment = self.temperature_int_df[mask].copy()
    segment['switch_period_start'] = start_time
    return segment

def _identify_min_max(self, segment, is_cooling=True):
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
    if is_cooling:
        max_temp_idx = segment['temperature'].idxmax()
        T0 = segment.loc[max_temp_idx, 'temperature']
        t0 = segment.loc[max_temp_idx, 'date']

        # Get the first temperature reading after t1
        t1 = t0 + dt.timedelta(hours=1)
        mask = (segment['date'] >= t1)
        T1 = segment[mask].iloc[0]['temperature']
        t1 = segment[mask].iloc[0]['date']
    else:
        min_temp_idx = segment['temperature'].idxmin()
        T0 = segment.loc[min_temp_idx, 'temperature']
        t0 = segment.loc[min_temp_idx, 'date']

        # Get the first temperature reading after t1
        t1 = t0 + dt.timedelta(hours=.5)
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

def get_T_ext_w_voisin(T_ext, consider_neighboors=True):
    if consider_neighboors:
        if T_ext>10:
            T_lim = T_ext
        elif T_ext>0:
            T_lim = 10
        else:
            T_lim = T_ext + 10
        return T_lim
    else:
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
    segments = pd.concat([self.select_temperature_after_switch(switch_event) for _, switch_event in self.selected_switches_off.iterrows()], ignore_index=True)

    tau_values = []
    total_periods = 0
    valid_periods = 0
    
    # Group by cooling period
    for period_start, segment in segments.groupby('switch_period_start'):
        total_periods += 1
        [T0, t0], [T1, t1] = self.identify_min_max(segment, is_cooling=True)
        t_margin = dt.timedelta(hours=5)
        T_ext = self.get_temperature_ext(t0 - t_margin, t1 + t_margin)
        delta_t = (t1 - t0).total_seconds() / 3600  # Convert to hours
        tau = (T0 - get_T_ext_w_voisin(T_ext, self.consider_neighboors)) * delta_t / (T0 - T1)
        # st.markdown(f"Text: {T_ext} - Tlim: {get_T_ext_w_voisin(T_ext)}")
        if tau <= 0:
            print("ERROR ERROR ERROR : Tau is <= 0 !!!")

        tau_values.append(tau)
        valid_periods += 1
    
    self.tau = np.mean(tau_values)
    st.session_state.tau_values = tau_values
    return {
        'tau_mean': np.mean(tau_values),
        'tau_std': np.std(tau_values),
        'tau_values': tau_values,
        'valid_periods': valid_periods,
        'total_periods': total_periods
    }

def _compute_tau2(self):
    """
    Compute tau values for all cooling periods using the formula:
    tau = (t1-t0)/ln((T0-Text)/(T1 - T_ext))
    
    Returns:
        dict: Dictionary containing:
            - 'tau_mean': mean tau value
            - 'tau_std': standard deviation of tau values
            - 'tau_values': list of individual tau values
            - 'valid_periods': number of valid cooling periods used
            - 'total_periods': total number of cooling periods found
    """
    self.identify_switch_offs()
    segments = pd.concat([self.select_temperature_after_switch(switch_event) for _, switch_event in self.selected_switches_off.iterrows()], ignore_index=True)

    tau_values = []
    total_periods = 0
    valid_periods = 0
    
    # Group by cooling period
    for period_start, segment in segments.groupby('switch_period_start'):
        total_periods += 1
        [T0, t0], [T1, t1] = self.identify_min_max(segment, is_cooling=True)
        t_margin = dt.timedelta(hours=5)
        T_ext = self.get_temperature_ext(t0 - t_margin, t1 + t_margin)
        delta_t = (t1 - t0).total_seconds() / 3600  # Convert to hours
        tau = delta_t/np.log((T0 - get_T_ext_w_voisin(T_ext, self.consider_neighboors))/(T1 - get_T_ext_w_voisin(T_ext, self.consider_neighboors)))
        if tau <= 0:
            print("ERROR ERROR ERROR : Tau is <= 0 !!!")

        tau_values.append(tau)
        valid_periods += 1
    
    self.tau = np.mean(tau_values)
    st.session_state.tau_values = tau_values
    return {
        'tau_mean': np.mean(tau_values),
        'tau_std': np.std(tau_values),
        'tau_values': tau_values,
        'valid_periods': valid_periods,
        'total_periods': total_periods
    }

def _compute_C(self):
    """
    Compute C values for all heating periods using the formula:
    C = tau*phi_rad / [tau*(T1-T0)/(t1-t0) + T0 - T_ext]
    
    Returns:
        dict: Dictionary containing:
            - 'C_mean': mean C value
            - 'C_std': standard deviation of C values
            - 'C_values': list of individual C values
            - 'valid_periods': number of valid heating periods used
            - 'total_periods': total number of heating periods found
    """
    self.identify_switch_ons()
    segments = pd.concat([self.select_temperature_after_switch(switch_event, time_delta=2) for _, switch_event in self.selected_switches_on.iterrows()], ignore_index=True)

    C_values = []
    total_periods = 0
    valid_periods = 0
    
    # Group by heating period
    for period_start, segment in segments.groupby('switch_period_start'):
        total_periods += 1
        [T0, t0], [T1, t1] = self.identify_min_max(segment, is_cooling=False)
        t_margin = dt.timedelta(hours=5)
        T_ext = self.get_temperature_ext(t0 - t_margin, t1 + t_margin)
        delta_t = (t1 - t0).total_seconds() / 3600  # Convert to hours
        
        tau = self.tau
        phi_rad = self.mean_consumption
        
        denominator = (T1 - T0) / delta_t + (T0 - get_T_ext_w_voisin(T_ext, self.consider_neighboors)) / tau
        if denominator != 0:
            C = phi_rad / denominator
            if C <= 0:
                print("ERROR ERROR ERROR : C is <= 0 !!!")
            C_values.append(C)
            valid_periods += 1
        else:
            print("ERROR ERROR ERROR : Denominator is 0 !!!")
    
    self.C = np.mean(C_values)
    st.session_state.C_values = C_values
    return {
        'C_mean': np.mean(C_values),
        'C_std': np.std(C_values),
        'C_values': C_values,
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

def _verify_switches(self, switch_events, is_cooling=True):
    """
    Interactive verification of switch events using Streamlit.
    
    Args:
        switch_events (pd.DataFrame): DataFrame containing switch events to verify
        is_cooling (bool): True if verifying switch-offs, False for switch-ons
        
    Returns:
        pd.DataFrame: Verified switch events
    """
    if 'verified_switches' not in st.session_state:
        st.session_state.verified_switches = {}
    
    event_type = 'switch_offs' if is_cooling else 'switch_ons'
    cache_key = f"{self._name}_{event_type}"
    
    # If already verified, return cached results
    if cache_key in st.session_state.verified_switches:
        return st.session_state.verified_switches[cache_key]
    
    switch_events = switch_events.reset_index(drop=True)
    verified_events = []
    
    with st.form(key=f"verify_{event_type}"):
        st.write(f"### Verify {event_type.replace('_', ' ').title()}")
        st.write(f"Total events to verify: {len(switch_events)}")
        
        # Store selections in a dictionary
        selections = {}
        
        for idx, switch_event in switch_events.iterrows():
            # Get temperature data around the switch event
            segment = self.select_temperature_after_switch(
                switch_event, 
                time_delta=5 if is_cooling else 2
            )
            
            # Create figure
            fig = go.Figure()
            
            # Add temperature trace
            fig.add_trace(go.Scatter(
                x=segment['date'],
                y=segment['temperature'],
                name='Interior Temperature',
                mode='lines+markers'
            ))
            
            # Update layout
            fig.update_layout(
                title=f"Switch Event at {switch_event['date']}",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                height=400
            )
            
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                event_to_metric = {"switch_offs": {"name": "tau", "values": st.session_state.tau_values}, "switch_ons": {"name": "C", "values": st.session_state.C_values}}
                st.metric(
                    label=f"Associated computed {event_to_metric[event_type]["name"]}",
                    value = round(event_to_metric[event_type]["values"][idx], 1)
                )
                selections[idx] = st.radio(
                    f"Keep this event? (Event {idx + 1}/{len(switch_events)})",
                    options=['Keep', 'Remove'],
                    key=f'selection_{event_type}_{idx}'
                )
            
            st.markdown("---")
        
        # Add submit button at the bottom of the form
        submitted = st.form_submit_button("Submit All Selections")
            
        if submitted:
            # Process selections
            for idx, selection in selections.items():
                if selection == 'Keep':
                    verified_events.append(switch_events.iloc[idx])
            
            verified_df = pd.DataFrame(verified_events)
            st.session_state.verified_switches[cache_key] = verified_df
            st.success("Selections saved successfully!")
            return verified_df
            
        # If form not submitted yet, return empty DataFrame
        return pd.DataFrame(columns=switch_events.columns)
