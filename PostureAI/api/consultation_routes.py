import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Header
from modules.supabase_client import get_admin_client, get_client

router = APIRouter()


def get_user(authorization: str):
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "").strip()
    try:
        sb   = get_client()
        user = sb.auth.get_user(token)
        if user and user.user:
            return user.user
    except Exception as e:
        print(f"Auth error: {e}")
    raise HTTPException(status_code=401, detail="Session expired. Please login again.")


@router.get("/physiotherapists")
async def list_physiotherapists():
    sb = get_admin_client()
    r  = sb.table("profiles").select("*").eq("role", "physiotherapist").execute()
    return {"physiotherapists": r.data or []}


@router.post("/request")
async def request_consultation(data: dict, authorization: str = Header(None)):
    user      = get_user(authorization)
    physio_id = data.get("physio_id")
    message   = data.get("message", "")

    if not physio_id:
        raise HTTPException(status_code=400, detail="physio_id required")

    sb = get_admin_client()

    # Check existing
    existing = sb.table("consultations").select("*") \
        .eq("user_id",  str(user.id)) \
        .eq("physio_id", physio_id).execute()

    if existing.data:
        cid = existing.data[0]["id"]
        if message:
            sb.table("messages").insert({
                "consultation_id": cid,
                "sender_id"      : str(user.id),
                "message"        : message,
                "message_type"   : "text",
            }).execute()
            sb.table("consultations").update({"updated_at": "now()"}).eq("id", cid).execute()
        return {"success": True, "consultation_id": cid}

    result = sb.table("consultations").insert({
        "user_id"       : str(user.id),
        "physio_id"     : physio_id,
        "status"        : "pending",
        "user_message"  : message,
        "access_granted": False,
    }).execute()

    if result.data and message:
        cid = result.data[0]["id"]
        sb.table("messages").insert({
            "consultation_id": cid,
            "sender_id"      : str(user.id),
            "message"        : message,
            "message_type"   : "text",
        }).execute()

    return {
        "success"        : True,
        "consultation_id": result.data[0]["id"] if result.data else None,
    }


