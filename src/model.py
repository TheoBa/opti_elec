import numpy as np
import pandas as pd
import streamlit as st
import datetime as dt
from src.data_loader import populate_database
from src.data_processing import prepare_switch_df, prepare_temperature_df, prepare_weather_df
import plotly.graph_objects as go
from src.optimizer import optimize_parameters


class TemperatureModel:
    def __init__(self, module_config):
        self.features_df = None
        self.P_consigne = module_config["P_consigne"]
        self.module_config = module_config

    def load_data(self):
        for k, v in self.module_config["entities"].items():
            setattr(self, f"{k}_df", pd.read_csv(f"data/{self.module_config["db_name"]}/{k}.csv", sep=","))
        self.weather_df = pd.read_csv(f"data/{self.module_config["db_name"]}/weather.csv", sep=",")

    def preprocess_data(self):
        self.temperature_int_df = prepare_temperature_df(self.temperature_int_df)
        self.switch_df = prepare_switch_df(self.switch_df)
        self.weather_df = prepare_weather_df(self.weather_df)

    def build_features_df(self):
        self.features_df = (
            self.weather_df.copy()
            .merge(self.temperature_int_df, on='date', how='right', suffixes=["_ext", "_int"])
            .merge(self.switch_df, on='date', how='outer')
            .loc[:, ['date', 'temperature_ext', 'all_day_temperature', 'roll5_avg_temperature', 'temperature_int', 'state', 'direct_radiation']]
            .loc[lambda x: x["date"]> '2025-01-04']
        )

    def cost_function_wrapped_RMSE(self, parameters):
        pred_df = self.predict(parameters)
        return get_rmse(pred_df)
    
    def cost_function_wrapped_MAE(self, parameters):
        pred_df = self.predict(parameters)
        return get_mae(pred_df)

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
        pred_df = getattr(self, "pred_df", self.features_df.copy())
        prediction_df = (
            pred_df
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
        if getattr(self, "debug_pred_df", False):
            st.dataframe(prediction_df)
        TINT_PRED = []
        for d in prediction_df.day.unique():
            pred_df = prediction_df[prediction_df.day==d].reset_index(drop=True)
            Tint_pred = [pred_df.temperature_int.loc[0]]
            for idx in range(1, len(pred_df.index)):
                Tlim = pred_df.Tlim.loc[idx]
                T0 = Tint_pred[-1]
                
                Tint_pred += [compute_temperature_int(t=300, T0=T0, Tlim=Tlim, R=parameters[0], C=parameters[1])]
            TINT_PRED += Tint_pred

        prediction_df["T_int_pred"] = pd.Series(TINT_PRED)
        return prediction_df

    @staticmethod
    def select_timeframe(df, predict_timeframe):
        return (
            df.copy()
            .loc[lambda x: x["date"] > predict_timeframe[0]]
            .loc[lambda x: x["date"] < predict_timeframe[1]]
        )
    
    def log_run(self, train_timeframe, temp_min, temp_max):
        date = dt.datetime.now()
        params = self.optimal_parameters
        pred_df = self.predict(params)
        module_name = self.module_config["module_name"]
        row = [date, module_name, train_timeframe] + list(params)
        df = pd.DataFrame([row], columns=["date", "module_name", "train_timeframe", "R", "C", "alpha", "Pvoisin", "time_shift"])
        df = df.assign(
            rmse=get_rmse(pred_df),
            mae=get_mae(pred_df),
            temp_min=temp_min,
            temp_max=temp_max,
        )
        populate_database(df, "data/logs/runs.csv")

    def get_optimal_parameters(self, train_timeframe=None, temp_min=None, temp_max=None):
        initial_guess = [1e-2, 4.3e6, 87, 65.5, 2] # R, C, alpha, Pvoisin, time_shift switch / T

        if train_timeframe:
            self.pred_df = self.select_timeframe(self.features_df, train_timeframe)
        elif (temp_min or temp_max):
            self.pred_df = select_features_from_temperature_window(self.features_df, temp_min, temp_max)
            if len(self.pred_df.index) == 0:
                self.pred_df = self.features_df
                st.warning("No data in temperature window, using all data")
                temp_max = None
                temp_min = None
        else:
            self.pred_df = self.features_df
            
        # opti_func = self.cost_function_wrapped_MAE
        opti_func = self.cost_function_wrapped_RMSE

        results = optimize_parameters(
            loss_function=opti_func,
            initial_guess=initial_guess,
        )
        # Store the optimal parameters
        self.optimal_parameters = None
        # Display results
        st.header('Optimization Results')
        for method, result in results.items():
            if isinstance(result, dict) and result['success']:
                st.subheader(method)
                st.markdown(f"Parameters: {result['parameters']}")
                st.markdown(f"RMSE: {result['rmse']:.6f}")
                self.optimal_parameters = result['parameters']
                self.log_run(train_timeframe, temp_min, temp_max)

    def test_model(self, test_timeframe=None, test_parameters=None, use_optimal_parameters=False):
        """"
        Test the model on a given timeframe with the given parameters.
        if test_parameters is "optimal", use the optimal parameters found by the optimizer.
        if test_parameters is None, return an error.
        if test_timeframe is None, return an error.
        """
        if test_timeframe is None:
            st.error('Please select a test timeframe.')
            return
        if test_parameters is None:
            st.error('Please select test parameters.')
            return
        if use_optimal_parameters:
            test_parameters = self.optimal_parameters
        self.pred_df = self.select_timeframe(self.features_df,test_timeframe)
        test_df = self.predict(test_parameters)
        rmse = self.cost_function_wrapped(test_parameters)
        return test_df, rmse
    
    def plot_paintings(self, parameters):
        """
        Plot Tlim contributions as a stacked area chart showing how:
        Tlim = T_ext + T_heating + T_radiation + T_voisin
        """
        today = dt.date.today().strftime("%Y-%m-%d")
        lower_bound = (dt.datetime.strptime(today, "%Y-%m-%d") - dt.timedelta(days=10)).strftime("%Y-%m-%d")
        plot_timeframe = [str(lower_bound), str(today)]
        df = (
            self.features_df.copy()
            .loc[lambda x: x["date"] > plot_timeframe[0]]
            .loc[lambda x: x["date"] < plot_timeframe[1]]
            .assign(
                state=lambda df: df["state"].shift(int(parameters[4])),
                shape_t_ext=lambda df: 15-df["temperature_ext"],
                is_heating=lambda df: (df["state"]=="on").astype(int),
                T_heating=lambda df: parameters[0] * self.P_consigne * df["is_heating"],
                T_radiation=lambda df: parameters[0] * parameters[2] * df["direct_radiation"],
                T_voisin=lambda df: parameters[0] * parameters[3] * df["shape_t_ext"],
                T_lim=lambda df: df["temperature_ext"] + df["T_heating"] + df["T_radiation"] + df["T_voisin"],
            )
        )
        fig = go.Figure()

        # Add each contribution as a separate bar in the bar chart
        for contribution in ['temperature_ext', 'T_voisin', 'T_radiation', 'T_heating']:
            fig.add_trace(
                go.Bar(
                    x=df['date'],
                    y=df[contribution],
                    name=contribution
                )
            )

        fig.update_layout(
            title='Temperature Limit Contributions',
            xaxis_title='Date',
            yaxis_title='Temperature (°C)',
            showlegend=True,
            barmode='stack'  # This makes the bar chart stacked
        )

        st.plotly_chart(fig)


def compute_temperature_int(t, T0, Tlim, R, C):
    return Tlim + (T0 - Tlim) * np.exp(-t / (R * C))

def get_rmse(pred_df):
        squared_errors = (pred_df["temperature_int"] - pred_df["T_int_pred"]) ** 2
        mse = squared_errors.mean()
        rmse = mse ** 0.5
        return rmse

def get_mae(pred_df):
        abs_error = abs(pred_df["temperature_int"] - pred_df["T_int_pred"])
        mae = abs_error.mean()
        return mae

def select_features_from_temperature_window(features_df, temp_min=None, temp_max=None):
    if (temp_min and temp_max):
        return features_df.loc[lambda df: (df["all_day_temperature"] > temp_min) & (df["all_day_temperature"] < temp_max)]
    elif temp_min:
            return features_df.loc[lambda df: df["all_day_temperature"] > temp_min]
    elif temp_max:
        return features_df.loc[lambda df: df["all_day_temperature"] < temp_max]
    else:
        return features_df