from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from bson.objectid import ObjectId
import shutil
import os
import uuid
import json
from db import cases, case_status_history

case_router = APIRouter()


# === Pydantic Models ===
class Perpetrator(BaseModel):
    name: str
    type: str


class Evidence(BaseModel):
    type: str
    url: str
    description: Optional[str]
    date_captured: Optional[datetime]


class CaseLocation(BaseModel):
    country: str
    region: Optional[str]
    coordinates: dict


class CaseModel(BaseModel):
    case_id: str
    title: str
    description: str
    violation_types: List[str]
    status: str
    priority: Optional[str]
    location: CaseLocation
    date_occurred: datetime
    date_reported: datetime
    victims: Optional[List[str]] = []
    perpetrators: Optional[List[Perpetrator]] = []
    evidence: Optional[List[Evidence]] = []
    created_by: Optional[str]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    incident_report_id: Optional[str] = None


# === Helper: Save uploaded file ===
def save_file(file: UploadFile) -> str:
    os.makedirs("media/case_evidence", exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    path = os.path.join("media/case_evidence", unique_filename)
    with open(path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return f"/{path}"


# === POST /cases/ ===
@case_router.post("/", response_model=dict)
async def create_case(
    case: str = Form(...), evidence_files: List[UploadFile] = File(default=[])
):
    try:
        case_data = json.loads(case)
        case_obj = CaseModel(**case_data)

        # Save uploaded files and construct Evidence list
        saved_evidence = []
        for file in evidence_files:
            url = save_file(file)
            saved_evidence.append(
                Evidence(
                    type=file.content_type.split("/")[0],
                    url=url,
                    description=file.filename,
                    date_captured=datetime.now(timezone.utc),
                )
            )

        case_dict = case_obj.dict()
        case_dict["evidence"] = [e.dict() for e in saved_evidence]
        case_dict["created_at"] = datetime.now(timezone.utc)
        case_dict["updated_at"] = datetime.now(timezone.utc)

        cases.insert_one(case_dict)
        case_status_history.insert_one(
            {
                "case_id": case_obj.case_id,
                "status": case_obj.status,
                "timestamp": datetime.now(timezone.utc),
                "changed_by": case_obj.created_by or "unknown",
            }
        )

        return {"message": "Case created successfully", "case_id": case_obj.case_id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing case: {str(e)}")


# === GET /cases/ ===
@case_router.get("/", response_model=List[CaseModel])
def list_cases(
    status: Optional[str] = None,
    country: Optional[str] = None,
    violation: Optional[str] = None,
):
    query = {}
    if status:
        query["status"] = status
    if country:
        query["location.country"] = country
    if violation:
        query["violation_types"] = {"$in": [violation]}

    results = list(cases.find(query))
    for r in results:
        r["_id"] = str(r["_id"])  # Convert ObjectId to string
    return results


# === GET /cases/{case_id} ===
@case_router.get("/{case_id}", response_model=CaseModel)
def get_case(case_id: str):
    result = cases.find_one({"case_id": case_id})
    if not result:
        raise HTTPException(status_code=404, detail="Case not found")
    result["_id"] = str(result["_id"])  # Convert ObjectId to string
    return result


# === PATCH /cases/{case_id} ===
@case_router.patch("/{case_id}", response_model=dict)
def update_case_status(case_id: str, status: str):
    result = cases.update_one(
        {"case_id": case_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Case not found")

    case_status_history.insert_one(
        {
            "case_id": case_id,
            "status": status,
            "timestamp": datetime.now(timezone.utc),
            "changed_by": "admin",
        }
    )

    return {"message": "Case status updated"}


# === DELETE /cases/{case_id} ===
@case_router.delete("/{case_id}", response_model=dict)
def archive_case(case_id: str):
    result = cases.delete_one({"case_id": case_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Case not found")
    return {"message": "Case archived successfully"}
