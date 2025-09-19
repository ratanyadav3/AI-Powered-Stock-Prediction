# ml_scripts/db_handler.py

from pymongo import MongoClient
import pandas as pd
import config

def get_db_collection():
    """Establishes a connection to MongoDB and returns the collection object."""
    client = MongoClient(config.MONGO_URI)
    db = client[config.DATABASE_NAME]
    collection = db[config.COLLECTION_NAME]
    # Create an index to prevent duplicates and speed up queries
    collection.create_index([("Date", 1), ("ticker", 1)], unique=True)
    return collection, client

def save_data_to_db(collection, data_records):
    """Saves a list of data records to the database, avoiding duplicates."""
    if not data_records:
        return 0
    
    upsert_count = 0
    for record in data_records:
        # update_one with upsert=True is the key to avoiding duplicates.
        # It finds a document with the same Date & ticker and updates it,
        # or inserts a new one if it doesn't exist.
        result = collection.update_one(
            {"Date": record["Date"], "ticker": record["ticker"]},
            {"$set": record},
            upsert=True
        )
        if result.upserted_id:
            upsert_count += 1
            
    return upsert_count

def fetch_data_from_db(collection, ticker, num_records):
    """Fetches the most recent N records for a ticker from the database."""
    cursor = collection.find({"ticker": ticker}).sort("Date", -1).limit(num_records)
    data = list(cursor)
    
    if len(data) < num_records:
        raise ValueError(f"Insufficient data in DB for {ticker}. Need {num_records}, found {len(data)}.")
        
    # Convert to DataFrame and sort chronologically
    df = pd.DataFrame(data).sort_values(by="Date").reset_index(drop=True)
    return df