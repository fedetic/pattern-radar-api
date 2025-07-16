try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("Warning: ta-lib not available, using fallback pattern detection")

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

class PatternDetector:
    def __init__(self):
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
    
    def detect_candlestick_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect candlestick patterns using ta-lib or fallback"""
        patterns = []
        
        if not TALIB_AVAILABLE:
            # Fallback patterns when ta-lib is not available
            return self._detect_fallback_patterns(df)
        
        try:
            open_prices = df['open'].values
            high_prices = df['high'].values
            low_prices = df['low'].values
            close_prices = df['close'].values
            
            for pattern_func, pattern_name in self.candlestick_patterns.items():
                try:
                    # Get the pattern function from talib
                    func = getattr(talib, pattern_func)
                    result = func(open_prices, high_prices, low_prices, close_prices)
                    
                    # Find non-zero values (pattern occurrences)
                    pattern_indices = np.where(result != 0)[0]
                    
                    if len(pattern_indices) > 0:
                        # Get the most recent pattern occurrence
                        latest_index = pattern_indices[-1]
                        pattern_value = result[latest_index]
                        
                        # Calculate confidence based on pattern value
                        confidence = min(abs(pattern_value), 100)
                        
                        # Determine if bullish or bearish
                        direction = "bullish" if pattern_value > 0 else "bearish"
                        
                        patterns.append({
                            "name": pattern_name,
                            "category": "Candle",
                            "confidence": int(confidence),
                            "direction": direction,
                            "latest_occurrence": int(latest_index),
                            "timestamp": df.index[latest_index].isoformat(),
                            "coordinates": self._get_pattern_range_coordinates(df, latest_index, pattern_name),
                            "description": f"A {direction} {pattern_name.lower()} pattern detected"
                        })
                        
                except Exception as e:
                    print(f"Error detecting {pattern_name}: {e}")
                    continue
            
            # Sort by confidence
            patterns.sort(key=lambda x: x['confidence'], reverse=True)
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
                patterns.append({
                    "name": "Hammer",
                    "category": "Candle",
                    "confidence": 75,
                    "direction": "bullish",
                    "latest_occurrence": int(i),
                    "timestamp": df.index[i].isoformat(),
                    "coordinates": self._get_pattern_range_coordinates(df, i, "Hammer"),
                    "description": "A bullish hammer pattern detected (fallback detection)"
                })
                break
        
        # Simple doji pattern detection
        for i in range(len(df) - 1, max(0, len(df) - 10), -1):
            row = df.iloc[i]
            body_size = abs(row['close'] - row['open'])
            total_range = row['high'] - row['low']
            
            # Doji pattern: very small body relative to total range
            if body_size < total_range * 0.1:
                patterns.append({
                    "name": "Doji",
                    "category": "Candle",
                    "confidence": 70,
                    "direction": "neutral",
                    "latest_occurrence": int(i),
                    "timestamp": df.index[i].isoformat(),
                    "coordinates": self._get_pattern_range_coordinates(df, i, "Doji"),
                    "description": "A doji pattern detected (fallback detection)"
                })
                break
        
        return patterns
    
    def detect_chart_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect basic chart patterns"""
        patterns = []
        
        # Simple support/resistance detection
        support_resistance = self._detect_support_resistance(df)
        patterns.extend(support_resistance)
        
        # Simple trend pattern detection
        trend_patterns = self._detect_trend_patterns(df)
        patterns.extend(trend_patterns)
        
        return patterns
    
    def _detect_support_resistance(self, df: pd.DataFrame, window: int = 20) -> List[Dict[str, Any]]:
        """Detect support and resistance levels"""
        patterns = []
        
        # Rolling min/max for support/resistance
        support_level = df['low'].rolling(window=window).min().iloc[-1]
        resistance_level = df['high'].rolling(window=window).max().iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # Check if current price is near support or resistance
        support_distance = abs(current_price - support_level) / current_price
        resistance_distance = abs(current_price - resistance_level) / current_price
        
        if support_distance < 0.02:  # Within 2% of support
            patterns.append({
                "name": "Support Level Test",
                "category": "Price Action",
                "confidence": 75,
                "direction": "bullish",
                "coordinates": {
                    "level": float(support_level),
                    "type": "horizontal_line",
                    "start_time": df.index[-window].isoformat(),
                    "end_time": df.index[-1].isoformat()
                },
                "description": "Price is testing a key support level"
            })
        
        if resistance_distance < 0.02:  # Within 2% of resistance
            patterns.append({
                "name": "Resistance Level Test",
                "category": "Price Action", 
                "confidence": 75,
                "direction": "bearish",
                "coordinates": {
                    "level": float(resistance_level),
                    "type": "horizontal_line",
                    "start_time": df.index[-window].isoformat(),
                    "end_time": df.index[-1].isoformat()
                },
                "description": "Price is testing a key resistance level"
            })
        
        return patterns
    
    def _detect_trend_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect basic trend patterns"""
        patterns = []
        
        # Simple moving averages
        df_copy = df.copy()
        df_copy['sma_20'] = df_copy['close'].rolling(window=20).mean()
        df_copy['sma_50'] = df_copy['close'].rolling(window=50).mean()
        
        current_price = df_copy['close'].iloc[-1]
        sma_20 = df_copy['sma_20'].iloc[-1]
        sma_50 = df_copy['sma_50'].iloc[-1]
        
        # Bullish trend pattern
        if current_price > sma_20 > sma_50:
            patterns.append({
                "name": "Bullish Trend",
                "category": "Chart",
                "confidence": 70,
                "direction": "bullish", 
                "coordinates": {
                    "sma_20": float(sma_20),
                    "sma_50": float(sma_50),
                    "type": "trend_lines",
                    "start_time": df.index[-50].isoformat() if len(df) >= 50 else df.index[0].isoformat(),
                    "end_time": df.index[-1].isoformat()
                },
                "description": "Price is above both 20 and 50 period moving averages"
            })
        
        # Bearish trend pattern  
        elif current_price < sma_20 < sma_50:
            patterns.append({
                "name": "Bearish Trend",
                "category": "Chart",
                "confidence": 70,
                "direction": "bearish",
                "coordinates": {
                    "sma_20": float(sma_20),
                    "sma_50": float(sma_50),
                    "type": "trend_lines",
                    "start_time": df.index[-50].isoformat() if len(df) >= 50 else df.index[0].isoformat(),
                    "end_time": df.index[-1].isoformat()
                },
                "description": "Price is below both 20 and 50 period moving averages"
            })
        
        return patterns
    
    def _get_candlestick_coordinates(self, df: pd.DataFrame, index: int) -> Dict[str, Any]:
        """Get coordinates for highlighting candlestick patterns"""
        if index >= len(df):
            return {}
        
        return {
            "index": int(index),
            "timestamp": df.index[index].isoformat(),
            "open": float(df['open'].iloc[index]),
            "high": float(df['high'].iloc[index]),
            "low": float(df['low'].iloc[index]),
            "close": float(df['close'].iloc[index]),
            "type": "candlestick_highlight"
        }
    
    def _get_pattern_range_coordinates(self, df: pd.DataFrame, index: int, pattern_name: str) -> Dict[str, Any]:
        """Get coordinates for highlighting pattern ranges with start and end times"""
        if index >= len(df):
            return {}
        
        # Determine pattern duration based on pattern type
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
            "start_time": df.index[start_index].isoformat(),
            "end_time": df.index[end_index].isoformat(),
            "pattern_high": pattern_high,
            "pattern_low": pattern_low,
            "highlight_color": self._get_pattern_color(pattern_name),
            "pattern_name": pattern_name
        }
    
    def _get_pattern_duration(self, pattern_name: str) -> int:
        """Get the typical duration (in candles) for different pattern types"""
        # Single candlestick patterns
        single_candle_patterns = ['Doji', 'Hammer', 'Hanging Man', 'Shooting Star', 
                                'Dragonfly Doji', 'Gravestone Doji', 'Marubozu', 'Spinning Top']
        
        # Two-candle patterns
        two_candle_patterns = ['Engulfing Pattern', 'Piercing Pattern', 'Dark Cloud Cover', 
                             'Harami Pattern', 'Harami Cross', 'Thrusting Pattern']
        
        # Three-candle patterns
        three_candle_patterns = ['Morning Star', 'Evening Star', 'Three Black Crows', 
                               'Three White Soldiers', 'Three Inside Up/Down', 'Three Outside Up/Down', 'Advance Block']
        
        if pattern_name in single_candle_patterns:
            return 1
        elif pattern_name in two_candle_patterns:
            return 2
        elif pattern_name in three_candle_patterns:
            return 3
        else:
            # Default for unknown patterns
            return 3
    
    def _get_pattern_color(self, pattern_name: str) -> str:
        """Get the highlight color for different pattern types"""
        bullish_patterns = ['Hammer', 'Morning Star', 'Piercing Pattern', 'Three White Soldiers', 
                          'Dragonfly Doji', 'Bullish Engulfing']
        bearish_patterns = ['Hanging Man', 'Evening Star', 'Dark Cloud Cover', 'Three Black Crows', 
                          'Gravestone Doji', 'Bearish Engulfing', 'Shooting Star']
        
        if any(bullish in pattern_name for bullish in bullish_patterns):
            return "#10B981"  # Green for bullish
        elif any(bearish in pattern_name for bearish in bearish_patterns):
            return "#EF4444"  # Red for bearish
        else:
            return "#F59E0B"  # Amber for neutral/other
    
    
    def analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Main method to analyze all patterns"""
        if df is None or df.empty:
            return {"patterns": [], "market_data": []}
        
        # Detect all pattern types
        candlestick_patterns = self.detect_candlestick_patterns(df)
        chart_patterns = self.detect_chart_patterns(df)
        
        # Combine all patterns
        all_patterns = candlestick_patterns + chart_patterns
        
        # Sort by confidence
        all_patterns.sort(key=lambda x: x['confidence'], reverse=True)
        
        # Convert DataFrame to market data format
        market_data = []
        for timestamp, row in df.iterrows():
            market_data.append({
                "timestamp": timestamp.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close'])
            })
        
        return {
            "patterns": all_patterns,
            "market_data": market_data,
            "strongest_pattern": all_patterns[0] if all_patterns else None
        }

# Global detector instance
pattern_detector = PatternDetector()