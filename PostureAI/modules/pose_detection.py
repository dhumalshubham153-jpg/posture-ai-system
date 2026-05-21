import cv2
import mediapipe as mp

mp_pose = mp.solutions.pose

class PoseDetector:
    def __init__(self):
        self.pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.75,
            min_tracking_confidence=0.75
        )
        self.results = None

    def find_pose(self, frame):
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.pose.process(rgb)
        return self.results

    def draw_landmarks(self, frame):
        if self.results and self.results.pose_landmarks:

            POSTURE_LANDMARKS = [
                7,  8,
                11, 12,
                13, 14,
                15, 16,
                23, 24,
            ]

            CONNECTIONS = [
                (7,  11),
                (8,  12),
                (11, 12),
                (11, 13),
                (12, 14),
                (13, 15),
                (14, 16),
                (11, 23),
                (12, 24),
                (23, 24),
            ]

            h, w = frame.shape[:2]
            lm = self.results.pose_landmarks.landmark

            for start, end in CONNECTIONS:
                if lm[start].visibility > 0.5 and lm[end].visibility > 0.5:
                    x1 = int(lm[start].x * w)
                    y1 = int(lm[start].y * h)
                    x2 = int(lm[end].x * w)
                    y2 = int(lm[end].y * h)
                    cv2.line(frame, (x1, y1), (x2, y2), (0, 200, 255), 2)

            for idx in POSTURE_LANDMARKS:
                if lm[idx].visibility > 0.5:
                    x = int(lm[idx].x * w)
                    y = int(lm[idx].y * h)
                    cv2.circle(frame, (x, y), 6, (0, 255, 0), -1)
                    cv2.circle(frame, (x, y), 6, (255, 255, 255), 1)

        return frame

    def get_landmarks(self, frame):
        h, w = frame.shape[:2]
        landmarks = {}
        if self.results and self.results.pose_landmarks:
            for idx, lm in enumerate(self.results.pose_landmarks.landmark):
                landmarks[idx] = {
                    'x'          : int(lm.x * w),
                    'y'          : int(lm.y * h),
                    'z'          : lm.z,
                    'visibility' : lm.visibility
                }
        return landmarks