@router.get("/my-consultations")
async def my_consultations(authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()

    profile = sb.table("profiles").select("role").eq("id", str(user.id)).single().execute()
    role    = profile.data.get("role", "user") if profile.data else "user"

    if role == "physiotherapist":
        consults = sb.table("consultations") \
            .select("*, profiles!consultations_user_id_fkey(name,email,age,body_weight,height,id)") \
            .eq("physio_id", str(user.id)) \
            .order("updated_at", desc=True).execute()
    else:
        consults = sb.table("consultations") \
            .select("*, profiles!consultations_physio_id_fkey(name,speciality,experience,license_number,id)") \
            .eq("user_id", str(user.id)) \
            .order("updated_at", desc=True).execute()

    return {"consultations": consults.data or [], "role": role}


@router.put("/update-status/{consultation_id}")
async def update_status(consultation_id: str, data: dict, authorization: str = Header(None)):
    get_user(authorization)
    sb = get_admin_client()
    sb.table("consultations").update({
        "status"    : data.get("status"),
        "updated_at": "now()"
    }).eq("id", consultation_id).execute()
    return {"success": True}


@router.put("/grant-access/{consultation_id}")
async def grant_access(consultation_id: str, authorization: str = Header(None)):
    """Patient grants physiotherapist full access to their data"""
    user = get_user(authorization)
    sb   = get_admin_client()
    sb.table("consultations").update({
        "access_granted"   : True,
        "access_granted_at": "now()",
        "updated_at"       : "now()",
    }).eq("id", consultation_id).eq("user_id", str(user.id)).execute()

    # Notify physio
    sb.table("messages").insert({
        "consultation_id": consultation_id,
        "sender_id"      : str(user.id),
        "message"        : "✅ Patient has granted you full access to their posture data and progress tracking.",
        "message_type"   : "system",
    }).execute()

    return {"success": True, "message": "Access granted to physiotherapist"}


@router.put("/revoke-access/{consultation_id}")
async def revoke_access(consultation_id: str, authorization: str = Header(None)):
    """Patient revokes physiotherapist access"""
    user = get_user(authorization)
    sb   = get_admin_client()
    sb.table("consultations").update({
        "access_granted": False,
        "updated_at"    : "now()",
    }).eq("id", consultation_id).eq("user_id", str(user.id)).execute()

    sb.table("messages").insert({
        "consultation_id": consultation_id,
        "sender_id"      : str(user.id),
        "message"        : "ℹ️ Patient has revoked full data access.",
        "message_type"   : "system",
    }).execute()

    return {"success": True}


@router.post("/send-message")
async def send_message(data: dict, authorization: str = Header(None)):
    user            = get_user(authorization)
    consultation_id = data.get("consultation_id")
    message         = data.get("message")
    message_type    = data.get("message_type", "text")

    if not consultation_id or not message:
        raise HTTPException(status_code=400, detail="Missing fields")

    sb = get_admin_client()
    r  = sb.table("messages").insert({
        "consultation_id": consultation_id,
        "sender_id"      : str(user.id),
        "message"        : message,
        "message_type"   : message_type,
    }).execute()

    sb.table("consultations").update({"updated_at": "now()"}).eq("id", consultation_id).execute()
    return {"success": True, "message_id": r.data[0]["id"] if r.data else None}


@router.get("/messages/{consultation_id}")
async def get_messages(consultation_id: str, authorization: str = Header(None)):
    get_user(authorization)
    sb       = get_admin_client()
    messages = sb.table("messages") \
        .select("*, profiles(name, role)") \
        .eq("consultation_id", consultation_id) \
        .order("created_at").execute()
    return {"messages": messages.data or []}


@router.post("/share-report")
async def share_report(data: dict, authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()

    report = sb.table("shared_reports").insert({
        "consultation_id": data.get("consultation_id"),
        "user_id"        : str(user.id),
        "physio_id"      : data.get("physio_id"),
        "posture_score"  : data.get("result", {}).get("score"),
        "risk_score"     : data.get("risk",   {}).get("risk_score"),
        "risk_severity"  : data.get("risk",   {}).get("severity"),
        "classification" : data.get("result", {}).get("classification"),
        "features"       : data.get("features", {}),
        "recommendations": data.get("recommendations", []),
        "as_risk"        : data.get("as_risk", {}),
        "status"         : "pending",
    }).execute()

    cid    = data.get("consultation_id")
    result = data.get("result", {})
    snaps  = data.get("snapshot_names", [])

    if cid:
        msg = f"📊 Shared posture report — Score: {result.get('score',0)}/100 | Risk: {data.get('risk',{}).get('severity','N/A')}"
        if snaps:
            msg += f" | {len(snaps)} snapshot(s) attached"
        sb.table("messages").insert({
            "consultation_id": cid,
            "sender_id"      : str(user.id),
            "message"        : msg,
            "message_type"   : "report",
        }).execute()
        sb.table("consultations").update({"updated_at": "now()"}).eq("id", cid).execute()

    return {"success": True, "report_id": report.data[0]["id"] if report.data else None}


@router.get("/reports/{consultation_id}")
async def get_reports(consultation_id: str, authorization: str = Header(None)):
    get_user(authorization)
    sb      = get_admin_client()
    reports = sb.table("shared_reports").select("*") \
        .eq("consultation_id", consultation_id) \
        .order("created_at", desc=True).execute()
    return {"reports": reports.data or []}


@router.post("/add-guidance/{report_id}")
async def add_guidance(report_id: str, data: dict, authorization: str = Header(None)):
    get_user(authorization)
    sb = get_admin_client()
    sb.table("shared_reports").update({
        "physio_notes"   : data.get("notes", ""),
        "physio_guidance": data.get("guidance", ""),
        "status"         : "reviewed",
    }).eq("id", report_id).execute()
    return {"success": True}


@router.post("/prescribe")
async def create_prescription(data: dict, authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()

    result = sb.table("prescriptions").insert({
        "consultation_id": data.get("consultation_id"),
        "physio_id"      : str(user.id),
        "user_id"        : data.get("user_id"),
        "title"          : data.get("title", "Exercise Prescription"),
        "exercises"      : data.get("exercises", []),
        "notes"          : data.get("notes", ""),
        "follow_up_date" : data.get("follow_up_date"),
    }).execute()

    cid = data.get("consultation_id")
    if cid:
        sb.table("messages").insert({
            "consultation_id": cid,
            "sender_id"      : str(user.id),
            "message"        : f"💊 New prescription sent: {data.get('title','Exercise Prescription')}",
            "message_type"   : "prescription",
        }).execute()
        sb.table("consultations").update({"updated_at": "now()"}).eq("id", cid).execute()

    return {"success": True, "prescription_id": result.data[0]["id"] if result.data else None}


@router.get("/prescriptions")
async def get_prescriptions(authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()
    p    = sb.table("prescriptions") \
        .select("*, profiles!prescriptions_physio_id_fkey(name, speciality)") \
        .eq("user_id", str(user.id)) \
        .order("created_at", desc=True).execute()
    return {"prescriptions": p.data or []}


@router.get("/prescriptions-by-physio")
async def get_prescriptions_by_physio(authorization: str = Header(None)):
    """Physio gets all prescriptions they created"""
    user = get_user(authorization)
    sb   = get_admin_client()
    p    = sb.table("prescriptions") \
        .select("*, profiles!prescriptions_user_id_fkey(name, age, body_weight, height)") \
        .eq("physio_id", str(user.id)) \
        .order("created_at", desc=True).execute()
    return {"prescriptions": p.data or []}


@router.post("/log-daily")
async def log_daily_tracking(data: dict, authorization: str = Header(None)):
    """Patient logs daily posture score and exercises done"""
    user = get_user(authorization)
    sb   = get_admin_client()

    # Check if already logged today
    today   = __import__('datetime').date.today().isoformat()
    cid     = data.get("consultation_id")
    existing = sb.table("daily_tracking") \
        .select("id") \
        .eq("user_id", str(user.id)) \
        .eq("date", today).execute()

    if existing.data:
        # Update today's entry
        sb.table("daily_tracking").update({
            "posture_score" : data.get("posture_score"),
            "risk_score"    : data.get("risk_score"),
            "classification": data.get("classification"),
            "exercises_done": data.get("exercises_done", []),
            "pain_level"    : data.get("pain_level", 0),
            "notes"         : data.get("notes", ""),
            "features"      : data.get("features", {}),
        }).eq("id", existing.data[0]["id"]).execute()
        return {"success": True, "action": "updated"}

    sb.table("daily_tracking").insert({
        "user_id"        : str(user.id),
        "consultation_id": cid,
        "date"           : today,
        "posture_score"  : data.get("posture_score"),
        "risk_score"     : data.get("risk_score"),
        "classification" : data.get("classification"),
        "exercises_done" : data.get("exercises_done", []),
        "pain_level"     : data.get("pain_level", 0),
        "notes"          : data.get("notes", ""),
        "features"       : data.get("features", {}),
    }).execute()

    return {"success": True, "action": "created"}


@router.get("/patient-progress/{user_id}")
async def get_patient_progress(user_id: str, authorization: str = Header(None)):
    """Physio views patient's full progress data"""
    physio = get_user(authorization)
    sb     = get_admin_client()

    # Verify physio has access
    access = sb.table("consultations").select("*") \
        .eq("physio_id", str(physio.id)) \
        .eq("user_id",   user_id) \
        .execute()

    if not access.data:
        raise HTTPException(status_code=403, detail="No consultation with this patient")

    consultation    = access.data[0]
    access_granted  = consultation.get("access_granted", False)

    # Always return basic info
    profile = sb.table("profiles").select("*").eq("id", user_id).single().execute()

    # Daily tracking — always visible to physio
    tracking = sb.table("daily_tracking") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("date", desc=True) \
        .limit(30).execute()

    # Shared reports
    reports = sb.table("shared_reports").select("*") \
        .eq("consultation_id", consultation["id"]) \
        .order("created_at", desc=True).execute()

    # Prescriptions for this patient
    prescriptions = sb.table("prescriptions").select("*") \
        .eq("user_id",   user_id) \
        .eq("physio_id", str(physio.id)) \
        .order("created_at", desc=True).execute()

    # Full history — only if access granted
    full_history = None
    if access_granted:
        full_history = sb.table("daily_tracking") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("date", desc=False).execute()

    return {
        "patient"        : profile.data or {},
        "consultation"   : consultation,
        "access_granted" : access_granted,
        "tracking"       : tracking.data or [],
        "reports"        : reports.data or [],
        "prescriptions"  : prescriptions.data or [],
        "full_history"   : full_history.data if full_history else [],
    }


@router.get("/my-daily-progress")
async def my_daily_progress(authorization: str = Header(None)):
    """Patient views their own progress"""
    user = get_user(authorization)
    sb   = get_admin_client()
    r    = sb.table("daily_tracking") \
        .select("*") \
        .eq("user_id", str(user.id)) \
        .order("date", desc=False) \
        .limit(30).execute()
    return {"tracking": r.data or []}


@router.get("/profile")
async def get_profile(authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()
    p    = sb.table("profiles").select("*").eq("id", str(user.id)).single().execute()
    return p.data or {}


@router.put("/update-profile")
async def update_profile(data: dict, authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()
    sb.table("profiles").update({
        "name"          : data.get("name"),
        "speciality"    : data.get("speciality"),
        "experience"    : data.get("experience"),
        "bio"           : data.get("bio"),
        "phone"         : data.get("phone"),
        "license_number": data.get("license_number"),
    }).eq("id", str(user.id)).execute()
    return {"success": True}