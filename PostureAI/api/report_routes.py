import os
import sys
import json
import glob
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


def get_latest_snapshots(session_ts=None):
    """Get all snapshot paths sorted by time"""
    files = sorted(glob.glob("data/snapshot_*.jpg"), reverse=True)
    if not files:
        return []
    # Try to group by session — get most recent set (front, left, right)
    if session_ts:
        session_files = [f for f in files if session_ts in f]
        if session_files:
            return session_files[:3]
    # Return latest 3
    return files[:3]


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
    snapshot_paths  = data.get('snapshot_paths', [])

    # Auto-collect snapshots if not provided
    if not snapshot_paths:
        snapshot_paths = get_latest_snapshots()

    recs     = recommender.recommend(features)
    as_data  = as_risk_mod.calculate(features)
    filepath = pdf_gen.generate(
        features, result, risk, recs, as_data,
        snapshot_paths=snapshot_paths
    )
    return FileResponse(filepath, media_type="application/pdf", filename="posture_report.pdf")


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
    """Return paths of latest captured snapshots"""
    files = get_latest_snapshots()
    return {"snapshots": files, "count": len(files)}