import requests
import pandas as pd

def main():
    # --- Configuration ---
    symbol = 'BTCUSDT'
    interval = '15m'
    limit = 1000
    output_filename = 'btc_15m_data.csv'

    # Binance API endpoint for historical klines (candles)
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

    print(f"--- Fetching real-world data from Binance for {symbol} ({interval}) ---")

    try:
        # Make the request to Binance's public API
        response = requests.get(url)
        # Raise an error if the request was not successful
        response.raise_for_status() 

        data = response.json()

        # The data comes as a list of lists. We need to structure it.
        # Define the column names based on Binance API documentation
        columns = [
            'timestamp', 'open', 'high', 'low', 'close', 'volume', 
            'close_time', 'quote_asset_volume', 'number_of_trades', 
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ]
        
        df = pd.DataFrame(data, columns=columns)

        # --- Data Cleaning & Formatting ---
        # We only need the essential columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        # Convert timestamp to a readable datetime format
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # Convert price and volume columns to numeric types
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])

        # Save the clean data to a CSV file
        df.to_csv(output_filename, index=False)

        print(f"\nSUCCESS: Data fetch complete.")
        print(f"Saved {len(df)} rows of real-world data to '{output_filename}'.")
        print("\n--- Data Sample ---")
        print(df.head())
        print("-------------------")

    except requests.exceptions.RequestException as e:
        print(f"\nSCRIPT FAILED: An error occurred while fetching data from Binance.")
        print(f"Error details: {e}")

if __name__ == "__main__":
    main()