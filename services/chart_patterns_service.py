"""
Chart Pattern Service - Service for detecting chart-based patterns like support/resistance, trends
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any
from .base_pattern_service import BasePatternService

class ChartPatternsService(BasePatternService):
    """Service for detecting chart patterns like support/resistance and trends"""
    
    def detect_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect chart patterns"""
        if not self._validate_dataframe(df, min_length=20):
            return []
        
        patterns = []
        
        # Detect support/resistance patterns
        patterns.extend(self._detect_support_resistance(df))
        
        # Detect trend patterns
        patterns.extend(self._detect_trend_patterns(df))
        
        # Detect breakout patterns
        patterns.extend(self._detect_breakout_patterns(df))
        
        self.log_detection_result(len(patterns))
        return patterns
    
    def _detect_support_resistance(self, df: pd.DataFrame, window: int = 20) -> List[Dict[str, Any]]:
        """Detect support and resistance levels"""
        patterns = []
        
        try:
            # Rolling min/max for support/resistance
            support_level = df['low'].rolling(window=window).min().iloc[-1]
            resistance_level = df['high'].rolling(window=window).max().iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Check if current price is near support or resistance
            support_distance = abs(current_price - support_level) / current_price
            resistance_distance = abs(current_price - resistance_level) / current_price
            
            if support_distance < 0.02:  # Within 2% of support
                confidence_factors = [
                    0.75,  # Base confidence
                    min(1.0, 0.5 + (0.02 - support_distance) * 25),  # Proximity bonus
                ]
                
                if self._is_volume_significant(df, len(df) - 1):
                    confidence_factors.append(0.9)  # Volume confirmation
                
                pattern = self._create_pattern_dict(
                    name="Support Level Test",
                    category="Price Action",
                    confidence=self._calculate_confidence(confidence_factors),
                    direction="bullish",
                    description="Price is testing a key support level",
                    coordinates={
                        "level": float(support_level),
                        "type": "horizontal_line",
                        "start_time": self._get_coordinate_timestamp(df, len(df) - window),
                        "end_time": self._get_coordinate_timestamp(df, len(df) - 1),
                        "highlight_color": self._get_pattern_color("bullish")
                    }
                )
                patterns.append(pattern)
            
            if resistance_distance < 0.02:  # Within 2% of resistance
                confidence_factors = [
                    0.75,  # Base confidence
                    min(1.0, 0.5 + (0.02 - resistance_distance) * 25),  # Proximity bonus
                ]
                
                if self._is_volume_significant(df, len(df) - 1):
                    confidence_factors.append(0.9)  # Volume confirmation
                
                pattern = self._create_pattern_dict(
                    name="Resistance Level Test",
                    category="Price Action",
                    confidence=self._calculate_confidence(confidence_factors),
                    direction="bearish",
                    description="Price is testing a key resistance level",
                    coordinates={
                        "level": float(resistance_level),
                        "type": "horizontal_line",
                        "start_time": self._get_coordinate_timestamp(df, len(df) - window),
                        "end_time": self._get_coordinate_timestamp(df, len(df) - 1),
                        "highlight_color": self._get_pattern_color("bearish")
                    }
                )
                patterns.append(pattern)
                
        except Exception as e:
            print(f"Error detecting support/resistance: {e}")
        
        return patterns
    
    def _detect_trend_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect basic trend patterns using moving averages"""
        patterns = []
        
        try:
            # Calculate moving averages
            df_copy = df.copy()
            df_copy['sma_20'] = df_copy['close'].rolling(window=20).mean()
            df_copy['sma_50'] = df_copy['close'].rolling(window=50).mean()
            
            current_price = df_copy['close'].iloc[-1]
            sma_20 = df_copy['sma_20'].iloc[-1]
            sma_50 = df_copy['sma_50'].iloc[-1]
            
            if pd.isna(sma_20) or pd.isna(sma_50):
                return patterns
            
            # Bullish trend pattern
            if current_price > sma_20 > sma_50:
                # Calculate trend strength
                price_above_20 = (current_price - sma_20) / sma_20
                ma_separation = (sma_20 - sma_50) / sma_50
                
                confidence_factors = [
                    0.70,  # Base confidence
                    min(1.0, price_above_20 * 10),  # Price momentum
                    min(1.0, ma_separation * 20),   # MA separation
                ]
                
                pattern = self._create_pattern_dict(
                    name="Bullish Trend",
                    category="Chart",
                    confidence=self._calculate_confidence(confidence_factors),
                    direction="bullish",
                    description="Price is above both 20 and 50 period moving averages",
                    coordinates={
                        "sma_20": float(sma_20),
                        "sma_50": float(sma_50),
                        "type": "trend_lines",
                        "start_time": self._get_coordinate_timestamp(df, max(0, len(df) - 50)),
                        "end_time": self._get_coordinate_timestamp(df, len(df) - 1),
                        "highlight_color": self._get_pattern_color("bullish")
                    }
                )
                patterns.append(pattern)
            
            # Bearish trend pattern  
            elif current_price < sma_20 < sma_50:
                # Calculate trend strength
                price_below_20 = (sma_20 - current_price) / sma_20
                ma_separation = (sma_50 - sma_20) / sma_50
                
                confidence_factors = [
                    0.70,  # Base confidence
                    min(1.0, price_below_20 * 10),  # Price momentum
                    min(1.0, ma_separation * 20),   # MA separation
                ]
                
                pattern = self._create_pattern_dict(
                    name="Bearish Trend",
                    category="Chart",
                    confidence=self._calculate_confidence(confidence_factors),
                    direction="bearish",
                    description="Price is below both 20 and 50 period moving averages",
                    coordinates={
                        "sma_20": float(sma_20),
                        "sma_50": float(sma_50),
                        "type": "trend_lines",
                        "start_time": self._get_coordinate_timestamp(df, max(0, len(df) - 50)),
                        "end_time": self._get_coordinate_timestamp(df, len(df) - 1),
                        "highlight_color": self._get_pattern_color("bearish")
                    }
                )
                patterns.append(pattern)
                
        except Exception as e:
            print(f"Error detecting trend patterns: {e}")
        
        return patterns
    
    def _detect_breakout_patterns(self, df: pd.DataFrame, window: int = 20) -> List[Dict[str, Any]]:
        """Detect breakout patterns"""
        patterns = []
        
        try:
            if len(df) < window + 5:
                return patterns
            
            # Calculate recent trading range
            recent_data = df.tail(window)
            range_high = recent_data['high'].max()
            range_low = recent_data['low'].min()
            range_size = range_high - range_low
            
            current_price = df['close'].iloc[-1]
            previous_close = df['close'].iloc[-2]
            
            # Upward breakout
            if (current_price > range_high and 
                previous_close <= range_high and 
                range_size > 0):
                
                breakout_strength = (current_price - range_high) / range_size
                
                confidence_factors = [
                    0.75,  # Base confidence
                    min(1.0, breakout_strength * 2),  # Breakout magnitude
                ]
                
                if self._is_volume_significant(df, len(df) - 1):
                    confidence_factors.append(0.95)  # Volume confirmation
                
                pattern = self._create_pattern_dict(
                    name="Upward Breakout",
                    category="Chart",
                    confidence=self._calculate_confidence(confidence_factors),
                    direction="bullish",
                    description=f"Price broke above {window}-period trading range",
                    coordinates={
                        "breakout_level": float(range_high),
                        "type": "horizontal_line",
                        "start_time": self._get_coordinate_timestamp(df, len(df) - window),
                        "end_time": self._get_coordinate_timestamp(df, len(df) - 1),
                        "highlight_color": self._get_pattern_color("bullish")
                    }
                )
                patterns.append(pattern)
            
            # Downward breakout
            elif (current_price < range_low and 
                  previous_close >= range_low and 
                  range_size > 0):
                
                breakout_strength = (range_low - current_price) / range_size
                
                confidence_factors = [
                    0.75,  # Base confidence
                    min(1.0, breakout_strength * 2),  # Breakout magnitude
                ]
                
                if self._is_volume_significant(df, len(df) - 1):
                    confidence_factors.append(0.95)  # Volume confirmation
                
                pattern = self._create_pattern_dict(
                    name="Downward Breakout",
                    category="Chart",
                    confidence=self._calculate_confidence(confidence_factors),
                    direction="bearish",
                    description=f"Price broke below {window}-period trading range",
                    coordinates={
                        "breakout_level": float(range_low),
                        "type": "horizontal_line",
                        "start_time": self._get_coordinate_timestamp(df, len(df) - window),
                        "end_time": self._get_coordinate_timestamp(df, len(df) - 1),
                        "highlight_color": self._get_pattern_color("bearish")
                    }
                )
                patterns.append(pattern)
                
        except Exception as e:
            print(f"Error detecting breakout patterns: {e}")
        
        return patterns