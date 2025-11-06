"""
Contact Information API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.api.dependencies import get_db
from app.api.schemas import (
    ContactResponse,
    ContactListResponse
)
from app.repositories.contact_repository import ContactRepository
from app.models.contact import Contact

router = APIRouter(prefix="/api/contacts", tags=["Contacts"])


@router.get("", response_model=ContactListResponse)
async def get_contacts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    country: Optional[str] = Query(None, description="Filter by country code"),
    keyword: Optional[str] = Query(None, description="Filter by search keyword"),
    city: Optional[str] = Query(None, description="Filter by city"),
    institution_type: Optional[str] = Query(None, description="Filter by institution type"),
    source_platform: Optional[str] = Query(None, description="Filter by source platform"),
    min_quality_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum quality score"),
    has_email: Optional[bool] = Query(None, description="Filter by email presence"),
    has_whatsapp: Optional[bool] = Query(None, description="Filter by WhatsApp presence"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    date_from: Optional[datetime] = Query(None, description="Filter by extraction date (from)"),
    date_to: Optional[datetime] = Query(None, description="Filter by extraction date (to)"),
    search: Optional[str] = Query(None, description="Search in institution name"),
    db: Session = Depends(get_db)
):
    """
    查詢聯絡資訊
    
    Query contact information with filtering and pagination support.
    """
    contact_repo = ContactRepository(db)
    
    # Build query filters
    from app.models.task import Task
    from sqlalchemy.orm import joinedload
    
    # Use joinedload to avoid N+1 queries when accessing Task relationship
    # Always join with Task table to get city information efficiently
    query = db.query(Contact).join(Task, Contact.task_id == Task.id)
    
    # Filter by city if provided
    if city:
        query = query.filter(Task.city == city)
    
    if country:
        query = query.filter(Contact.country == country)
    
    if keyword:
        query = query.filter(Contact.keyword == keyword)
    
    if institution_type:
        query = query.filter(Contact.institution_type == institution_type)
    
    if source_platform:
        query = query.filter(Contact.source_platform == source_platform)
    
    if min_quality_score is not None:
        query = query.filter(Contact.quality_score >= min_quality_score)
    
    if has_email is not None:
        if has_email:
            query = query.filter(Contact.email.isnot(None))
        else:
            query = query.filter(Contact.email.is_(None))
    
    if has_whatsapp is not None:
        if has_whatsapp:
            query = query.filter(Contact.whatsapp.isnot(None))
        else:
            query = query.filter(Contact.whatsapp.is_(None))
    
    if is_verified is not None:
        query = query.filter(Contact.is_verified == is_verified)
    
    if date_from:
        query = query.filter(Contact.extracted_at >= date_from)
    
    if date_to:
        query = query.filter(Contact.extracted_at <= date_to)
    
    if search:
        query = query.filter(Contact.institution_name.ilike(f"%{search}%"))
    
    # Get total count (use distinct count for accuracy)
    total = query.with_entities(func.count(func.distinct(Contact.id))).scalar()
    
    # Apply pagination and ordering with eager loading
    # Use joinedload to eagerly load Task relationship to avoid N+1 queries
    results = (
        query
        .options(joinedload(Contact.task))
        .order_by(Contact.extracted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    # Convert results to ContactResponse with city (efficiently accessed from loaded relationship)
    contacts = [
        ContactResponse(
            id=contact.id,
            task_id=contact.task_id,
            country=contact.country,
            city=contact.task.city if contact.task else None,
            keyword=contact.keyword,
            institution_name=contact.institution_name,
            institution_type=contact.institution_type,
            source_url=contact.source_url,
            source_platform=contact.source_platform,
            email=contact.email,
            whatsapp=contact.whatsapp,
            additional_info=contact.additional_info,
            quality_score=contact.quality_score,
            is_verified=contact.is_verified,
            extracted_at=contact.extracted_at,
        )
        for contact in results
    ]
    
    return ContactListResponse(
        total=total,
        skip=skip,
        limit=limit,
        contacts=contacts
    )


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(
    contact_id: UUID,
    db: Session = Depends(get_db)
):
    """
    獲取單筆資料
    
    Get detailed information about a specific contact.
    """
    from sqlalchemy.orm import joinedload
    contact_repo = ContactRepository(db)
    
    # Use eager loading to avoid N+1 query
    contact = (
        db.query(Contact)
        .options(joinedload(Contact.task))
        .filter(Contact.id == contact_id)
        .first()
    )
    
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    
    # Create response with city (efficiently accessed from loaded relationship)
    return ContactResponse(
        id=contact.id,
        task_id=contact.task_id,
        country=contact.country,
        city=contact.task.city if contact.task else None,
        keyword=contact.keyword,
        institution_name=contact.institution_name,
        institution_type=contact.institution_type,
        source_url=contact.source_url,
        source_platform=contact.source_platform,
        email=contact.email,
        whatsapp=contact.whatsapp,
        additional_info=contact.additional_info,
        quality_score=contact.quality_score,
        is_verified=contact.is_verified,
        extracted_at=contact.extracted_at,
    )


@router.get("/task/{task_id}", response_model=ContactListResponse)
async def get_contacts_by_task(
    task_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    獲取特定任務的聯絡資訊
    
    Get all contacts extracted by a specific task.
    """
    from sqlalchemy.orm import joinedload
    from app.models.task import Task
    
    # Get task once to retrieve city
    task = db.query(Task).filter(Task.id == task_id).first()
    city = task.city if task else None
    
    # Get contacts with eager loading to avoid N+1 queries
    contacts_raw = (
        db.query(Contact)
        .options(joinedload(Contact.task))
        .filter(Contact.task_id == task_id)
        .order_by(Contact.extracted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    total = db.query(Contact).filter(Contact.task_id == task_id).count()
    
    # Convert contacts to include city (from pre-loaded task)
    contacts = [
        ContactResponse(
            id=contact.id,
            task_id=contact.task_id,
            country=contact.country,
            city=city,
            keyword=contact.keyword,
            institution_name=contact.institution_name,
            institution_type=contact.institution_type,
            source_url=contact.source_url,
            source_platform=contact.source_platform,
            email=contact.email,
            whatsapp=contact.whatsapp,
            additional_info=contact.additional_info,
            quality_score=contact.quality_score,
            is_verified=contact.is_verified,
            extracted_at=contact.extracted_at,
        )
        for contact in contacts_raw
    ]
    
    return ContactListResponse(
        total=total,
        skip=skip,
        limit=limit,
        contacts=contacts
    )


@router.get("/stats/summary", response_model=dict)
async def get_contact_summary(
    db: Session = Depends(get_db)
):
    """
    獲取聯絡資訊統計摘要
    
    Get summary statistics about contacts.
    """
    contact_repo = ContactRepository(db)
    
    total = contact_repo.count()
    with_email = db.query(Contact).filter(Contact.email.isnot(None)).count()
    with_whatsapp = db.query(Contact).filter(Contact.whatsapp.isnot(None)).count()
    with_both = db.query(Contact).filter(
        and_(Contact.email.isnot(None), Contact.whatsapp.isnot(None))
    ).count()
    
    # Get average quality score
    avg_score = db.query(func.avg(Contact.quality_score)).scalar()
    
    # Get counts by institution type
    by_type = db.query(
        Contact.institution_type,
        func.count(Contact.id)
    ).group_by(Contact.institution_type).all()
    
    # Get counts by platform
    by_platform = db.query(
        Contact.source_platform,
        func.count(Contact.id)
    ).group_by(Contact.source_platform).all()
    
    return {
        "total_contacts": total,
        "contacts_with_email": with_email,
        "contacts_with_whatsapp": with_whatsapp,
        "contacts_with_both": with_both,
        "average_quality_score": float(avg_score) if avg_score else None,
        "by_institution_type": {inst_type or "unknown": count for inst_type, count in by_type},
        "by_platform": {platform: count for platform, count in by_platform}
    }
