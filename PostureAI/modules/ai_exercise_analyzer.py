import anthropic
import json
import base64
import os

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class AIExerciseAnalyzer:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def analyze_from_features(self, features, result, risk):
        if not features:
            return self._fallback_analysis()
        prompt = f"""You are a physiotherapy AI. Analyze posture data and recommend exercises.

POSTURE DATA:
- Score: {result.get('score', 0)}/100
- Classification: {result.get('classification', 'N/A')}
- Risk Score: {risk.get('risk_score', 0)}/100
- Severity: {risk.get('severity', 'N/A')}

MEASUREMENTS:
- Neck Forward Angle: {features.get('neck_forward_angle', 'N/A')} degrees
- Shoulder Slope: {features.get('shoulder_slope', 'N/A')} px
- Rounded Shoulder Angle: {features.get('rounded_shoulder_angle', 'N/A')} degrees
- Pelvic Tilt: {features.get('pelvic_tilt', 'N/A')} px
- Spine Deviation: {features.get('spine_deviation', 'N/A')} px

Return ONLY valid JSON, no extra text:
{{
  "summary": "2 sentence posture assessment",
  "urgency": "low",
  "exercises": [
    {{
      "name": "Chin Tuck",
      "issue": "Forward head posture",
      "description": "Step by step instructions",
      "sets": 3,
      "reps": 10,
      "hold_secs": 5,
      "frequency": "Daily",
      "difficulty": "Easy",
      "benefit": "Reduces neck strain"
    }}
  ],
  "lifestyle_tips": ["tip1", "tip2"],
  "when_to_see_doctor": "advice"
}}"""
        try:
            msg = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=2000,
                messages=[{"role":"user","content":prompt}]
            )
            text = msg.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            print(f"AI features error: {e}")
            return self._fallback_analysis()

    def analyze_from_image(self, image_path, features=None):
        if not os.path.exists(image_path):
            return self._fallback_analysis()
        try:
            with open(image_path, "rb") as f:
                img_data = base64.standard_b64encode(f.read()).decode("utf-8")

            feat_txt = ""
            if features:
                feat_txt = f"\nMeasurements: Neck={features.get('neck_forward_angle','N/A')}deg, Shoulder={features.get('shoulder_slope','N/A')}px"

            prompt = f"""Analyze this posture image and recommend exercises.{feat_txt}

Return ONLY valid JSON:
{{
  "summary": "2 sentence assessment",
  "urgency": "low",
  "exercises": [
    {{
      "name": "Exercise name",
      "issue": "Issue it fixes",
      "description": "Instructions",
      "sets": 3,
      "reps": 10,
      "hold_secs": 5,
      "frequency": "Daily",
      "difficulty": "Easy",
      "benefit": "Benefit"
    }}
  ],
  "lifestyle_tips": ["tip1", "tip2"],
  "when_to_see_doctor": "advice"
}}"""
            msg = self.client.messages.create(
                model="claude-opus-4-5",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type":"image","source":{"type":"base64","media_type":"image/jpeg","data":img_data}},
                        {"type":"text","text":prompt}
                    ]
                }]
            )
            text = msg.content[0].text
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            return json.loads(text)
        except Exception as e:
            print(f"AI image error: {e}")
            return self.analyze_from_features(features or {}, {}, {})

    def _fallback_analysis(self):
        """Returns basic exercises if AI fails"""
        return {
            "summary": "Based on typical posture patterns, here are recommended exercises to improve your posture and reduce spinal strain.",
            "urgency": "medium",
            "exercises": [
                {"name":"Chin Tuck","issue":"Forward head posture","description":"Sit straight. Gently pull chin back creating a double chin. Hold 5 seconds. Repeat 10 times.","sets":3,"reps":10,"hold_secs":5,"frequency":"Daily","difficulty":"Easy","benefit":"Reduces forward head posture"},
                {"name":"Wall Angels","issue":"Rounded shoulders","description":"Stand against wall with arms at 90 degrees. Slide arms up and down like making a snow angel. Keep back flat.","sets":3,"reps":10,"hold_secs":3,"frequency":"Daily","difficulty":"Medium","benefit":"Opens chest and corrects shoulder alignment"},
                {"name":"Cat Cow Stretch","issue":"Spine stiffness","description":"On hands and knees. Arch back up like a cat then drop belly down like a cow. Breathe slowly.","sets":3,"reps":10,"hold_secs":3,"frequency":"Daily","difficulty":"Easy","benefit":"Improves spinal flexibility"},
                {"name":"Thoracic Extension","issue":"Upper back rounding","description":"Sit on chair edge. Clasp hands behind head. Gently extend upper back over chair back. Hold 5 seconds.","sets":3,"reps":8,"hold_secs":5,"frequency":"Daily","difficulty":"Easy","benefit":"Reduces upper back rounding"},
            ],
            "lifestyle_tips":["Take a 5-minute standing break every 30 minutes","Keep screen at eye level to avoid neck strain","Strengthen core muscles with daily exercises"],
            "when_to_see_doctor":"If you experience persistent pain, numbness or tingling, consult a physiotherapist immediately."
        }