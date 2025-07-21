"""
Base Pattern Service - Common functionality for all pattern services
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

class BasePatternService(ABC):
    """Base class for all pattern detection services"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        
    @abstractmethod
    def detect_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect patterns and return list of pattern dictionaries"""
        pass
        
    def _validate_dataframe(self, df: pd.DataFrame, min_length: int = 5) -> bool:
        """Validate DataFrame has required columns and minimum length"""
        if df is None or df.empty:
            return False
            
        required_columns = ['open', 'high', 'low', 'close']
        if not all(col in df.columns for col in required_columns):
            return False
            
        if len(df) < min_length:
            return False
            
        return True
    
    def _get_pattern_color(self, direction: str) -> str:
        """Get standardized color for pattern direction"""
        color_map = {
            'bullish': '#10B981',
            'bearish': '#EF4444', 
            'neutral': '#F59E0B',
            'continuation': '#3B82F6'
        }
        return color_map.get(direction, '#6B7280')
    
    def _calculate_confidence(self, strength_factors: List[float]) -> int:
        """Calculate pattern confidence based on multiple strength factors"""
        if not strength_factors:
            return 50  # Default confidence
            
        # Weighted average of factors, capped at 100
        avg_strength = sum(strength_factors) / len(strength_factors)
        confidence = min(int(avg_strength * 100), 100)
        return max(confidence, 10)  # Minimum 10% confidence
    
    def _get_coordinate_timestamp(self, df: pd.DataFrame, index: int) -> str:
        """Get ISO timestamp for given index"""
        try:
            return df.index[index].isoformat()
        except (IndexError, AttributeError):
            return pd.Timestamp.now().isoformat()
    
    def _create_pattern_dict(self, 
                           name: str,
                           category: str, 
                           confidence: int,
                           direction: str,
                           description: str,
                           coordinates: Optional[Dict[str, Any]] = None,
                           **kwargs) -> Dict[str, Any]:
        """Create standardized pattern dictionary"""
        pattern = {
            "name": name,
            "category": category,
            "confidence": max(10, min(100, confidence)),  # Clamp between 10-100
            "direction": direction,
            "description": description,
            "service": self.name
        }
        
        if coordinates:
            pattern["coordinates"] = coordinates
            
        # Add any additional fields
        pattern.update(kwargs)
        
        return pattern
    
    def _find_pivot_points(self, df: pd.DataFrame, window: int = 5) -> List[Dict[str, Any]]:
        """Find pivot highs and lows in price data"""
        pivots = []
        
        for i in range(window, len(df) - window):
            current_high = df['high'].iloc[i]
            current_low = df['low'].iloc[i]
            
            # Check for pivot high
            is_pivot_high = all(current_high >= df['high'].iloc[i-j] for j in range(1, window+1)) and \
                           all(current_high >= df['high'].iloc[i+j] for j in range(1, window+1))
            
            # Check for pivot low  
            is_pivot_low = all(current_low <= df['low'].iloc[i-j] for j in range(1, window+1)) and \
                          all(current_low <= df['low'].iloc[i+j] for j in range(1, window+1))
            
            if is_pivot_high:
                pivots.append({
                    'index': i,
                    'price': current_high,
                    'type': 'high',
                    'timestamp': df.index[i]
                })
            elif is_pivot_low:
                pivots.append({
                    'index': i,
                    'price': current_low,
                    'type': 'low', 
                    'timestamp': df.index[i]
                })
        
        return pivots
    
    def _calculate_price_change(self, start_price: float, end_price: float) -> float:
        """Calculate percentage price change"""
        if start_price == 0:
            return 0
        return ((end_price - start_price) / start_price) * 100
    
    def _is_volume_significant(self, df: pd.DataFrame, index: int, multiplier: float = 1.5) -> bool:
        """Check if volume at index is significantly higher than average"""
        if 'volume' not in df.columns or df['volume'].isna().all():
            return False
            
        volume_window = df['volume'].rolling(window=20, min_periods=5)
        avg_volume = volume_window.mean().iloc[index]
        current_volume = df['volume'].iloc[index]
        
        return current_volume > (avg_volume * multiplier)
    
    def log_detection_result(self, patterns_found: int):
        """Log pattern detection results"""
        print(f"{self.name}: Detected {patterns_found} patterns")