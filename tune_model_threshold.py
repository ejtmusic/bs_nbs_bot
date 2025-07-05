import pandas as pd
import joblib
from sklearn.metrics import confusion_matrix

def main():
    # --- Configuration ---
    model_file = 'master_model.joblib'
    x_test_file = 'X_test.csv' # We need to save this file first
    y_test_file = 'y_test.csv' # and this one

    print(f"--- Tuning Prediction Threshold for {model_file} ---")

    try:
        # Load the model and the test data
        model = joblib.load(model_file)
        X_test = pd.read_csv(x_test_file)
        y_test = pd.read_csv(y_test_file).values.ravel()

        # --- Get Prediction Probabilities ---
        # Instead of a hard 0 or 1, we get the model's confidence for class '1'
        probabilities = model.predict_proba(X_test)[:, 1]

        # --- Test Different Thresholds ---
        print("\n--- Threshold Analysis ---")
        thresholds_to_test = [0.5, 0.45, 0.4, 0.35, 0.3]
        
        for threshold in thresholds_to_test:
            # Apply the current threshold to the probabilities
            predictions = (probabilities >= threshold).astype(int)
            
            cm = confusion_matrix(y_test, predictions)
            
            trades_taken = cm[1][1] + cm[0][1]
            correct_trades = cm[1][1]

            if trades_taken > 0:
                win_rate = correct_trades / trades_taken * 100
                # Expected profit for 100 trades = (Wins * 3 Reward) - (Losses * 1 Risk)
                # We scale this to a "per trade" value
                expected_profit_per_trade = ((correct_trades * 3) - (trades_taken - correct_trades)) / trades_taken
                
                print(f"\nThreshold: {threshold:.2f}")
                print(f"  Trades Taken: {trades_taken} (out of 54 opportunities)")
                print(f"  Win Rate: {win_rate:.2f}%")
                print(f"  Expected Profit Per Trade: {expected_profit_per_trade:.2f}R")
            else:
                print(f"\nThreshold: {threshold:.2f} -> No trades were taken.")
        
        print("\n--------------------------")
        print("Goal: Find the threshold with the best balance of Trades Taken and Expected Profit.")


    except FileNotFoundError:
        # We need to update our training script to save the test data first
        print("SCRIPT FAILED: Test data files not found.")
        print("Please run the updated 'train_unified_model.py' first to generate them.")
    except Exception as e:
        print(f"SCRIPT FAILED: An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()