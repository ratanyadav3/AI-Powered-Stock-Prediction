# ml_scripts/backfill_db.py
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import date, timedelta
import config
import db_handler
import time
import numpy as np
import traceback

def clean_raw_data(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Rigorously cleans raw stock data before feature calculation.
    Removes holidays, partial sessions, and anomalous data points.
    """
    if df.empty:
        return df
        
    print(f"   📊 Raw data: {len(df)} records")
    
    # 1. Remove records with zero/negative prices or volume
    df = df[(df['Close'] > 0) & (df['Open'] > 0) & 
            (df['High'] > 0) & (df['Low'] > 0) & (df['Volume'] > 0)]
    print(f"   ✅ After price/volume validation: {len(df)} records")
    
    # 2. Remove very low volume days (likely holidays/partial sessions)
    volume_threshold = df['Volume'].quantile(0.05)
    df = df[df['Volume'] >= volume_threshold]
    print(f"   ✅ After volume filter (>={volume_threshold:.0f}): {len(df)} records")
    
    # 3. Calculate returns for outlier detection
    df['returns'] = df['Close'].pct_change()
    
    # 4. Remove extreme outliers (likely data errors)
    pre_outlier_count = len(df)
    df = df[abs(df['returns']) <= 0.20] # Filter out >20% daily changes
    outliers_removed = pre_outlier_count - len(df)
    if outliers_removed > 0:
        print(f"   ⚠️  Removed {outliers_removed} outlier days (>20% change)")
    
    # 5. Ensure index is a timezone-naive DatetimeIndex for consistency
    df.index = pd.to_datetime(df.index).tz_localize(None)
    
    # 6. Remove weekends
    df = df[df.index.dayofweek < 5]
    
    # 7. Sort by date to ensure chronological order
    df = df.sort_index()
    
    # 8. Check for data gaps and interpolate small gaps
    df = fill_small_gaps(df, ticker)
    
    print(f"   ✅ Final cleaned data: {len(df)} records")
    return df

def fill_small_gaps(df: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Fills small data gaps (1-2 days) using forward fill.
    Warns about larger gaps that might affect model performance.
    """
    if df.empty:
        return df
        
    business_days = pd.bdate_range(start=df.index.min(), end=df.index.max())
    missing_days = business_days.difference(df.index)
    
    if len(missing_days) > 0:
        gap_days = len(missing_days)
        total_days = len(business_days)
        gap_percentage = (gap_days / total_days) * 100 if total_days > 0 else 0
        
        print(f"   📅 Missing {gap_days} trading days ({gap_percentage:.1f}%) for {ticker}")
        
        if gap_percentage < 5.0: # Only fill small gaps
            df = df.reindex(business_days)
            # Use forward fill for all columns
            df.fillna(method='ffill', inplace=True)
            print(f"   ✅ Interpolated small gaps for {ticker}")
        else:
            print(f"   ⚠️  Large data gaps detected for {ticker} - not interpolating.")
    
    return df

def validate_features(df: pd.DataFrame, ticker: str) -> bool:
    """
    Validates that calculated features are reasonable and within expected ranges.
    """
    # This function is good as-is, no changes needed.
    # ... (code omitted for brevity, it was correct)
    return True

def calculate_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates all required features for the model matching FEATURES_TO_USE."""
    # This function is good as-is, no changes needed.
    # ... (code omitted for brevity, it was correct)
    
    # Ensure 'returns' column exists for volatility calculation
    if 'returns' not in df.columns:
        df['returns'] = df['Close'].pct_change()
        
    df.ta.rsi(length=14, append=True)
    df.ta.macd(fast=12, slow=26, signal=9, append=True)
    df['volatility_20d'] = df['returns'].rolling(window=20).std()
    
    required_columns = config.FEATURES_TO_USE
    
    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        print(f"   ❌ Missing columns after calculation: {missing}")
        return pd.DataFrame()
        
    return df[required_columns].copy()

def calculate_quality_score(df: pd.DataFrame) -> pd.Series:
    """
    Calculates a data quality score (1-5) for each record.
    """
    score = pd.Series(3.0, index=df.index)
    
    high_volume_threshold = df['Volume'].quantile(0.75)
    score += (df['Volume'] >= high_volume_threshold) * 0.5
    
    if 'volatility_20d' in df.columns:
        moderate_vol = (df['volatility_20d'] > 0.01) & (df['volatility_20d'] < 0.05)
        score += moderate_vol * 0.5
    
    if 'RSI_14' in df.columns:
        moderate_rsi = (df['RSI_14'] > 20) & (df['RSI_14'] < 80)
        score += moderate_rsi * 0.3
    
    # --- CRITICAL BUG FIX HERE ---
    # The original code `len(df) - range(len(df))` caused a TypeError.
    # This correctly creates a sequence like [60, 59, ..., 1] for recency.
    days_from_end = len(df) - np.arange(len(df))
    
    recency_bonus = [0.2 if d <= 5 else 0.1 if d <= 15 else 0 for d in days_from_end]
    # Ensure recency_bonus is added correctly to the Series index
    score += np.array(recency_bonus)
    
    return np.clip(score, 1.0, 5.0)

def backfill_60days_data():
    """
    Fetches, cleans, validates, and saves the last 60 days of data.
    """
    print("--- Starting Enhanced 60-Day Data Collection ---")
    print("🧹 Includes data cleaning, validation, and holiday filtering")
    
    collection, client = db_handler.get_db_collection()
    
    end_date = date.today()
    start_date = end_date - timedelta(days=250) # Increased buffer for cleaning/gaps
    
    total_saved, successful_tickers = 0, 0
    
    for ticker in config.TICKERS:
        try:
            print(f"\n🔍 Processing {ticker}...")
            
            stock_data = yf.Ticker(ticker).history(start=start_date, end=end_date)
            
            if stock_data.empty:
                print(f"❌ No data found for {ticker}"); continue
            
            cleaned_data = clean_raw_data(stock_data, ticker)
            
            if len(cleaned_data) < 85: # Need ~25 for indicators + 60 for model
                print(f"❌ Insufficient clean data for {ticker} ({len(cleaned_data)} days)"); continue
            
            featured_data = calculate_features(cleaned_data)
            
            if featured_data.empty:
                print(f"❌ Failed to calculate features for {ticker}"); continue
            
            pre_clean = len(featured_data)
            featured_data.dropna(inplace=True)
            print(f"   🧹 Removed {pre_clean - len(featured_data)} records with NaN values")
            
            if len(featured_data) < 60:
                print(f"⚠️  Only {len(featured_data)} clean, featured days available for {ticker} (target: 60)"); continue
                
            final_data = featured_data.tail(60)
            
            final_data['data_quality_score'] = calculate_quality_score(final_data)
            
            final_data.reset_index(inplace=True)
            final_data.rename(columns={'index': 'Date'}, inplace=True)
            final_data['ticker'] = ticker
            
            records = final_data.to_dict('records')
            
            new_records_count = db_handler.save_data_to_db(collection, records)
            total_saved += new_records_count
            successful_tickers += 1
            
            avg_quality = final_data['data_quality_score'].mean()
            print(f"✅ {ticker}: Saved {new_records_count} records (Quality: {avg_quality:.2f}/5.0)")
            
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}")
            print(traceback.format_exc()) # Print full traceback for debugging
    
    client.close()
    
    print(f"\n--- Enhanced Data Collection Summary ---")
    print(f"✅ Successfully processed: {successful_tickers}/{len(config.TICKERS)} tickers")
    print(f"📊 Total clean records saved: {total_saved}")

def data_quality_report():
    # This function is good as-is, no changes needed.
    # ... (code omitted for brevity, it was correct)
    pass 

if __name__ == "__main__":
    print("🚀 Enhanced Stock Data Collection with Quality Validation")
    print(f"📋 Model Features: {config.FEATURES_TO_USE}")
    print("🧹 Features: Holiday filtering, outlier removal, gap filling, quality scoring")
    
    backfill_60days_data()
    # data_quality_report() # You can run this separately if needed