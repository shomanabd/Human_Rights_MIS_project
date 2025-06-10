from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import os
import json
import shutil
import uuid
from bson.objectid import ObjectId
from db import incident_reports, report_evidence, cases

report_router = APIRouter()
MEDIA_DIR = "media"


# === Models ===
class ReportEvidence(BaseModel):
    type: str
    url: str
    description: Optional[str] = None


class IncidentLocation(BaseModel):
    country: str
    city: Optional[str]
    coordinates: Optional[dict]


class IncidentDetails(BaseModel):
    date: datetime
    location: IncidentLocation
    description: str
    violation_types: List[str]


class ContactInfo(BaseModel):
    email: Optional[str]
    phone: Optional[str]
    preferred_contact: Optional[str]


class ReportModel(BaseModel):
    report_id: str
    reporter_type: str
    anonymous: bool
    contact_info: Optional[ContactInfo]
    incident_details: IncidentDetails
    evidence: Optional[List[ReportEvidence]] = []
    status: str = "new"
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# === File saving helper ===
def save_file(file: UploadFile) -> str:
    os.makedirs(MEDIA_DIR, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join(MEDIA_DIR, unique_filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return f"/{MEDIA_DIR}/{unique_filename}"


# === POST /reports/ ===
@report_router.post("/")
async def create_report(
    report_id: str = Form(...),
    reporter_type: str = Form(...),
    anonymous: str = Form(...),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    preferred_contact: Optional[str] = Form(None),
    date: str = Form(...),
    country: str = Form(...),
    city: Optional[str] = Form(None),
    lat: float = Form(...),
    lon: float = Form(...),
    description: str = Form(...),
    violation_types_str: str = Form(...),
    evidence_files: List[UploadFile] = File(default=[]),
):
    # Validate coordinates
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=400,
            detail="Latitude must be between -90 and 90, Longitude between -180 and 180",
        )

    is_anonymous = anonymous.lower() == "true"

    contact_info = (
        {"email": email, "phone": phone, "preferred_contact": preferred_contact}
        if not is_anonymous
        else None
    )

    coordinates = {"type": "Point", "coordinates": [lon, lat]}

    violation_types = [v.strip() for v in violation_types_str.split(",") if v.strip()]

    # Handle evidence files
    saved_evidence = []
    for file in evidence_files:
        url = save_file(file)
        saved_evidence.append(
            {
                "type": file.content_type.split("/")[0],
                "url": url,
                "description": file.filename,
            }
        )
        report_evidence.insert_one(
            {
                "report_id": report_id,
                "type": file.content_type.split("/")[0],
                "url": url,
                "description": file.filename,
                "date_uploaded": datetime.utcnow(),
            }
        )

    report = {
        "report_id": report_id,
        "reporter_type": reporter_type,
        "anonymous": is_anonymous,
        "contact_info": contact_info,
        "incident_details": {
            "date": datetime.fromisoformat(date),
            "location": {"country": country, "city": city, "coordinates": coordinates},
            "description": description,
            "violation_types": violation_types,
        },
        "evidence": saved_evidence,
        "status": "new",
        "created_at": datetime.utcnow(),
    }

    incident_reports.insert_one(report)
    return {"message": "Report submitted", "report_id": report_id}


# === GET /reports/ ===
@report_router.get("/")
def list_reports(
    status: Optional[str] = None,
    country: Optional[str] = None,
    violation: Optional[str] = None,
    date: Optional[str] = None,
):
    query = {}
    if status:
        query["status"] = status
    if country:
        query["incident_details.location.country"] = country
    if violation:
        query["incident_details.violation_types"] = {"$in": [violation]}
    if date:
        query["incident_details.date"] = datetime.fromisoformat(date)

    results = list(incident_reports.find(query))
    for r in results:
        r["_id"] = str(r["_id"])
    return results


# === PATCH /reports/{report_id} ===
@report_router.patch("/{report_id}")
def update_report_status(report_id: str, status: str):
    result = incident_reports.update_one(
        {"_id": ObjectId(report_id)}, {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Status updated"}


# === DELETE /reports/{report_id} ===
@report_router.delete("/{report_id}")
def delete_report(report_id: str):
    cases.update_many(
        {"incident_report_id": report_id}, {"$set": {"incident_report_id": None}}
    )
    result = incident_reports.delete_one({"report_id": report_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"message": "Report deleted and unlinked from cases"}


# === GET /reports/analytics ===
@report_router.get("/analytics")
def report_analytics():
    pipeline = [
        {"$unwind": "$incident_details.violation_types"},
        {"$group": {"_id": "$incident_details.violation_types", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    stats = list(incident_reports.aggregate(pipeline))
    return [{"violation_type": s["_id"], "count": s["count"]} for s in stats]


# === GET /reports/analytics/timeline ===
@report_router.get("/analytics/timeline")
def report_timeline():
    pipeline = [
        {
            "$group": {
                "_id": {
                    "$dateToString": {
                        "format": "%Y-%m-%d",
                        "date": "$incident_details.date",
                    }
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    data = list(incident_reports.aggregate(pipeline))
    return [{"date": d["_id"], "count": d["count"]} for d in data]


# === GET /reports/analytics/geodata ===
@report_router.get("/analytics/geodata")
def report_geodata():
    results = incident_reports.find(
        {"incident_details.location.coordinates": {"$ne": None}}
    )
    markers = []
    for r in results:
        coords = r["incident_details"]["location"]["coordinates"]["coordinates"]
        markers.append(
            {
                "lat": coords[1],
                "lon": coords[0],
                "violations": r["incident_details"]["violation_types"],
                "description": r["incident_details"]["description"],
            }
        )
    return markers
