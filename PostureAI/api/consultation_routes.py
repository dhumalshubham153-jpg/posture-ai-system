import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Header
from modules.supabase_client import get_admin_client, get_client

try:
    import jwt as pyjwt
    _JWT_AVAILABLE = True
except ImportError:
    _JWT_AVAILABLE = False

router = APIRouter()

# ── Get from Supabase dashboard → Settings → API → JWT Secret ─────────────────
SUPABASE_JWT_SECRET = os.getenv(
    "SUPABASE_JWT_SECRET",
    "your-supabase-jwt-secret-here"   # fallback — set the env var instead
)


class _UserObj:
    """Minimal object so the rest of the code can do user.id"""
    def __init__(self, uid: str):
        self.id = uid


def get_user(authorization: str) -> _UserObj:
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "").strip()

    # Structural check — catch corrupted/empty tokens immediately
    if not token or token.count(".") != 2:
        raise HTTPException(
            status_code=401,
            detail="Malformed token — please logout and login again"
        )

    # Check token is not obviously empty after stripping
    parts = token.split(".")
    if any(len(p) < 4 for p in parts):
        raise HTTPException(
            status_code=401,
            detail="Incomplete token — please logout and login again"
        )

    # ── Path 1: local JWT verification (fast, no network, no timeout) ─────────
    if _JWT_AVAILABLE and SUPABASE_JWT_SECRET != "your-supabase-jwt-secret-here":
        try:
            payload = pyjwt.decode(
                token,
                SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
            return _UserObj(payload["sub"])
        except pyjwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Session expired. Please login again.")
        except pyjwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
        except Exception as e:
            # Fall through to remote verification
            print(f"Local JWT verify failed, trying remote: {e}")

    # ── Path 2: remote Supabase verification (fallback) ───────────────────────
    try:
        sb   = get_client()
        user = sb.auth.get_user(token)
        if user and user.user:
            return _UserObj(str(user.user.id))
    except Exception as e:
        print(f"Auth error: {e}")

    raise HTTPException(status_code=401, detail="Session expired. Please login again.")


def safe_get_profile(sb, user_id: str, fields: list):
    """Fetch a profile row safely — returns {} on any error"""
    if not user_id:
        return {}
    try:
        field_str = "*" if fields == ["*"] else ", ".join(fields)
        r = sb.table("profiles").select(field_str).eq("id", user_id).single().execute()
        return r.data or {}
    except Exception:
        return {}


# ── Routes ────────────────────────────────────────────────────────────────────

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

    existing = sb.table("consultations").select("*") \
        .eq("user_id",   str(user.id)) \
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

    role = "user"
    try:
        profile_r = sb.table("profiles").select("role").eq("id", str(user.id)).single().execute()
        role      = profile_r.data.get("role", "user") if profile_r.data else "user"
    except Exception:
        pass

    try:
        if role == "physiotherapist":
            consults_r = sb.table("consultations").select("*") \
                .eq("physio_id", str(user.id)) \
                .order("updated_at", desc=True).execute()
        else:
            consults_r = sb.table("consultations").select("*") \
                .eq("user_id", str(user.id)) \
                .order("updated_at", desc=True).execute()
        consultations = consults_r.data or []
    except Exception as e:
        print(f"Consultations fetch error: {e}")
        consultations = []

    for c in consultations:
        if role == "physiotherapist":
            c["profiles"] = safe_get_profile(
                sb, c.get("user_id", ""),
                ["name", "email", "age", "body_weight", "height", "id"]
            )
        else:
            c["profiles"] = safe_get_profile(
                sb, c.get("physio_id", ""),
                ["name", "speciality", "experience", "license_number", "id"]
            )

    return {"consultations": consultations, "role": role}


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
    user = get_user(authorization)
    sb   = get_admin_client()
    sb.table("consultations").update({
        "access_granted"   : True,
        "access_granted_at": "now()",
        "updated_at"       : "now()",
    }).eq("id", consultation_id).eq("user_id", str(user.id)).execute()
    sb.table("messages").insert({
        "consultation_id": consultation_id,
        "sender_id"      : str(user.id),
        "message"        : "✅ Patient has granted you full access to their posture data and progress tracking.",
        "message_type"   : "system",
    }).execute()
    return {"success": True, "message": "Access granted to physiotherapist"}


@router.put("/revoke-access/{consultation_id}")
async def revoke_access(consultation_id: str, authorization: str = Header(None)):
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
    sb         = get_admin_client()
    messages_r = sb.table("messages").select("*") \
        .eq("consultation_id", consultation_id) \
        .order("created_at").execute()
    messages = messages_r.data or []
    for m in messages:
        m["profiles"] = safe_get_profile(sb, m.get("sender_id", ""), ["name", "role"])
    return {"messages": messages}


@router.post("/share-report")
async def share_report(data: dict, authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()
    pdf_filename = data.get("pdf_filename", "")
    pdf_url      = data.get("pdf_url", "")
    patient_name = data.get("patient_name", "Patient")
    report_date  = data.get("report_date", "")

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
        "pdf_filename"   : pdf_filename,
        "pdf_url"        : pdf_url,
        "patient_name"   : patient_name,
        "report_date"    : report_date,
        "status"         : "pending",
    }).execute()
    cid    = data.get("consultation_id")
    result = data.get("result", {})
    snaps  = data.get("snapshot_names", [])
    if cid:
        msg = f"📊 Shared posture report — Score: {result.get('score',0)}/100 | Risk: {data.get('risk',{}).get('severity','N/A')}"
        if snaps:
            msg += f" | {len(snaps)} snapshot(s) attached"
        if pdf_filename:
            msg += f" | 📄 PDF: {pdf_filename}"
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
    p    = sb.table("prescriptions").select("*") \
        .eq("user_id", str(user.id)) \
        .order("created_at", desc=True).execute()
    prescriptions = p.data or []
    for presc in prescriptions:
        presc["profiles"] = safe_get_profile(sb, presc.get("physio_id", ""), ["name", "speciality"])
    return {"prescriptions": prescriptions}


