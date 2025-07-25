from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, asc, and_, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging

from ..models import DetectedPattern, PatternType, TradingPair
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)

class DetectedPatternsRepository(BaseRepository[DetectedPattern]):
    """Repository for detected patterns operations"""
    
    def __init__(self, session: Session):
        super().__init__(session, DetectedPattern)
    
    def get_patterns_for_pair(self, pair_id: int, limit: int = 50, 
                             min_confidence: int = 0) -> List[DetectedPattern]:
        """Get detected patterns for a specific pair"""
        try:
            return self.session.query(DetectedPattern).filter(
                DetectedPattern.pair_id == pair_id,
                DetectedPattern.confidence_level >= min_confidence
            ).order_by(
                desc(DetectedPattern.detection_timestamp),
                desc(DetectedPattern.confidence_level)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting patterns for pair {pair_id}: {e}")
            return []
    
    def get_patterns_by_coin_id(self, coin_id: str, timeframe: str = '1d', 
                               days: int = 7, min_confidence: int = 0) -> List[DetectedPattern]:
        """Get detected patterns by coin_id"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            return self.session.query(DetectedPattern).join(TradingPair).filter(
                TradingPair.coin_id == coin_id,
                DetectedPattern.timeframe == timeframe,
                DetectedPattern.detection_timestamp >= start_time,
                DetectedPattern.confidence_level >= min_confidence
            ).order_by(
                desc(DetectedPattern.detection_timestamp),
                desc(DetectedPattern.confidence_level)
            ).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting patterns for coin {coin_id}: {e}")
            return []
    
    def get_recent_patterns(self, hours: int = 24, limit: int = 100) -> List[DetectedPattern]:
        """Get recently detected patterns across all pairs"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            return self.session.query(DetectedPattern).filter(
                DetectedPattern.detection_timestamp >= start_time
            ).order_by(
                desc(DetectedPattern.detection_timestamp),
                desc(DetectedPattern.confidence_level)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting recent patterns: {e}")
            return []
    
    def get_high_confidence_patterns(self, min_confidence: int = 80, 
                                   days: int = 7, limit: int = 50) -> List[DetectedPattern]:
        """Get high confidence patterns"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            return self.session.query(DetectedPattern).filter(
                DetectedPattern.confidence_level >= min_confidence,
                DetectedPattern.detection_timestamp >= start_time
            ).order_by(
                desc(DetectedPattern.confidence_level),
                desc(DetectedPattern.detection_timestamp)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting high confidence patterns: {e}")
            return []
    
    def get_patterns_by_type(self, pattern_type_id: int, days: int = 30) -> List[DetectedPattern]:
        """Get all patterns of a specific type"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            return self.session.query(DetectedPattern).filter(
                DetectedPattern.pattern_type_id == pattern_type_id,
                DetectedPattern.detection_timestamp >= start_time
            ).order_by(desc(DetectedPattern.detection_timestamp)).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting patterns by type {pattern_type_id}: {e}")
            return []
    
    def get_patterns_by_direction(self, direction: str, days: int = 7, 
                                 limit: int = 50) -> List[DetectedPattern]:
        """Get patterns by direction (bullish, bearish, neutral)"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            return self.session.query(DetectedPattern).filter(
                DetectedPattern.direction == direction,
                DetectedPattern.detection_timestamp >= start_time
            ).order_by(
                desc(DetectedPattern.confidence_level),
                desc(DetectedPattern.detection_timestamp)
            ).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting patterns by direction {direction}: {e}")
            return []
    
    def save_detected_pattern(self, pair_id: int, pattern_type_id: int, 
                             confidence_level: int, direction: str,
                             pattern_start_time: datetime, pattern_end_time: datetime,
                             timeframe: str, coordinates: Dict[str, Any] = None,
                             pattern_high: float = None, pattern_low: float = None) -> Optional[DetectedPattern]:
        """Save a newly detected pattern"""
        try:
            pattern = DetectedPattern(
                pair_id=pair_id,
                pattern_type_id=pattern_type_id,
                confidence_level=confidence_level,
                direction=direction,
                pattern_start_time=pattern_start_time,
                pattern_end_time=pattern_end_time,
                timeframe=timeframe,
                coordinates=coordinates,
                pattern_high=pattern_high,
                pattern_low=pattern_low
            )
            
            self.session.add(pattern)
            self.session.flush()
            logger.info(f"Saved detected pattern: {pattern.id}")
            return pattern
            
        except SQLAlchemyError as e:
            logger.error(f"Error saving detected pattern: {e}")
            self.session.rollback()
            return None
    
    def bulk_save_patterns(self, patterns_data: List[Dict[str, Any]]) -> int:
        """Bulk save detected patterns"""
        try:
            saved_count = 0
            for pattern_data in patterns_data:
                pattern = DetectedPattern(**pattern_data)
                self.session.add(pattern)
                saved_count += 1
            
            self.session.flush()
            logger.info(f"Bulk saved {saved_count} detected patterns")
            return saved_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error in bulk save patterns: {e}")
            self.session.rollback()
            return 0
    
    def get_pattern_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get pattern detection statistics"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            # Total patterns
            total_patterns = self.session.query(DetectedPattern).filter(
                DetectedPattern.detection_timestamp >= start_time
            ).count()
            
            # Patterns by direction
            direction_stats = self.session.query(
                DetectedPattern.direction,
                func.count(DetectedPattern.id).label('count'),
                func.avg(DetectedPattern.confidence_level).label('avg_confidence')
            ).filter(
                DetectedPattern.detection_timestamp >= start_time
            ).group_by(DetectedPattern.direction).all()
            
            # Top patterns by frequency
            top_patterns = self.session.query(
                PatternType.name,
                func.count(DetectedPattern.id).label('count'),
                func.avg(DetectedPattern.confidence_level).label('avg_confidence')
            ).join(PatternType).filter(
                DetectedPattern.detection_timestamp >= start_time
            ).group_by(PatternType.name).order_by(
                desc(func.count(DetectedPattern.id))
            ).limit(10).all()
            
            # Confidence distribution
            confidence_stats = self.session.query(
                func.min(DetectedPattern.confidence_level).label('min_confidence'),
                func.max(DetectedPattern.confidence_level).label('max_confidence'),
                func.avg(DetectedPattern.confidence_level).label('avg_confidence'),
                func.count().filter(DetectedPattern.confidence_level >= 80).label('high_confidence'),
                func.count().filter(DetectedPattern.confidence_level >= 60).label('medium_confidence'),
                func.count().filter(DetectedPattern.confidence_level < 60).label('low_confidence')
            ).filter(DetectedPattern.detection_timestamp >= start_time).first()
            
            return {
                'total_patterns': total_patterns,
                'by_direction': {row.direction: {'count': row.count, 'avg_confidence': float(row.avg_confidence) if row.avg_confidence else 0} for row in direction_stats},
                'top_patterns': [{'name': row.name, 'count': row.count, 'avg_confidence': float(row.avg_confidence) if row.avg_confidence else 0} for row in top_patterns],
                'confidence_stats': {
                    'min': confidence_stats.min_confidence if confidence_stats else 0,
                    'max': confidence_stats.max_confidence if confidence_stats else 0,
                    'avg': float(confidence_stats.avg_confidence) if confidence_stats and confidence_stats.avg_confidence else 0,
                    'high_confidence_count': confidence_stats.high_confidence if confidence_stats else 0,
                    'medium_confidence_count': confidence_stats.medium_confidence if confidence_stats else 0,
                    'low_confidence_count': confidence_stats.low_confidence if confidence_stats else 0
                }
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {}
    
    def get_patterns_with_full_details(self, pair_id: int = None, days: int = 7, 
                                     limit: int = 50) -> List[Dict[str, Any]]:
        """Get patterns with full trading pair and pattern type details"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            query = self.session.query(
                DetectedPattern,
                TradingPair.coin_id,
                TradingPair.symbol,
                TradingPair.name.label('pair_name'),
                PatternType.name.label('pattern_name'),
                PatternType.category,
                PatternType.reliability_score
            ).join(TradingPair).join(PatternType).filter(
                DetectedPattern.detection_timestamp >= start_time
            )
            
            if pair_id:
                query = query.filter(DetectedPattern.pair_id == pair_id)
            
            query = query.order_by(
                desc(DetectedPattern.detection_timestamp),
                desc(DetectedPattern.confidence_level)
            ).limit(limit)
            
            results = []
            for row in query.all():
                pattern_dict = row.DetectedPattern.to_dict()
                pattern_dict.update({
                    'coin_id': row.coin_id,
                    'symbol': row.symbol,
                    'pair_name': row.pair_name,
                    'pattern_name': row.pattern_name,
                    'category': row.category,
                    'reliability_score': row.reliability_score
                })
                results.append(pattern_dict)
            
            return results
            
        except SQLAlchemyError as e:
            logger.error(f"Error getting patterns with full details: {e}")
            return []
    
    def cleanup_old_patterns(self, days_to_keep: int = 90) -> int:
        """Remove detected patterns older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            deleted_count = self.session.query(DetectedPattern).filter(
                DetectedPattern.detection_timestamp < cutoff_date
            ).delete()
            
            self.session.flush()
            logger.info(f"Cleaned up {deleted_count} old detected patterns")
            return deleted_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up old patterns: {e}")
            self.session.rollback()
            return 0
    
    def find_similar_patterns(self, pattern_id: int, similarity_threshold: float = 0.8) -> List[DetectedPattern]:
        """Find similar patterns based on type, direction, and confidence"""
        try:
            base_pattern = self.get_by_id(pattern_id)
            if not base_pattern:
                return []
            
            confidence_range = base_pattern.confidence_level * similarity_threshold
            
            return self.session.query(DetectedPattern).filter(
                DetectedPattern.id != pattern_id,
                DetectedPattern.pattern_type_id == base_pattern.pattern_type_id,
                DetectedPattern.direction == base_pattern.direction,
                DetectedPattern.confidence_level >= confidence_range,
                DetectedPattern.timeframe == base_pattern.timeframe
            ).order_by(desc(DetectedPattern.confidence_level)).limit(10).all()
            
        except SQLAlchemyError as e:
            logger.error(f"Error finding similar patterns: {e}")
            return []