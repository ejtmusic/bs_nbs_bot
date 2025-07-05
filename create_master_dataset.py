import pandas as pd
import numpy as np

def main():
    input_file = 'btc_15m_data.csv'
    output_file = 'master_training_data.csv'
    
    RR_RATIO = 3.0
    RISK_PERCENT = 0.005 
    LOOKAHEAD_CANDLES = 100
    
    feature_columns = [
        'return_1', 'return_5', 'return_10',
        'volume_change_1', 'volume_change_5',
        'candle_range', 'volatility_10'
    ]

    print(f"--- Creating Unified Master Dataset from '{input_file}' ---")

    try:
        df = pd.read_csv(input_file)

        # --- 1. Calculate Features on Normal Data ---
        df['return_1'] = df['close'].pct_change(1)
        df['return_5'] = df['close'].pct_change(5)
        df['return_10'] = df['close'].pct_change(10)
        df['volume_change_1'] = df['volume'].pct_change(1)
        df['volume_change_5'] = df['volume'].pct_change(5)
        df['candle_range'] = (df['high'] - df['low']) / df['close']
        df['volatility_10'] = df['return_1'].rolling(window=10).std()

        # --- 2. Calculate Both Buy and Sell Labels on Normal Data ---
        df['label_buy'] = 0
        df['label_sell'] = 0
        for i in range(len(df) - LOOKAHEAD_CANDLES):
            entry = df['close'].iloc[i]
            # Buy targets
            sl_buy, tp_buy = entry * (1 - RISK_PERCENT), entry * (1 + (RISK_PERCENT * RR_RATIO))
            # Sell targets
            sl_sell, tp_sell = entry * (1 + RISK_PERCENT), entry * (1 - (RISK_PERCENT * RR_RATIO))

            for j in range(1, LOOKAHEAD_CANDLES + 1):
                high, low = df['high'].iloc[i+j], df['low'].iloc[i+j]
                # Check buy
                if df['label_buy'].iloc[i] == 0 and low <= sl_buy: df.loc[df.index[i], 'label_buy'] = -1
                if df['label_buy'].iloc[i] == 0 and high >= tp_buy: df.loc[df.index[i], 'label_buy'] = 1
                # Check sell
                if df['label_sell'].iloc[i] == 0 and high >= sl_sell: df.loc[df.index[i], 'label_sell'] = -1
                if df['label_sell'].iloc[i] == 0 and low <= tp_sell: df.loc[df.index[i], 'label_sell'] = 1
        
        # --- 3. Create the Separate Datasets ---
        df_buy = df.copy()
        df_buy['label'] = df_buy['label_buy'].apply(lambda x: 1 if x == 1 else 0)

        df_sell = df.copy()
        df_sell['label'] = df_sell['label_sell'].apply(lambda x: 1 if x == 1 else 0)

        # --- 4. THE REAL FIX: Invert the features for the sell dataset ---
        directional_features = ['return_1', 'return_5', 'return_10']
        for col in directional_features:
            df_sell[col] = df_sell[col] * -1

        # --- 5. Combine and Save ---
        # We only need the features and the final 'label' column
        final_buy_df = df_buy[feature_columns + ['label']]
        final_sell_df = df_sell[feature_columns + ['label']]
        
        master_df = pd.concat([final_buy_df, final_sell_df], ignore_index=True)
        master_df.dropna(inplace=True) # Clean up any remaining NaN values

        master_df.to_csv(output_file, index=False)
        
        print(f"\nSUCCESS: Master dataset created at '{output_file}'")
        print(f"Total rows: {len(master_df)}")
        print(f"Total positive signals: {master_df['label'].sum()}")

    except Exception as e:
        print(f"SCRIPT FAILED: An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()