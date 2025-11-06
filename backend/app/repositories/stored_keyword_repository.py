"""
Stored Keyword Repository
"""
from typing import List, Optional, Literal
from sqlalchemy.orm import Session
from sqlalchemy import and_, update

from app.repositories.base import BaseRepository
from app.models.stored_keyword import StoredKeyword


class StoredKeywordRepository(BaseRepository[StoredKeyword]):
    """Repository for stored keywords and cities"""
    
    def __init__(self, db: Session):
        super().__init__(StoredKeyword, db)
    
    def _get_by_country(self, country: str, field: Literal["keyword", "city"]) -> List[str]:
        """Internal method to get keywords or cities by country"""
        field_column = getattr(StoredKeyword, field)
        items = (
            self.db.query(field_column)
            .filter(
                and_(
                    StoredKeyword.country == country,
                    StoredKeyword.is_deleted == False,
                    field_column.isnot(None),
                    field_column != ''
                )
            )
            .distinct()
            .order_by(field_column)
            .all()
        )
        return [item[0] for item in items if item[0]]
    
    def get_keywords_by_country(self, country: str) -> List[str]:
        """Get all keywords for a specific country (not deleted)"""
        return self._get_by_country(country, "keyword")
    
    def get_cities_by_country(self, country: str) -> List[str]:
        """Get all cities for a specific country (not deleted)"""
        return self._get_by_country(country, "city")
    
    def _exists(self, country: str, value: str, field: Literal["keyword", "city"]) -> bool:
        """Internal method to check if keyword or city exists"""
        field_column = getattr(StoredKeyword, field)
        exists = (
            self.db.query(StoredKeyword)
            .filter(
                and_(
                    StoredKeyword.country == country,
                    field_column == value,
                    StoredKeyword.is_deleted == False
                )
            )
            .first()
        )
        return exists is not None
    
    def keyword_exists(self, country: str, keyword: str) -> bool:
        """Check if a keyword exists for a country"""
        return self._exists(country, keyword, "keyword")
    
    def city_exists(self, country: str, city: str) -> bool:
        """Check if a city exists for a country"""
        return self._exists(country, city, "city")
    
    def _add_item(
        self, 
        country: str, 
        value: str, 
        field: Literal["keyword", "city"]
    ) -> Optional[StoredKeyword]:
        """Internal method to add keyword or city"""
        if not value or not value.strip():
            return None
        
        value = value.strip()
        field_column = getattr(StoredKeyword, field)
        
        # Check if already exists and not deleted
        if self._exists(country, value, field):
            return None
        
        # Check if exists but deleted - restore it (single query)
        deleted_item = (
            self.db.query(StoredKeyword)
            .filter(
                and_(
                    StoredKeyword.country == country,
                    field_column == value,
                    StoredKeyword.is_deleted == True
                )
            )
            .first()
        )
        
        if deleted_item:
            # Restore deleted item
            deleted_item.is_deleted = False
            try:
                self.db.commit()
                self.db.refresh(deleted_item)
                return deleted_item
            except Exception:
                self.db.rollback()
                raise
        
        # Create new item
        create_data = {
            "country": country,
            field: value,
            "city" if field == "keyword" else "keyword": None
        }
        return self.create(create_data)
    
    def add_keyword(self, country: str, keyword: str) -> Optional[StoredKeyword]:
        """Add a new keyword for a country. If deleted, restore it."""
        return self._add_item(country, keyword, "keyword")
    
    def add_city(self, country: str, city: str) -> Optional[StoredKeyword]:
        """Add a new city for a country. If deleted, restore it."""
        return self._add_item(country, city, "city")
    
    def _delete_item(
        self, 
        country: str, 
        value: str, 
        field: Literal["keyword", "city"]
    ) -> bool:
        """Internal method to soft delete keyword or city (optimized batch update)"""
        field_column = getattr(StoredKeyword, field)
        
        # Use bulk update for better performance
        result = (
            self.db.execute(
                update(StoredKeyword)
                .where(
                    and_(
                        StoredKeyword.country == country,
                        field_column == value,
                        StoredKeyword.is_deleted == False
                    )
                )
                .values(is_deleted=True)
            )
        )
        
        if result.rowcount > 0:
            try:
                self.db.commit()
                return True
            except Exception:
                self.db.rollback()
                raise
        return False
    
    def delete_keyword(self, country: str, keyword: str) -> bool:
        """Soft delete a keyword (mark as deleted)"""
        return self._delete_item(country, keyword, "keyword")
    
    def delete_city(self, country: str, city: str) -> bool:
        """Soft delete a city (mark as deleted)"""
        return self._delete_item(country, city, "city")

