import numpy as np

class FeatureExtractor:

    def calculate_angle(self, a, b, c):
        """Calculate angle at point B between lines BA and BC"""
        a = np.array([a['x'], a['y']])
        b = np.array([b['x'], b['y']])
        c = np.array([c['x'], c['y']])

        ba = a - b
        bc = c - b

        cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
        angle = np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0)))
        return round(angle, 2)

    def is_visible(self, landmark, threshold=0.5):
        """Only use landmark if confidence is high enough"""
        return landmark.get('visibility', 0) > threshold

    def neck_forward_angle(self, landmarks):
        """
        Forward head posture — angle between ear, shoulder, hip
        Normal: ~170-180 degrees
        Forward head: drops below 160
        """
        try:
            ear      = landmarks[7]   # left ear
            shoulder = landmarks[11]  # left shoulder
            hip      = landmarks[23]  # left hip

            if not self.is_visible(ear) or not self.is_visible(shoulder):
                return None

            angle = self.calculate_angle(ear, shoulder, hip)
            deviation = round(180 - angle, 2)
            return deviation
        except:
            return None

    def shoulder_slope(self, landmarks):
        """
        Shoulder asymmetry — height difference between left/right shoulder
        Normal: < 5px difference
        """
        try:
            left_sh  = landmarks[11]
            right_sh = landmarks[12]

            if not self.is_visible(left_sh) or not self.is_visible(right_sh):
                return None

            slope = abs(left_sh['y'] - right_sh['y'])
            return slope
        except:
            return None

    def rounded_shoulder_angle(self, landmarks):
        """
        Rounded shoulders — angle at shoulder between ear and elbow
        Normal: > 160 degrees
        Rounded: drops below 140
        """
        try:
            ear   = landmarks[7]   # left ear
            sh    = landmarks[11]  # left shoulder
            elbow = landmarks[13]  # left elbow

            if not self.is_visible(ear) or not self.is_visible(sh) or not self.is_visible(elbow):
                return None

            angle = self.calculate_angle(ear, sh, elbow)
            return round(angle, 2)
        except:
            return None

    def pelvic_tilt(self, landmarks):
        """
        Pelvic tilt — height difference between left/right hip
        Normal: < 5px difference
        """
        try:
            left_hip  = landmarks[23]
            right_hip = landmarks[24]

            if not self.is_visible(left_hip) or not self.is_visible(right_hip):
                return None

            tilt = abs(left_hip['y'] - right_hip['y'])
            return tilt
        except:
            return None

    def spine_alignment(self, landmarks):
        """
        Spine deviation — horizontal offset between nose and mid-hip
        Normal: < 10px
        """
        try:
            nose      = landmarks[0]
            left_hip  = landmarks[23]
            right_hip = landmarks[24]

            if not self.is_visible(left_hip) or not self.is_visible(right_hip):
                return None

            mid_hip_x = (left_hip['x'] + right_hip['x']) / 2
            deviation = abs(nose['x'] - mid_hip_x)
            return round(deviation, 2)
        except:
            return None

    def extract_all(self, landmarks):
        """Extract all features and return as dictionary"""
        if not landmarks:
            return None

        return {
            'neck_forward_angle'    : self.neck_forward_angle(landmarks),
            'shoulder_slope'        : self.shoulder_slope(landmarks),
            'rounded_shoulder_angle': self.rounded_shoulder_angle(landmarks),
            'pelvic_tilt'           : self.pelvic_tilt(landmarks),
            'spine_deviation'       : self.spine_alignment(landmarks),
        }