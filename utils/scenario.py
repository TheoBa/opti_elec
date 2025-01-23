import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

class SimulationHome():
    """
    Object created to simulate a given module and its consumption accross a range of scenarios for a day
    """
    
    def init(
            self,
            name: str,
            T_0: str,
            T_ext: str,
            mean_consumption: int,
            tau: float,
            C: float,
            granularity: int = .25
    ) -> None:
        """Initialize the simulation"""
        self.name = name
        self.T_0 = T_0
        self.T_ext = T_ext
        self.phi_rad = mean_consumption
        self.tau = tau
        self.C = C
        self.granularity = granularity # time granularity in hours
        self.time = 0

    def temperature_evolution_heating(self, temp_start, t_heating):
        """
        T_int(t) = T_lim + (T_0 - T_lim)*exp(-t/tau)
        Where T_lim = T_ext + tau * phi_rad / C
        """
        T_lim = self.T_ext + self.tau*self.phi_rad/self.C
        return T_lim + (temp_start - T_lim)*np.exp(-(t_heating)/self.tau)
    
    def temperature_evolution_cooling(self, temp_start, t_cooling):
        """
        T_int(t) = T_ext + (T_0 - T_ext)*exp(-t/tau)
        """
        return self.T_ext + (temp_start - self.T_ext)*np.exp(-(t_cooling)/self.tau)
    
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
        st.markdown("Launch scenario computation")
        time = 0
        temperature = self.T_0
        is_heating = False
        data = [[time, temperature, is_heating]]
        while time < 7:
            time += self.granularity
            temperature = self.temperature_evolution_cooling(temperature, self.granularity)
            data += [[time, temperature, is_heating]]
        st.markdown(f"simu ok après 7h, time={time}")
        data += self.thermostat(temp_start=temperature, T_target=T_target, t_init=7, t_end=9, hysteresis=.4)
        temperature = data[-1][1]
        time = 9
        st.markdown(f"simu ok après 17h, time={data[-1][0]}, temp={data[-1][1]}")
        while time < 17:
            time += self.granularity
            temperature = self.temperature_evolution_cooling(temperature, self.granularity)
            data += [[time, temperature, is_heating]]
        data += self.thermostat(temp_start=temperature, T_target=T_target, t_init=17, t_end=24, hysteresis=.4)
        st.markdown(f"simulation over, time={time}")
        return data
    
    def plot_data(self, df: pd.DataFrame):
        fig = go.Figure()

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
