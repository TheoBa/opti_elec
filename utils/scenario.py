import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from utils.inertie_thermique import get_T_ext_w_voisin


SCENARIOS = {
    "Full thermostat": "scenario_full_thermostat",
    "Thermostat de 7 à 9 puis 17 à minuit":  "scenario_1"
    }


class SimulationHome():
    """
    Object created to simulate a given module and its consumption accross a range of scenarios for a day
    """
    
    def init(
            self,
            name: str,
            T_0: str,
            T_ext: str,
            T_target: str,
            mean_consumption: int,
            tau: float,
            C: float,
            granularity: int = .25,
            consider_neighboors: bool = True
    ) -> None:
        """Initialize the simulation"""
        self.name = name
        self.T_0 = T_0
        self.T_ext = T_ext
        self.T_target = T_target
        self.phi_rad = mean_consumption
        self.tau = tau
        self.C = C
        self.granularity = granularity # time granularity in hours
        self.time = 0
        self.consider_neighboors = consider_neighboors

    def temperature_evolution_heating(self, temp_start, t_heating):
        """
        T_int(t) = T_lim + (T_0 - T_lim)*exp(-t/tau)
        Where T_lim = T_ext + tau * phi_rad / C
        """
        T_lim = get_T_ext_w_voisin(self.T_ext, self.consider_neighboors) + self.tau*self.phi_rad/self.C
        return T_lim + (temp_start - T_lim)*np.exp(-(t_heating)/self.tau)
    
    def temperature_evolution_cooling(self, temp_start, t_cooling):
        """
        T_int(t) = T_ext + (T_0 - T_ext)*exp(-t/tau)
        """
        return get_T_ext_w_voisin(self.T_ext, self.consider_neighboors) + (temp_start - get_T_ext_w_voisin(self.T_ext, self.consider_neighboors))*np.exp(-(t_cooling)/self.tau)
    
    def thermostat(self, temp_start, T_target, t_init, t_end, hysteresis = 0.4):
        time = t_init
        temperature = temp_start
        is_heating = False
        data = [[time, temperature, is_heating]]
        while time < t_end:
            time += self.granularity
            if temperature < T_target - hysteresis:
                temperature = self.temperature_evolution_heating(temperature, self.granularity)
                is_heating = True
            elif temperature >= T_target + hysteresis:
                temperature = self.temperature_evolution_cooling(temperature, self.granularity)
                is_heating = False
            else: # if temperature within the hysteresis
                if is_heating:
                    temperature = self.temperature_evolution_heating(temperature, self.granularity)
                else:
                    temperature = self.temperature_evolution_cooling(temperature, self.granularity)
            data += [[time, temperature, is_heating]]
        return data

    def scenario_1(self, T_target):
        """
        Thermostat entre 7h et 9h, entre 17h et minuit
        Off le reste du temps
        """
        time = 0
        temperature = self.T_0
        is_heating = False
        data = [[time, temperature, is_heating]]
        while time < 7:
            time += self.granularity
            temperature = self.temperature_evolution_cooling(temperature, self.granularity)
            data += [[time, temperature, is_heating]]
        data += self.thermostat(temp_start=temperature, T_target=T_target, t_init=7, t_end=9, hysteresis=.4)
        temperature = data[-1][1]
        time = 9
        while time < 17:
            time += self.granularity
            temperature = self.temperature_evolution_cooling(temperature, self.granularity)
            data += [[time, temperature, is_heating]]
        data += self.thermostat(temp_start=temperature, T_target=T_target, t_init=17, t_end=24, hysteresis=.4)
        return data
    
    def scenario_full_thermostat(self, T_target):
        """
        Thermostat tout le temps
        """
        time = 0
        temperature = self.T_0
        is_heating = False
        data = [[time, temperature, is_heating]]
        data += self.thermostat(temp_start=temperature, T_target=T_target, t_init=time, t_end=24, hysteresis=.4)
        return data
    
    def pick_scenario(self, scenario_name):
        if scenario_name=="Full thermostat":
            return self.scenario_full_thermostat(T_target=self.T_target)
        elif scenario_name=="Thermostat de 7 à 9 puis 17 à minuit":
            return self.scenario_1(T_target=self.T_target)
    
    def plot_data(self, df: pd.DataFrame):
        fig = go.Figure()

        # Add comfort zone shaded area
        fig.add_trace(
            go.Scatter(
                x=[0, 24],  # Full time range
                y=[self.T_target + 1, self.T_target + 1],
                fill=None,
                mode='lines',
                line=dict(color='rgba(168, 168, 168, 0.3)', width=0),
                showlegend=False,
                hoverinfo='skip'
            )
        )
        fig.add_trace(
            go.Scatter(
                x=[0, 24],  # Full time range
                y=[self.T_target - 1, self.T_target - 1],
                fill='tonexty',
                mode='lines',
                line=dict(color='rgba(168, 168, 168, 0.3)', width=0),
                name='Comfort Zone',
                hoverinfo='skip'
            )
        )

        # Add external temperature line
        fig.add_trace(
            go.Scatter(
                x=[0, 24],  # Full time range
                y=[self.T_ext, self.T_ext],
                name="External Temperature",
                line=dict(color='green', dash='dash'),
                yaxis="y"
            )
        )

        # Add temperature trace
        fig.add_trace(
            go.Scatter(
                x=df['time'],
                y=df['temperature'],
                name="Temperature",
                line=dict(color='red'),
                yaxis="y"
            )
        )

        # Add heating status trace
        fig.add_trace(
            go.Scatter(
                x=df['time'],
                y=df['switch'].astype(int),
                name="Heating Status",
                line=dict(color='blue', shape='hv'),
                yaxis="y2"
            )
        )

        # Update layout with secondary y-axis
        fig.update_layout(
            title=f'Temperature Evolution and Heating Status - {self.name}',
            xaxis=dict(title="Time (hours)"),
            yaxis=dict(
                title="Temperature (°C)",
                titlefont=dict(color="red"),
                tickfont=dict(color="red")
            ),
            yaxis2=dict(
                title="Heating Status",
                titlefont=dict(color="blue"),
                tickfont=dict(color="blue"),
                overlaying="y",
                side="right",
                range=[-1, 2],
                tickvals=[0, 1],
                ticktext=["OFF", "ON"]
            ),
            showlegend=True
        )

        return fig

    def get_daily_consumption(self, df: pd.DataFrame):
        """
        Calculate daily energy consumption based on heater operation time
        
        Args:
            data: pd.Dataframe with columns [time, temperature, switch]
            
        Returns:
            float: Daily energy consumption in kWh
        """
        total_heating_time = 0
        
        for i in range(1, len(df.index)):
            if df.loc[i, 'switch']:
                total_heating_time += self.granularity
        
        # Calculate energy consumption in kWh
        # Power (W) * time (h) / 1000 to convert from Joules to kWh
        daily_consumption = self.phi_rad * total_heating_time / 1000
        
        return total_heating_time, daily_consumption
    
    def time_to_target(self, delta_T):
        """
        Compute time it takes to reach target temperature from a delta_T below for the given module
        """
        T_lim = get_T_ext_w_voisin(self.T_ext, self.consider_neighboors) + self.tau*self.phi_rad/self.C
        T_init = (self.T_target - delta_T)
        time = - 60 * self.tau * np.log( (self.T_target - T_lim) / (T_init- T_lim) )
        return round(time)