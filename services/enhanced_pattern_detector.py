"""
Enhanced pattern detector with database persistence
Extends the original detector to save detected patterns to database
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .pattern_detector import PatternDetector
from database.connection import get_database_manager
from database.repositories.trading_pairs_repository import TradingPairsRepository
from database.repositories.pattern_types_repository import PatternTypesRepository
from database.repositories.detected_patterns_repository import DetectedPatternsRepository

logger = logging.getLogger(__name__)

class EnhancedPatternDetector(PatternDetector):
    """Enhanced pattern detector with database persistence"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = get_database_manager()
        self._pattern_types_cache = None
    
    def _get_pattern_types_lookup(self) -> Dict[str, Any]:
        """Get pattern types lookup dictionary with caching"""
        if self._pattern_types_cache is None:
            try:
                with self.db_manager.get_db_session() as session:
                    pattern_types_repo = PatternTypesRepository(session)
                    self._pattern_types_cache = pattern_types_repo.get_pattern_types_for_detection()
                    logger.info(f"Cached {len(self._pattern_types_cache)} pattern types for detection")
            except Exception as e:
                logger.error(f"Error loading pattern types: {e}")
                self._pattern_types_cache = {}
        
        return self._pattern_types_cache
    
    def analyze_patterns_with_persistence(self, df: pd.DataFrame, coin_id: str, 
                                        timeframe: str = "1d", save_to_db: bool = True) -> Dict[str, Any]:
        """Analyze patterns and optionally save to database"""
        try:
            # Run original pattern analysis
            analysis_result = super().analyze_patterns(df)
            
            if not save_to_db or not analysis_result.get('patterns'):
                return analysis_result
            
            # Save detected patterns to database
            with self.db_manager.get_db_session() as session:
                pairs_repo = TradingPairsRepository(session)
                pattern_types_repo = PatternTypesRepository(session)
                detected_repo = DetectedPatternsRepository(session)
                
                # Get trading pair
                trading_pair = pairs_repo.get_by_coin_id(coin_id)
                if not trading_pair:
                    logger.warning(f"Trading pair not found for {coin_id}, skipping database save")
                    return analysis_result
                
                # Get pattern types lookup within current session
                pattern_types = pattern_types_repo.get_pattern_types_for_detection()
                
                saved_patterns = []
                detection_timestamp = datetime.now()
                
                for pattern in analysis_result['patterns']:
                    pattern_name = pattern.get('name')
                    pattern_type = pattern_types.get(pattern_name)
                    
                    if not pattern_type:
                        logger.warning(f"Pattern type '{pattern_name}' not found in database")
                        continue
                    
                    # Determine pattern timing
                    pattern_start_time = detection_timestamp
                    pattern_end_time = detection_timestamp
                    
                    if pattern.get('timestamp'):
                        try:
                            pattern_start_time = datetime.fromisoformat(pattern['timestamp'].replace('Z', '+00:00'))
                            pattern_end_time = pattern_start_time
                        except:
                            pass
                    
                    # Adjust end time based on pattern duration
                    pattern_duration = pattern_type.typical_duration
                    if timeframe == "1d":
                        pattern_end_time = pattern_start_time + timedelta(days=pattern_duration)
                    elif timeframe == "1h":
                        pattern_end_time = pattern_start_time + timedelta(hours=pattern_duration)
                    elif timeframe == "4h":
                        pattern_end_time = pattern_start_time + timedelta(hours=pattern_duration * 4)
                    
                    # Prepare pattern data
                    pattern_data = {
                        'pair_id': trading_pair.id,
                        'pattern_type_id': pattern_type.id,
                        'confidence_level': pattern.get('confidence', 0),
                        'direction': pattern.get('direction', 'neutral'),
                        'pattern_start_time': pattern_start_time,
                        'pattern_end_time': pattern_end_time,
                        'timeframe': timeframe,
                        'coordinates': pattern.get('coordinates'),
                        'pattern_high': None,
                        'pattern_low': None
                    }
                    
                    # Extract pattern high/low from coordinates if available
                    coordinates = pattern.get('coordinates')
                    if coordinates:
                        pattern_data['pattern_high'] = coordinates.get('pattern_high')
                        pattern_data['pattern_low'] = coordinates.get('pattern_low')
                    
                    # Save pattern
                    saved_pattern = detected_repo.save_detected_pattern(**pattern_data)
                    if saved_pattern:
                        saved_patterns.append(saved_pattern)
                
                logger.info(f"Saved {len(saved_patterns)} patterns for {coin_id} to database")
                
                # Add database IDs to the analysis result
                for i, pattern in enumerate(analysis_result['patterns']):
                    if i < len(saved_patterns):
                        pattern['db_id'] = saved_patterns[i].id
                
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in analyze_patterns_with_persistence for {coin_id}: {e}")
            # Return original analysis without database save if error occurs
            return super().analyze_patterns(df)
    
    def get_recent_patterns_for_coin(self, coin_id: str, days: int = 7, 
                                   min_confidence: int = 0) -> List[Dict[str, Any]]:
        """Get recent patterns for a coin from database"""
        try:
            with self.db_manager.get_db_session() as session:
                detected_repo = DetectedPatternsRepository(session)
                patterns = detected_repo.get_patterns_by_coin_id(
                    coin_id, timeframe="1d", days=days, min_confidence=min_confidence
                )
                
                return [pattern.to_dict() for pattern in patterns]
                
        except Exception as e:
            logger.error(f"Error getting recent patterns for {coin_id}: {e}")
            return []
    
    def get_pattern_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get pattern detection statistics from database"""
        try:
            with self.db_manager.get_db_session() as session:
                detected_repo = DetectedPatternsRepository(session)
                return detected_repo.get_pattern_statistics(days)
                
        except Exception as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {}
    
    def get_high_confidence_patterns(self, min_confidence: int = 80, 
                                   days: int = 7) -> List[Dict[str, Any]]:
        """Get high confidence patterns from database"""
        try:
            with self.db_manager.get_db_session() as session:
                detected_repo = DetectedPatternsRepository(session)
                patterns = detected_repo.get_high_confidence_patterns(
                    min_confidence=min_confidence, days=days
                )
                
                return [pattern.to_dict() for pattern in patterns]
                
        except Exception as e:
            logger.error(f"Error getting high confidence patterns: {e}")
            return []
    
    def get_patterns_by_direction(self, direction: str, days: int = 7) -> List[Dict[str, Any]]:
        """Get patterns by direction from database"""
        try:
            with self.db_manager.get_db_session() as session:
                detected_repo = DetectedPatternsRepository(session)
                patterns = detected_repo.get_patterns_by_direction(direction, days)
                
                return [pattern.to_dict() for pattern in patterns]
                
        except Exception as e:
            logger.error(f"Error getting patterns by direction {direction}: {e}")
            return []
    
    def analyze_and_compare_with_history(self, df: pd.DataFrame, coin_id: str, 
                                       timeframe: str = "1d") -> Dict[str, Any]:
        """Analyze current patterns and compare with historical patterns"""
        try:
            # Get current analysis
            current_analysis = self.analyze_patterns_with_persistence(
                df, coin_id, timeframe, save_to_db=True
            )
            
            # Get historical patterns for comparison
            historical_patterns = self.get_recent_patterns_for_coin(coin_id, days=30)
            
            # Analyze pattern trends
            pattern_trends = self._analyze_pattern_trends(
                current_analysis.get('patterns', []), 
                historical_patterns
            )
            
            # Add historical context to analysis
            current_analysis.update({
                'historical_patterns': historical_patterns[:10],  # Last 10 patterns
                'pattern_trends': pattern_trends,
                'total_historical_patterns': len(historical_patterns)
            })
            
            return current_analysis
            
        except Exception as e:
            logger.error(f"Error in analyze_and_compare_with_history for {coin_id}: {e}")
            return self.analyze_patterns_with_persistence(df, coin_id, timeframe)
    
    def _analyze_pattern_trends(self, current_patterns: List[Dict], 
                               historical_patterns: List[Dict]) -> Dict[str, Any]:
        """Analyze trends in pattern detection"""
        try:
            trends = {
                'frequent_patterns': {},
                'confidence_trend': 'stable',
                'direction_trend': 'neutral',
                'pattern_frequency': 0
            }
            
            # Count frequent patterns
            pattern_counts = {}
            total_confidence = 0
            bullish_count = 0
            bearish_count = 0
            
            for pattern in historical_patterns:
                name = pattern.get('name', 'Unknown')
                pattern_counts[name] = pattern_counts.get(name, 0) + 1
                
                confidence = pattern.get('confidence', 0)
                total_confidence += confidence
                
                direction = pattern.get('direction', 'neutral')
                if direction == 'bullish':
                    bullish_count += 1
                elif direction == 'bearish':
                    bearish_count += 1
            
            # Sort patterns by frequency
            trends['frequent_patterns'] = dict(
                sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            )
            
            # Calculate average confidence
            if historical_patterns:
                avg_confidence = total_confidence / len(historical_patterns)
                trends['average_confidence'] = round(avg_confidence, 2)
                
                # Determine confidence trend
                recent_patterns = historical_patterns[:5]
                if recent_patterns:
                    recent_confidence = sum(p.get('confidence', 0) for p in recent_patterns) / len(recent_patterns)
                    if recent_confidence > avg_confidence * 1.1:
                        trends['confidence_trend'] = 'improving'
                    elif recent_confidence < avg_confidence * 0.9:
                        trends['confidence_trend'] = 'declining'
                
                # Determine direction trend
                if bullish_count > bearish_count * 1.5:
                    trends['direction_trend'] = 'bullish'
                elif bearish_count > bullish_count * 1.5:
                    trends['direction_trend'] = 'bearish'
                
                # Calculate pattern frequency (patterns per week)
                trends['pattern_frequency'] = round(len(historical_patterns) / 4.3, 2)  # Assume 30 days ≈ 4.3 weeks
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing pattern trends: {e}")
            return {}
    
    def cleanup_old_patterns(self, days_to_keep: int = 90) -> int:
        """Clean up old detected patterns"""
        try:
            with self.db_manager.get_db_session() as session:
                detected_repo = DetectedPatternsRepository(session)
                deleted_count = detected_repo.cleanup_old_patterns(days_to_keep)
                logger.info(f"Cleaned up {deleted_count} old patterns")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error cleaning up old patterns: {e}")
            return 0
    
    def get_database_pattern_summary(self) -> Dict[str, Any]:
        """Get comprehensive pattern database summary"""
        try:
            with self.db_manager.get_db_session() as session:
                pattern_types_repo = PatternTypesRepository(session)
                detected_repo = DetectedPatternsRepository(session)
                
                return {
                    'pattern_types_count': pattern_types_repo.count(),
                    'detected_patterns_count': detected_repo.count(),
                    'categories_summary': pattern_types_repo.get_categories_summary(),
                    'recent_statistics': detected_repo.get_pattern_statistics(days=7),
                    'monthly_statistics': detected_repo.get_pattern_statistics(days=30)
                }
                
        except Exception as e:
            logger.error(f"Error getting database pattern summary: {e}")
            return {}

# Global enhanced detector instance
enhanced_pattern_detector = EnhancedPatternDetector()