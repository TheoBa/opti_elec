from scipy.optimize import minimize, differential_evolution
import time
import streamlit as st

def create_optimization_function(loss_function, fixed_params):
    """
    Create a wrapped RMSE function that only takes optimization parameters.
    
    Parameters:
    -----------
    rmse_function : callable
        Your RMSE function that takes parameters and DataFrames
    fixed_params : dict
        Dictionary containing fixed parameters
    
    Returns:
    --------
    callable : Function that only takes optimization parameters
    """
    def wrapped_loss(opt_params):
        return loss_function(opt_params, **fixed_params)
    return wrapped_loss

def optimize_parameters(loss_function, initial_guess, bounds):
    """
    Optimize parameters using multiple methods.
    
    Parameters:
    -----------
    loss_function : callable
        Your LOSS function
    initial_guess : array-like
        Initial parameter values
    bounds : list of tuples
        Parameter bounds [(min1, max1), (min2, max2)]
    
    Returns:
    --------
    dict : Results from different optimization methods
    """
    results = {}
    # Local optimization methods
    local_methods = [
        #'Nelder-Mead', 
        'Powell', 
        #'BFGS'
        ]
    for local_method in local_methods:
        try:
            start_time = time.time()
            st.markdown(f"\nTrying {local_method} optimization...")
            result = minimize(loss_function, initial_guess, method=local_method)
            results[local_method] = {
                'parameters': result.x,
                'rmse': result.fun,
                'success': result.success,
                'message': result.message
            }
            end_time = time.time()

            elapsed_time = end_time - start_time
            st.markdown(f"Time taken: {elapsed_time} seconds")
            st.markdown(f"{local_method} completed: RMSE = {result.fun:.4f}")
        except Exception as e:
            results[local_method] = f"Failed: {str(e)}"
            st.markdown(f"{local_method} failed with error: {str(e)}")    
    return results