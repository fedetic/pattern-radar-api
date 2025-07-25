"""
Seed data for pattern types table
Contains comprehensive pattern definitions with metadata
"""

from typing import List, Dict, Any

PATTERN_TYPES_DATA: List[Dict[str, Any]] = [
    # Candlestick Patterns (36 patterns)
    {
        "name": "Doji",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 1,
        "description": "A candle with virtually the same opening and closing price, indicating market indecision.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Hammer",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 1,
        "description": "A small body with a long lower shadow, appearing after a downtrend.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Hanging Man",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 1,
        "description": "Similar to hammer but appears after an uptrend, signaling potential bearish reversal.",
        "reliability_score": 75,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Shooting Star",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 1,
        "description": "Small body with long upper shadow after an uptrend, showing rejection at higher levels.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Engulfing Pattern",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 2,
        "description": "A large candle that completely engulfs the previous candle's body.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Morning Star",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 3,
        "description": "Three-candle bullish reversal pattern: bearish candle, small-bodied candle, then bullish candle.",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Evening Star",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 3,
        "description": "Three-candle bearish reversal pattern: bullish candle, small-bodied candle, then bearish candle.",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Three Black Crows",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 3,
        "description": "Three consecutive bearish candles with progressively lower closes.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": True
    },
    {
        "name": "Three White Soldiers",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 3,
        "description": "Three consecutive bullish candles with progressively higher closes.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": True
    },
    {
        "name": "Dragonfly Doji",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 1,
        "description": "A candle with long lower shadow, no upper shadow, and open/close at or near the high.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Gravestone Doji",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 1,
        "description": "A candle with long upper shadow, no lower shadow, and open/close at or near the low.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Marubozu",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 1,
        "description": "A large candle with no shadows, indicating strong directional momentum.",
        "reliability_score": 85,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Spinning Top",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 1,
        "description": "A candle with small body and long shadows on both sides, indicating market indecision.",
        "reliability_score": 65,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Piercing Pattern",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 2,
        "description": "Two-candle bullish reversal: bearish candle followed by bullish candle that opens below and closes above midpoint.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Dark Cloud Cover",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 2,
        "description": "Two-candle bearish reversal: bullish candle followed by bearish candle that opens above and closes below midpoint.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Harami Pattern",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 2,
        "description": "Large candle followed by smaller candle contained within the first candle's body.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Harami Cross",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 2,
        "description": "A harami pattern where the second candle is a doji, indicating stronger reversal signal.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Thrusting Pattern",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 2,
        "description": "Two-candle pattern: bearish candle followed by bullish candle that closes below the midpoint of the first.",
        "reliability_score": 65,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Advance Block",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 3,
        "description": "Three consecutive bullish candles with progressively smaller bodies and longer upper shadows.",
        "reliability_score": 75,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Three Inside Up/Down",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 3,
        "description": "Three-candle pattern: harami setup followed by confirmation candle.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Three Outside Up/Down",
        "category": "Candle",
        "pattern_type": "candlestick",
        "typical_duration": 3,
        "description": "Three-candle pattern: engulfing pattern followed by confirmation candle.",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": False
    },

    # Chart Patterns (4 patterns)
    {
        "name": "Support Level Test",
        "category": "Price Action",
        "pattern_type": "chart",
        "typical_duration": 5,
        "description": "Price is testing a key support level where buying interest has previously emerged.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Resistance Level Test",
        "category": "Price Action",
        "pattern_type": "chart",
        "typical_duration": 5,
        "description": "Price is testing a key resistance level where selling interest has previously emerged.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Bullish Trend",
        "category": "Chart",
        "pattern_type": "chart",
        "typical_duration": 20,
        "description": "Price is above both 20-period and 50-period moving averages in ascending order.",
        "reliability_score": 85,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Bearish Trend",
        "category": "Chart",
        "pattern_type": "chart",
        "typical_duration": 20,
        "description": "Price is below both 20-period and 50-period moving averages in descending order.",
        "reliability_score": 85,
        "is_reversal": False,
        "is_continuation": True
    },

    # Volume Patterns (17 patterns)
    {
        "name": "Volume Spike",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 1,
        "description": "Abnormally high trading volume compared to recent average, indicating significant market interest.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": True
    },
    {
        "name": "Volume Breakout",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 1,
        "description": "Price breakout above resistance accompanied by increased volume confirming the move.",
        "reliability_score": 90,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Accumulation Pattern",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 10,
        "description": "Volume shows accumulation supporting price rise, indicating institutional buying.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Distribution Pattern",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 10,
        "description": "Volume shows distribution supporting price decline, indicating institutional selling.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Volume Climax",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 1,
        "description": "Extreme volume combined with significant price movement, often marking exhaustion.",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Low Volume Pullback",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 3,
        "description": "Healthy pullback on declining volume suggesting the main trend will continue.",
        "reliability_score": 80,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Volume Confirmation",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 5,
        "description": "Volume trend confirms price movement direction, validating the current trend.",
        "reliability_score": 85,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Volume Divergence",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 5,
        "description": "Volume trend diverges from price trend, suggesting potential reversal.",
        "reliability_score": 75,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "High Volume Reversal",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 1,
        "description": "Price reversal accompanied by unusually high volume, confirming the direction change.",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Volume Thrust",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 1,
        "description": "Powerful upward price movement on exceptional volume, indicating strong buying pressure.",
        "reliability_score": 85,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Volume Drying Up",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 5,
        "description": "Volume declining significantly, often preceding a breakout in either direction.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Volume Expansion",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 3,
        "description": "Volume increasing significantly, supporting the current price trend.",
        "reliability_score": 80,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Volume Contraction",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 3,
        "description": "Systematic volume decline suggesting market consolidation or indecision.",
        "reliability_score": 65,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "OBV Bullish Trend",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 10,
        "description": "On-Balance Volume trending upward, confirming bullish price action.",
        "reliability_score": 85,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "OBV Bearish Trend",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 10,
        "description": "On-Balance Volume trending downward, confirming bearish price action.",
        "reliability_score": 85,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "VPT Confirmation",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 5,
        "description": "Volume Price Trend indicator confirming the current price movement direction.",
        "reliability_score": 80,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Heavy Volume Rejection",
        "category": "Volume-Based",
        "pattern_type": "volume",
        "typical_duration": 1,
        "description": "Heavy volume rejection at support or resistance levels indicating strong interest.",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": False
    },

    # Harmonic Patterns (12 patterns)
    {
        "name": "Gartley Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 15,
        "description": "Five-point harmonic pattern with specific Fibonacci retracements (XA-AB-BC-CD-DA structure).",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Butterfly Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 15,
        "description": "Harmonic pattern with 0.786 retracement and 1.27-1.618 extension, creating PRZ (Potential Reversal Zone).",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Bat Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 12,
        "description": "Harmonic pattern with 0.382-0.5 B point and precise 0.886 retracement at D point.",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Crab Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 18,
        "description": "Extreme harmonic pattern with 1.618 extension, representing deepest potential reversal zone.",
        "reliability_score": 95,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "ABCD Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 8,
        "description": "Simple harmonic pattern where CD leg equals AB leg in time and price proportion.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Three Drives Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 21,
        "description": "Seven-point harmonic pattern with three equal drives and Fibonacci relationships.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Cypher Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 12,
        "description": "Harmonic pattern with 0.786 retracement at D point and specific internal ratios.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Shark Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 15,
        "description": "Five-point harmonic pattern with 0.886-1.13 retracement zone (deeper than Cypher).",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "NenStar Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 20,
        "description": "Complex harmonic pattern combining multiple Fibonacci relationships at confluence zone.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Anti Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 12,
        "description": "Inverted harmonic structure providing alternative entry opportunities.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Deep Crab Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 20,
        "description": "Extreme harmonic pattern extending beyond traditional Crab with deeper retracements.",
        "reliability_score": 95,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Perfect Gartley Pattern",
        "category": "Harmonic",
        "pattern_type": "harmonic",
        "typical_duration": 15,
        "description": "Ideal Gartley pattern with perfect Fibonacci ratios and optimal market structure.",
        "reliability_score": 95,
        "is_reversal": True,
        "is_continuation": False
    },

    # Statistical Patterns (20+ patterns)
    {
        "name": "Bollinger Band Squeeze",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 5,
        "description": "Bollinger Bands contracting to unusually narrow width, indicating low volatility consolidation.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Bollinger Upper Breakout",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 1,
        "description": "Price closing above the upper Bollinger Band, indicating strong upward momentum.",
        "reliability_score": 80,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Bollinger Lower Breakout",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 1,
        "description": "Price closing below the lower Bollinger Band, indicating strong downward momentum.",
        "reliability_score": 80,
        "is_reversal": False,
        "is_continuation": True
    },
    {
        "name": "Bollinger Band Bounce",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 1,
        "description": "Price bouncing off Bollinger Bands, suggesting support or resistance.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "RSI Overbought",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 3,
        "description": "RSI above 70, indicating potential overbought conditions and possible reversal.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "RSI Oversold",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 3,
        "description": "RSI below 30, indicating potential oversold conditions and possible reversal.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "RSI Bearish Divergence",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 10,
        "description": "Price making higher highs while RSI making lower highs, indicating weakening momentum.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "RSI Bullish Divergence",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 10,
        "description": "Price making lower lows while RSI making higher lows, indicating strengthening momentum.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "MACD Bullish Crossover",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 3,
        "description": "MACD line crossing above signal line, indicating increasing bullish momentum.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": True
    },
    {
        "name": "MACD Bearish Crossover",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 3,
        "description": "MACD line crossing below signal line, indicating increasing bearish momentum.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": True
    },
    {
        "name": "MACD Zero Line Cross",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 1,
        "description": "MACD crossing above or below zero line, confirming trend strength.",
        "reliability_score": 90,
        "is_reversal": True,
        "is_continuation": True
    },
    {
        "name": "Stochastic Overbought",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 3,
        "description": "Stochastic oscillator above 80, indicating potential overbought conditions.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Stochastic Oversold",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 3,
        "description": "Stochastic oscillator below 20, indicating potential oversold conditions.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Williams %R Overbought",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 3,
        "description": "Williams %R above -20, indicating potential overbought conditions and reversal risk.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Williams %R Oversold",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 3,
        "description": "Williams %R below -80, indicating potential oversold conditions and bounce potential.",
        "reliability_score": 70,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Momentum Shift Bullish",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 5,
        "description": "Price momentum shifting from negative to positive, indicating trend change.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Momentum Shift Bearish",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 5,
        "description": "Price momentum shifting from positive to negative, indicating trend change.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "High Volatility Alert",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 1,
        "description": "Average True Range indicates unusually high volatility compared to recent periods.",
        "reliability_score": 85,
        "is_reversal": True,
        "is_continuation": True
    },
    {
        "name": "Low Volatility Alert",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 5,
        "description": "Average True Range indicates unusually low volatility compared to recent periods.",
        "reliability_score": 80,
        "is_reversal": True,
        "is_continuation": False
    },
    {
        "name": "Strong Trend Signal",
        "category": "Statistical",
        "pattern_type": "statistical",
        "typical_duration": 10,
        "description": "ADX above 25 indicates a strong trending market environment.",
        "reliability_score": 90,
        "is_reversal": False,
        "is_continuation": True
    }
]

def get_pattern_types_seed_data() -> List[Dict[str, Any]]:
    """Return the pattern types seed data"""
    return PATTERN_TYPES_DATA

def get_patterns_by_category() -> Dict[str, int]:
    """Get count of patterns by category"""
    category_counts = {}
    for pattern in PATTERN_TYPES_DATA:
        category = pattern['category']
        category_counts[category] = category_counts.get(category, 0) + 1
    return category_counts

def get_patterns_by_type() -> Dict[str, int]:
    """Get count of patterns by pattern type"""
    type_counts = {}
    for pattern in PATTERN_TYPES_DATA:
        pattern_type = pattern['pattern_type']
        type_counts[pattern_type] = type_counts.get(pattern_type, 0) + 1
    return type_counts

if __name__ == "__main__":
    print(f"Total patterns: {len(PATTERN_TYPES_DATA)}")
    print(f"By category: {get_patterns_by_category()}")
    print(f"By type: {get_patterns_by_type()}")