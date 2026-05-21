import os
import sys
import csv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter
from modules.as_risk       import AnkylosingSpondylitisRisk
from modules.risk_predictor import RiskPredictor

router    = APIRouter()
as_risk   = AnkylosingSpondylitisRisk()
predictor = RiskPredictor()


@router.post("/as-risk")
async def calculate_as_risk(features: dict):
    result = as_risk.calculate(features)
    return result


@router.get("/history")
async def get_history(limit: int = 50):
    filepath = 'data/posture_sessions.csv'
    if not os.path.exists(filepath):
        return {'sessions': [], 'count': 0}
    with open(filepath, 'r') as f:
        records = list(csv.DictReader(f))
    recent = records[-limit:] if len(records) > limit else records
    return {'sessions': recent, 'count': len(records)}


@router.get("/trend")
async def get_trend():
    trend = predictor.calculate_trend()
    return trend or {'trend': 'STABLE', 'arrow': '->', 'diff': 0}


@router.get("/stats")
async def get_stats():
    filepath = 'data/posture_sessions.csv'
    if not os.path.exists(filepath):
        return {}
    with open(filepath, 'r') as f:
        records = list(csv.DictReader(f))
    if not records:
        return {}

    scores          = []
    classifications = {'GOOD': 0, 'WARNING': 0, 'BAD': 0}

    for r in records:
        try:
            scores.append(float(r['posture_score']))
            c = r.get('classification', '')
            if c in classifications:
                classifications[c] += 1
        except:
            continue

    return {
        'total_sessions' : len(records),
        'avg_score'      : round(sum(scores)/len(scores), 1) if scores else 0,
        'best_score'     : max(scores) if scores else 0,
        'worst_score'    : min(scores) if scores else 0,
        'latest_score'   : scores[-1] if scores else 0,
        'classifications': classifications,
    }