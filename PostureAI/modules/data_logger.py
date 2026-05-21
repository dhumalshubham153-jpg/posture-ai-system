import csv
import os
from datetime import datetime

class DataLogger:

    def __init__(self, filepath='data/posture_sessions.csv'):
        self.filepath = filepath
        self.headers  = [
            'timestamp',
            'neck_forward_angle',
            'shoulder_slope',
            'rounded_shoulder_angle',
            'pelvic_tilt',
            'spine_deviation',
            'posture_score',
            'classification',
        ]
        self._init_file()

    def _init_file(self):
        """Create CSV file with headers if it doesn't exist"""
        if not os.path.exists(self.filepath):
            with open(self.filepath, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.headers)
                writer.writeheader()
            print(f"Data file created: {self.filepath}")

    def log(self, features, result):
        """Save one frame of posture data"""
        if not features or not result:
            return

        row = {
            'timestamp'              : datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'neck_forward_angle'     : features.get('neck_forward_angle')      or '',
            'shoulder_slope'         : features.get('shoulder_slope')           or '',
            'rounded_shoulder_angle' : features.get('rounded_shoulder_angle')  or '',
            'pelvic_tilt'            : features.get('pelvic_tilt')              or '',
            'spine_deviation'        : features.get('spine_deviation')          or '',
            'posture_score'          : result.get('score')                      or '',
            'classification'         : result.get('classification')             or '',
        }

        with open(self.filepath, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=self.headers)
            writer.writerow(row)

    def get_recent(self, n=100):
        """Get last N records as list of dicts"""
        if not os.path.exists(self.filepath):
            return []

        with open(self.filepath, 'r') as f:
            reader = list(csv.DictReader(f))

        return reader[-n:] if len(reader) > n else reader