@router.get("/prescriptions-by-physio")
async def get_prescriptions_by_physio(authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()
    p    = sb.table("prescriptions").select("*") \
        .eq("physio_id", str(user.id)) \
        .order("created_at", desc=True).execute()
    prescriptions = p.data or []
    for presc in prescriptions:
        presc["profiles"] = safe_get_profile(sb, presc.get("user_id", ""), ["name", "age", "body_weight", "height"])
    return {"prescriptions": prescriptions}


@router.post("/log-daily")
async def log_daily_tracking(data: dict, authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()
    today    = __import__('datetime').date.today().isoformat()
    existing = sb.table("daily_tracking").select("id") \
        .eq("user_id", str(user.id)).eq("date", today).execute()
    if existing.data:
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
        "consultation_id": data.get("consultation_id"),
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
    physio = get_user(authorization)
    sb     = get_admin_client()
    access = sb.table("consultations").select("*") \
        .eq("physio_id", str(physio.id)).eq("user_id", user_id).execute()
    if not access.data:
        raise HTTPException(status_code=403, detail="No consultation with this patient")
    consultation   = access.data[0]
    access_granted = consultation.get("access_granted", False)
    tracking = sb.table("daily_tracking").select("*") \
        .eq("user_id", user_id).order("date", desc=True).limit(30).execute()
    reports = sb.table("shared_reports").select("*") \
        .eq("consultation_id", consultation["id"]).order("created_at", desc=True).execute()
    prescriptions = sb.table("prescriptions").select("*") \
        .eq("user_id", user_id).eq("physio_id", str(physio.id)).order("created_at", desc=True).execute()
    full_history = None
    if access_granted:
        full_history = sb.table("daily_tracking").select("*") \
            .eq("user_id", user_id).order("date", desc=False).execute()
    return {
        "patient"       : safe_get_profile(sb, user_id, ["*"]),
        "consultation"  : consultation,
        "access_granted": access_granted,
        "tracking"      : tracking.data or [],
        "reports"       : reports.data or [],
        "prescriptions" : prescriptions.data or [],
        "full_history"  : full_history.data if full_history else [],
    }


@router.get("/my-daily-progress")
async def my_daily_progress(authorization: str = Header(None)):
    user = get_user(authorization)
    sb   = get_admin_client()
    r    = sb.table("daily_tracking").select("*") \
        .eq("user_id", str(user.id)).order("date", desc=False).limit(30).execute()
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