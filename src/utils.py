import pandas as pd

def prepare_logs():
    return (
        pd.read_csv("data/logs/runs.csv", sep=',')
        .assign(date=lambda x: pd.to_datetime(x['date']))
        .assign(parameters=lambda x: x[['R', 'C', 'alpha', 'Pvoisin', 'time_shift']].values.tolist())
        .assign(parameters_str=lambda x: x['parameters'].apply(lambda y: f"R={y[0]:.1e}, C={y[1]:.1e}, alpha={y[2]:.1e}, Pvoisin={y[3]:.1e}, delta_t={y[4]:.1e}"))
    )