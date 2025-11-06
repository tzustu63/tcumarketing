"""
Contact Repository
"""
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func
from datetime import datetime
from app.models.contact import Contact
from app.repositories.base import BaseRepository


class ContactRepository(BaseRepository[Contact]):
    """
    Repository for Contact model operations
    """
    
    def __init__(self, db: Session):
        super().__init__(Contact, db)
    
    def get_by_task(self, task_id: str, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Get contacts by task ID"""
        return (
            self.db.query(Contact)
            .filter(Contact.task_id == task_id)
            .order_by(desc(Contact.extracted_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_institution_type(self, institution_type: str, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Get contacts by institution type"""
        return (
            self.db.query(Contact)
            .filter(Contact.institution_type == institution_type)
            .order_by(desc(Contact.quality_score))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def check_duplicate(self, contact: Contact = None, source_url: str = None, email: Optional[str] = None, whatsapp: Optional[str] = None) -> bool:
        """
        Check if contact already exists
        
        Args:
            contact: Contact object to check (preferred)
            source_url: Source URL (fallback if contact not provided)
            email: Email address (fallback if contact not provided)
            whatsapp: WhatsApp number (fallback if contact not provided)
            
        Returns:
            True if duplicate exists, False otherwise
        """
        # Extract values from contact object if provided
        if contact:
            source_url = contact.source_url
            email = contact.email
            whatsapp = contact.whatsapp
        
        if not source_url:
            return False
        
        query = self.db.query(Contact).filter(Contact.source_url == source_url)
        
        if email and whatsapp:
            query = query.filter(
                or_(Contact.email == email, Contact.whatsapp == whatsapp)
            )
        elif email:
            query = query.filter(Contact.email == email)
        elif whatsapp:
            query = query.filter(Contact.whatsapp == whatsapp)
        
        return query.first() is not None
    
    def check_duplicate_dict(self, contact_data: Dict) -> bool:
        """
        Check if contact already exists using dictionary data
        
        Args:
            contact_data: Dictionary containing contact data
            
        Returns:
            True if duplicate exists, False otherwise
        """
        return self.check_duplicate(
            source_url=contact_data.get("source_url"),
            email=contact_data.get("email"),
            whatsapp=contact_data.get("whatsapp")
        )
    
    def search(
        self,
        institution_type: Optional[str] = None,
        city: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Contact]:
        """Search contacts with filters"""
        query = self.db.query(Contact)
        
        if institution_type:
            query = query.filter(Contact.institution_type == institution_type)
        
        if start_date:
            query = query.filter(Contact.extracted_at >= start_date)
        
        if end_date:
            query = query.filter(Contact.extracted_at <= end_date)
        
        return (
            query
            .order_by(desc(Contact.quality_score), desc(Contact.extracted_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_high_quality_contacts(self, min_score: float = 70.0, limit: int = 100) -> List[Contact]:
        """Get high quality contacts"""
        return (
            self.db.query(Contact)
            .filter(Contact.quality_score >= min_score)
            .order_by(desc(Contact.quality_score))
            .limit(limit)
            .all()
        )
    
    def count_by_institution_type(self) -> Dict[str, int]:
        """Count contacts by institution type"""
        results = (
            self.db.query(Contact.institution_type, func.count(Contact.id))
            .group_by(Contact.institution_type)
            .all()
        )
        return {inst_type: count for inst_type, count in results}
    
    def get_verified_contacts(self, skip: int = 0, limit: int = 100) -> List[Contact]:
        """Get verified contacts"""
        return (
            self.db.query(Contact)
            .filter(Contact.is_verified == True)
            .order_by(desc(Contact.quality_score))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def bulk_create(self, contacts: List[Dict]) -> List[Contact]:
        """Bulk create contacts"""
        db_contacts = [Contact(**contact) for contact in contacts]
        self.db.bulk_save_objects(db_contacts, return_defaults=True)
        self.db.commit()
        return db_contacts
