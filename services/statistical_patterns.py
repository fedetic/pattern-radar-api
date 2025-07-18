"""
Statistical Pattern Detection Module
Detects 20 different statistical and indicator-based trading patterns
"""

try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False
    print("Warning: ta-lib not available for statistical patterns")

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

class StatisticalPatternDetector:
    def __init__(self):
        self.patterns = []
    
    def detect_statistical_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Main method to detect all statistical patterns"""
        patterns = []
        
        if len(df) < 30:
            return patterns
        
        # Calculate required indicators
        df = self._calculate_indicators(df)
        
        patterns.extend(self._detect_bollinger_band_patterns(df))
        patterns.extend(self._detect_rsi_patterns(df))
        patterns.extend(self._detect_macd_patterns(df))
        patterns.extend(self._detect_stochastic_patterns(df))
        patterns.extend(self._detect_williams_r_patterns(df))
        patterns.extend(self._detect_momentum_patterns(df))
        patterns.extend(self._detect_cci_patterns(df))
        patterns.extend(self._detect_atr_patterns(df))
        patterns.extend(self._detect_adx_patterns(df))
        patterns.extend(self._detect_parabolic_sar_patterns(df))
        patterns.extend(self._detect_aroon_patterns(df))
        patterns.extend(self._detect_mfi_patterns(df))
        patterns.extend(self._detect_obv_patterns(df))
        patterns.extend(self._detect_ultimate_oscillator_patterns(df))
        patterns.extend(self._detect_trix_patterns(df))
        patterns.extend(self._detect_dmi_patterns(df))
        patterns.extend(self._detect_roc_patterns(df))
        patterns.extend(self._detect_ichimoku_patterns(df))
        patterns.extend(self._detect_keltner_channel_patterns(df))
        patterns.extend(self._detect_donchian_channel_patterns(df))
        
        return patterns
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all required technical indicators"""
        df = df.copy()
        
        # Add volume if missing
        if 'volume' not in df.columns:
            df['volume'] = 0
        
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        open_prices = df['open'].values
        volume = df['volume'].values
        
        if TALIB_AVAILABLE:
            try:
                # Bollinger Bands
                df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(close, timeperiod=20)
                
                # RSI
                df['rsi'] = talib.RSI(close, timeperiod=14)
                
                # MACD
                df['macd'], df['macd_signal'], df['macd_histogram'] = talib.MACD(close)
                
                # Stochastic
                df['stoch_k'], df['stoch_d'] = talib.STOCH(high, low, close)
                
                # Williams %R
                df['williams_r'] = talib.WILLR(high, low, close, timeperiod=14)
                
                # Momentum
                df['momentum'] = talib.MOM(close, timeperiod=10)
                
                # CCI
                df['cci'] = talib.CCI(high, low, close, timeperiod=14)
                
                # ATR
                df['atr'] = talib.ATR(high, low, close, timeperiod=14)
                
                # ADX
                df['adx'] = talib.ADX(high, low, close, timeperiod=14)
                
                # Parabolic SAR
                df['sar'] = talib.SAR(high, low)
                
                # Aroon
                df['aroon_up'], df['aroon_down'] = talib.AROON(high, low, timeperiod=14)
                
                # MFI
                df['mfi'] = talib.MFI(high, low, close, volume, timeperiod=14)
                
                # OBV
                df['obv'] = talib.OBV(close, volume)
                
                # Ultimate Oscillator
                df['ult_osc'] = talib.ULTOSC(high, low, close)
                
                # TRIX
                df['trix'] = talib.TRIX(close, timeperiod=14)
                
                # DMI
                df['plus_di'] = talib.PLUS_DI(high, low, close, timeperiod=14)
                df['minus_di'] = talib.MINUS_DI(high, low, close, timeperiod=14)
                
                # ROC
                df['roc'] = talib.ROC(close, timeperiod=10)
                
                # Moving averages for Ichimoku
                df['tenkan'] = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
                df['kijun'] = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
                
                # Keltner Channels
                df['kc_middle'] = df['close'].rolling(20).mean()
                df['kc_upper'] = df['kc_middle'] + (2 * df['atr'])
                df['kc_lower'] = df['kc_middle'] - (2 * df['atr'])
                
                # Donchian Channels
                df['dc_upper'] = df['high'].rolling(20).max()
                df['dc_lower'] = df['low'].rolling(20).min()
                df['dc_middle'] = (df['dc_upper'] + df['dc_lower']) / 2
                
            except Exception as e:
                print(f"Error calculating TA-Lib indicators: {e}")
                self._calculate_fallback_indicators(df)
        else:
            self._calculate_fallback_indicators(df)
        
        return df
    
    def _calculate_fallback_indicators(self, df: pd.DataFrame):
        """Calculate simplified indicators when TA-Lib is not available"""
        # Simple RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Simple Bollinger Bands
        df['bb_middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['bb_upper'] = df['bb_middle'] + (2 * bb_std)
        df['bb_lower'] = df['bb_middle'] - (2 * bb_std)
        
        # Simple MACD
        ema12 = df['close'].ewm(span=12).mean()
        ema26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
    
    def _detect_bollinger_band_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Bollinger Band patterns"""
        patterns = []
        
        if 'bb_upper' not in df.columns:
            return patterns
        
        current_price = df['close'].iloc[-1]
        bb_upper = df['bb_upper'].iloc[-1]
        bb_lower = df['bb_lower'].iloc[-1]
        bb_middle = df['bb_middle'].iloc[-1]
        
        # Bollinger Band Squeeze
        band_width = (bb_upper - bb_lower) / bb_middle
        avg_band_width = ((df['bb_upper'] - df['bb_lower']) / df['bb_middle']).rolling(20).mean().iloc[-1]
        
        if band_width < avg_band_width * 0.5:
            patterns.append({
                "name": "Bollinger Band Squeeze",
                "category": "Statistical",
                "confidence": 75,
                "direction": "neutral",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "bb_squeeze"),
                "description": "Low volatility squeeze, breakout expected"
            })
        
        # Bollinger Band Breakout
        if current_price > bb_upper:
            patterns.append({
                "name": "Bollinger Upper Breakout",
                "category": "Statistical",
                "confidence": 80,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "bb_breakout"),
                "description": "Price broke above upper Bollinger Band"
            })
        elif current_price < bb_lower:
            patterns.append({
                "name": "Bollinger Lower Breakout",
                "category": "Statistical",
                "confidence": 80,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "bb_breakout"),
                "description": "Price broke below lower Bollinger Band"
            })
        
        # Bollinger Band Bounce
        prev_price = df['close'].iloc[-2]
        if prev_price <= bb_lower and current_price > bb_lower:
            patterns.append({
                "name": "Bollinger Band Bounce",
                "category": "Statistical",
                "confidence": 72,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "bb_bounce"),
                "description": "Bullish bounce off lower Bollinger Band"
            })
        elif prev_price >= bb_upper and current_price < bb_upper:
            patterns.append({
                "name": "Bollinger Band Bounce",
                "category": "Statistical",
                "confidence": 72,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "bb_bounce"),
                "description": "Bearish bounce off upper Bollinger Band"
            })
        
        return patterns
    
    def _detect_rsi_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect RSI patterns"""
        patterns = []
        
        if 'rsi' not in df.columns:
            return patterns
        
        current_rsi = df['rsi'].iloc[-1]
        
        # RSI Overbought/Oversold
        if current_rsi > 70:
            patterns.append({
                "name": "RSI Overbought",
                "category": "Statistical",
                "confidence": 68,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "rsi_overbought"),
                "description": f"RSI at {current_rsi:.1f} indicates overbought conditions"
            })
        elif current_rsi < 30:
            patterns.append({
                "name": "RSI Oversold",
                "category": "Statistical",
                "confidence": 68,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "rsi_oversold"),
                "description": f"RSI at {current_rsi:.1f} indicates oversold conditions"
            })
        
        # RSI Divergence
        if len(df) >= 20:
            price_trend = df['close'].iloc[-10:].diff().mean()
            rsi_trend = df['rsi'].iloc[-10:].diff().mean()
            
            if price_trend > 0 and rsi_trend < 0:
                patterns.append({
                    "name": "RSI Bearish Divergence",
                    "category": "Statistical",
                    "confidence": 78,
                    "direction": "bearish",
                    "coordinates": self._get_statistical_coordinates(df, len(df)-1, "rsi_divergence"),
                    "description": "Price making higher highs while RSI making lower highs"
                })
            elif price_trend < 0 and rsi_trend > 0:
                patterns.append({
                    "name": "RSI Bullish Divergence",
                    "category": "Statistical",
                    "confidence": 78,
                    "direction": "bullish",
                    "coordinates": self._get_statistical_coordinates(df, len(df)-1, "rsi_divergence"),
                    "description": "Price making lower lows while RSI making higher lows"
                })
        
        return patterns
    
    def _detect_macd_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect MACD patterns"""
        patterns = []
        
        if 'macd' not in df.columns:
            return patterns
        
        current_macd = df['macd'].iloc[-1]
        current_signal = df['macd_signal'].iloc[-1]
        prev_macd = df['macd'].iloc[-2]
        prev_signal = df['macd_signal'].iloc[-2]
        
        # MACD Crossover
        if prev_macd <= prev_signal and current_macd > current_signal:
            patterns.append({
                "name": "MACD Bullish Crossover",
                "category": "Statistical",
                "confidence": 75,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "macd_crossover"),
                "description": "MACD line crossed above signal line"
            })
        elif prev_macd >= prev_signal and current_macd < current_signal:
            patterns.append({
                "name": "MACD Bearish Crossover",
                "category": "Statistical",
                "confidence": 75,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "macd_crossover"),
                "description": "MACD line crossed below signal line"
            })
        
        # MACD Zero Line Cross
        if prev_macd <= 0 and current_macd > 0:
            patterns.append({
                "name": "MACD Zero Line Cross",
                "category": "Statistical",
                "confidence": 70,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "macd_zero_cross"),
                "description": "MACD crossed above zero line"
            })
        elif prev_macd >= 0 and current_macd < 0:
            patterns.append({
                "name": "MACD Zero Line Cross",
                "category": "Statistical",
                "confidence": 70,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "macd_zero_cross"),
                "description": "MACD crossed below zero line"
            })
        
        return patterns
    
    def _detect_stochastic_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Stochastic patterns"""
        patterns = []
        
        if 'stoch_k' not in df.columns:
            return patterns
        
        current_k = df['stoch_k'].iloc[-1] if not pd.isna(df['stoch_k'].iloc[-1]) else 50
        current_d = df['stoch_d'].iloc[-1] if not pd.isna(df['stoch_d'].iloc[-1]) else 50
        
        # Stochastic Overbought/Oversold
        if current_k > 80 and current_d > 80:
            patterns.append({
                "name": "Stochastic Overbought",
                "category": "Statistical",
                "confidence": 65,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "stoch_overbought"),
                "description": "Stochastic in overbought territory"
            })
        elif current_k < 20 and current_d < 20:
            patterns.append({
                "name": "Stochastic Oversold",
                "category": "Statistical",
                "confidence": 65,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "stoch_oversold"),
                "description": "Stochastic in oversold territory"
            })
        
        return patterns
    
    def _detect_williams_r_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Williams %R patterns"""
        patterns = []
        
        if 'williams_r' not in df.columns:
            return patterns
        
        current_wr = df['williams_r'].iloc[-1]
        
        if pd.isna(current_wr):
            return patterns
        
        if current_wr > -20:
            patterns.append({
                "name": "Williams %R Overbought",
                "category": "Statistical",
                "confidence": 62,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "williams_overbought"),
                "description": "Williams %R indicates overbought conditions"
            })
        elif current_wr < -80:
            patterns.append({
                "name": "Williams %R Oversold",
                "category": "Statistical",
                "confidence": 62,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "williams_oversold"),
                "description": "Williams %R indicates oversold conditions"
            })
        
        return patterns
    
    def _detect_momentum_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Momentum patterns"""
        patterns = []
        
        if 'momentum' not in df.columns:
            return patterns
        
        current_momentum = df['momentum'].iloc[-1]
        prev_momentum = df['momentum'].iloc[-2]
        
        if pd.isna(current_momentum) or pd.isna(prev_momentum):
            return patterns
        
        # Momentum Direction Change
        if prev_momentum < 0 and current_momentum > 0:
            patterns.append({
                "name": "Momentum Shift Bullish",
                "category": "Statistical",
                "confidence": 70,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "momentum_shift"),
                "description": "Momentum shifted from negative to positive"
            })
        elif prev_momentum > 0 and current_momentum < 0:
            patterns.append({
                "name": "Momentum Shift Bearish",
                "category": "Statistical",
                "confidence": 70,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "momentum_shift"),
                "description": "Momentum shifted from positive to negative"
            })
        
        return patterns
    
    def _detect_cci_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect CCI patterns"""
        patterns = []
        
        if 'cci' not in df.columns:
            return patterns
        
        current_cci = df['cci'].iloc[-1]
        
        if pd.isna(current_cci):
            return patterns
        
        if current_cci > 100:
            patterns.append({
                "name": "CCI Overbought",
                "category": "Statistical",
                "confidence": 60,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "cci_overbought"),
                "description": f"CCI at {current_cci:.1f} indicates overbought"
            })
        elif current_cci < -100:
            patterns.append({
                "name": "CCI Oversold",
                "category": "Statistical",
                "confidence": 60,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "cci_oversold"),
                "description": f"CCI at {current_cci:.1f} indicates oversold"
            })
        
        return patterns
    
    def _detect_atr_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect ATR patterns"""
        patterns = []
        
        if 'atr' not in df.columns:
            return patterns
        
        current_atr = df['atr'].iloc[-1]
        avg_atr = df['atr'].rolling(20).mean().iloc[-1]
        
        if pd.isna(current_atr) or pd.isna(avg_atr):
            return patterns
        
        if current_atr > avg_atr * 1.5:
            patterns.append({
                "name": "High Volatility Alert",
                "category": "Statistical",
                "confidence": 72,
                "direction": "neutral",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "high_volatility"),
                "description": "ATR indicates unusually high volatility"
            })
        elif current_atr < avg_atr * 0.5:
            patterns.append({
                "name": "Low Volatility Alert",
                "category": "Statistical",
                "confidence": 68,
                "direction": "neutral",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "low_volatility"),
                "description": "ATR indicates unusually low volatility"
            })
        
        return patterns
    
    def _detect_adx_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect ADX patterns"""
        patterns = []
        
        if 'adx' not in df.columns:
            return patterns
        
        current_adx = df['adx'].iloc[-1]
        
        if pd.isna(current_adx):
            return patterns
        
        if current_adx > 25:
            patterns.append({
                "name": "Strong Trend Signal",
                "category": "Statistical",
                "confidence": 75,
                "direction": "neutral",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "strong_trend"),
                "description": f"ADX at {current_adx:.1f} indicates strong trend"
            })
        elif current_adx < 20:
            patterns.append({
                "name": "Weak Trend Signal",
                "category": "Statistical",
                "confidence": 65,
                "direction": "neutral",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "weak_trend"),
                "description": f"ADX at {current_adx:.1f} indicates weak trend"
            })
        
        return patterns
    
    def _detect_parabolic_sar_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Detect Parabolic SAR patterns"""
        patterns = []
        
        if 'sar' not in df.columns:
            return patterns
        
        current_price = df['close'].iloc[-1]
        current_sar = df['sar'].iloc[-1]
        prev_sar = df['sar'].iloc[-2]
        
        if pd.isna(current_sar) or pd.isna(prev_sar):
            return patterns
        
        # SAR Flip
        if prev_sar > df['close'].iloc[-2] and current_sar < current_price:
            patterns.append({
                "name": "Parabolic SAR Bullish",
                "category": "Statistical",
                "confidence": 73,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "sar_flip"),
                "description": "Parabolic SAR flipped to bullish"
            })
        elif prev_sar < df['close'].iloc[-2] and current_sar > current_price:
            patterns.append({
                "name": "Parabolic SAR Bearish",
                "category": "Statistical",
                "confidence": 73,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, "sar_flip"),
                "description": "Parabolic SAR flipped to bearish"
            })
        
        return patterns
    
    # Add simplified versions of remaining pattern detectors
    def _detect_aroon_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._generic_pattern_detector(df, "Aroon Signal", "aroon_up", 70)
    
    def _detect_mfi_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._generic_pattern_detector(df, "MFI Signal", "mfi", 80, 20)
    
    def _detect_obv_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._trend_pattern_detector(df, "OBV Trend", "obv")
    
    def _detect_ultimate_oscillator_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._generic_pattern_detector(df, "Ultimate Oscillator", "ult_osc", 70, 30)
    
    def _detect_trix_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._zero_line_cross_detector(df, "TRIX Signal", "trix")
    
    def _detect_dmi_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._crossover_detector(df, "DMI Signal", "plus_di", "minus_di")
    
    def _detect_roc_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._zero_line_cross_detector(df, "ROC Signal", "roc")
    
    def _detect_ichimoku_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._crossover_detector(df, "Ichimoku Signal", "tenkan", "kijun")
    
    def _detect_keltner_channel_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._channel_pattern_detector(df, "Keltner Channel", "kc_upper", "kc_lower")
    
    def _detect_donchian_channel_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        return self._channel_pattern_detector(df, "Donchian Channel", "dc_upper", "dc_lower")
    
    def _generic_pattern_detector(self, df: pd.DataFrame, name: str, column: str, overbought: float = 70, oversold: float = 30) -> List[Dict[str, Any]]:
        """Generic overbought/oversold pattern detector"""
        patterns = []
        if column not in df.columns or pd.isna(df[column].iloc[-1]):
            return patterns
        
        value = df[column].iloc[-1]
        if value > overbought:
            patterns.append({
                "name": f"{name} Overbought",
                "category": "Statistical",
                "confidence": 60,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, f"{column}_overbought"),
                "description": f"{name} indicates overbought conditions"
            })
        elif value < oversold:
            patterns.append({
                "name": f"{name} Oversold", 
                "category": "Statistical",
                "confidence": 60,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, f"{column}_oversold"),
                "description": f"{name} indicates oversold conditions"
            })
        
        return patterns
    
    def _trend_pattern_detector(self, df: pd.DataFrame, name: str, column: str) -> List[Dict[str, Any]]:
        """Generic trend pattern detector"""
        patterns = []
        if column not in df.columns or len(df) < 10:
            return patterns
        
        trend = df[column].iloc[-5:].diff().mean()
        if not pd.isna(trend):
            direction = "bullish" if trend > 0 else "bearish"
            patterns.append({
                "name": f"{name} {direction.capitalize()}",
                "category": "Statistical",
                "confidence": 65,
                "direction": direction,
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, f"{column}_trend"),
                "description": f"{name} shows {direction} trend"
            })
        
        return patterns
    
    def _zero_line_cross_detector(self, df: pd.DataFrame, name: str, column: str) -> List[Dict[str, Any]]:
        """Generic zero line cross detector"""
        patterns = []
        if column not in df.columns or len(df) < 2:
            return patterns
        
        current = df[column].iloc[-1]
        previous = df[column].iloc[-2]
        
        if pd.isna(current) or pd.isna(previous):
            return patterns
        
        if previous <= 0 and current > 0:
            patterns.append({
                "name": f"{name} Bullish Cross",
                "category": "Statistical",
                "confidence": 67,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, f"{column}_cross"),
                "description": f"{name} crossed above zero line"
            })
        elif previous >= 0 and current < 0:
            patterns.append({
                "name": f"{name} Bearish Cross",
                "category": "Statistical",
                "confidence": 67,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, f"{column}_cross"),
                "description": f"{name} crossed below zero line"
            })
        
        return patterns
    
    def _crossover_detector(self, df: pd.DataFrame, name: str, fast_col: str, slow_col: str) -> List[Dict[str, Any]]:
        """Generic crossover detector"""
        patterns = []
        if fast_col not in df.columns or slow_col not in df.columns or len(df) < 2:
            return patterns
        
        current_fast = df[fast_col].iloc[-1]
        current_slow = df[slow_col].iloc[-1]
        prev_fast = df[fast_col].iloc[-2]
        prev_slow = df[slow_col].iloc[-2]
        
        if any(pd.isna(val) for val in [current_fast, current_slow, prev_fast, prev_slow]):
            return patterns
        
        if prev_fast <= prev_slow and current_fast > current_slow:
            patterns.append({
                "name": f"{name} Bullish Cross",
                "category": "Statistical",
                "confidence": 70,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, f"{fast_col}_{slow_col}_cross"),
                "description": f"{name} bullish crossover signal"
            })
        elif prev_fast >= prev_slow and current_fast < current_slow:
            patterns.append({
                "name": f"{name} Bearish Cross",
                "category": "Statistical",
                "confidence": 70,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, f"{fast_col}_{slow_col}_cross"),
                "description": f"{name} bearish crossover signal"
            })
        
        return patterns
    
    def _channel_pattern_detector(self, df: pd.DataFrame, name: str, upper_col: str, lower_col: str) -> List[Dict[str, Any]]:
        """Generic channel pattern detector"""
        patterns = []
        if upper_col not in df.columns or lower_col not in df.columns:
            return patterns
        
        current_price = df['close'].iloc[-1]
        upper_band = df[upper_col].iloc[-1]
        lower_band = df[lower_col].iloc[-1]
        
        if any(pd.isna(val) for val in [current_price, upper_band, lower_band]):
            return patterns
        
        if current_price > upper_band:
            patterns.append({
                "name": f"{name} Upper Breakout",
                "category": "Statistical",
                "confidence": 72,
                "direction": "bullish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, f"{upper_col}_breakout"),
                "description": f"Price broke above {name} upper band"
            })
        elif current_price < lower_band:
            patterns.append({
                "name": f"{name} Lower Breakout",
                "category": "Statistical",
                "confidence": 72,
                "direction": "bearish",
                "coordinates": self._get_statistical_coordinates(df, len(df)-1, f"{lower_col}_breakout"),
                "description": f"Price broke below {name} lower band"
            })
        
        return patterns
    
    def _get_statistical_coordinates(self, df: pd.DataFrame, index: int, pattern_type: str) -> Dict[str, Any]:
        """Get coordinates for statistical pattern visualization"""
        return {
            "type": "statistical_pattern",
            "pattern_type": pattern_type,
            "index": int(index),
            "timestamp": df.index[index].isoformat(),
            "price": float(df['close'].iloc[index]),
            "highlight_color": self._get_statistical_pattern_color(pattern_type)
        }
    
    def _get_statistical_pattern_color(self, pattern_type: str) -> str:
        """Get color for statistical pattern types"""
        if "bullish" in pattern_type or "oversold" in pattern_type:
            return "#2ECC71"
        elif "bearish" in pattern_type or "overbought" in pattern_type:
            return "#E74C3C"
        else:
            return "#F39C12"

# Global instance
statistical_detector = StatisticalPatternDetector()