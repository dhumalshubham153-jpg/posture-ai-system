import csv
import os
from datetime import datetime

class RiskPredictor:

    # Risk weights per issue
    RISK_WEIGHTS = {
        'neck_forward_angle'     : 0.35,
        'shoulder_slope'         : 0.15,
        'rounded_shoulder_angle' : 0.25,
        'pelvic_tilt'            : 0.10,
        'spine_deviation'        : 0.15,
    }

    # Thresholds same as scorer
    THRESHOLDS = {
        'neck_forward_angle'     : {'good': 15,  'warning': 25,  'bad': 35},
        'shoulder_slope'         : {'good': 10,  'warning': 20,  'bad': 35},
        'rounded_shoulder_angle' : {'good': 150, 'warning': 130, 'bad': 110},
        'pelvic_tilt'            : {'good': 10,  'warning': 20,  'bad': 35},
        'spine_deviation'        : {'good': 20,  'warning': 40,  'bad': 60},
    }

    def calculate_risk(self, features):
        """Calculate spinal disorder risk score from features"""
        if not features:
            return None

        risk_score = 0
        total_weight = 0

        for name, weight in self.RISK_WEIGHTS.items():
            value = features.get(name)
            if value is None:
                continue

            t = self.THRESHOLDS[name]

            # Calculate feature risk (0-100)
            if name == 'rounded_shoulder_angle':
                if value >= t['good']:
                    feature_risk = 0
                elif value >= t['warning']:
                    ratio = (t['good'] - value) / (t['good'] - t['warning'])
                    feature_risk = ratio * 40
                elif value >= t['bad']:
                    ratio = (t['warning'] - value) / (t['warning'] - t['bad'])
                    feature_risk = 40 + ratio * 40
                else:
                    feature_risk = 90
            else:
                if value <= t['good']:
                    feature_risk = 0
                elif value <= t['warning']:
                    ratio = (value - t['good']) / (t['warning'] - t['good'])
                    feature_risk = ratio * 40
                elif value <= t['bad']:
                    ratio = (value - t['warning']) / (t['bad'] - t['warning'])
                    feature_risk = 40 + ratio * 40
                else:
                    feature_risk = 90

            risk_score   += feature_risk * weight
            total_weight += weight

        if total_weight == 0:
            return None

        final_risk = round(risk_score / total_weight)

        # Severity level
        if final_risk < 20:
            severity = 'LOW'
            color    = (0, 255, 100)
            message  = 'Spine health looks good'
        elif final_risk < 40:
            severity = 'MODERATE'
            color    = (0, 200, 255)
            message  = 'Monitor your posture regularly'
        elif final_risk < 65:
            severity = 'HIGH'
            color    = (0, 100, 255)
            message  = 'Corrective action recommended'
        else:
            severity = 'CRITICAL'
            color    = (0, 50, 220)
            message  = 'Consult a physiotherapist'

        return {
            'risk_score' : final_risk,
            'severity'   : severity,
            'color'      : color,
            'message'    : message,
        }

    def calculate_trend(self, filepath='data/posture_sessions.csv'):
        """
        Analyze historical data to find risk trend
        Returns: improving / worsening / stable
        """
        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, 'r') as f:
                records = list(csv.DictReader(f))

            if len(records) < 5:
                return None

            # Get last 10 scores
            recent = records[-10:]
            scores = []
            for r in recent:
                try:
                    scores.append(float(r['posture_score']))
                except:
                    continue

            if len(scores) < 3:
                return None

            # Compare first half vs second half
            mid        = len(scores) // 2
            first_avg  = sum(scores[:mid]) / mid
            second_avg = sum(scores[mid:]) / (len(scores) - mid)
            diff       = second_avg - first_avg

            if diff > 5:
                return {'trend': 'IMPROVING',  'color': (0, 255, 100),  'arrow': '↑', 'diff': round(diff)}
            elif diff < -5:
                return {'trend': 'WORSENING',  'color': (0, 80, 255),   'arrow': '↓', 'diff': round(abs(diff))}
            else:
                return {'trend': 'STABLE',     'color': (0, 200, 255),  'arrow': '→', 'diff': round(abs(diff))}

        except:
            return None

    def as_risk_panel(self, risk, trend):
        """Format risk info for display — returns list of lines"""
        lines = []
        if risk:
            lines.append(('SPINAL RISK SCORE', (180, 180, 180)))
            lines.append((f"{risk['risk_score']}/100  {risk['severity']}", risk['color']))
            lines.append((risk['message'], risk['color']))
        if trend:
            lines.append((f"Trend: {trend['arrow']} {trend['trend']} ({trend['diff']} pts)", trend['color']))
        return lines