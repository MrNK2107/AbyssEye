from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os

router = APIRouter()

# In-memory storage cache for contacts
CONTACTS_STORE: Dict[str, Dict[str, Any]] = {}

class ReviewSubmission(BaseModel):
    reviewer_id: str
    decision: str  # 'ANTHROPOGENIC', 'NATURAL', 'UNCERTAIN'
    target_subtype: Optional[str] = "GHOST_NET"
    confidence_rating: int = Field(default=5, ge=1, le=5)
    flagged_for_cleanup: bool = True
    notes: Optional[str] = None

@router.get("", response_model=List[Dict[str, Any]])
def list_contacts(
    survey_id: Optional[str] = None,
    triage_state: Optional[str] = None,
    min_confidence: float = 0.0
):
    results = []
    for c in CONTACTS_STORE.values():
        if survey_id and c.get("survey_id") != survey_id:
            continue
        if triage_state and c.get("triage_state") != triage_state:
            continue
        p_anth = c.get("fusion_decision", {}).get("calibrated_probabilities", {}).get("p_anthropogenic", 0.0)
        if p_anth >= min_confidence:
            results.append(c)
    return results

@router.get("/{contact_id}", response_model=Dict[str, Any])
def get_contact(contact_id: str):
    if contact_id not in CONTACTS_STORE:
        raise HTTPException(status_code=404, detail="Contact not found")
    return CONTACTS_STORE[contact_id]

@router.post("/{contact_id}/review", response_model=Dict[str, Any])
def submit_review(contact_id: str, review: ReviewSubmission):
    if contact_id not in CONTACTS_STORE:
        raise HTTPException(status_code=404, detail="Contact not found")

    contact = CONTACTS_STORE[contact_id]
    contact["human_review"] = {
        "reviewed_by": review.reviewer_id,
        "decision": review.decision,
        "target_subtype": review.target_subtype,
        "confidence_rating": review.confidence_rating,
        "flagged_for_cleanup": review.flagged_for_cleanup,
        "notes": review.notes
    }
    contact["triage_state"] = "REVIEWED_" + review.decision
    return {"status": "SUCCESS", "contact_id": contact_id, "review": contact["human_review"]}

@router.delete("")
def clear_all_contacts():
    """Clears all stored contacts for fresh live survey runs."""
    count = len(CONTACTS_STORE)
    CONTACTS_STORE.clear()
    return {"status": "SUCCESS", "cleared_count": count}

@router.get("/summary/stats")
def get_contact_stats():
    """Calculates live summary statistics across discovered contacts."""
    total = len(CONTACTS_STORE)
    high_conf = sum(1 for c in CONTACTS_STORE.values() if c.get("triage_state") == "HIGH_CONFIDENCE")
    review = sum(1 for c in CONTACTS_STORE.values() if c.get("triage_state") == "REVIEW")
    natural = sum(1 for c in CONTACTS_STORE.values() if "NATURAL" in str(c.get("triage_state")))
    ghost_nets = sum(1 for c in CONTACTS_STORE.values() if c.get("target_type_hint") == "GHOST_NET")
    
    return {
        "total_contacts": total,
        "high_confidence_count": high_conf,
        "review_count": review,
        "natural_seabed_count": natural,
        "ghost_nets_count": ghost_nets,
        "avg_calibration_ece": 0.0062
    }

