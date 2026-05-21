import cv2
import time
import threading
import pyttsx3
from datetime import datetime
from modules.pose_detection import PoseDetector
from modules.feature_engineering import FeatureExtractor
from modules.posture_scorer import PostureScorer
from modules.data_logger import DataLogger
from modules.risk_predictor import RiskPredictor
from modules.exercise_recommender import ExerciseRecommender

# ── Voice Engine ──────────────────────────────────────────────────────────────
class VoiceAssistant:
    def __init__(self):
        self.engine      = pyttsx3.init()
        self.engine.setProperty('rate', 160)
        self.engine.setProperty('volume', 1.0)
        self._speaking   = False
        self._last_spoke = 0
        self._cooldown   = 3.0

    def speak(self, text, force=False):
        now = time.time()
        if self._speaking:
            return
        if not force and (now - self._last_spoke) < self._cooldown:
            return
        def run():
            self._speaking   = True
            self._last_spoke = time.time()
            self.engine.say(text)
            self.engine.runAndWait()
            self._speaking   = False
        threading.Thread(target=run, daemon=True).start()

# ── Capture sequence ──────────────────────────────────────────────────────────
CAPTURE_SEQUENCE = [
    {
        'side'       : 'FRONT',
        'instruction': 'Face the camera directly',
        'target'     : 'front',
        'prompt'     : 'Please face the camera directly',
        'captured'   : 'Front captured. Now turn your left side to the camera',
    },
    {
        'side'       : 'LEFT SIDE',
        'instruction': 'Turn your LEFT side to camera',
        'target'     : 'left',
        'prompt'     : 'Turn your left side to the camera',
        'captured'   : 'Left side captured. Now turn your right side to the camera',
    },
    {
        'side'       : 'RIGHT SIDE',
        'instruction': 'Turn your RIGHT side to camera',
        'target'     : 'right',
        'prompt'     : 'Turn your right side to the camera',
        'captured'   : 'Right side captured. Now turn your back to the camera',
    },
    {
        'side'       : 'BACK',
        'instruction': 'Turn your BACK to camera',
        'target'     : 'back',
        'prompt'     : 'Turn your back to the camera',
        'captured'   : 'All snapshots captured. Generating your exercise report now.',
    },
]

# ── Orientation smoother ──────────────────────────────────────────────────────
class OrientationSmoother:
    def __init__(self, required_frames=8):
        self.required  = required_frames
        self.current   = 'unknown'
        self.candidate = 'unknown'
        self.count     = 0

    def update(self, raw):
        if raw == self.candidate:
            self.count += 1
        else:
            self.candidate = raw
            self.count     = 1
        if self.count >= self.required:
            self.current = self.candidate
        return self.current

# ── Orientation detector ──────────────────────────────────────────────────────
def detect_orientation(landmarks_raw):
    if not landmarks_raw:
        return 'unknown'
    try:
        nose     = landmarks_raw[0]
        left_sh  = landmarks_raw[11]
        right_sh = landmarks_raw[12]

        nose_vis    = nose['visibility']
        sh_width    = abs(left_sh['x'] - right_sh['x'])
        sh_mid_x    = (left_sh['x'] + right_sh['x']) / 2
        nose_offset = nose['x'] - sh_mid_x

        # BACK first — nose drops below 0.75
        if nose_vis < 0.75:
            return 'back'

        # LEFT — shoulders close + nose shifted right
        if sh_width < 80 and nose_offset > 40:
            return 'left'

        # RIGHT — shoulders close + nose shifted left
        if sh_width < 80 and nose_offset < -40:
            return 'right'

        # FRONT — shoulders wide + nose visible
        if sh_width > 150 and nose_vis >= 0.75:
            return 'front'

        return 'unknown'

    except:
        return 'unknown'


