from src.model import TemperatureModel
import json

def validate_model(train_timeframe, test_timeframe):
    # Initialize the model
    config = json.load(open("config.json", "r"))
    model = TemperatureModel(config["caussa"])

    # Optimize the model for the given train_timeframe
    model.get_optimal_parameters(train_timeframe=train_timeframe)

    # Test the model on the given test_timeframe
    test_df, rmse = model.test_model(
        test_timeframe=test_timeframe,
        test_parameters=model.optimal_parameters
        )

    return test_df, rmse

