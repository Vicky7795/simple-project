from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from db.session import get_db
import db.models as models
import schemas

router = APIRouter(prefix="/hcps", tags=["HCPs"])

@router.get("", response_model=List[schemas.HCPResponse])
def get_hcps(
    search: Optional[str] = Query(None, description="Fuzzy search by name or specialty"),
    db: Session = Depends(get_db)
):
    query = db.query(models.HCP)
    if search:
        query = query.filter(
            (models.HCP.name.like(f"%{search}%")) |
            (models.HCP.specialty.like(f"%{search}%")) |
            (models.HCP.hospital_affiliation.like(f"%{search}%"))
        )
    return query.all()

@router.post("", response_model=schemas.HCPResponse, status_code=201)
def create_hcp(hcp_data: schemas.HCPCreate, db: Session = Depends(get_db)):
    # Check if duplicate email exists
    if hcp_data.email:
        existing = db.query(models.HCP).filter(models.HCP.email == hcp_data.email).first()
        if existing:
            raise HTTPException(status_code=400, detail="HCP with this email already exists.")
            
    db_hcp = models.HCP(**hcp_data.model_dump())
    db.add(db_hcp)
    db.commit()
    db.refresh(db_hcp)
    return db_hcp

@router.get("/{hcp_id}", response_model=schemas.HCPResponse)
def get_hcp(hcp_id: int, db: Session = Depends(get_db)):
    hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
    if not hcp:
        raise HTTPException(status_code=404, detail=f"HCP with ID {hcp_id} not found.")
    return hcp