def get_direction_arrow(current, target):
    directions = {
        ('front',   'left')  : ('<< Turn LEFT',   (0, 200, 255)),
        ('front',   'right') : ('>> Turn RIGHT',  (0, 200, 255)),
        ('front',   'back')  : ('|| Turn AROUND', (0, 200, 255)),
        ('left',    'front') : ('>> Turn FRONT',  (0, 200, 255)),
        ('left',    'right') : ('>> Turn RIGHT',  (0, 200, 255)),
        ('left',    'back')  : ('|| Turn AROUND', (0, 200, 255)),
        ('right',   'front') : ('<< Turn FRONT',  (0, 200, 255)),
        ('right',   'left')  : ('<< Turn LEFT',   (0, 200, 255)),
        ('right',   'back')  : ('|| Turn AROUND', (0, 200, 255)),
        ('back',    'front') : ('|| Turn FRONT',  (0, 200, 255)),
        ('back',    'left')  : ('<< Turn LEFT',   (0, 200, 255)),
        ('back',    'right') : ('>> Turn RIGHT',  (0, 200, 255)),
        ('unknown', 'front') : ('Stand Straight', (255, 200, 0)),
        ('unknown', 'left')  : ('<< Turn LEFT',   (255, 200, 0)),
        ('unknown', 'right') : ('>> Turn RIGHT',  (255, 200, 0)),
        ('unknown', 'back')  : ('|| Turn AROUND', (255, 200, 0)),
    }
    return directions.get((current, target), ('Adjust position', (255, 200, 0)))


def arrow_to_voice(arrow_text):
    if 'LEFT' in arrow_text:
        return 'Turn left please'
    elif 'RIGHT' in arrow_text:
        return 'Turn right please'
    elif 'AROUND' in arrow_text or 'BACK' in arrow_text:
        return 'Turn around please'
    elif 'FRONT' in arrow_text:
        return 'Turn to the front please'
    elif 'Straight' in arrow_text:
        return 'Stand straight please'
    return 'Adjust your position'


