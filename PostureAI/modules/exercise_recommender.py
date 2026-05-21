class ExerciseRecommender:

    EXERCISES = {
        'neck_forward_angle': [
            {
                'name'        : 'Chin Tuck',
                'description' : 'Pull chin straight back creating a double chin',
                'sets'        : 3,
                'reps'        : 10,
                'hold_secs'   : 5,
                'difficulty'  : 'Easy',
            },
            {
                'name'        : 'Neck Retraction Stretch',
                'description' : 'Sit tall slowly retract head backwards',
                'sets'        : 3,
                'reps'        : 8,
                'hold_secs'   : 8,
                'difficulty'  : 'Easy',
            },
        ],
        'rounded_shoulder_angle': [
            {
                'name'        : 'Wall Angels',
                'description' : 'Stand against wall slide arms up and down',
                'sets'        : 3,
                'reps'        : 12,
                'hold_secs'   : 3,
                'difficulty'  : 'Medium',
            },
            {
                'name'        : 'Doorway Chest Stretch',
                'description' : 'Place forearms on doorframe lean forward gently',
                'sets'        : 3,
                'reps'        : 1,
                'hold_secs'   : 30,
                'difficulty'  : 'Easy',
            },
            {
                'name'        : 'Band Pull Apart',
                'description' : 'Hold band at shoulder height pull apart horizontally',
                'sets'        : 3,
                'reps'        : 15,
                'hold_secs'   : 2,
                'difficulty'  : 'Medium',
            },
        ],
        'shoulder_slope': [
            {
                'name'        : 'Shoulder Shrugs',
                'description' : 'Raise both shoulders to ears hold then release',
                'sets'        : 3,
                'reps'        : 12,
                'hold_secs'   : 3,
                'difficulty'  : 'Easy',
            },
            {
                'name'        : 'Lateral Neck Stretch',
                'description' : 'Tilt head to one side hold then switch sides',
                'sets'        : 2,
                'reps'        : 1,
                'hold_secs'   : 30,
                'difficulty'  : 'Easy',
            },
        ],
        'pelvic_tilt': [
            {
                'name'        : 'Pelvic Tilts',
                'description' : 'Lie on back flatten lower back against floor',
                'sets'        : 3,
                'reps'        : 15,
                'hold_secs'   : 5,
                'difficulty'  : 'Easy',
            },
            {
                'name'        : 'Hip Flexor Stretch',
                'description' : 'Lunge forward push hips forward gently',
                'sets'        : 2,
                'reps'        : 1,
                'hold_secs'   : 30,
                'difficulty'  : 'Medium',
            },
        ],
        'spine_deviation': [
            {
                'name'        : 'Cat Cow Stretch',
                'description' : 'On hands and knees arch and round your back',
                'sets'        : 3,
                'reps'        : 10,
                'hold_secs'   : 3,
                'difficulty'  : 'Easy',
            },
            {
                'name'        : 'Child Pose',
                'description' : 'Kneel and stretch arms forward on the floor',
                'sets'        : 2,
                'reps'        : 1,
                'hold_secs'   : 45,
                'difficulty'  : 'Easy',
            },
        ],
    }

    TRIGGER = {
        'neck_forward_angle'     : 15,
        'shoulder_slope'         : 10,
        'rounded_shoulder_angle' : 150,
        'pelvic_tilt'            : 10,
        'spine_deviation'        : 20,
    }

    def recommend(self, features):
        if not features:
            return []

        recommendations = []

        for name, value in features.items():
            if value is None:
                continue

            triggered = False
            t = self.TRIGGER[name]

            if name == 'rounded_shoulder_angle':
                if value < t:
                    triggered = True
            else:
                if value > t:
                    triggered = True

            if triggered and name in self.EXERCISES:
                for ex in self.EXERCISES[name]:
                    recommendations.append({
                        'issue'      : name.replace('_', ' ').title(),
                        'exercise'   : ex['name'],
                        'description': ex['description'],
                        'sets'       : ex['sets'],
                        'reps'       : ex['reps'],
                        'hold_secs'  : ex['hold_secs'],
                        'difficulty' : ex['difficulty'],
                    })

        return recommendations

    def to_voice(self, recommendations):
        if not recommendations:
            return "Your posture looks great! Keep it up."

        lines = []
        seen  = set()
        for r in recommendations:
            if r['exercise'] not in seen:
                lines.append(
                    f"{r['exercise']}. {r['description']}. "
                    f"{r['sets']} sets of {r['reps']} reps."
                )
                seen.add(r['exercise'])

        return "Recommended exercises: " + ". Next, ".join(lines[:3])

    def save_report(self, features, result, risk, recommendations,
                    filepath='reports/exercise_report.txt'):
        import os
        from datetime import datetime
        os.makedirs('reports', exist_ok=True)

        with open(filepath, 'w') as f:
            f.write("=" * 50 + "\n")
            f.write("   POSTUREAI EXERCISE REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("POSTURE SCORES\n")
            if result:
                f.write(f"Posture Score : {result['score']}/100\n")
                f.write(f"Classification: {result['classification']}\n")
            if risk:
                f.write(f"Spinal Risk   : {risk['risk_score']}/100\n")
                f.write(f"Severity      : {risk['severity']}\n")
            f.write("\n")

            f.write("FEATURE MEASUREMENTS\n")
            if features:
                for k, v in features.items():
                    label = k.replace('_', ' ').title()
                    value = str(v) if v is not None else 'Not visible'
                    f.write(f"{label:30s}: {value}\n")
            f.write("\n")

            f.write("RECOMMENDED EXERCISES\n")
            if recommendations:
                for i, r in enumerate(recommendations, 1):
                    f.write(f"\n{i}. {r['exercise']} [{r['difficulty']}]\n")
                    f.write(f"   Issue   : {r['issue']}\n")
                    f.write(f"   How to  : {r['description']}\n")
                    f.write(f"   Sets    : {r['sets']} sets x {r['reps']} reps\n")
                    f.write(f"   Hold    : {r['hold_secs']} seconds\n")
            else:
                f.write("No issues detected. Great posture!\n")

            f.write("\n" + "=" * 50 + "\n")
            f.write("Consult a physiotherapist for medical advice.\n")
            f.write("=" * 50 + "\n")

        print(f"Report saved: {filepath}")
        return filepath