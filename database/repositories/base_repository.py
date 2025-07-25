from abc import ABC, abstractmethod
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional, Dict, Any, Type, TypeVar, Generic
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    """Base repository class with common CRUD operations"""
    
    def __init__(self, session: Session, model_class: Type[T]):
        self.session = session
        self.model_class = model_class
    
    def create(self, **kwargs) -> Optional[T]:
        """Create a new record"""
        try:
            instance = self.model_class(**kwargs)
            self.session.add(instance)
            self.session.flush()  # Flush to get the ID without committing
            return instance
        except SQLAlchemyError as e:
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            self.session.rollback()
            return None
    
    def create_many(self, records: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records"""
        try:
            instances = [self.model_class(**record) for record in records]
            self.session.add_all(instances)
            self.session.flush()
            return instances
        except SQLAlchemyError as e:
            logger.error(f"Error creating multiple {self.model_class.__name__}: {e}")
            self.session.rollback()
            return []
    
    def get_by_id(self, record_id: int) -> Optional[T]:
        """Get record by ID"""
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.id == record_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting {self.model_class.__name__} by ID {record_id}: {e}")
            return None
    
    def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[T]:
        """Get all records with optional pagination"""
        try:
            query = self.session.query(self.model_class)
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting all {self.model_class.__name__}: {e}")
            return []
    
    def update(self, record_id: int, **kwargs) -> Optional[T]:
        """Update a record by ID"""
        try:
            instance = self.get_by_id(record_id)
            if instance:
                for key, value in kwargs.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)
                self.session.flush()
                return instance
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error updating {self.model_class.__name__} {record_id}: {e}")
            self.session.rollback()
            return None
    
    def delete(self, record_id: int) -> bool:
        """Delete a record by ID"""
        try:
            instance = self.get_by_id(record_id)
            if instance:
                self.session.delete(instance)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            logger.error(f"Error deleting {self.model_class.__name__} {record_id}: {e}")
            self.session.rollback()
            return False
    
    def count(self) -> int:
        """Count total records"""
        try:
            return self.session.query(self.model_class).count()
        except SQLAlchemyError as e:
            logger.error(f"Error counting {self.model_class.__name__}: {e}")
            return 0
    
    def exists(self, record_id: int) -> bool:
        """Check if record exists"""
        try:
            return self.session.query(self.model_class).filter(
                self.model_class.id == record_id
            ).first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Error checking existence of {self.model_class.__name__} {record_id}: {e}")
            return False