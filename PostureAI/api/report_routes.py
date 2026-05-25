import os
import sys
import json
import glob
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from fastapi.responses import FileResponse
from modules.exercise_recommender import ExerciseRecommender
from modules.as_risk              import AnkylosingSpondylitisRisk
from modules.pdf_report           import PDFReportGenerator
from modules.email_sender         import EmailSender

router       = APIRouter()
recommender  = ExerciseRecommender()
as_risk_mod  = AnkylosingSpondylitisRisk()
pdf_gen      = PDFReportGenerator()
email_sender = EmailSender()

# Canonical capture order — must match CAPTURE_SEQUENCE in api/main.py
CAPTURE_SIDES = ["FRONT", "LEFT_SIDE", "RIGHT_SIDE"]


def get_latest_snapshots(session_ts=None):
    """
    Return snapshot paths in CAPTURE ORDER: FRONT → LEFT_SIDE → RIGHT_SIDE.

    Previous bug: glob sorted with reverse=True returned files newest-first
    (RIGHT_SIDE, LEFT_SIDE, FRONT) which caused them to be mislabelled in
    the PDF (the first file was shown under "FRONT" etc.).

    Fix: sort ascending by modification time so the first-captured file
    (FRONT) comes first, then filter/reorder by side name so the order is
    always deterministic regardless of filesystem timestamps.
    """
    files = glob.glob("data/snapshot_*.jpg")
    if not files:
        return []

    # ── If a session timestamp is given, restrict to that session ────────────
    if session_ts:
        session_files = [f for f in files if session_ts in f]
        if session_files:
            files = session_files

    # ── Sort by modification time ASCENDING (oldest = first captured) ────────
    files.sort(key=lambda p: os.path.getmtime(p))

    # ── Within those files, reorder to match canonical capture order ─────────
    # This is robust even if the filesystem timestamps collide.
    ordered = []
    for side in CAPTURE_SIDES:
        for f in files:
            basename = os.path.basename(f).upper()
            if side.upper() in basename and f not in ordered:
                ordered.append(f)
                break

    # Append any remaining files not matched by side name (safety net)
    for f in files:
        if f not in ordered:
            ordered.append(f)

    # Return only the most-recent complete set (up to 3)
    return ordered[:3]


@router.post("/generate")
async def generate_report(data: dict):
    features = data.get('features', {})
    result   = data.get('result',   {})
    risk     = data.get('risk',     {})
    recs     = recommender.recommend(features)
    filepath = recommender.save_report(features, result, risk, recs)
    return {'report_path':filepath, 'recommendations':recs, 'count':len(recs)}


@router.post("/generate-pdf")
async def generate_pdf(data: dict):
    features        = data.get('features', {})
    result          = data.get('result',   {})
    risk            = data.get('risk',     {})
    # snapshot_paths sent from the frontend are already in capture order
    # (the camera state builds snapshot_urls in FRONT→LEFT→RIGHT order).
    # Only fall back to auto-discovery when the frontend sends nothing.
    snapshot_paths  = data.get('snapshot_paths', [])

    # Strip empty / None entries that sometimes come from the frontend
    snapshot_paths = [p for p in snapshot_paths if p]

    # Map frontend "data/filename.jpg" style paths → local paths
    resolved = []
    for p in snapshot_paths:
        # Frontend may send "data/snapshot_xxx_FRONT.jpg" — keep as-is
        if os.path.exists(p):
            resolved.append(p)
        # Try stripping leading path separator issues
        elif os.path.exists(p.lstrip("/")):
            resolved.append(p.lstrip("/"))

    if not resolved:
        resolved = get_latest_snapshots()

    patient_name = data.get('patient_name', 'Patient')
    report_date  = data.get('report_date', '')
    recs         = recommender.recommend(features)
    as_data      = as_risk_mod.calculate(features)

    # Build the filename the same way the frontend expects it
    today        = report_date or datetime.now().strftime('%Y-%m-%d')
    safe_name    = "".join(c for c in (patient_name or "Patient").replace(" ","_") if c.isalnum() or c=="_")
    pdf_filename = f"{safe_name}_{today}.pdf"

    filepath = pdf_gen.generate(
        features, result, risk, recs, as_data,
        snapshot_paths=resolved,
        patient_name=patient_name,
        report_date=report_date,
    )
    return FileResponse(filepath, media_type="application/pdf", filename=pdf_filename)


@router.get("/download")
async def download_report():
    path = 'reports/exercise_report.txt'
    if not os.path.exists(path):
        return {'error': 'No report yet'}
    return FileResponse(path, filename='posture_report.txt')


@router.get("/exercises")
async def get_exercises(features: str = ''):
    try:
        feat = json.loads(features) if features else {}
    except:
        feat = {}
    recs = recommender.recommend(feat)
    return {'exercises': recs, 'count': len(recs)}


@router.post("/send-email")
async def send_email_report(data: dict):
    to_email        = data.get('to_email')
    sender_email    = data.get('sender_email')
    sender_password = data.get('sender_password')
    features        = data.get('features', {})
    result          = data.get('result',   {})
    risk            = data.get('risk',     {})
    snapshot_paths  = data.get('snapshot_paths', [])

    if not all([to_email, sender_email, sender_password]):
        return {'error': 'Missing email credentials'}

    snapshot_paths = [p for p in snapshot_paths if p]
    if not snapshot_paths:
        snapshot_paths = get_latest_snapshots()

    recs     = recommender.recommend(features)
    as_data  = as_risk_mod.calculate(features)
    pdf_path = pdf_gen.generate(features, result, risk, recs, as_data,
                                snapshot_paths=snapshot_paths)
    success  = email_sender.send_report(
        to_email, sender_email, sender_password, pdf_path, result, risk
    )
    return {'success':success, 'message':'Email sent!' if success else 'Email failed', 'pdf_path':pdf_path}


@router.get("/snapshots/latest")
async def get_latest_snapshot_paths():
    """Return paths of latest captured snapshots in capture order"""
    files = get_latest_snapshots()
    return {"snapshots": files, "count": len(files)}