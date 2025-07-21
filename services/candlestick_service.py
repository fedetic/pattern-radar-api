"""
Candlestick Pattern Service - Specialized service for candlestick pattern detection
"""

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

import numpy as np
import pandas as pd
from typing import List, Dict, Any
from .base_pattern_service import BasePatternService

class CandlestickPatternService(BasePatternService):
    """Service for detecting candlestick patterns"""
    
    def __init__(self):
        super().__init__()
        # Define candlestick pattern functions and their names
        self.candlestick_patterns = {
            'CDLDOJI': 'Doji',
            'CDLHAMMER': 'Hammer',
            'CDLHANGINGMAN': 'Hanging Man',
            'CDLENGULFING': 'Engulfing Pattern',
            'CDLMORNINGSTAR': 'Morning Star',
            'CDLEVENINGSTAR': 'Evening Star',
            'CDLSHOOTINGSTAR': 'Shooting Star',
            'CDLDRAGONFLYDOJI': 'Dragonfly Doji',
            'CDLGRAVESTONEDOJI': 'Gravestone Doji',
            'CDLMARUBOZU': 'Marubozu',
            'CDLSPINNINGTOP': 'Spinning Top',
            'CDLPIERCING': 'Piercing Pattern',
            'CDLDARKCLOUDCOVER': 'Dark Cloud Cover',
            'CDLHARAMI': 'Harami Pattern',
            'CDLHARAMICROSS': 'Harami Cross',
            'CDLTHRUSTING': 'Thrusting Pattern',
            'CDLADVANCEBLOCK': 'Advance Block',
            'CDL3BLACKCROWS': 'Three Black Crows',
            'CDL3WHITESOLDIERS': 'Three White Soldiers',
            'CDL3INSIDE': 'Three Inside Up/Down',
            'CDL3OUTSIDE': 'Three Outside Up/Down'
        }
    
    def detect_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect candlestick patterns using ta-lib or fallback"""
        if not self._validate_dataframe(df, min_length=3):
            return []
        
        if TALIB_AVAILABLE:
            return self._detect_talib_patterns(df)
        else:
            return self._detect_fallback_patterns(df)
    
    def _detect_talib_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect patterns using ta-lib library"""
        patterns = []
        
        try:
            open_prices = df['open'].values
            high_prices = df['high'].values
            low_prices = df['low'].values
            close_prices = df['close'].values
            
            for pattern_func, pattern_name in self.candlestick_patterns.items():
                try:
                    func = getattr(talib, pattern_func)
                    result = func(open_prices, high_prices, low_prices, close_prices)
                    
                    # Find non-zero values (pattern occurrences)
                    pattern_indices = np.where(result != 0)[0]
                    
                    if len(pattern_indices) > 0:
                        # Get the most recent pattern occurrence
                        latest_index = pattern_indices[-1]
                        pattern_value = result[latest_index]
                        
                        confidence = min(abs(pattern_value), 100)
                        direction = "bullish" if pattern_value > 0 else "bearish"
                        
                        pattern = self._create_pattern_dict(
                            name=pattern_name,
                            category="Candle",
                            confidence=int(confidence),
                            direction=direction,
                            description=f"A {direction} {pattern_name.lower()} pattern detected",
                            coordinates=self._get_pattern_range_coordinates(df, latest_index, pattern_name),
                            latest_occurrence=int(latest_index),
                            timestamp=self._get_coordinate_timestamp(df, latest_index)
                        )
                        
                        patterns.append(pattern)
                        
                except Exception as e:
                    print(f"Error detecting {pattern_name}: {e}")
                    continue
            
            # Sort by confidence
            patterns.sort(key=lambda x: x['confidence'], reverse=True)
            self.log_detection_result(len(patterns))
            return patterns
            
        except Exception as e:
            print(f"Error in ta-lib pattern detection: {e}")
            return self._detect_fallback_patterns(df)
    
    def _detect_fallback_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Fallback pattern detection when ta-lib is not available"""
        patterns = []
        
        if len(df) < 3:
            return patterns
        
        # Simple hammer pattern detection
        for i in range(len(df) - 1, max(0, len(df) - 10), -1):
            row = df.iloc[i]
            body_size = abs(row['close'] - row['open'])
            lower_shadow = min(row['open'], row['close']) - row['low']
            upper_shadow = row['high'] - max(row['open'], row['close'])
            
            # Hammer pattern: long lower shadow, small body, small upper shadow
            if lower_shadow > 2 * body_size and upper_shadow < body_size:
                pattern = self._create_pattern_dict(
                    name="Hammer",
                    category="Candle",
                    confidence=75,
                    direction="bullish",
                    description="A bullish hammer pattern detected (fallback detection)",
                    coordinates=self._get_pattern_range_coordinates(df, i, "Hammer"),
                    latest_occurrence=int(i),
                    timestamp=self._get_coordinate_timestamp(df, i)
                )
                patterns.append(pattern)
                break
        
        # Simple doji pattern detection
        for i in range(len(df) - 1, max(0, len(df) - 10), -1):
            row = df.iloc[i]
            body_size = abs(row['close'] - row['open'])
            total_range = row['high'] - row['low']
            
            # Doji pattern: very small body relative to total range
            if body_size < total_range * 0.1 and total_range > 0:
                pattern = self._create_pattern_dict(
                    name="Doji",
                    category="Candle",
                    confidence=70,
                    direction="neutral",
                    description="A doji pattern detected (fallback detection)",
                    coordinates=self._get_pattern_range_coordinates(df, i, "Doji"),
                    latest_occurrence=int(i),
                    timestamp=self._get_coordinate_timestamp(df, i)
                )
                patterns.append(pattern)
                break
        
        self.log_detection_result(len(patterns))
        return patterns
    
    def _get_pattern_range_coordinates(self, df: pd.DataFrame, index: int, pattern_name: str) -> Dict[str, Any]:
        """Get coordinates for highlighting pattern ranges"""
        if index >= len(df):
            return {}
        
        # Determine pattern duration
        pattern_duration = self._get_pattern_duration(pattern_name)
        
        # Calculate start and end indices
        start_index = max(0, index - pattern_duration + 1)
        end_index = index
        
        # Get the price range for the pattern
        pattern_data = df.iloc[start_index:end_index + 1]
        pattern_high = float(pattern_data['high'].max())
        pattern_low = float(pattern_data['low'].min())
        
        return {
            "type": "pattern_range",
            "start_index": int(start_index),
            "end_index": int(end_index),
            "start_time": self._get_coordinate_timestamp(df, start_index),
            "end_time": self._get_coordinate_timestamp(df, end_index),
            "pattern_high": pattern_high,
            "pattern_low": pattern_low,
            "highlight_color": self._get_pattern_color_by_name(pattern_name),
            "pattern_name": pattern_name
        }
    
    def _get_pattern_duration(self, pattern_name: str) -> int:
        """Get the typical duration (in candles) for different pattern types"""
        single_candle_patterns = [
            'Doji', 'Hammer', 'Hanging Man', 'Shooting Star', 
            'Dragonfly Doji', 'Gravestone Doji', 'Marubozu', 'Spinning Top'
        ]
        
        two_candle_patterns = [
            'Engulfing Pattern', 'Piercing Pattern', 'Dark Cloud Cover', 
            'Harami Pattern', 'Harami Cross', 'Thrusting Pattern'
        ]
        
        three_candle_patterns = [
            'Morning Star', 'Evening Star', 'Three Black Crows', 
            'Three White Soldiers', 'Three Inside Up/Down', 'Three Outside Up/Down', 
            'Advance Block'
        ]
        
        if pattern_name in single_candle_patterns:
            return 1
        elif pattern_name in two_candle_patterns:
            return 2
        elif pattern_name in three_candle_patterns:
            return 3
        else:
            return 3  # Default
    
    def _get_pattern_color_by_name(self, pattern_name: str) -> str:
        """Get specific colors for different candlestick patterns"""
        bullish_patterns = [
            'Hammer', 'Morning Star', 'Piercing Pattern', 'Three White Soldiers', 
            'Dragonfly Doji', 'Bullish Engulfing'
        ]
        bearish_patterns = [
            'Hanging Man', 'Evening Star', 'Dark Cloud Cover', 'Three Black Crows', 
            'Gravestone Doji', 'Bearish Engulfing', 'Shooting Star'
        ]
        
        if any(bullish in pattern_name for bullish in bullish_patterns):
            return "#10B981"  # Green for bullish
        elif any(bearish in pattern_name for bearish in bearish_patterns):
            return "#EF4444"  # Red for bearish
        else:
            return "#F59E0B"  # Amber for neutral/other