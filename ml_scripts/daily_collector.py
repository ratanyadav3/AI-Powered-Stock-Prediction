# ml_scripts/daily_collector.py

import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import date, timedelta
import config
import db_handler
import time

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates all required features for the model, ensuring consistency
    with the backfill script and trained model features.
    FEATURES_TO_USE = ['Close', 'Volume', 'RSI_14', 'MACD_12_26_9', 'volatility_20d']
    """
    # --- MODEL KE FEATURES CALCULATE KAREIN ---
    # 1. RSI (Relative Strength Index)
    df.ta.rsi(length=14, append=True)
    
    # 2. MACD (Moving Average Convergence Divergence)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    
    # 3. Volatility (20-day rolling standard deviation of returns)
    df['returns'] = df['Close'].pct_change()
    df['volatility_20d'] = df['returns'].rolling(window=20).std()
    
    # --- MODEL KE EXACT FEATURES SELECT KAREIN ---
    required_columns = [
        'Close', 
        'Volume', 
        'RSI_14', 
        'MACD_12_26_9',  # pandas_ta creates this automatically
        'volatility_20d'
    ]
    
    # Check karein ki saare columns available hain
    available_cols = []
    missing_cols = []
    
    for col in required_columns:
        if col in df.columns:
            available_cols.append(col)
        else:
            missing_cols.append(col)
    
    if missing_cols:
        print(f"⚠️  Warning: Missing columns: {missing_cols}")
        print(f"📋 Available columns: {list(df.columns)}")
    
    # Sirf available columns ko select karein
    if available_cols:
        df_final = df[available_cols].copy()
    else:
        print("❌ No required columns found!")
        return pd.DataFrame()
        
    return df_final

def collect_latest_data():
    """
    Fetches latest data, calculates features matching the trained model,
    and saves it to MongoDB for daily predictions.
    """
    print("--- Starting Daily Data Collection ---")
    print("📋 Model Features: ['Close', 'Volume', 'RSI_14', 'MACD_12_26_9', 'volatility_20d']")
    
    collection, client = db_handler.get_db_collection()
    total_new_records = 0
    successful_tickers = 0
    failed_tickers = 0
    
    for ticker in config.TICKERS:
        try:
            print(f"📈 Processing {ticker}...")
            
            # Fetch larger window to calculate indicators accurately
            # Need extra days for technical indicators (especially 26-day MACD)
            start_date = date.today() - timedelta(days=100) 
            stock_data = yf.Ticker(ticker).history(start=start_date)
            
            if stock_data.empty:
                print(f"❌ No data found for {ticker}")
                failed_tickers += 1
                continue

            # Calculate features using updated function
            featured_data = calculate_features(stock_data)
            
            if featured_data.empty:
                print(f"❌ Failed to calculate features for {ticker}")
                failed_tickers += 1
                continue
            
            # Drop any rows with NaN values (created by technical indicators)
            featured_data.dropna(inplace=True)
            
            if featured_data.empty:
                print(f"❌ No valid data after cleaning for {ticker}")
                failed_tickers += 1
                continue

            # Reset index and add ticker info
            featured_data.reset_index(inplace=True)
            featured_data['ticker'] = ticker
            
            # Convert to records
            records = featured_data.to_dict('records')
            
            # Save only the most recent 5 records (adjust as needed)
            recent_records = records[-5:] if len(records) >= 5 else records
            
            # Save to database
            new_records_count = db_handler.save_data_to_db(collection, recent_records)
            total_new_records += new_records_count
            
            if new_records_count > 0:
                print(f"✅ Saved {new_records_count} new record(s) for {ticker}")
                successful_tickers += 1
            else:
                print(f"ℹ️  No new records to save for {ticker}")
                successful_tickers += 1
            
            # Be polite to the API
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")
            failed_tickers += 1
            continue
            
    client.close()
    
    # Summary report
    print(f"\n--- Daily Data Collection Summary ---")
    print(f"✅ Successful tickers: {successful_tickers}")
    print(f"❌ Failed tickers: {failed_tickers}")
    print(f"📊 Total new records added: {total_new_records}")
    print(f"🎯 Data ready for model predictions!")

def verify_latest_data():
    """Verify the latest collected data structure and show sample."""
    print("\n--- Verifying Latest Data ---")
    
    collection, client = db_handler.get_db_collection()
    
    # Get latest record for verification
    latest_record = collection.find_one(sort=[("Date", -1)])
    
    if latest_record:
        print("✅ Latest record structure:")
        expected_features = ['Close', 'Volume', 'RSI_14', 'MACD_12_26_9', 'volatility_20d']
        
        for feature in expected_features:
            if feature in latest_record:
                print(f"   ✓ {feature}: {latest_record[feature]:.4f}")
            else:
                print(f"   ❌ Missing: {feature}")
        
        print(f"   ✓ ticker: {latest_record.get('ticker', 'Not found')}")
        print(f"   ✓ Date: {latest_record.get('Date', 'Not found')}")
        
        # Show data freshness
        if 'Date' in latest_record:
            latest_date = pd.to_datetime(latest_record['Date']).date()
            days_old = (date.today() - latest_date).days
            print(f"   📅 Data freshness: {days_old} days old")
    else:
        print("❌ No records found in database")
    
    # Count records per ticker
    pipeline = [
        {"$group": {"_id": "$ticker", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    
    ticker_counts = list(collection.aggregate(pipeline))
    if ticker_counts:
        print(f"\n📈 Records per ticker:")
        for item in ticker_counts[:5]:  # Show top 5
            print(f"   {item['_id']}: {item['count']} records")
    
    client.close()

if __name__ == "__main__":
    print("🚀 Daily Stock Data Collection")
    print("🕒 Starting collection process...")
    
    # Collect latest data
    collect_latest_data()
    
    # Verify the collected data
    verify_latest_data()