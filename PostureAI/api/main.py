import os
import sys
import time
import cv2
import numpy as np
import base64

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse

from api.posture_routes      import router as posture_router
from api.risk_routes         import router as risk_router
from api.report_routes       import router as report_router
from api.auth_routes         import router as auth_router
from api.consultation_routes import router as consultation_router
from modules.ml_model            import PostureMLModel
from modules.pose_detection      import PoseDetector
from modules.feature_engineering import FeatureExtractor
from modules.posture_scorer      import PostureScorer
from modules.risk_predictor      import RiskPredictor
from modules.supabase_client     import get_admin_client as _get_sb

app = FastAPI(
    title      = "PostureAI API",
    description= "AI-Powered Posture Analysis & Spinal Risk Prediction",
    version    = "1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins    = ["*"],
    allow_credentials= True,
    allow_methods    = ["*"],
    allow_headers    = ["*"],
)

app.include_router(posture_router,      prefix="/posture", tags=["Posture"])
app.include_router(risk_router,         prefix="/risk",    tags=["Risk"])
app.include_router(report_router,       prefix="/report",  tags=["Report"])
app.include_router(auth_router,         prefix="/auth",    tags=["Auth"])
app.include_router(consultation_router, prefix="/consult", tags=["Consultation"])


@app.on_event("startup")
async def startup():
    ml = PostureMLModel()
    if not os.path.exists('models/posture_model.pkl'):
        print("Training ML model...")
        ml.train()
    else:
        print("ML model already trained")


