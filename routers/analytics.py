from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import List, Optional
from db import cases, incident_reports
import pandas as pd

analytics_router = APIRouter()


# === Models ===
class ViolationCount(BaseModel):
    violation_type: str
    count: int


class TimelineData(BaseModel):
    date: str
    count: int


class GeoMarker(BaseModel):
    lat: float
    lon: float
    violations: List[str]
    description: str


# === GET /analytics/violations ===
@analytics_router.get("/violations", response_model=List[ViolationCount])
def get_violation_counts(source: str = "reports", days: Optional[int] = None):
    """Get counts of violations by type from either cases or reports"""
    collection = incident_reports if source == "reports" else cases
    date_filter = {}

    if days:
        start_date = datetime.utcnow() - timedelta(days=days)
        date_field = "incident_details.date" if source == "reports" else "date_occurred"
        date_filter[date_field] = {"$gte": start_date}

    pipeline = [
        {"$match": date_filter},
        {
            "$unwind": (
                "$violation_types"
                if source == "cases"
                else "$incident_details.violation_types"
            )
        },
        {
            "$group": {
                "_id": (
                    "$violation_types"
                    if source == "cases"
                    else "$incident_details.violation_types"
                ),
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"count": -1}},
        {"$project": {"violation_type": "$_id", "count": 1, "_id": 0}},
    ]

    try:
        results = list(collection.aggregate(pipeline))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === GET /analytics/timeline ===
@analytics_router.get("/timeline", response_model=List[TimelineData])
def get_timeline_data(source: str = "reports", time_period: str = "month"):
    """Get timeline data grouped by day/week/month/year"""
    collection = incident_reports if source == "reports" else cases
    date_field = "incident_details.date" if source == "reports" else "date_occurred"

    format_map = {"day": "%Y-%m-%d", "week": "%Y-%U", "month": "%Y-%m", "year": "%Y"}
    date_format = format_map.get(time_period, "%Y-%m")

    pipeline = [
        {"$match": {date_field: {"$exists": True, "$type": "date"}}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": date_format, "date": f"${date_field}"}
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    try:
        results = list(collection.aggregate(pipeline))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# === GET /analytics/geodata ===
@analytics_router.get("/geodata", response_model=List[GeoMarker])
def get_geodata(source: str = "reports"):
    """Get geographic data for mapping"""
    collection = incident_reports if source == "reports" else cases
    location_field = "incident_details.location" if source == "reports" else "location"

    query = {f"{location_field}.coordinates": {"$ne": None}}

    markers = []
    for doc in collection.find(query):
        if source == "reports":
            coords = doc["incident_details"]["location"]["coordinates"]["coordinates"]
            violations = doc["incident_details"]["violation_types"]
            description = doc["incident_details"]["description"]
        else:
            coords = doc["location"]["coordinates"]["coordinates"]
            violations = doc["violation_types"]
            description = doc["title"]

        markers.append(
            {
                "lat": coords[1],
                "lon": coords[0],
                "violations": violations,
                "description": (
                    description[:100] + "..." if len(description) > 100 else description
                ),
            }
        )

    return markers


# === GET /analytics/summary ===
@analytics_router.get("/summary")
def get_system_summary():
    """Get summary statistics for dashboard"""
    # Case statistics
    case_stats = {
        "total": cases.count_documents({}),
        "by_status": list(
            cases.aggregate(
                [
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                ]
            )
        ),
        "by_priority": list(
            cases.aggregate(
                [
                    {"$group": {"_id": "$priority", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                ]
            )
        ),
    }

    # Report statistics
    report_stats = {
        "total": incident_reports.count_documents({}),
        "by_status": list(
            incident_reports.aggregate(
                [
                    {"$group": {"_id": "$status", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                ]
            )
        ),
        "by_reporter": list(
            incident_reports.aggregate(
                [
                    {"$group": {"_id": "$reporter_type", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                ]
            )
        ),
    }

    return {"cases": case_stats, "reports": report_stats}
