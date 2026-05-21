import os
import sys
import cv2
import numpy as np
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, UploadFile, File
from modules.ml_model             import PostureMLModel
from modules.shap_explainer       import ShapExplainer
from modules.pose_detection       import PoseDetector
from modules.feature_engineering  import FeatureExtractor
from modules.posture_scorer       import PostureScorer
from modules.risk_predictor       import RiskPredictor
from modules.ai_exercise_analyzer import AIExerciseAnalyzer

router      = APIRouter()
ml          = PostureMLModel()
explainer   = None
ai_analyzer = AIExerciseAnalyzer()

ml.load()
explainer = ShapExplainer(ml)
explainer.setup()


@router.post("/predict")
async def predict_posture(features: dict):
    return ml.predict(features)


@router.post("/explain")
async def explain_posture(features: dict):
    explanation = explainer.explain(features)
    plot_path   = explainer.plot(features)
    return {'explanation':explanation, 'plot_path':plot_path}


@router.post("/ai-analyze")
async def ai_analyze(data: dict):
    """AI exercise analysis from features"""
    features = data.get("features", {})
    result   = data.get("result",   {})
    risk     = data.get("risk",     {})

    if not features or all(v is None for v in features.values()):
        return {"success":False, "error":"No feature data available"}

    analysis = ai_analyzer.analyze_from_features(features, result, risk)
    if analysis:
        return {"success":True, "analysis":analysis}
    return {"success":False, "error":"AI analysis failed"}


@router.post("/ai-analyze-snapshots")
async def ai_analyze_snapshots(data: dict):
    """AI analysis from multiple snapshot images"""
    import glob

    snapshot_paths = data.get("snapshot_paths", [])
    features       = data.get("features", {})
    result         = data.get("result",   {})
    risk           = data.get("risk",     {})

    # If no paths provided, use latest snapshots
    if not snapshot_paths:
        snapshot_paths = sorted(glob.glob("data/snapshot_*.jpg"), reverse=True)[:3]

    if not snapshot_paths:
        # Fall back to feature-based analysis
        if features:
            analysis = ai_analyzer.analyze_from_features(features, result, risk)
            return {"success":bool(analysis), "analysis":analysis}
        return {"success":False, "error":"No snapshots or features available"}

    # Use the front snapshot for image analysis (best for posture assessment)
    front_snap = None
    for p in snapshot_paths:
        if "FRONT" in p.upper():
            front_snap = p
            break

    if not front_snap and snapshot_paths:
        front_snap = snapshot_paths[0]

    # Load features from image if not provided
    if not features or all(v is None for v in features.values()):
        try:
            frame     = cv2.imread(front_snap)
            det       = PoseDetector()
            ext       = FeatureExtractor()
            sc        = PostureScorer()
            rp        = RiskPredictor()
            det.find_pose(frame)
            landmarks = det.get_landmarks(frame)
            features  = ext.extract_all(landmarks)
            result    = sc.calculate(features) or {}
            risk      = rp.calculate_risk(features) or {}
        except:
            pass

    # Try image-based AI analysis first
    analysis = ai_analyzer.analyze_from_image(front_snap, features)

    # Fallback to feature-based if image fails
    if not analysis and features:
        analysis = ai_analyzer.analyze_from_features(features, result, risk)

    if analysis:
        return {"success":True, "analysis":analysis, "snapshots_used":len(snapshot_paths)}

    return {"success":False, "error":"AI analysis failed"}


@router.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr    = np.frombuffer(contents, np.uint8)
    frame    = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return {'error':'Invalid image'}

    temp_path = "data/temp_analysis.jpg"
    cv2.imwrite(temp_path, frame)

    det  = PoseDetector()
    ext  = FeatureExtractor()
    sc   = PostureScorer()
    rp   = RiskPredictor()

    det.find_pose(frame)
    landmarks = det.get_landmarks(frame)
    features  = ext.extract_all(landmarks)
    result    = sc.calculate(features)
    risk      = rp.calculate_risk(features)
    ml_result = ml.predict(features) if features else None
    ai_result = ai_analyzer.analyze_from_image(temp_path, features)

    return {'features':features, 'score':result, 'risk':risk, 'ml_predict':ml_result, 'ai_analysis':ai_result}


@router.post("/analyze-snapshot")
async def analyze_snapshot(data: dict):
    filename = data.get("filename")
    path     = f"data/{filename}"
    if not os.path.exists(path):
        return {"error":"Snapshot not found"}

    frame = cv2.imread(path)
    det   = PoseDetector()
    ext   = FeatureExtractor()
    sc    = PostureScorer()
    rp    = RiskPredictor()

    det.find_pose(frame)
    landmarks = det.get_landmarks(frame)
    features  = ext.extract_all(landmarks)
    result    = sc.calculate(features)
    risk      = rp.calculate_risk(features)
    ml_result = ml.predict(features) if features else None
    ai_result = ai_analyzer.analyze_from_image(path, features)

    return {'filename':filename, 'features':features, 'score':result, 'risk':risk, 'ml_predict':ml_result, 'ai_analysis':ai_result}