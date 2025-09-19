# ml_scripts/prediction_handler.py

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import json
import numpy as np
import pandas as pd
from datetime import timedelta

import config
import db_handler
from model_loader import load_prediction_assets

def generate_single_prediction(ticker: str):
    """
    Pipeline to generate a single next-day prediction using PRE-CALCULATED data from MongoDB.
    """
    try:
        collection, client = db_handler.get_db_collection()
        model, scalers = load_prediction_assets(config.MODEL_PATH, config.SCALERS_PATH)
        
        latest_data = db_handler.fetch_data_from_db(collection, ticker, config.LOOKBACK_PERIOD)
        client.close()

        if len(latest_data) < config.LOOKBACK_PERIOD:
            message = f"Insufficient data in DB for {ticker}. Need {config.LOOKBACK_PERIOD}, found {len(latest_data)}."
            raise ValueError(message)

        scaler = scalers.get(ticker)
        if not scaler:
            raise ValueError(f"No scaler found for {ticker}.")

        scaled_input = scaler.transform(latest_data[config.FEATURES_TO_USE])
        X_pred = np.reshape(scaled_input, (1, config.LOOKBACK_PERIOD, len(config.FEATURES_TO_USE)))

        scaled_prediction = model.predict(X_pred, verbose=0)
        
        target_col_index = config.FEATURES_TO_USE.index(config.TARGET_COLUMN)
        dummy_array = np.zeros((1, len(config.FEATURES_TO_USE)))
        dummy_array[0, target_col_index] = scaled_prediction[0, 0]
        actual_prediction = scaler.inverse_transform(dummy_array)
        predicted_price = actual_prediction[0, target_col_index]

        # --- NEW: Data range ko result mein show karne ke liye ---
        start_point_date = pd.to_datetime(latest_data['Date'].iloc[0]).strftime('%Y-%m-%d')
        start_point_price = round(float(latest_data['Close'].iloc[0]), 2)

        end_point_date = pd.to_datetime(latest_data['Date'].iloc[-1]).strftime('%Y-%m-%d')
        end_point_price = round(float(latest_data['Close'].iloc[-1]), 2)
        
        prediction_date = pd.to_datetime(end_point_date) + timedelta(days=1)
        
        result = {
            "status": "success",
            "ticker": ticker,
            "prediction_date": prediction_date.strftime('%Y-%m-%d'),
            "predicted_price": round(float(predicted_price), 2),
            "data_used": {
                "start_point": {
                    "date": start_point_date,
                    "price": start_point_price
                },
                "end_point": {
                    "date": end_point_date,
                    "price": end_point_price
                }
            }
        }
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"status": "error", "message": "Usage: python3 prediction_handler.py <TICKER_SYMBOL.NS>"}))
    else:
        ticker_symbol = sys.argv[1].upper()
        final_result = generate_single_prediction(ticker_symbol)
        print(json.dumps(final_result, indent=4))