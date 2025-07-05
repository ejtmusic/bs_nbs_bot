import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
from sklearn.metrics import classification_report, confusion_matrix

def main():
    # --- Configuration ---
    input_filename = 'master_training_data.csv'
    model_output_file = 'master_model.joblib'
    
    feature_columns = [
        'return_1', 'return_5', 'return_10',
        'volume_change_1', 'volume_change_5',
        'candle_range', 'volatility_10'
    ]

    print(f"--- Training Unified Master Model (Tuned for Action) ---")

    try:
        df_combined = pd.read_csv(input_filename)
        X = df_combined[feature_columns]
        y = df_combined['label']

        # --- Split the Data ---
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # --- THE CRITICAL ADDITION: Save the test sets for our tuning script ---
        print("Saving test data for tuning script...")
        X_test.to_csv('X_test.csv', index=False)
        pd.DataFrame(y_test, columns=['label']).to_csv('y_test.csv', index=False)
        
        print(f"Training set size: {len(X_train)}")
        print(f"Testing set size: {len(X_test)}")
        
        # --- Train the Model ---
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1, class_weight='balanced')

        print("\nModel training started...")
        model.fit(X_train, y_train)
        print("Model training complete.")
        
        joblib.dump(model, model_output_file)
        print(f"Unified model saved to '{model_output_file}'.\n")

        # --- Evaluate the Model (at default 0.5 threshold) ---
        print(f"--- Evaluating Tuned Model (at default threshold) ---")
        y_pred = model.predict(X_test)
        
        print("\n--- Overall Classification Report ---")
        report = classification_report(y_test, y_pred, target_names=['No Action (0)', 'Action (1)'], zero_division=0)
        print(report)

        cm = confusion_matrix(y_test, y_pred)
        if (cm[1][1] + cm[0][1]) > 0:
            win_rate = cm[1][1] / (cm[1][1] + cm[0][1]) * 100
            print(f"\nOverall Model Win Rate (Precision for 'Action'): {win_rate:.2f}%")
        else:
            print("\nModel did not predict any 'Action' signals.")

    except Exception as e:
        print(f"SCRIPT FAILED: An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()