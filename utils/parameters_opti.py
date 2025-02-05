from scipy.optimize import minimize, differential_evolution

import numpy as np
from scipy.optimize import minimize, differential_evolution
import pandas as pd

def create_optimization_function(rmse_function, fixed_params):
    """
    Create a wrapped RMSE function that only takes optimization parameters.
    
    Parameters:
    -----------
    rmse_function : callable
        Your RMSE function that takes parameters and DataFrames
    fixed_params : dict
        Dictionary containing DataFrames and other fixed parameters
    
    Returns:
    --------
    callable : Function that only takes optimization parameters
    """
    def wrapped_rmse(opt_params):
        return rmse_function(opt_params, **fixed_params)
    return wrapped_rmse

def optimize_parameters(rmse_function, initial_guess, bounds, fixed_params, method='all'):
    """
    Optimize parameters using multiple methods.
    
    Parameters:
    -----------
    rmse_function : callable
        Your RMSE function
    initial_guess : array-like
        Initial parameter values
    bounds : list of tuples
        Parameter bounds [(min1, max1), (min2, max2)]
    fixed_params : dict
        Dictionary containing daily_switch_inputs_df and daily_temp_int
    method : str
        'all', 'local', or 'global'
    
    Returns:
    --------
    dict : Results from different optimization methods
    """
    # Create optimization function with fixed parameters
    opt_function = create_optimization_function(rmse_function, fixed_params)
    
    results = {}
    
    if method in ['all', 'local']:
        # Local optimization methods
        local_methods = [
            'Nelder-Mead', 
            #'Powell', 
            #'BFGS'
            ]
        for local_method in local_methods:
            try:
                print(f"\nTrying {local_method} optimization...")
                result = minimize(opt_function, initial_guess, method=local_method)
                results[local_method] = {
                    'parameters': result.x,
                    'rmse': result.fun,
                    'success': result.success,
                    'message': result.message
                }
                print(f"{local_method} completed: RMSE = {result.fun:.4f}")
            except Exception as e:
                results[local_method] = f"Failed: {str(e)}"
                print(f"{local_method} failed with error: {str(e)}")
    
    if method in ['all', 'global']:
        try:
            print("\nTrying Differential Evolution optimization...")
            result = differential_evolution(opt_function, bounds)
            results['differential_evolution'] = {
                'parameters': result.x,
                'rmse': result.fun,
                'success': result.success,
                'message': result.message
            }
            print(f"Differential Evolution completed: RMSE = {result.fun:.4f}")
        except Exception as e:
            results['differential_evolution'] = f"Failed: {str(e)}"
            print(f"Differential Evolution failed with error: {str(e)}")
    
    return results