from flask import Flask, request, jsonify
import pandas as pd
import datetime as dt
from src.utils import prepare_logs  
from src.sandbox import Simulation
import json
import os

app = Flask(__name__)

@app.route('/compute_simulation', methods=['POST'])
def compute_simulation():
    data = request.json
    module_name = data.get('module_name')
    heating_scenario = data.get('heating_scenario')

    if not module_name or not heating_scenario:
        return jsonify({'error': 'module_name and heating_scenario are required'}), 400

    # Load module configuration (adjust this based on your actual configuration loading mechanism)
    config = json.load(open("config.json", "r"))
    module_config = config[module_name]

    # Find best model's parameters
    log_runs = prepare_logs()
    logs_df = log_runs[log_runs['module_name'] == module_name][["date", "R", "C", "alpha", "Pvoisin", "time_shift"]]
    parameters = logs_df.sort_values(by='date', ascending=False).reset_index(drop=True).loc[0, ["R", "C", "alpha", "Pvoisin", "time_shift"]].values.flatten().tolist()

    # Initialize the Simulation class
    simu = Simulation(module_config, mode="forecasted", parameters=parameters, scenario=heating_scenario)

    # Get the simulation DataFrame
    simulation_df = simu.simulation_df

    # Prepare the response
    response = {
        #'temperature_evolution': simu.simulation_df[["date", "T_int_pred"]].to_dict(orient='records'),
        'parameters': simu.parameters,
        'consumption': simu.compute_scenarios_consumption()
    }

    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)