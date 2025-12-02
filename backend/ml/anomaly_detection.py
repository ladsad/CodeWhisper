import json
import argparse
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from typing import List, Dict, Any

def detect_anomalies(metrics_file: str, output_file: str, contamination: float = 0.1):
    try:
        with open(metrics_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Metrics file '{metrics_file}' not found.")
        return

    if not data:
        print("No data to analyze.")
        return

    # Prepare features
    # Features: LOC, SLOC, Maintainability Index, Avg Function Complexity
    features = []
    valid_indices = []

    for i, item in enumerate(data):
        # Calculate average function complexity
        funcs = item.get('functions', [])
        if funcs:
            avg_complexity = sum(f.get('cyclomatic_complexity', 0) for f in funcs) / len(funcs)
        else:
            avg_complexity = 0
            
        # We want to detect high complexity and low maintainability.
        # Isolation Forest detects "rare" points. 
        # High complexity/LOC and low MI are rare in good codebases (hopefully).
        
        loc = item.get('loc', 0)
        sloc = item.get('sloc', 0)
        mi = item.get('maintainability_index', 100) # Default to 100 if missing
        
        # Skip empty files or files with 0 LOC if desired, but here we include them
        features.append([loc, sloc, mi, avg_complexity])
        valid_indices.append(i)

    if not features:
        print("No valid features extracted.")
        return

    X = np.array(features)
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Isolation Forest
    clf = IsolationForest(contamination=contamination, random_state=42)
    preds = clf.fit_predict(X_scaled)
    
    # preds: 1 for inliers, -1 for outliers
    anomalies = []
    
    print(f"Analyzed {len(X)} files. Found {list(preds).count(-1)} anomalies.")

    for idx, pred in zip(valid_indices, preds):
        if pred == -1:
            item = data[idx]
            # Determine why it's anomalous (simple heuristic for display)
            # High complexity or Low MI?
            reasons = []
            if features[idx][0] > np.mean(X[:, 0]) + np.std(X[:, 0]):
                reasons.append("High LOC")
            if features[idx][2] < np.mean(X[:, 2]) - np.std(X[:, 2]):
                reasons.append("Low Maintainability")
            if features[idx][3] > np.mean(X[:, 3]) + np.std(X[:, 3]):
                reasons.append("High Avg Complexity")
                
            anomalies.append({
                "file_path": item['file_path'],
                "metrics": {
                    "loc": features[idx][0],
                    "sloc": features[idx][1],
                    "maintainability_index": features[idx][2],
                    "avg_complexity": features[idx][3]
                },
                "reasons": reasons
            })

    # Save results
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(anomalies, f, indent=2)
        
    print(f"Anomalies saved to {output_file}")
    
    # Print to console
    print("\nFlagged Files:")
    for anomaly in anomalies:
        print(f"- {anomaly['file_path']}: {', '.join(anomaly['reasons'])}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Detect Code Anomalies")
    parser.add_argument("--metrics_file", type=str, default="metrics_results.json", help="Input metrics JSON")
    parser.add_argument("--output", type=str, default="anomalies.json", help="Output JSON file")
    parser.add_argument("--contamination", type=float, default=0.1, help="Expected proportion of outliers")
    
    args = parser.parse_args()
    
    detect_anomalies(args.metrics_file, args.output, args.contamination)
