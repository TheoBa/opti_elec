import numpy as np


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
                temperature = self.temperature_evolution_heating(self, temperature, time)
                is_heating = True
            elif temperature >= T_target + hysteresis:
                temperature = self.temperature_evolution_cooling(self, temperature, time)
                is_heating = False
            else: # if temperature within the hysteresis
                if is_heating:
                    temperature = self.temperature_evolution_heating(self, temperature, time)
                else:
                    temperature = self.temperature_evolution_cooling(self, temperature, time)
            data += [[time, temperature, is_heating]]
        return data

    
    def scenario_1(self):
        """
        Thermostat entre 7h et 9h, entre 17h et minuit
        Off le reste du temps
        """
        time = 0
        temperature = self.T_0
        is_heating = False
        data = [[time, temperature, is_heating]]
        for t in range(0, 7, self.granularity):
            1 == 2
        return 
