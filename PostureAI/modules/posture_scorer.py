class PostureScorer:

    # Normal ranges for each feature
    THRESHOLDS = {
        'neck_forward_angle'    : {'good': 15,  'warning': 25,  'bad': 35},
        'shoulder_slope'        : {'good': 10,  'warning': 20,  'bad': 35},
        'rounded_shoulder_angle': {'good': 150, 'warning': 130, 'bad': 110},
        'pelvic_tilt'           : {'good': 10,  'warning': 20,  'bad': 35},
        'spine_deviation'       : {'good': 20,  'warning': 40,  'bad': 60},
    }

    # How much each feature affects the final score
    WEIGHTS = {
        'neck_forward_angle'    : 0.30,
        'shoulder_slope'        : 0.20,
        'rounded_shoulder_angle': 0.25,
        'pelvic_tilt'           : 0.10,
        'spine_deviation'       : 0.15,
    }

    def score_feature(self, name, value):
        """
        Score a single feature from 0 to 100
        100 = perfect, 0 = very bad
        """
        t = self.THRESHOLDS[name]

        # rounded_shoulder_angle is inverse (higher = better)
        if name == 'rounded_shoulder_angle':
            if value >= t['good']:
                return 100
            elif value >= t['warning']:
                # Scale between 60-100
                ratio = (value - t['warning']) / (t['good'] - t['warning'])
                return round(60 + ratio * 40)
            elif value >= t['bad']:
                # Scale between 20-60
                ratio = (value - t['bad']) / (t['warning'] - t['bad'])
                return round(20 + ratio * 40)
            else:
                return 10
        else:
            # Lower = better for all other features
            if value <= t['good']:
                return 100
            elif value <= t['warning']:
                # Scale between 60-100
                ratio = (value - t['good']) / (t['warning'] - t['good'])
                return round(100 - ratio * 40)
            elif value <= t['bad']:
                # Scale between 20-60
                ratio = (value - t['warning']) / (t['bad'] - t['warning'])
                return round(60 - ratio * 40)
            else:
                return 10

    def calculate(self, features):
        """
        Calculate overall posture score from all features
        Returns score, classification, and per-feature breakdown
        """
        if not features:
            return None

        total_weight  = 0
        weighted_sum  = 0
        breakdown     = {}
        issues        = []

        for name, value in features.items():
            if value is None:
                continue

            feature_score = self.score_feature(name, value)
            weight        = self.WEIGHTS[name]

            weighted_sum  += feature_score * weight
            total_weight  += weight
            breakdown[name] = feature_score

            # Collect issues
            t = self.THRESHOLDS[name]
            if name == 'rounded_shoulder_angle':
                if value < t['warning']:
                    issues.append(f"Rounded shoulders detected")
            else:
                if value > t['warning']:
                    issues.append(f"{name.replace('_', ' ').title()} is high")

        # Final score
        if total_weight == 0:
            return None

        final_score = round(weighted_sum / total_weight)

        # Classification
        if final_score >= 75:
            classification = 'GOOD'
            color          = (0, 255, 100)
        elif final_score >= 50:
            classification = 'WARNING'
            color          = (0, 200, 255)
        else:
            classification = 'BAD'
            color          = (0, 80, 255)

        return {
            'score'          : final_score,
            'classification' : classification,
            'color'          : color,
            'breakdown'      : breakdown,
            'issues'         : issues,
        }