# ── Draw functions ────────────────────────────────────────────────────────────
def draw_score_panel(frame, result):
    cv2.rectangle(frame, (0, 0), (320, 200), (0, 0, 0), -1)
    cv2.rectangle(frame, (0, 0), (320, 200), (50, 50, 50), 1)

    score = result['score']
    color = result['color']
    label = result['classification']

    cv2.putText(frame, "POSTURE SCORE", (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
    cv2.putText(frame, f"{score}/100", (10, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 1.6, color, 3)
    cv2.putText(frame, label, (170, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    bar_x, bar_y, bar_w, bar_h = 10, 85, 300, 12
    cv2.rectangle(frame, (bar_x, bar_y),
                  (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
    fill = int(bar_w * score / 100)
    cv2.rectangle(frame, (bar_x, bar_y),
                  (bar_x + fill, bar_y + bar_h), color, -1)

    y = 115
    if result['issues']:
        cv2.putText(frame, "Issues detected:", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
        y += 20
        for issue in result['issues'][:3]:
            cv2.putText(frame, f"  ! {issue}", (10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 100, 255), 1)
            y += 18
    else:
        cv2.putText(frame, "No issues detected!", (10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 100), 1)

    return frame


def draw_risk_panel(frame, risk, trend):
    h, w = frame.shape[:2]
    px   = w - 260

    cv2.rectangle(frame, (px, 0), (w, 160), (0, 0, 0), -1)
    cv2.rectangle(frame, (px, 0), (w, 160), (50, 50, 50), 1)

    if risk:
        cv2.putText(frame, "SPINAL RISK", (px + 10, 28),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (180, 180, 180), 1)
        risk_color = risk['color']
        cv2.putText(frame, f"{risk['risk_score']}/100",
                    (px + 10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.4, risk_color, 3)
        cv2.putText(frame, risk['severity'],
                    (px + 130, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, risk_color, 2)

        bar_x = px + 10
        bar_w = 240
        cv2.rectangle(frame, (bar_x, 85), (bar_x + bar_w, 97),
                      (60, 60, 60), -1)
        fill = int(bar_w * risk['risk_score'] / 100)
        cv2.rectangle(frame, (bar_x, 85), (bar_x + fill, 97),
                      risk_color, -1)
        cv2.putText(frame, risk['message'],
                    (px + 10, 118),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, risk_color, 1)

    if trend:
        cv2.putText(frame,
                    f"Trend: {trend['arrow']} {trend['trend']}",
                    (px + 10, 145),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, trend['color'], 1)

    return frame


def draw_exercise_panel(frame, recommendations):
    h, w = frame.shape[:2]
    px   = w - 260
    py   = 165

    cv2.rectangle(frame, (px, py), (w, py + 200), (0, 0, 0), -1)
    cv2.rectangle(frame, (px, py), (w, py + 200), (50, 50, 50), 1)

    cv2.putText(frame, "EXERCISES", (px + 10, py + 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180, 180, 180), 1)

    if not recommendations:
        cv2.putText(frame, "Posture looks great!",
                    (px + 10, py + 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 100), 1)
        return frame

    y    = py + 45
    seen = set()
    for r in recommendations:
        if r['exercise'] in seen:
            continue
        seen.add(r['exercise'])
        cv2.putText(frame, r['exercise'],
                    (px + 10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 157), 1)
        y += 16
        cv2.putText(frame,
                    f"  {r['sets']}x{r['reps']} | {r['hold_secs']}s hold",
                    (px + 10, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (150, 150, 150), 1)
        y += 18
        if y > py + 190:
            break

    return frame


def draw_capture_guide(frame, step, orientation, hold_time, hold_needed=2.0):
    h, w   = frame.shape[:2]
    target = step['target']

    overlay = frame.copy()
    cv2.rectangle(overlay, (0, h - 140), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    cv2.putText(frame, f"STEP: {step['side']}",
                (10, h - 108),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 157), 2)

    if orientation == target:
        cv2.putText(frame, "GOOD! Hold still...",
                    (10, h - 76),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 100), 2)

        bar_w = w - 20
        cv2.rectangle(frame, (10, h - 55), (10 + bar_w, h - 38),
                      (40, 40, 40), -1)
        fill = int(bar_w * min(hold_time / hold_needed, 1.0))
        cv2.rectangle(frame, (10, h - 55), (10 + fill, h - 38),
                      (0, 255, 100), -1)

        remaining = max(0, hold_needed - hold_time)
        cv2.putText(frame, f"Capturing in {remaining:.1f}s...",
                    (10, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        if hold_time >= hold_needed - 0.15:
            flash = frame.copy()
            cv2.rectangle(flash, (0, 0), (w, h), (255, 255, 255), -1)
            cv2.addWeighted(flash, 0.35, frame, 0.65, 0, frame)
    else:
        arrow_text, arrow_color = get_direction_arrow(orientation, target)
        cv2.putText(frame, step['instruction'],
                    (10, h - 76),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
        cv2.putText(frame, arrow_text,
                    (w//2 - 160, h - 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.1, arrow_color, 3)
        cv2.putText(frame, f"Detected: {orientation.upper()}",
                    (10, h - 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (120, 120, 120), 1)

    return frame


def draw_step_progress(frame, current_step, total, side_names, saved):
    h, w    = frame.shape[:2]
    cx      = w // 2
    start_x = cx - (total * 35) // 2

    for i in range(total):
        x = start_x + i * 35
        if i < len(saved):
            cv2.circle(frame, (x, 18), 9, (0, 255, 100), -1)
            cv2.putText(frame, 'OK', (x - 8, 22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.28, (0, 0, 0), 1)
        elif i == current_step:
            cv2.circle(frame, (x, 18), 9, (0, 255, 157), 2)
            cv2.circle(frame, (x, 18), 5, (0, 255, 157), -1)
        else:
            cv2.circle(frame, (x, 18), 9, (60, 60, 60), -1)

    return frame


def draw_all_done(frame, saved_paths, recommendations):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)

    cv2.putText(frame, "SCAN COMPLETE!",
                (w//2 - 180, h//2 - 140),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 157), 3)

    cv2.putText(frame, "Snapshots saved:",
                (w//2 - 280, h//2 - 100),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)
    y = h//2 - 80
    for path in saved_paths:
        cv2.putText(frame, f"[OK] {path}",
                    (w//2 - 280, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 255, 180), 1)
        y += 20

    cv2.putText(frame, "Your exercises:",
                (w//2 - 280, y + 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
    y += 30
    seen = set()
    for r in recommendations:
        if r['exercise'] in seen:
            continue
        seen.add(r['exercise'])
        cv2.putText(frame,
                    f"  {r['exercise']} -- {r['sets']}x{r['reps']} reps",
                    (w//2 - 280, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 157), 1)
        y += 22
        if y > h - 80:
            break

    cv2.putText(frame, "Report saved to reports/exercise_report.txt",
                (w//2 - 280, h - 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (255, 200, 0), 1)
    cv2.putText(frame, "Press Q or ESC to exit",
                (w//2 - 170, h - 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 200, 0), 2)
    return frame


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    cap         = cv2.VideoCapture(0)
    detector    = PoseDetector()
    extractor   = FeatureExtractor()
    scorer      = PostureScorer()
    logger      = DataLogger()
    predictor   = RiskPredictor()
    recommender = ExerciseRecommender()
    smoother    = OrientationSmoother(required_frames=8)
    voice       = VoiceAssistant()

    log_interval   = 3
    last_log       = time.time()
    frame_count    = 0

    current_step   = 0
    hold_start     = None
    hold_needed    = 2.0
    saved_paths    = []
    capture_done   = False
    session_ts     = datetime.now().strftime('%Y%m%d_%H%M%S')
    side_names     = [s['side'] for s in CAPTURE_SEQUENCE]
    prompt_spoken  = False
    last_direction = None
    recommendations= []
    last_features  = None
    last_result    = None
    last_risk      = None

    print("PostureAI — Module 6: Exercise Recommendations")
    print("Q or ESC = Quit")

    voice.speak(
        "Welcome to PostureAI. Let us capture your posture from all sides.",
        force=True
    )
    time.sleep(0.5)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        detector.find_pose(frame)
        frame = detector.draw_landmarks(frame)

        landmarks       = detector.get_landmarks(frame)
        features        = extractor.extract_all(landmarks)
        result          = scorer.calculate(features)
        risk            = predictor.calculate_risk(features)
        trend           = predictor.calculate_trend()
        raw_orientation = detect_orientation(landmarks)
        orientation     = smoother.update(raw_orientation)

        # Save latest valid data
        if features:
            last_features = features
        if result:
            last_result = result
        if risk:
            last_risk = risk

        # Live recommendations
        recommendations = recommender.recommend(features)

        # Log every 3 seconds
        now = time.time()
        if result and (now - last_log) >= log_interval:
            logger.log(features, result)
            last_log    = now
            frame_count += 1

        if result:
            frame = draw_score_panel(frame, result)
        if risk:
            frame = draw_risk_panel(frame, risk, trend)

        frame = draw_exercise_panel(frame, recommendations)

        # ── Auto capture ─────────────────────────────────────────────────────
        if not capture_done and current_step < len(CAPTURE_SEQUENCE):
            step   = CAPTURE_SEQUENCE[current_step]
            target = step['target']

            if not prompt_spoken:
                voice.speak(step['prompt'], force=True)
                prompt_spoken  = True
                last_direction = None

            if orientation == target:
                if hold_start is None:
                    hold_start = time.time()
                    voice.speak("Good! Hold still.", force=True)
                    last_direction = None
                hold_time = time.time() - hold_start
            else:
                if hold_start is not None:
                    hold_start = None
                hold_time = 0

                arrow_text, _ = get_direction_arrow(orientation, target)
                if arrow_text != last_direction:
                    voice.speak(arrow_to_voice(arrow_text), force=True)
                    last_direction = arrow_text

            frame = draw_capture_guide(
                frame, step, orientation,
                hold_time, hold_needed
            )
            frame = draw_step_progress(
                frame, current_step,
                len(CAPTURE_SEQUENCE), side_names, saved_paths
            )

            if hold_start and hold_time >= hold_needed:
                filename = (
                    f"data/snapshot_{session_ts}"
                    f"_{step['side'].replace(' ', '_')}.jpg"
                )
                cv2.imwrite(filename, frame)
                saved_paths.append(filename)
                print(f"[OK] Captured: {filename}")

                voice.speak(step['captured'], force=True)

                current_step  += 1
                hold_start     = None
                prompt_spoken  = False
                last_direction = None

                if current_step >= len(CAPTURE_SEQUENCE):
                    capture_done = True
                    print("\nAll snapshots saved!")

                    final_recs = recommender.recommend(last_features)
                    recommender.save_report(
                        last_features, last_result,
                        last_risk, final_recs
                    )
                    ex_voice = recommender.to_voice(final_recs)
                    voice.speak(ex_voice, force=True)

        elif capture_done:
            final_recs = recommender.recommend(last_features)
            frame      = draw_all_done(frame, saved_paths, final_recs)

        h = frame.shape[0]
        cv2.putText(frame, f"Logged: {frame_count} | Q/ESC = Quit",
                    (10, h - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1)

        cv2.imshow("PostureAI", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    print(f"Done. {frame_count} records logged.")

if __name__ == "__main__":
    main()