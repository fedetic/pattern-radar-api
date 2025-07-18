"""
Volume Pattern Detection Module
Detects 15 different volume-based trading patterns
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

class VolumePatternDetector:
    def __init__(self):
        self.patterns = []
    
    def detect_volume_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Main method to detect all volume patterns"""
        patterns = []
        
        if len(df) < 5:
            print(f"Volume patterns: insufficient data ({len(df)} points)")
            return patterns
        
        # Add volume column if missing (use reasonable defaults)
        if 'volume' not in df.columns:
            df['volume'] = 1000  # Use reasonable default instead of 0
            print("Volume patterns: using default volume data")
        
        # Check if volume data is meaningful
        if df['volume'].sum() == 0:
            df['volume'] = 1000  # Set reasonable default
            print("Volume patterns: volume data was zero, using defaults")
        
        try:
            # Calculate volume moving averages
            df = df.copy()
            df['volume_ma_20'] = df['volume'].rolling(window=min(20, len(df))).mean()
            df['volume_ma_50'] = df['volume'].rolling(window=min(50, len(df))).mean()
            df['price_change'] = df['close'].pct_change()
            
            patterns.extend(self._detect_volume_spike(df))
            patterns.extend(self._detect_volume_breakout(df))
            patterns.extend(self._detect_accumulation_distribution(df))
            patterns.extend(self._detect_volume_climax(df))
            patterns.extend(self._detect_low_volume_pullback(df))
            patterns.extend(self._detect_volume_confirmation(df))
            patterns.extend(self._detect_volume_divergence(df))
            patterns.extend(self._detect_high_volume_reversal(df))
            patterns.extend(self._detect_volume_thrust(df))
            patterns.extend(self._detect_volume_drying_up(df))
            patterns.extend(self._detect_volume_expansion(df))
            patterns.extend(self._detect_volume_contraction(df))
            patterns.extend(self._detect_on_balance_volume_trend(df))
            patterns.extend(self._detect_volume_price_trend(df))
            patterns.extend(self._detect_heavy_volume_rejection(df))
            
            print(f"Volume patterns detected: {len(patterns)}")
            return patterns
            
        except Exception as e:
            print(f"Error in volume pattern detection: {e}")
            return []
    
    def _detect_volume_spike(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect abnormally high volume spikes"""
        patterns = []
        
        # Look for volume > 2x average volume
        recent_volume = df['volume'].iloc[-1]
        avg_volume = df['volume_ma_20'].iloc[-1]
        
        if recent_volume > 2 * avg_volume and avg_volume > 0:
            price_change = df['price_change'].iloc[-1]
            direction = "bullish" if price_change > 0 else "bearish"
            
            patterns.append({
                "name": "Volume Spike",
                "category": "Volume",
                "confidence": min(85, int((recent_volume / avg_volume) * 30)),
                "direction": direction,
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "spike"),
                "description": f"Abnormal volume spike with {direction} price movement"
            })
        
        return patterns
    
    def _detect_volume_breakout(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume breakout patterns"""
        patterns = []
        
        if len(df) < 5:
            return patterns
        
        # Check for price breakout with volume confirmation
        recent_high = df['high'].rolling(window=20).max().iloc[-1]
        current_price = df['close'].iloc[-1]
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume_ma_20'].iloc[-1]
        
        if current_price >= recent_high * 0.99 and current_volume > 1.5 * avg_volume:
            patterns.append({
                "name": "Volume Breakout",
                "category": "Volume",
                "confidence": 80,
                "direction": "bullish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "breakout"),
                "description": "Price breakout confirmed by increased volume"
            })
        
        return patterns
    
    def _detect_accumulation_distribution(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect accumulation/distribution patterns"""
        patterns = []
        
        if len(df) < 10:
            return patterns
        
        # Calculate basic A/D line
        df_copy = df.copy()
        df_copy['ad_line'] = ((df_copy['close'] - df_copy['low']) - (df_copy['high'] - df_copy['close'])) / (df_copy['high'] - df_copy['low']) * df_copy['volume']
        df_copy['ad_line'] = df_copy['ad_line'].fillna(0).cumsum()
        
        # Check trend in A/D line vs price
        ad_trend = df_copy['ad_line'].iloc[-5:].diff().mean()
        price_trend = df_copy['close'].iloc[-5:].diff().mean()
        
        if ad_trend > 0 and price_trend > 0:
            patterns.append({
                "name": "Accumulation Pattern",
                "category": "Volume",
                "confidence": 75,
                "direction": "bullish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "accumulation"),
                "description": "Volume shows accumulation supporting price rise"
            })
        elif ad_trend < 0 and price_trend < 0:
            patterns.append({
                "name": "Distribution Pattern",
                "category": "Volume",
                "confidence": 75,
                "direction": "bearish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "distribution"),
                "description": "Volume shows distribution supporting price decline"
            })
        
        return patterns
    
    def _detect_volume_climax(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume climax patterns"""
        patterns = []
        
        current_volume = df['volume'].iloc[-1]
        max_volume_20 = df['volume'].rolling(window=20).max().iloc[-1]
        price_change = df['price_change'].iloc[-1]
        
        if current_volume >= max_volume_20 * 0.95 and abs(price_change) > 0.03:
            direction = "bearish" if price_change > 0 else "bullish"  # Climax often signals reversal
            
            patterns.append({
                "name": "Volume Climax",
                "category": "Volume",
                "confidence": 82,
                "direction": direction,
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "climax"),
                "description": "Extreme volume climax suggesting potential reversal"
            })
        
        return patterns
    
    def _detect_low_volume_pullback(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect low volume pullback patterns"""
        patterns = []
        
        if len(df) < 5:
            return patterns
        
        # Check for declining volume during pullback
        recent_volumes = df['volume'].iloc[-5:]
        recent_prices = df['close'].iloc[-5:]
        avg_volume = df['volume_ma_20'].iloc[-1]
        
        volume_declining = recent_volumes.iloc[-1] < recent_volumes.iloc[0]
        price_pullback = recent_prices.iloc[-1] < recent_prices.iloc[0]
        low_volume = recent_volumes.iloc[-1] < avg_volume * 0.7
        
        if volume_declining and price_pullback and low_volume:
            patterns.append({
                "name": "Low Volume Pullback",
                "category": "Volume",
                "confidence": 70,
                "direction": "bullish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "pullback"),
                "description": "Healthy pullback on declining volume suggests continuation"
            })
        
        return patterns
    
    def _detect_volume_confirmation(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume confirmation patterns"""
        patterns = []
        
        if len(df) < 3:
            return patterns
        
        price_trend = df['close'].iloc[-3:].diff().mean()
        volume_trend = df['volume'].iloc[-3:].diff().mean()
        
        if price_trend > 0 and volume_trend > 0:
            patterns.append({
                "name": "Volume Confirmation",
                "category": "Volume",
                "confidence": 78,
                "direction": "bullish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "confirmation"),
                "description": "Rising volume confirms upward price movement"
            })
        elif price_trend < 0 and volume_trend > 0:
            patterns.append({
                "name": "Volume Confirmation",
                "category": "Volume",
                "confidence": 78,
                "direction": "bearish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "confirmation"),
                "description": "Rising volume confirms downward price movement"
            })
        
        return patterns
    
    def _detect_volume_divergence(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume divergence patterns"""
        patterns = []
        
        if len(df) < 10:
            return patterns
        
        # Compare recent volume vs price trends
        price_trend_recent = df['close'].iloc[-5:].diff().mean()
        volume_trend_recent = df['volume'].iloc[-5:].diff().mean()
        
        # Bearish divergence: price up, volume down
        if price_trend_recent > 0 and volume_trend_recent < 0:
            patterns.append({
                "name": "Volume Divergence",
                "category": "Volume",
                "confidence": 72,
                "direction": "bearish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "divergence"),
                "description": "Bearish divergence: price rising but volume declining"
            })
        # Bullish divergence: price down, volume up
        elif price_trend_recent < 0 and volume_trend_recent > 0:
            patterns.append({
                "name": "Volume Divergence",
                "category": "Volume",
                "confidence": 72,
                "direction": "bullish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "divergence"),
                "description": "Bullish divergence: price falling but volume increasing"
            })
        
        return patterns
    
    def _detect_high_volume_reversal(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect high volume reversal patterns"""
        patterns = []
        
        if len(df) < 2:
            return patterns
        
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume_ma_20'].iloc[-1]
        price_change_today = df['price_change'].iloc[-1]
        price_change_yesterday = df['price_change'].iloc[-2]
        
        # High volume reversal
        if (current_volume > 1.8 * avg_volume and 
            price_change_today * price_change_yesterday < 0 and 
            abs(price_change_today) > 0.02):
            
            direction = "bullish" if price_change_today > 0 else "bearish"
            patterns.append({
                "name": "High Volume Reversal",
                "category": "Volume",
                "confidence": 85,
                "direction": direction,
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "reversal"),
                "description": f"High volume {direction} reversal pattern"
            })
        
        return patterns
    
    def _detect_volume_thrust(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume thrust patterns"""
        patterns = []
        
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume_ma_20'].iloc[-1]
        price_change = df['price_change'].iloc[-1]
        
        if current_volume > 2.5 * avg_volume and price_change > 0.04:
            patterns.append({
                "name": "Volume Thrust",
                "category": "Volume",
                "confidence": 88,
                "direction": "bullish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "thrust"),
                "description": "Powerful upward thrust on exceptional volume"
            })
        
        return patterns
    
    def _detect_volume_drying_up(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume drying up patterns"""
        patterns = []
        
        if len(df) < 10:
            return patterns
        
        recent_avg_volume = df['volume'].iloc[-5:].mean()
        historical_avg_volume = df['volume'].iloc[-20:-5].mean()
        
        if recent_avg_volume < historical_avg_volume * 0.6 and historical_avg_volume > 0:
            patterns.append({
                "name": "Volume Drying Up",
                "category": "Volume",
                "confidence": 68,
                "direction": "neutral",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "drying"),
                "description": "Volume drying up suggests potential breakout preparation"
            })
        
        return patterns
    
    def _detect_volume_expansion(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume expansion patterns"""
        patterns = []
        
        if len(df) < 10:
            return patterns
        
        recent_avg_volume = df['volume'].iloc[-5:].mean()
        historical_avg_volume = df['volume'].iloc[-20:-5].mean()
        
        if recent_avg_volume > historical_avg_volume * 1.4 and historical_avg_volume > 0:
            price_trend = df['close'].iloc[-5:].diff().mean()
            direction = "bullish" if price_trend > 0 else "bearish"
            
            patterns.append({
                "name": "Volume Expansion",
                "category": "Volume",
                "confidence": 75,
                "direction": direction,
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "expansion"),
                "description": f"Volume expansion supporting {direction} move"
            })
        
        return patterns
    
    def _detect_volume_contraction(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect volume contraction patterns"""
        patterns = []
        
        if len(df) < 10:
            return patterns
        
        recent_volumes = df['volume'].iloc[-5:]
        volume_decreasing = all(recent_volumes.iloc[i] <= recent_volumes.iloc[i-1] for i in range(1, len(recent_volumes)))
        
        if volume_decreasing:
            patterns.append({
                "name": "Volume Contraction",
                "category": "Volume", 
                "confidence": 65,
                "direction": "neutral",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "contraction"),
                "description": "Systematic volume contraction suggests consolidation"
            })
        
        return patterns
    
    def _detect_on_balance_volume_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect On-Balance Volume trend patterns"""
        patterns = []
        
        if len(df) < 15:
            return patterns
        
        # Calculate OBV
        df_copy = df.copy()
        df_copy['obv'] = 0
        for i in range(1, len(df_copy)):
            if df_copy['close'].iloc[i] > df_copy['close'].iloc[i-1]:
                df_copy['obv'].iloc[i] = df_copy['obv'].iloc[i-1] + df_copy['volume'].iloc[i]
            elif df_copy['close'].iloc[i] < df_copy['close'].iloc[i-1]:
                df_copy['obv'].iloc[i] = df_copy['obv'].iloc[i-1] - df_copy['volume'].iloc[i]
            else:
                df_copy['obv'].iloc[i] = df_copy['obv'].iloc[i-1]
        
        # Check OBV trend
        obv_trend = df_copy['obv'].iloc[-10:].diff().mean()
        price_trend = df_copy['close'].iloc[-10:].diff().mean()
        
        if obv_trend > 0 and price_trend > 0:
            patterns.append({
                "name": "OBV Bullish Trend",
                "category": "Volume",
                "confidence": 77,
                "direction": "bullish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "obv_trend"),
                "description": "On-Balance Volume confirms bullish price trend"
            })
        elif obv_trend < 0 and price_trend < 0:
            patterns.append({
                "name": "OBV Bearish Trend", 
                "category": "Volume",
                "confidence": 77,
                "direction": "bearish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "obv_trend"),
                "description": "On-Balance Volume confirms bearish price trend"
            })
        
        return patterns
    
    def _detect_volume_price_trend(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Volume Price Trend (VPT) patterns"""
        patterns = []
        
        if len(df) < 15:
            return patterns
        
        # Calculate VPT
        df_copy = df.copy()
        df_copy['vpt'] = df_copy['volume'] * df_copy['price_change'].fillna(0)
        df_copy['vpt'] = df_copy['vpt'].cumsum()
        
        # Check VPT trend vs price trend
        vpt_trend = df_copy['vpt'].iloc[-10:].diff().mean()
        price_trend = df_copy['close'].iloc[-10:].diff().mean()
        
        if vpt_trend > 0 and price_trend > 0:
            patterns.append({
                "name": "VPT Confirmation",
                "category": "Volume",
                "confidence": 73,
                "direction": "bullish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "vpt"),
                "description": "Volume Price Trend confirms bullish momentum"
            })
        elif vpt_trend < 0 and price_trend < 0:
            patterns.append({
                "name": "VPT Confirmation",
                "category": "Volume",
                "confidence": 73,
                "direction": "bearish",
                "coordinates": self._get_volume_coordinates(df, len(df)-1, "vpt"),
                "description": "Volume Price Trend confirms bearish momentum"
            })
        
        return patterns
    
    def _detect_heavy_volume_rejection(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect heavy volume rejection patterns"""
        patterns = []
        
        if len(df) < 2:
            return patterns
        
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume_ma_20'].iloc[-1]
        
        # High volume day with long wick (rejection)
        current_candle = df.iloc[-1]
        body_size = abs(current_candle['close'] - current_candle['open'])
        upper_wick = current_candle['high'] - max(current_candle['close'], current_candle['open'])
        lower_wick = min(current_candle['close'], current_candle['open']) - current_candle['low']
        
        if current_volume > 1.5 * avg_volume:
            if upper_wick > 2 * body_size:
                patterns.append({
                    "name": "Heavy Volume Rejection",
                    "category": "Volume",
                    "confidence": 80,
                    "direction": "bearish",
                    "coordinates": self._get_volume_coordinates(df, len(df)-1, "rejection"),
                    "description": "Heavy volume rejection at higher levels"
                })
            elif lower_wick > 2 * body_size:
                patterns.append({
                    "name": "Heavy Volume Rejection",
                    "category": "Volume",
                    "confidence": 80,
                    "direction": "bullish", 
                    "coordinates": self._get_volume_coordinates(df, len(df)-1, "rejection"),
                    "description": "Heavy volume rejection at lower levels"
                })
        
        return patterns
    
    def _get_volume_coordinates(self, df: pd.DataFrame, index: int, pattern_type: str) -> Dict[str, Any]:
        """Get coordinates for volume pattern visualization"""
        return {
            "type": "volume_pattern",
            "pattern_type": pattern_type,
            "index": int(index),
            "timestamp": df.index[index].isoformat(),
            "volume": float(df['volume'].iloc[index]),
            "volume_ma_20": float(df['volume_ma_20'].iloc[index]) if 'volume_ma_20' in df.columns else 0,
            "price": float(df['close'].iloc[index]),
            "highlight_color": self._get_volume_pattern_color(pattern_type)
        }
    
    def _get_volume_pattern_color(self, pattern_type: str) -> str:
        """Get color for volume pattern types"""
        color_map = {
            "spike": "#FF6B6B",
            "breakout": "#4ECDC4", 
            "accumulation": "#45B7D1",
            "distribution": "#96CEB4",
            "climax": "#FFEAA7",
            "pullback": "#DDA0DD",
            "confirmation": "#98D8C8",
            "divergence": "#F7DC6F",
            "reversal": "#BB8FCE",
            "thrust": "#85C1E9",
            "drying": "#F8C471",
            "expansion": "#82E0AA",
            "contraction": "#F1948A",
            "obv_trend": "#AED6F1",
            "vpt": "#A9DFBF",
            "rejection": "#F5B7B1"
        }
        return color_map.get(pattern_type, "#BDC3C7")

# Global instance
volume_detector = VolumePatternDetector()