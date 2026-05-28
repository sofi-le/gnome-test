import json
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from fastapi import FastAPI, File, Header, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from parser import parse_dna_file
from pgx import run_pharmacogenomics
from prs import compute_risk_scores
from carrier import check_carrier_status
from traits import analyze_traits
from report import generate_report
from pdf import render_pdf
from supabase_client import get_supabase


# Persistent session storage (local disk fallback)
SESSIONS_DIR = Path(__file__).parent / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# In-memory session store: session_id -> { snps: DataFrame, ancestry: dict, results: dict }
sessions: dict[str, dict[str, Any]] = {}


# -- Auth helper --

async def _get_user_id(authorization: str | None) -> str | None:
    """Extract user_id from Supabase JWT. Returns None if no auth configured."""
    sb = get_supabase()
    if not sb or not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    try:
        resp = sb.auth.get_user(token)
        return str(resp.user.id) if resp and resp.user else None
    except Exception:
        return None


# -- Local disk persistence --

def _save_session_disk(session_id: str, session: dict):
    path = SESSIONS_DIR / session_id
    path.mkdir(exist_ok=True)
    session["snps"].to_parquet(path / "snps.parquet", index=False)
    meta = {"ancestry": session.get("ancestry", {}), "sex": session.get("sex", "Unknown"), "source": session.get("source", "")}
    (path / "meta.json").write_text(json.dumps(meta))


def _load_sessions_disk():
    if not SESSIONS_DIR.exists():
        return
    for p in SESSIONS_DIR.iterdir():
        if not p.is_dir() or p.name.startswith("."):
            continue
        snps_path = p / "snps.parquet"
        meta_path = p / "meta.json"
        if snps_path.exists() and meta_path.exists():
            meta = json.loads(meta_path.read_text())
            sessions[p.name] = {
                "snps": pd.read_parquet(snps_path),
                "ancestry": meta.get("ancestry", {}),
                "sex": meta.get("sex", "Unknown"),
                "source": meta.get("source", ""),
            }


# -- Supabase persistence --

def _save_session_supabase(session_id: str, user_id: str, filename: str,
                           source: str, snp_count: int, ancestry: dict, raw_bytes: bytes):
    sb = get_supabase()
    if not sb:
        return

    # Upload raw DNA file to storage
    file_path = f"{user_id}/{session_id}/{filename}"
    try:
        sb.storage.from_("dna-files").upload(
            path=file_path, file=raw_bytes,
            file_options={"content-type": "text/plain"},
        )
    except Exception:
        pass  # file may already exist

    # Insert session row
    dominant = max(ancestry, key=ancestry.get) if ancestry else None
    sb.table("sessions").insert({
        "id": session_id,
        "user_id": user_id,
        "filename": filename,
        "dna_source": source,
        "snp_count": snp_count,
        "dna_file_path": file_path,
        "ancestry_group": dominant,
        "status": "pending",
    }).execute()


def _save_report_supabase(session_id: str, user_id: str, modules: dict, narrative):
    sb = get_supabase()
    if not sb:
        return

    sb.table("reports").insert({
        "session_id": session_id,
        "user_id": user_id,
        "pgx": modules.get("pharmacogenomics"),
        "disease_risk": modules.get("disease_risk"),
        "carrier_status": modules.get("carrier_status"),
        "traits": modules.get("nutrition_traits"),
        "narrative": json.dumps(narrative) if isinstance(narrative, dict) else narrative,
    }).execute()

    sb.table("sessions").update({"status": "complete"}).eq("id", session_id).execute()


def _save_scan_supabase(session_id: str, user_id: str, scan_type: str,
                        result: dict, img_bytes: bytes):
    sb = get_supabase()
    if not sb:
        return

    image_path = f"{user_id}/{session_id}/{scan_type}_{uuid.uuid4().hex[:8]}.jpg"
    try:
        sb.storage.from_("scan-images").upload(
            path=image_path, file=img_bytes,
            file_options={"content-type": "image/jpeg"},
        )
    except Exception:
        pass

    row = {
        "session_id": session_id,
        "user_id": user_id,
        "scan_type": scan_type,
        "image_path": image_path,
        "disclaimer": result.get("disclaimer", ""),
    }
    if scan_type == "skin":
        row.update({
            "urgency": result.get("urgency"),
            "fused_score": result.get("fused_risk_pct"),
            "p_melanoma_raw": result.get("melanoma_probability"),
            "mc1r_multiplier": result.get("genetic_multiplier"),
            "all_class_probs": {c["class"]: c["probability"] for c in result.get("classifications", [])},
        })
    elif scan_type == "selfie":
        row.update({
            "detected": result.get("observed"),
            "concordance": result.get("match_result"),
        })

    sb.table("scan_results").insert(row).execute()


