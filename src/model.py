import numpy as np
import pandas as pd
import streamlit as st
from src.data_processing import prepare_switch_df, prepare_temperature_df, prepare_weather_df


class TemperatureModel:
    def __init__(self, initial_params, P_consigne):
        self.features_df = None
        self.params = initial_params # Rth, C, alpha, Pvoisinnage
        self.P_consigne = P_consigne

    def load_data(self, PATH_FILES):
        self.temperature_ext_df = pd.read_csv(PATH_FILES["temperature_ext_csv"], sep=",")
        self.temperature_int_df = pd.read_csv(PATH_FILES["temperature_int_csv"], sep=",")
        self.switch_df = pd.read_csv(PATH_FILES["switch_csv"], sep=",")
        self.weather_df = pd.read_csv(PATH_FILES["weather_csv"], sep=",")

    def preprocess_data(self):
        self.temperature_ext_df = prepare_temperature_df(self.temperature_ext_df)
        self.temperature_int_df = prepare_temperature_df(self.temperature_int_df)
        self.switch_df = prepare_switch_df(self.switch_df)
        self.weather_df = prepare_weather_df(self.weather_df)

    def build_features_df(self):
        self.features_df = (
            self.temperature_ext_df.copy()
            .merge(self.temperature_int_df, on='date', how='outer', suffixes=["_ext", "_int"])
            .merge(self.switch_df, on='date', how='outer')
            .merge(self.weather_df, on='date', how='left')
            .loc[:, ['date', 'temperature_ext', 'temperature_ext2', 'all_day_temperature', 'roll5_avg_temperature', 'temperature_int', 'state', 'direct_radiation']]
            .loc[lambda x: x["date"]> '2025-01-04']
        )

    def cost_function(self, parameters):
        pred_df = self.predict(parameters)
        squared_errors = (pred_df["temperature_int"] - pred_df["T_int_pred"]) ** 2
        mse = squared_errors.mean()
        rmse = mse ** 0.5
        return rmse
    
    # TODO: other cost functions that would only compute rmse for a given timeframe
    # espacially the last 2 weeks should have more importance thant overall data
    # would enable the data scientist to eventually exclude a useless timeframe
    def cost_function_timeframe(self, parameters):
            pred_df = (
                self.predict(parameters)
                .loc[lambda x: x["date"] > self.opti_timeframe[0]]
                .loc[lambda x: x["date"] < self.opti_timeframe[1]]
            )
            squared_errors = (pred_df["temperature_int"] - pred_df["T_int_pred"]) ** 2
            mse = squared_errors.mean()
            rmse = mse ** 0.5
            return rmse

    def predict(self, parameters):
        """
        This function builds the predicted Tint(t) for a given set of parameter
        parameters is a list of 5 values
        - Rth positive float
        - C positive float
        - alpha_rad positive float
        - Pvoisinnage positive float
        - time shift of switch
        """
        prediction_df = (
            self.features_df.copy()
            .assign(
                state=lambda df: df["state"].shift(int(parameters[4])),
                day=lambda df: df['date'].dt.date,
                shape_t_ext=lambda df: 15-df["temperature_ext"],
                is_heating=lambda df: (df["state"]=="on").astype(int),
                Tlim=lambda df: (
                    df["temperature_ext"] + parameters[0] * (
                        self.P_consigne * df["is_heating"] + 
                        parameters[2] * df["direct_radiation"] + 
                        parameters[3] * df["shape_t_ext"]
                    )
                )
            )
            .reset_index(drop=True)
        )
        if self.debug_pred_df:
            st.dataframe(prediction_df)
        TINT_PRED = []
        for d in prediction_df.day.unique():
            pred_df = prediction_df[prediction_df.day==d].reset_index(drop=True)
            Tint_pred = [pred_df.temperature_int.loc[0]]
            for idx in range(1, len(pred_df.index)):
                Tlim = pred_df.Tlim.loc[idx]
                T0 = Tint_pred[-1]
                
                Tint_pred += [self.temperature_model(t=300, T0=T0, Tlim=Tlim, R=parameters[0], C=parameters[1])]
            TINT_PRED += Tint_pred

        prediction_df["T_int_pred"] = pd.Series(TINT_PRED)
        return prediction_df

    @staticmethod
    def temperature_model(t, T0, Tlim, R, C):
        return Tlim + (T0 - Tlim) * np.exp(-t / (R * C))

    def get_optimal_parameters(self, opti_timeframe=None):
        from src.optimizer import optimize_parameters

        initial_guess = [.005, 5e6, 0.1, 500, 5] # R, C, alpha, Pvoisin, time_shift switch / T

        if opti_timeframe:
            self.opti_timeframe = opti_timeframe
            opti_func = self.cost_function_timeframe
        else:
            opti_func = self.cost_function

        results = optimize_parameters(
            loss_function=opti_func,
            initial_guess=initial_guess,
        )
        # Display results
        st.header('Optimization Results')
        for method, result in results.items():
            if isinstance(result, dict) and result['success']:
                st.subheader(method)
                st.markdown(f"Parameters: {result['parameters']}")
                st.markdown(f"RMSE: {result['rmse']:.6f}")