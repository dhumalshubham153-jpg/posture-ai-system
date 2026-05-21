from datetime import datetime

class AnkylosingSpondylitisRisk:
    """
    Simulates Ankylosing Spondylitis (AS) progression risk
    based on posture measurements over time
    """

    # AS risk factors mapped to posture features
    AS_WEIGHTS = {
        'neck_forward_angle'     : 0.35,
        'rounded_shoulder_angle' : 0.30,
        'spine_deviation'        : 0.25,
        'shoulder_slope'         : 0.05,
        'pelvic_tilt'            : 0.05,
    }

    STAGES = [
        {
            'stage'      : 0,
            'name'       : 'No Risk',
            'range'      : (0,  20),
            'color'      : '#34d399',
            'description': 'Excellent spinal health. Keep maintaining good posture.',
            'timeline'   : 'No progression expected',
        },
        {
            'stage'      : 1,
            'name'       : 'Early Risk',
            'range'      : (20, 40),
            'color'      : '#fbbf24',
            'description': 'Minor postural deviations detected. Corrective exercises advised.',
            'timeline'   : 'Progression possible in 5-10 years without correction',
        },
        {
            'stage'      : 2,
            'name'       : 'Moderate Risk',
            'range'      : (40, 60),
            'color'      : '#fb923c',
            'description': 'Significant postural issues. Physiotherapy strongly recommended.',
            'timeline'   : 'Progression likely in 2-5 years without intervention',
        },
        {
            'stage'      : 3,
            'name'       : 'High Risk',
            'range'      : (60, 80),
            'color'      : '#f87171',
            'description': 'Severe postural deviations. Immediate medical consultation advised.',
            'timeline'   : 'Progression likely in 1-2 years without intervention',
        },
        {
            'stage'      : 4,
            'name'       : 'Critical Risk',
            'range'      : (80, 100),
            'color'      : '#dc2626',
            'description': 'Critical spinal risk. Consult a rheumatologist immediately.',
            'timeline'   : 'Immediate medical intervention required',
        },
    ]

    def calculate(self, features):
        """Calculate AS risk score from features"""
        if not features:
            return None

        raw_score  = 0
        total_w    = 0
        indicators = []

        for feat, weight in self.AS_WEIGHTS.items():
            value = features.get(feat)
            if value is None:
                continue

            # Normalize to 0-100 risk
            if feat == 'neck_forward_angle':
                risk = min(100, (value / 45) * 100)
                if value > 20:
                    indicators.append(f"Forward head posture ({value:.1f} deg)")

            elif feat == 'rounded_shoulder_angle':
                risk = min(100, max(0, (160 - value) / 80 * 100))
                if value < 140:
                    indicators.append(f"Rounded shoulders ({value:.1f} deg)")

            elif feat == 'spine_deviation':
                risk = min(100, (value / 80) * 100)
                if value > 30:
                    indicators.append(f"Spinal deviation ({value:.1f}px)")

            elif feat == 'shoulder_slope':
                risk = min(100, (value / 50) * 100)
                if value > 15:
                    indicators.append(f"Shoulder asymmetry ({value:.1f}px)")

            elif feat == 'pelvic_tilt':
                risk = min(100, (value / 50) * 100)
                if value > 15:
                    indicators.append(f"Pelvic tilt ({value:.1f}px)")

            else:
                risk = 0

            raw_score += risk * weight
            total_w   += weight

        if total_w == 0:
            return None

        as_score = round(raw_score / total_w)

        # Find stage
        stage_info = self.STAGES[0]
        for s in self.STAGES:
            lo, hi = s['range']
            if lo <= as_score < hi:
                stage_info = s
                break

        # Progression simulation
        progression = self._simulate_progression(as_score)

        return {
            'as_score'   : as_score,
            'stage'      : stage_info['stage'],
            'stage_name' : stage_info['name'],
            'color'      : stage_info['color'],
            'description': stage_info['description'],
            'timeline'   : stage_info['timeline'],
            'indicators' : indicators,
            'progression': progression,
        }

    def _simulate_progression(self, current_score):
        """Simulate AS progression over 10 years"""
        progression = []
        year        = datetime.now().year
        score       = current_score

        for i in range(11):
            # Without intervention score worsens
            no_intervention = min(100, score + i * 2.5)

            # With intervention score improves
            with_intervention = max(0, score - i * 3.0)

            progression.append({
                'year'             : year + i,
                'no_intervention'  : round(no_intervention, 1),
                'with_intervention': round(with_intervention, 1),
            })

        return progression