# -- Lifespan --

@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_sessions_disk()
    sb = get_supabase()
    print(f"Restored {len(sessions)} local session(s) | Supabase: {'connected' if sb else 'not configured'}")
    yield


app = FastAPI(title="G-Nome API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    sb = get_supabase()
    return {"status": "ok", "sessions": len(sessions), "supabase": sb is not None}


@app.post("/api/parse")
async def parse(file: UploadFile = File(...), authorization: str | None = Header(None)):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    raw = await file.read()
    try:
        result = parse_dna_file(raw, file.filename)
    except Exception as e:
        raise HTTPException(422, f"Could not parse DNA file: {e}")

    user_id = await _get_user_id(authorization)
    session_id = uuid.uuid4().hex[:12]
    session = {
        "snps": result["snps"],
        "ancestry": result.get("ancestry", {}),
        "sex": result.get("sex", "Unknown"),
        "source": result["source"],
        "user_id": user_id,
    }
    sessions[session_id] = session
    _save_session_disk(session_id, session)

    if user_id:
        _save_session_supabase(
            session_id, user_id, file.filename,
            result["source"], len(result["snps"]),
            result.get("ancestry", {}), raw,
        )

    return {
        "session_id": session_id,
        "source": result["source"],
        "snp_count": len(result["snps"]),
        "chromosomes": result["snps"]["chrom"].nunique(),
        "ancestry": result.get("ancestry", {}),
    }


@app.post("/api/report")
async def report(session_id: str, authorization: str | None = Header(None)):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    user_id = await _get_user_id(authorization) or session.get("user_id")
    snps = session["snps"]
    ancestry = session.get("ancestry", {})
    sex = session.get("sex", "Unknown")

    if user_id:
        sb = get_supabase()
        if sb:
            sb.table("sessions").update({"status": "processing"}).eq("id", session_id).execute()

    pgx = run_pharmacogenomics(snps)
    risk = compute_risk_scores(snps, ancestry, sex)
    carriers = check_carrier_status(snps)
    nutrition = analyze_traits(snps, ancestry)

    modules = {
        "pharmacogenomics": pgx,
        "disease_risk": risk,
        "carrier_status": carriers,
        "nutrition_traits": nutrition,
    }

    llm_report = await generate_report(modules, ancestry)
    full_report = {**modules, "report_text": llm_report}
    session["results"] = full_report

    if user_id:
        _save_report_supabase(session_id, user_id, modules, llm_report)

    return full_report


@app.post("/api/cv/selfie")
async def cv_selfie(session_id: str, image: UploadFile = File(...),
                    authorization: str | None = Header(None)):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    from cv_selfie import analyze_selfie

    img_bytes = await image.read()
    result = analyze_selfie(img_bytes, session["snps"], session.get("ancestry", {}))

    user_id = await _get_user_id(authorization) or session.get("user_id")
    if user_id:
        _save_scan_supabase(session_id, user_id, "selfie", result, img_bytes)

    return result


@app.post("/api/cv/skin")
async def cv_skin(session_id: str, image: UploadFile = File(...),
                  authorization: str | None = Header(None)):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(404, "Session not found")

    from cv_skin import analyze_skin_lesion

    img_bytes = await image.read()
    result = analyze_skin_lesion(img_bytes, session["snps"])

    user_id = await _get_user_id(authorization) or session.get("user_id")
    if user_id:
        _save_scan_supabase(session_id, user_id, "skin", result, img_bytes)

    return result


@app.get("/api/sessions")
async def list_sessions(authorization: str = Header(...)):
    """Return all sessions for the authenticated user."""
    user_id = await _get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Supabase not configured")
    result = sb.table("sessions") \
        .select("id, created_at, dna_source, snp_count, ancestry_group, status") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .execute()
    return result.data


@app.get("/api/sessions/{session_id}/report")
async def get_saved_report(session_id: str, authorization: str = Header(...)):
    """Fetch a previously generated report from Supabase."""
    user_id = await _get_user_id(authorization)
    if not user_id:
        raise HTTPException(401, "Not authenticated")
    sb = get_supabase()
    if not sb:
        raise HTTPException(503, "Supabase not configured")
    result = sb.table("reports") \
        .select("*") \
        .eq("session_id", session_id) \
        .eq("user_id", user_id) \
        .single() \
        .execute()
    if not result.data:
        raise HTTPException(404, "Report not found")
    return result.data


@app.get("/api/pdf/{session_id}")
async def get_pdf(session_id: str):
    session = sessions.get(session_id)
    if not session or "results" not in session:
        raise HTTPException(404, "No report found — run /api/report first")

    pdf_bytes = render_pdf(session["results"], session.get("ancestry", {}))
    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=gnome_passport_{session_id}.pdf"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
