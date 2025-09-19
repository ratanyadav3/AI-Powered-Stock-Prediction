# ml_scripts/model_loader.py

import pickle
from tensorflow.keras.saving import load_model

def load_prediction_assets(model_path: str, scalers_path: str):
    """Loads the trained model and scalers from disk."""
    try:
        model = load_model(model_path)
        # Re-compile to avoid a warning when predicting
        model.compile(optimizer='adam', loss='mean_squared_error')
        
        with open(scalers_path, 'rb') as f:
            scalers = pickle.load(f)
            
        return model, scalers
    except FileNotFoundError:
        raise FileNotFoundError("Model or scalers not found. Please ensure they are in the 'models' directory.")