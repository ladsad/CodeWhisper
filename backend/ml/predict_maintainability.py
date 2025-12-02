import json
import argparse
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from typing import List, Dict, Any

def predict_maintainability(metrics_file: str, output_file: str):
    try:
        with open(metrics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Metrics file '{metrics_file}' not found.")
        return

    if not data:
        print("No data to analyze.")
        return

    # Prepare features and target
    features = []
    targets = []
    file_paths = []

    for item in data:
        # Target: Maintainability Index
        mi = item.get('maintainability_index', None)
        if mi is None:
            continue
            
        # Features: LOC, SLOC, Avg Complexity, Avg NLOC, Avg Token Count
        loc = item.get('loc', 0)
        sloc = item.get('sloc', 0)
        
        funcs = item.get('functions', [])
        if funcs:
            avg_complexity = sum(f.get('cyclomatic_complexity', 0) for f in funcs) / len(funcs)
            avg_nloc = sum(f.get('nloc', 0) for f in funcs) / len(funcs)
            avg_tokens = sum(f.get('token_count', 0) for f in funcs) / len(funcs)
            num_funcs = len(funcs)
        else:
            avg_complexity = 0
            avg_nloc = 0
            avg_tokens = 0
            num_funcs = 0
            
        features.append([loc, sloc, avg_complexity, avg_nloc, avg_tokens, num_funcs])
        targets.append(mi)
        file_paths.append(item['file_path'])

    if not features:
        print("No valid features extracted.")
        return

    X = np.array(features)
    y = np.array(targets)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train XGBoost Regressor
    model = xgb.XGBRegressor(objective='reg:squarederror', n_estimators=100, seed=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    preds = model.predict(X_test)
    mse = mean_squared_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    
    print(f"Model Trained. MSE: {mse:.4f}, R2: {r2:.4f}")
    
    # Predict on all data to find discrepancies
    all_preds = model.predict(X)
    
    results = []
    print("\nPrediction Analysis:")
    for i, (pred, actual) in enumerate(zip(all_preds, y)):
        diff = actual - pred
        # If Actual is much lower than Predicted, it means the code is LESS maintainable than its metrics suggest (Risky?)
        # Or if Actual is much higher, maybe it's surprisingly clean?
        
        status = "Normal"
        if diff < -10: # Actual is 10 points lower than predicted
            status = "Deteriorating (Lower MI than expected)"
        elif diff > 10:
            status = "Better than expected"
            
        results.append({
            "file_path": file_paths[i],
            "actual_mi": float(actual),
            "predicted_mi": float(pred),
            "difference": float(diff),
            "status": status
        })
        
        if status != "Normal":
            print(f"{file_paths[i]}: Actual={actual:.2f}, Pred={pred:.2f} ({status})")

    # Feature Importance
    print("\nFeature Importance:")
    feature_names = ['LOC', 'SLOC', 'Avg Complexity', 'Avg NLOC', 'Avg Tokens', 'Num Functions']
    importances = model.feature_importances_
    for name, imp in zip(feature_names, importances):
        print(f"{name}: {imp:.4f}")

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print(f"Results saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predict Maintainability Index")
    parser.add_argument("--metrics_file", type=str, default="metrics_results.json", help="Input metrics JSON")
    parser.add_argument("--output", type=str, default="maintainability_predictions.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    predict_maintainability(args.metrics_file, args.output)
