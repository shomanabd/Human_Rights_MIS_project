from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
from models.victim import VictimCreate, VictimUpdate, VictimResponse, RiskLevel
from models.user import User, UserRole
from db import individuals_collection, victim_risk_assessments  # Updated import
from security.auth import get_current_user, require_roles
from security.encryption import encrypt_sensitive_data, decrypt_sensitive_data

router = APIRouter(prefix="/victims", tags=["victims"])

# Helper function to convert ObjectId to string
def victim_helper(victim) -> dict:
    victim["_id"] = str(victim["_id"])
    return victim

@router.post("/", response_model=dict)
async def create_victim(
    victim: VictimCreate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.CASE_MANAGER]))
):
    """Create a new victim/witness record"""
    victim_dict = victim.dict()

    # Encrypt sensitive contact information
    if victim_dict.get("contact_info"):
        contact_info = victim_dict["contact_info"]
        if contact_info.get("email"):
            contact_info["email"] = encrypt_sensitive_data(contact_info["email"])
        if contact_info.get("phone"):
            contact_info["phone"] = encrypt_sensitive_data(contact_info["phone"])

    # Add metadata
    victim_dict["created_at"] = datetime.utcnow()
    victim_dict["updated_at"] = datetime.utcnow()
    victim_dict["created_by"] = current_user.username
    victim_dict["cases_involved"] = []

    result = individuals_collection.insert_one(victim_dict)  # Updated collection name

    # Log risk assessment
    risk_log = {
        "victim_id": result.inserted_id,
        "risk_level": victim.risk_assessment.level,
        "assessed_by": current_user.username,
        "assessed_at": datetime.utcnow(),
        "notes": victim.risk_assessment.notes
    }
    victim_risk_assessments.insert_one(risk_log)

    return {"message": "Victim/witness created successfully", "id": str(result.inserted_id)}

@router.get("/{victim_id}", response_model=VictimResponse)
async def get_victim(
    victim_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.CASE_MANAGER, UserRole.ANALYST]))
):
    """Retrieve a specific victim/witness (restricted access)"""
    if not ObjectId.is_valid(victim_id):
        raise HTTPException(status_code=400, detail="Invalid victim ID format")

    victim = individuals_collection.find_one({"_id": ObjectId(victim_id)})  # Updated collection name
    if not victim:
        raise HTTPException(status_code=404, detail="Victim/witness not found")

    # Decrypt sensitive data for authorized users
    if victim.get("contact_info") and UserRole.ADMIN in current_user.roles:
        contact_info = victim["contact_info"]
        if contact_info.get("email"):
            contact_info["email"] = decrypt_sensitive_data(contact_info["email"])
        if contact_info.get("phone"):
            contact_info["phone"] = decrypt_sensitive_data(contact_info["phone"])
    elif victim.get("contact_info") and UserRole.ADMIN not in current_user.roles:
        # Hide sensitive contact info for non-admin users
        victim["contact_info"] = {"preferred_contact": victim["contact_info"].get("preferred_contact")}

    return victim_helper(victim)

