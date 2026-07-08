from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import datetime

from db.session import get_db
import db.models as models
import schemas

router = APIRouter(prefix="/followups", tags=["Followups"])

@router.get("", response_model=List[schemas.FollowUpResponse])
def get_followups(
    due_before: Optional[datetime.date] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(models.Interaction).filter(models.Interaction.follow_up_required == True)
    
    if due_before:
        query = query.filter(models.Interaction.follow_up_date <= due_before)
        
    interactions = query.order_by(models.Interaction.follow_up_date.asc()).all()
    
    results = []
    for inter in interactions:
        hcp = inter.hcp
        results.append(schemas.FollowUpResponse(
            id=inter.id,  # maps to follow-up ID or interaction ID
            hcp_name=hcp.name if hcp else "Unknown Doctor",
            specialty=hcp.specialty if hcp else None,
            interaction_id=inter.id,
            follow_up_date=inter.follow_up_date,
            topics=inter.topics_discussed or [],
            products=inter.products_discussed or []
        ))
        
    return results