@app.get("/")
async def root():
    return {"message": "PostureAI API is running", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# ── Supabase upload helper ────────────────────────────────────────────────────
def upload_to_supabase(local_path: str, filename: str):
    """Upload snapshot to Supabase Storage bucket 'snapshots'"""
    try:
        sb = _get_sb()
        with open(local_path, 'rb') as f:
            data = f.read()
        sb.storage.from_("snapshots").upload(
            filename,
            data,
            {"content-type": "image/jpeg", "x-upsert": "true"}
        )
        url = sb.storage.from_("snapshots").get_public_url(filename)
        print(f"✅ Uploaded to Supabase: {filename}")
        return url
    except Exception as e:
        print(f"❌ Supabase upload error: {e}")
        return None


# ── Global camera state ───────────────────────────────────────────────────────
camera_running = False

camera_state = {
    "features"      : {},
    "score"         : {},
    "risk"          : {},
    "orientation"   : "unknown",
    "current_step"  : 0,
    "capture_done"  : False,
    "saved_paths"   : [],
    "snapshot_urls" : [],
    "instruction"   : "Please face the camera directly",
    "hold_progress" : 0.0,
    "voice_message" : "",
    "capture_flash" : False,
}

CAPTURE_SEQUENCE = [
    {'side': 'FRONT',      'target': 'front', 'instruction': 'Face the camera directly'},
    {'side': 'LEFT_SIDE',  'target': 'left',  'instruction': 'Show your LEFT side to camera'},
    {'side': 'RIGHT_SIDE', 'target': 'right', 'instruction': 'Show your RIGHT side to camera'},
]

CAPTURED_MSGS = [
    'Front captured. Now show your left side to the camera',
    'Left captured. Now show your right side to the camera',
    'All snapshots captured. Great job!',
]

detector  = PoseDetector()
extractor = FeatureExtractor()
scorer    = PostureScorer()
predictor = RiskPredictor()


def detect_orientation(landmarks_raw):
    if not landmarks_raw:
        return 'unknown'
    try:
        nose     = landmarks_raw[0]
        left_sh  = landmarks_raw[11]
        right_sh = landmarks_raw[12]

        nose_vis  = nose['visibility']
        sh_width  = abs(left_sh['x'] - right_sh['x'])
        sh_mid_x  = (left_sh['x'] + right_sh['x']) / 2
        nose_off  = nose['x'] - sh_mid_x

        # LEFT side — shoulders close + nose shifted right
        if sh_width < 80 and nose_off > 40:
            return 'left'

        # RIGHT side — shoulders close + nose shifted left
        if sh_width < 80 and nose_off < -40:
            return 'right'

        # FRONT — shoulders wide + nose visible
        if sh_width > 150 and nose_vis >= 0.75:
            return 'front'

        return 'unknown'

    except:
        return 'unknown'


class OrientationSmoother:
    def __init__(self, required_frames=6):
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


def generate_frames():
    global camera_running
    camera_running = True

    cap      = cv2.VideoCapture(0)
    smoother = OrientationSmoother(required_frames=6)

    current_step   = 0
    hold_start     = None
    hold_needed    = 2.0
    saved_paths    = []
    capture_done   = False
    session_ts     = time.strftime('%Y%m%d_%H%M%S')
    last_direction = None
    os.makedirs('data', exist_ok=True)

    camera_state['voice_message'] = 'Welcome to PostureAI. Please face the camera directly.'
    camera_state['instruction']   = CAPTURE_SEQUENCE[0]['instruction']
    camera_state['snapshot_urls'] = []

    ARROWS = {
        ('front',   'left')  : 'Show your LEFT side',
        ('front',   'right') : 'Show your RIGHT side',
        ('left',    'front') : 'Face the camera',
        ('left',    'right') : 'Show your RIGHT side',
        ('right',   'front') : 'Face the camera',
        ('right',   'left')  : 'Show your LEFT side',
        ('unknown', 'front') : 'Stand straight and face camera',
        ('unknown', 'left')  : 'Show your LEFT side',
        ('unknown', 'right') : 'Show your RIGHT side',
    }

    VOICE_MAP = {
        'Show your LEFT side'           : 'Please show your left side to the camera',
        'Show your RIGHT side'          : 'Please show your right side to the camera',
        'Face the camera'               : 'Please face the camera directly',
        'Stand straight and face camera': 'Please stand straight and face the camera',
    }

    while camera_running:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w  = frame.shape[:2]

        detector.find_pose(frame)
        frame     = detector.draw_landmarks(frame)
        landmarks = detector.get_landmarks(frame)
        features  = extractor.extract_all(landmarks)
        result    = scorer.calculate(features)
        risk      = predictor.calculate_risk(features)

        raw_orientation = detect_orientation(landmarks)
        orientation     = smoother.update(raw_orientation)

        # Update global camera state
        if features:
            camera_state['features']     = features
        if result:
            camera_state['score']        = result
        if risk:
            camera_state['risk']         = risk
        camera_state['orientation']      = orientation
        camera_state['current_step']     = current_step
        camera_state['capture_done']     = capture_done
        camera_state['saved_paths']      = saved_paths
        camera_state['capture_flash']    = False

        # Debug text at bottom
        cv2.putText(
            frame,
            f"Orient: {orientation.upper()} | nose: {round(landmarks.get(0,{}).get('visibility',0),2) if landmarks else 0}",
            (10, h-15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80,80,80), 1
        )

        # Score overlay top-left
        if result:
            score = result['score']
            color = (0,255,100) if score>=75 else (0,200,255) if score>=50 else (0,80,255)
            cv2.rectangle(frame, (0,0), (240,75), (0,0,0), -1)
            cv2.putText(frame, f"Score: {score}/100",
                        (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
            cv2.putText(frame, result['classification'],
                        (10,58), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Risk overlay top-right
        if risk:
            rv     = risk.get('risk_score', 0)
            rcolor = (0,255,100) if rv<30 else (0,200,255) if rv<60 else (0,80,255)
            cv2.rectangle(frame, (w-200,0), (w,45), (0,0,0), -1)
            cv2.putText(frame, f"Risk: {rv}/100",
                        (w-190,20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, rcolor, 1)
            cv2.putText(frame, risk.get('severity',''),
                        (w-190,38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, rcolor, 1)

        if not capture_done and current_step < len(CAPTURE_SEQUENCE):
            step   = CAPTURE_SEQUENCE[current_step]
            target = step['target']
            camera_state['instruction'] = step['instruction']

            # Progress dots
            dot_start = w//2 - (len(CAPTURE_SEQUENCE)*30)//2
            for i in range(len(CAPTURE_SEQUENCE)):
                dx = dot_start + i*30
                if i < len(saved_paths):
                    cv2.circle(frame, (dx,20), 9, (0,255,100), -1)
                    cv2.putText(frame, 'OK', (dx-9,24),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.26, (0,0,0), 1)
                elif i == current_step:
                    cv2.circle(frame, (dx,20), 9, (0,255,157), 2)
                    cv2.circle(frame, (dx,20), 5, (0,255,157), -1)
                else:
                    cv2.circle(frame, (dx,20), 9, (60,60,60), -1)

            # Bottom guide panel
            overlay = frame.copy()
            cv2.rectangle(overlay, (0,h-135), (w,h), (0,0,0), -1)
            cv2.addWeighted(overlay, 0.78, frame, 0.22, 0, frame)
            cv2.putText(frame, f"STEP {current_step+1}/{len(CAPTURE_SEQUENCE)}: {step['side']}",
                        (10,h-103), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,157), 2)

            if orientation == target:
                if hold_start is None:
                    hold_start     = time.time()
                    last_direction = None
                    camera_state['voice_message'] = 'Good! Hold still.'

                hold_time = time.time() - hold_start
                hold_pct  = min(hold_time / hold_needed, 1.0)
                camera_state['hold_progress'] = hold_pct

                cv2.putText(frame, "GOOD! Hold still...",
                            (10,h-72), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,255,100), 2)

                bw = w - 20
                cv2.rectangle(frame, (10,h-52), (10+bw,h-37), (40,40,40), -1)
                fill = int(bw * hold_pct)
                cv2.rectangle(frame, (10,h-52), (10+fill,h-37), (0,255,100), -1)

                remaining = max(0, hold_needed - hold_time)
                cv2.putText(frame, f"Capturing in {remaining:.1f}s...",
                            (10,h-16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

                # Flash effect just before capture
                if hold_time >= hold_needed - 0.15:
                    flash = frame.copy()
                    cv2.rectangle(flash, (0,0), (w,h), (255,255,255), -1)
                    cv2.addWeighted(flash, 0.4, frame, 0.6, 0, frame)

                # ── CAPTURE SAVE BLOCK ────────────────────────────────────
                if hold_time >= hold_needed:
                    snap_name  = f"snapshot_{session_ts}_{step['side'].replace(' ','_')}.jpg"
                    local_path = f"data/{snap_name}"

                    # Save locally
                    cv2.imwrite(local_path, frame)
                    saved_paths.append(local_path)

                    # Upload to Supabase Storage
                    supabase_url = upload_to_supabase(local_path, snap_name)
                    camera_state['snapshot_urls'].append({
                        'side'    : step['side'],
                        'filename': snap_name,
                        'url'     : supabase_url or '',
                    })

                    camera_state['capture_flash'] = True
                    camera_state['voice_message'] = CAPTURED_MSGS[current_step]
                    current_step  += 1
                    hold_start     = None
                    last_direction = None
                    if current_step >= len(CAPTURE_SEQUENCE):
                        capture_done = True
                        camera_state['capture_done'] = True
                # ── END CAPTURE SAVE BLOCK ────────────────────────────────

            else:
                hold_start = None
                camera_state['hold_progress'] = 0.0

                arrow = ARROWS.get((orientation, target), 'Adjust position')
                voice = VOICE_MAP.get(arrow, 'Adjust your position')

                if arrow != last_direction:
                    camera_state['voice_message'] = voice
                    last_direction = arrow

                cv2.putText(frame, step['instruction'],
                            (10,h-72), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200,200,200), 1)
                cv2.putText(frame, arrow,
                            (w//2-160,h-35), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0,200,255), 3)

        elif capture_done:
            overlay = frame.copy()
            cv2.rectangle(overlay, (0,0), (w,h), (0,0,0), -1)
            cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
            cv2.putText(frame, "ALL SNAPSHOTS SAVED!",
                        (w//2-220,h//2-20), cv2.FONT_HERSHEY_SIMPLEX,
                        1.1, (0,255,157), 3)
            cv2.putText(frame, "Check your dashboard",
                        (w//2-160,h//2+30), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (200,200,200), 1)

        _, buffer   = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes +
            b"\r\n"
        )

    cap.release()
    camera_running = False


# ── Camera endpoints ──────────────────────────────────────────────────────────
@app.get("/camera/stream")
async def camera_stream():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace;boundary=frame"
    )


@app.get("/camera/state")
async def camera_state_api():
    return camera_state


@app.post("/camera/stop")
async def camera_stop():
    global camera_running
    camera_running = False
    return {"stopped": True}


@app.post("/camera/reset")
async def camera_reset():
    global camera_running
    camera_running = False
    camera_state['current_step']  = 0
    camera_state['capture_done']  = False
    camera_state['saved_paths']   = []
    camera_state['snapshot_urls'] = []
    camera_state['voice_message'] = 'Please face the camera directly'
    camera_state['hold_progress'] = 0.0
    camera_state['capture_flash'] = False
    return {"reset": True}


# ── Snapshot endpoints ────────────────────────────────────────────────────────
@app.get("/snapshots/list")
async def list_snapshots():
    """List all saved snapshots from local data/ folder"""
    import glob
    files = sorted(glob.glob("data/snapshot_*.jpg"), reverse=True)
    snapshots = []
    for f in files:
        name = os.path.basename(f)
        snapshots.append({
            "filename": name,
            "name"    : name,
            "path"    : f,
            "size"    : os.path.getsize(f),
            "url"     : f"/snapshots/view/{name}",
        })
    return {"snapshots": snapshots, "count": len(snapshots)}


@app.get("/snapshots/view/{filename}")
async def view_snapshot(filename: str):
    """Serve a snapshot image file"""
    path = f"data/{filename}"
    if not os.path.exists(path):
        return {"error": "Not found"}
    return FileResponse(path, media_type="image/jpeg")


@app.delete("/snapshots/delete/{filename}")
async def delete_snapshot(filename: str):
    """Delete a local snapshot"""
    path = f"data/{filename}"
    if os.path.exists(path):
        os.remove(path)
        return {"deleted": True, "filename": filename}
    return {"error": "Not found"}