@router.get("/", response_model=List[dict])
async def list_victims(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    risk_level: Optional[RiskLevel] = None,
    victim_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List victims/witnesses with filters"""
    query = {}

    if risk_level:
        query["risk_assessment.level"] = risk_level
    if victim_type:
        query["type"] = victim_type

    victims = list(individuals_collection.find(query).skip(skip).limit(limit))  # Updated collection name

    # Filter sensitive data based on user role
    filtered_victims = []
    for victim in victims:
        victim_data = victim_helper(victim)

        # Hide sensitive information for non-admin users
        if UserRole.ADMIN not in current_user.roles:
            if victim_data.get("contact_info"):
                victim_data["contact_info"] = {
                    "preferred_contact": victim_data["contact_info"].get("preferred_contact")
                }
            # Show only pseudonym if anonymous
            if victim_data.get("anonymous"):
                victim_data["demographics"] = None

        filtered_victims.append(victim_data)

    return filtered_victims

@router.patch("/{victim_id}", response_model=dict)
async def update_victim_risk(
    victim_id: str,
    victim_update: VictimUpdate,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.CASE_MANAGER]))
):
    """Update victim/witness risk level and other information"""
    if not ObjectId.is_valid(victim_id):
        raise HTTPException(status_code=400, detail="Invalid victim ID format")

    # Check if victim exists
    existing_victim = individuals_collection.find_one({"_id": ObjectId(victim_id)})  # Updated collection name
    if not existing_victim:
        raise HTTPException(status_code=404, detail="Victim/witness not found")

    # Prepare update data
    update_data = {k: v for k, v in victim_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()

    # Encrypt sensitive contact information if being updated
    if "contact_info" in update_data and update_data["contact_info"]:
        contact_info = update_data["contact_info"]
        if contact_info.get("email"):
            contact_info["email"] = encrypt_sensitive_data(contact_info["email"])
        if contact_info.get("phone"):
            contact_info["phone"] = encrypt_sensitive_data(contact_info["phone"])

    result = individuals_collection.update_one(  # Updated collection name
        {"_id": ObjectId(victim_id)},
        {"$set": update_data}
    )

    # Log risk assessment change if updated
    if "risk_assessment" in update_data:
        risk_log = {
            "victim_id": ObjectId(victim_id),
            "risk_level": update_data["risk_assessment"]["level"],
            "assessed_by": current_user.username,
            "assessed_at": datetime.utcnow(),
            "notes": update_data["risk_assessment"].get("notes"),
            "previous_level": existing_victim["risk_assessment"]["level"]
        }
        victim_risk_assessments.insert_one(risk_log)

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Victim/witness not found")

    return {"message": "Victim/witness updated successfully"}

@router.get("/case/{case_id}", response_model=List[dict])
async def get_victims_by_case(
    case_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.CASE_MANAGER, UserRole.ANALYST]))
):
    """List victims/witnesses linked to a specific case"""
    if not ObjectId.is_valid(case_id):
        raise HTTPException(status_code=400, detail="Invalid case ID format")

    victims = list(individuals_collection.find({"cases_involved": ObjectId(case_id)}))  # Updated collection name

    # Filter sensitive data based on user role
    filtered_victims = []
    for victim in victims:
        victim_data = victim_helper(victim)

        if UserRole.ADMIN not in current_user.roles:
            if victim_data.get("contact_info"):
                victim_data["contact_info"] = {
                    "preferred_contact": victim_data["contact_info"].get("preferred_contact")
                }
            if victim_data.get("anonymous"):
                victim_data["demographics"] = None

        filtered_victims.append(victim_data)

    return filtered_victims

@router.get("/{victim_id}/risk-history", response_model=List[dict])
async def get_victim_risk_history(
    victim_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.CASE_MANAGER]))
):
    """Get risk assessment history for a victim/witness"""
    if not ObjectId.is_valid(victim_id):
        raise HTTPException(status_code=400, detail="Invalid victim ID format")

    risk_history = list(victim_risk_assessments.find(
        {"victim_id": ObjectId(victim_id)}
    ).sort("assessed_at", -1))

    # Convert ObjectId to string
    for entry in risk_history:
        entry["_id"] = str(entry["_id"])
        entry["victim_id"] = str(entry["victim_id"])

    return risk_history

@router.delete("/{victim_id}")
async def delete_victim(
    victim_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN]))
):
    """Delete a victim/witness record (Admin only)"""
    if not ObjectId.is_valid(victim_id):
        raise HTTPException(status_code=400, detail="Invalid victim ID format")

    result = individuals_collection.delete_one({"_id": ObjectId(victim_id)})  # Updated collection name
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Victim/witness not found")

    # Also delete risk assessment history
    victim_risk_assessments.delete_many({"victim_id": ObjectId(victim_id)})

    return {"message": "Victim/witness deleted successfully"}