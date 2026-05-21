import os
import csv
import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import pickle

class PostureMLModel:

    def __init__(self, model_path='models/posture_model.pkl'):
        self.model_path = model_path
        self.model      = None
        self.encoder    = LabelEncoder()
        self.features   = [
            'neck_forward_angle',
            'shoulder_slope',
            'rounded_shoulder_angle',
            'pelvic_tilt',
            'spine_deviation',
        ]
        os.makedirs('models', exist_ok=True)

    def load_data(self, filepath='data/posture_sessions.csv'):
        """Load and clean session CSV data"""
        if not os.path.exists(filepath):
            return None, None

        rows = []
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    feature_row = []
                    valid = True
                    for feat in self.features:
                        val = row.get(feat, '')
                        if val == '' or val is None:
                            valid = False
                            break
                        feature_row.append(float(val))
                    if valid:
                        rows.append({
                            'features'      : feature_row,
                            'classification': row['classification'],
                        })
                except:
                    continue

        if len(rows) < 10:
            # Not enough real data — generate synthetic
            return self._generate_synthetic()

        X = np.array([r['features'] for r in rows])
        y = np.array([r['classification'] for r in rows])
        return X, y

    def _generate_synthetic(self):
        """Generate synthetic training data"""
        np.random.seed(42)
        n = 500
        X, y = [], []

        # GOOD posture samples
        for _ in range(n//3):
            X.append([
                np.random.uniform(0,  15),   # neck
                np.random.uniform(0,  10),   # shoulder slope
                np.random.uniform(150,180),  # rounded shoulder
                np.random.uniform(0,  10),   # pelvic
                np.random.uniform(0,  20),   # spine
            ])
            y.append('GOOD')

        # WARNING posture samples
        for _ in range(n//3):
            X.append([
                np.random.uniform(15, 30),
                np.random.uniform(10, 25),
                np.random.uniform(120,150),
                np.random.uniform(10, 25),
                np.random.uniform(20, 50),
            ])
            y.append('WARNING')

        # BAD posture samples
        for _ in range(n//3):
            X.append([
                np.random.uniform(30, 50),
                np.random.uniform(25, 50),
                np.random.uniform(80, 120),
                np.random.uniform(25, 50),
                np.random.uniform(50, 100),
            ])
            y.append('BAD')

        return np.array(X), np.array(y)

    def train(self):
        """Train XGBoost model"""
        X, y = self.load_data()
        if X is None:
            print("No data available")
            return False

        y_enc = self.encoder.fit_transform(y)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y_enc, test_size=0.2, random_state=42
        )

        self.model = XGBClassifier(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            random_state=42,
            eval_metric='mlogloss',
        )
        self.model.fit(X_train, y_train)

        preds    = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, preds)
        print(f"Model trained — Accuracy: {accuracy:.2%}")

        # Save model
        with open(self.model_path, 'wb') as f:
            pickle.dump({'model': self.model, 'encoder': self.encoder}, f)

        return accuracy

    def load(self):
        """Load saved model"""
        if not os.path.exists(self.model_path):
            print("No saved model — training now...")
            self.train()
            return

        with open(self.model_path, 'rb') as f:
            data = pickle.load(f)
        self.model   = data['model']
        self.encoder = data['encoder']
        print("Model loaded successfully")

    def predict(self, features):
        """Predict posture class from features dict"""
        if self.model is None:
            self.load()

        vals = []
        for feat in self.features:
            v = features.get(feat)
            vals.append(float(v) if v is not None else 0.0)

        X    = np.array([vals])
        pred = self.model.predict(X)[0]
        prob = self.model.predict_proba(X)[0]

        label = self.encoder.inverse_transform([pred])[0]
        conf  = float(np.max(prob))

        return {
            'prediction'  : label,
            'confidence'  : round(conf * 100, 1),
            'probabilities': {
                cls: round(float(p) * 100, 1)
                for cls, p in zip(self.encoder.classes_, prob)
            },
            'features_used': dict(zip(self.features, vals)),
        }