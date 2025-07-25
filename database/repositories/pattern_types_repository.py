from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
import logging

from ..models import PatternType
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)

class PatternTypesRepository(BaseRepository[PatternType]):
    """Repository for pattern types operations"""
    
    def __init__(self, session: Session):
        super().__init__(session, PatternType)
    
    def get_by_name(self, name: str) -> Optional[PatternType]:
        """Get pattern type by name"""
        try:
            return self.session.query(PatternType).filter(
                PatternType.name == name
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting pattern type by name {name}: {e}")
            return None
    
    def get_by_category(self, category: str) -> List[PatternType]:
        """Get all pattern types in a category"""
        try:
            return self.session.query(PatternType).filter(
                PatternType.category == category
            ).order_by(desc(PatternType.reliability_score)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting pattern types by category {category}: {e}")
            return []
    
    def get_by_pattern_type(self, pattern_type: str) -> List[PatternType]:
        """Get all pattern types by pattern type (candlestick, harmonic, etc.)"""
        try:
            return self.session.query(PatternType).filter(
                PatternType.pattern_type == pattern_type
            ).order_by(desc(PatternType.reliability_score)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting pattern types by type {pattern_type}: {e}")
            return []
    
    def get_reversal_patterns(self) -> List[PatternType]:
        """Get all reversal patterns"""
        try:
            return self.session.query(PatternType).filter(
                PatternType.is_reversal == True
            ).order_by(desc(PatternType.reliability_score)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting reversal patterns: {e}")
            return []
    
    def get_continuation_patterns(self) -> List[PatternType]:
        """Get all continuation patterns"""
        try:
            return self.session.query(PatternType).filter(
                PatternType.is_continuation == True
            ).order_by(desc(PatternType.reliability_score)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting continuation patterns: {e}")
            return []
    
    def get_high_reliability_patterns(self, min_reliability: int = 80) -> List[PatternType]:
        """Get patterns with high reliability scores"""
        try:
            return self.session.query(PatternType).filter(
                PatternType.reliability_score >= min_reliability
            ).order_by(desc(PatternType.reliability_score)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting high reliability patterns: {e}")
            return []
    
    def search_patterns(self, search_term: str) -> List[PatternType]:
        """Search patterns by name or description"""
        try:
            search_pattern = f"%{search_term.lower()}%"
            return self.session.query(PatternType).filter(
                (PatternType.name.ilike(search_pattern)) |
                (PatternType.description.ilike(search_pattern))
            ).order_by(desc(PatternType.reliability_score)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching patterns with term '{search_term}': {e}")
            return []
    
    def upsert_pattern_type(self, pattern_data: Dict[str, Any]) -> Optional[PatternType]:
        """Insert or update a pattern type"""
        try:
            existing_pattern = self.get_by_name(pattern_data.get('name'))
            
            if existing_pattern:
                # Update existing pattern
                for key, value in pattern_data.items():
                    if hasattr(existing_pattern, key) and key != 'id':
                        setattr(existing_pattern, key, value)
                self.session.flush()
                logger.info(f"Updated pattern type: {existing_pattern.name}")
                return existing_pattern
            else:
                # Create new pattern
                new_pattern = self.create(**pattern_data)
                logger.info(f"Created new pattern type: {new_pattern.name if new_pattern else 'Failed'}")
                return new_pattern
                
        except SQLAlchemyError as e:
            logger.error(f"Error upserting pattern type {pattern_data.get('name', 'unknown')}: {e}")
            self.session.rollback()
            return None
    
    def bulk_insert_pattern_types(self, patterns_data: List[Dict[str, Any]]) -> int:
        """Bulk insert pattern types"""
        try:
            inserted_count = 0
            for pattern_data in patterns_data:
                existing = self.get_by_name(pattern_data.get('name'))
                if not existing:
                    new_pattern = PatternType(**pattern_data)
                    self.session.add(new_pattern)
                    inserted_count += 1
                else:
                    # Update existing
                    for key, value in pattern_data.items():
                        if hasattr(existing, key) and key not in ['id', 'created_at']:
                            setattr(existing, key, value)
            
            self.session.flush()
            logger.info(f"Bulk inserted {inserted_count} pattern types")
            return inserted_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error in bulk insert pattern types: {e}")
            self.session.rollback()
            return 0
    
    def get_categories_summary(self) -> List[Dict[str, Any]]:
        """Get summary of pattern types by category"""
        try:
            from sqlalchemy import func
            
            result = self.session.query(
                PatternType.category,
                func.count(PatternType.id).label('count'),
                func.avg(PatternType.reliability_score).label('avg_reliability'),
                func.count().filter(PatternType.is_reversal == True).label('reversal_count'),
                func.count().filter(PatternType.is_continuation == True).label('continuation_count')
            ).group_by(PatternType.category).order_by(PatternType.category).all()
            
            summary = []
            for row in result:
                summary.append({
                    'category': row.category,
                    'count': row.count,
                    'avg_reliability': float(row.avg_reliability) if row.avg_reliability else 0,
                    'reversal_count': row.reversal_count or 0,
                    'continuation_count': row.continuation_count or 0
                })
            
            return summary
        except SQLAlchemyError as e:
            logger.error(f"Error getting categories summary: {e}")
            return []
    
    def get_pattern_types_for_detection(self) -> Dict[str, PatternType]:
        """Get all pattern types as a lookup dictionary for detection"""
        try:
            patterns = self.get_all()
            return {pattern.name: pattern for pattern in patterns}
        except SQLAlchemyError as e:
            logger.error(f"Error getting pattern types for detection: {e}")
            return {}
    
    def update_reliability_score(self, pattern_name: str, new_score: int) -> Optional[PatternType]:
        """Update reliability score for a pattern"""
        try:
            pattern = self.get_by_name(pattern_name)
            if pattern:
                pattern.reliability_score = new_score
                self.session.flush()
                return pattern
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error updating reliability score for {pattern_name}: {e}")
            self.session.rollback()
            return None