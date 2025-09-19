# ml_scripts/main.py

import sys
import json
from datetime import timedelta
import numpy as np

import config
from data_handler import get_latest_data
from model_loader import load_prediction_assets
from predict import make_multistep_forecast

def generate_recommendation(ticker: str, forecast_days: int):
    """
    Main pipeline to generate a stock purchase recommendation.
    """
    try:
        # 1. Load assets
        model, scalers = load_prediction_assets(config.MODEL_PATH, config.SCALERS_PATH)
        
        # 2. Get and prepare latest data
        latest_data = get_latest_data(ticker, config.LOOKBACK_PERIOD)
        scaler = scalers.get(ticker)
        if not scaler:
            return {"error": f"No scaler found for ticker {ticker}."}

        # 3. Make forecast
        forecasted_prices = make_multistep_forecast(
            model, 
            latest_data, 
            scaler, 
            forecast_days,
            config.FEATURES_TO_USE,
            config.TARGET_COLUMN
        )
        
        # 4. Generate recommendation
        lowest_price = min(forecasted_prices)
        best_day_index = int(np.argmin(forecasted_prices))
        
        last_date = latest_data.index[-1]
        recommendation_date = last_date + timedelta(days=best_day_index + 1)
        
        # 5. Format the JSON output
        result = {
            "status": "success",
            "ticker": ticker,
            "recommendation": f"The best day to purchase is expected to be {recommendation_date.strftime('%Y-%m-%d')}.",
            "recommended_price": round(lowest_price, 2),
            "forecast_window_days": forecast_days,
            "forecast": [
                {"date": (last_date + timedelta(days=i+1)).strftime('%Y-%m-%d'), "predicted_price": round(price, 2)}
                for i, price in enumerate(forecasted_prices)
            ]
        }
        return result

    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    # This part is executed when the script is called from the command line (e.g., by Node.js)
    if len(sys.argv) != 3:
        error_response = {
            "status": "error", 
            "message": "Usage: python3 main.py <TICKER_SYMBOL.NS> <forecast_days>"
        }
        print(json.dumps(error_response))
    else:
        ticker_symbol = sys.argv[1].upper()
        days_to_forecast = int(sys.argv[2])
        
        final_recommendation = generate_recommendation(ticker_symbol, days_to_forecast)
        
        # Print the final result as a JSON string
        print(json.dumps(final_recommendation, indent=4))