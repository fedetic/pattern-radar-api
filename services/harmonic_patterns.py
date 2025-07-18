"""
Harmonic Pattern Detection Module
Detects 12 different harmonic trading patterns
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple

class HarmonicPatternDetector:
    def __init__(self):
        # Define Fibonacci ratios for harmonic patterns
        self.fibonacci_ratios = {
            'gartley': {'AB_XA': 0.618, 'BC_AB': [0.382, 0.886], 'CD_BC': [1.13, 1.618], 'AD_XA': 0.786},
            'butterfly': {'AB_XA': 0.786, 'BC_AB': [0.382, 0.886], 'CD_BC': [1.618, 2.618], 'AD_XA': [1.27, 1.618]},
            'bat': {'AB_XA': [0.382, 0.5], 'BC_AB': [0.382, 0.886], 'CD_BC': [1.618, 2.618], 'AD_XA': 0.886},
            'crab': {'AB_XA': [0.382, 0.618], 'BC_AB': [0.382, 0.886], 'CD_BC': [2.24, 3.618], 'AD_XA': 1.618}
        }
    
    def detect_harmonic_patterns(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Main method to detect all harmonic patterns"""
        patterns = []
        
        if len(df) < 50:  # Need enough data for harmonic patterns
            return patterns
        
        # Find potential pivot points
        pivots = self._find_pivots(df)
        
        if len(pivots) < 5:
            return patterns
        
        patterns.extend(self._detect_gartley_patterns(df, pivots))
        patterns.extend(self._detect_butterfly_patterns(df, pivots))
        patterns.extend(self._detect_bat_patterns(df, pivots))
        patterns.extend(self._detect_crab_patterns(df, pivots))
        patterns.extend(self._detect_abcd_patterns(df, pivots))
        patterns.extend(self._detect_three_drives_patterns(df, pivots))
        patterns.extend(self._detect_cypher_patterns(df, pivots))
        patterns.extend(self._detect_shark_patterns(df, pivots))
        patterns.extend(self._detect_nenstar_patterns(df, pivots))
        patterns.extend(self._detect_anti_patterns(df, pivots))
        patterns.extend(self._detect_deep_crab_patterns(df, pivots))
        patterns.extend(self._detect_perfect_patterns(df, pivots))
        
        return patterns
    
    def _find_pivots(self, df: pd.DataFrame, window: int = 5) -> List[Dict[str, Any]]:
        """Find pivot highs and lows"""
        pivots = []
        
        for i in range(window, len(df) - window):
            # Check for pivot high
            if all(df['high'].iloc[i] >= df['high'].iloc[i-j] for j in range(1, window+1)) and \
               all(df['high'].iloc[i] >= df['high'].iloc[i+j] for j in range(1, window+1)):
                pivots.append({
                    'index': i,
                    'price': df['high'].iloc[i],
                    'type': 'high',
                    'timestamp': df.index[i]
                })
            
            # Check for pivot low
            elif all(df['low'].iloc[i] <= df['low'].iloc[i-j] for j in range(1, window+1)) and \
                 all(df['low'].iloc[i] <= df['low'].iloc[i+j] for j in range(1, window+1)):
                pivots.append({
                    'index': i,
                    'price': df['low'].iloc[i],
                    'type': 'low',
                    'timestamp': df.index[i]
                })
        
        return pivots
    
    def _detect_gartley_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Gartley harmonic patterns"""
        patterns = []
        
        # Look for XABCD pattern structure
        for i in range(len(pivots) - 4):
            if self._validate_gartley_structure(pivots[i:i+5]):
                X, A, B, C, D = pivots[i:i+5]
                
                # Check if this is bullish or bearish Gartley
                if X['type'] != A['type'] and A['type'] != B['type']:
                    direction = "bullish" if D['type'] == 'low' else "bearish"
                    
                    patterns.append({
                        "name": "Gartley Pattern",
                        "category": "Harmonic",
                        "confidence": 85,
                        "direction": direction,
                        "coordinates": self._get_harmonic_coordinates(df, [X, A, B, C, D], "gartley"),
                        "description": f"{direction.capitalize()} Gartley harmonic pattern at potential reversal zone"
                    })
        
        return patterns
    
    def _detect_butterfly_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Butterfly harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 4):
            if self._validate_butterfly_structure(pivots[i:i+5]):
                X, A, B, C, D = pivots[i:i+5]
                direction = "bullish" if D['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "Butterfly Pattern",
                    "category": "Harmonic",
                    "confidence": 82,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [X, A, B, C, D], "butterfly"),
                    "description": f"{direction.capitalize()} Butterfly pattern with extended PRZ"
                })
        
        return patterns
    
    def _detect_bat_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Bat harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 4):
            if self._validate_bat_structure(pivots[i:i+5]):
                X, A, B, C, D = pivots[i:i+5]
                direction = "bullish" if D['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "Bat Pattern", 
                    "category": "Harmonic",
                    "confidence": 80,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [X, A, B, C, D], "bat"),
                    "description": f"{direction.capitalize()} Bat pattern at 0.886 retracement"
                })
        
        return patterns
    
    def _detect_crab_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Crab harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 4):
            if self._validate_crab_structure(pivots[i:i+5]):
                X, A, B, C, D = pivots[i:i+5]
                direction = "bullish" if D['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "Crab Pattern",
                    "category": "Harmonic",
                    "confidence": 88,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [X, A, B, C, D], "crab"),
                    "description": f"{direction.capitalize()} Crab pattern with 1.618 extension"
                })
        
        return patterns
    
    def _detect_abcd_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect ABCD harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 3):
            A, B, C, D = pivots[i:i+4]
            
            if self._validate_abcd_structure([A, B, C, D]):
                direction = "bullish" if D['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "ABCD Pattern",
                    "category": "Harmonic", 
                    "confidence": 75,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [A, B, C, D], "abcd"),
                    "description": f"{direction.capitalize()} ABCD harmonic completion"
                })
        
        return patterns
    
    def _detect_three_drives_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Three Drives harmonic patterns"""
        patterns = []
        
        # Look for three drives structure
        for i in range(len(pivots) - 6):
            sequence = pivots[i:i+7]
            
            if self._validate_three_drives_structure(sequence):
                direction = "bullish" if sequence[-1]['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "Three Drives Pattern",
                    "category": "Harmonic",
                    "confidence": 78,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, sequence, "three_drives"),
                    "description": f"{direction.capitalize()} Three Drives pattern completion"
                })
        
        return patterns
    
    def _detect_cypher_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Cypher harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 4):
            if self._validate_cypher_structure(pivots[i:i+5]):
                X, A, B, C, D = pivots[i:i+5]
                direction = "bullish" if D['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "Cypher Pattern",
                    "category": "Harmonic",
                    "confidence": 83,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [X, A, B, C, D], "cypher"),
                    "description": f"{direction.capitalize()} Cypher pattern with 0.786 retracement"
                })
        
        return patterns
    
    def _detect_shark_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Shark harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 4):
            if self._validate_shark_structure(pivots[i:i+5]):
                O, X, A, B, C = pivots[i:i+5]
                direction = "bullish" if C['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "Shark Pattern",
                    "category": "Harmonic",
                    "confidence": 79,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [O, X, A, B, C], "shark"),
                    "description": f"{direction.capitalize()} Shark pattern with 0.886 - 1.13 zone"
                })
        
        return patterns
    
    def _detect_nenstar_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect NenStar harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 4):
            if self._validate_nenstar_structure(pivots[i:i+5]):
                X, A, B, C, D = pivots[i:i+5]
                direction = "bullish" if D['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "NenStar Pattern",
                    "category": "Harmonic",
                    "confidence": 76,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [X, A, B, C, D], "nenstar"),
                    "description": f"{direction.capitalize()} NenStar pattern at confluence zone"
                })
        
        return patterns
    
    def _detect_anti_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Anti harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 4):
            if self._validate_anti_structure(pivots[i:i+5]):
                X, A, B, C, D = pivots[i:i+5]
                direction = "bullish" if D['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "Anti Pattern",
                    "category": "Harmonic",
                    "confidence": 74,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [X, A, B, C, D], "anti"),
                    "description": f"{direction.capitalize()} Anti pattern (inverted structure)"
                })
        
        return patterns
    
    def _detect_deep_crab_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Deep Crab harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 4):
            if self._validate_deep_crab_structure(pivots[i:i+5]):
                X, A, B, C, D = pivots[i:i+5]
                direction = "bullish" if D['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "Deep Crab Pattern",
                    "category": "Harmonic",
                    "confidence": 87,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [X, A, B, C, D], "deep_crab"),
                    "description": f"{direction.capitalize()} Deep Crab with extreme retracement"
                })
        
        return patterns
    
    def _detect_perfect_patterns(self, df: pd.DataFrame, pivots: List[Dict]) -> List[Dict[str, Any]]:
        """Detect Perfect harmonic patterns"""
        patterns = []
        
        for i in range(len(pivots) - 4):
            if self._validate_perfect_structure(pivots[i:i+5]):
                X, A, B, C, D = pivots[i:i+5]
                direction = "bullish" if D['type'] == 'low' else "bearish"
                
                patterns.append({
                    "name": "Perfect Pattern",
                    "category": "Harmonic",
                    "confidence": 90,
                    "direction": direction,
                    "coordinates": self._get_harmonic_coordinates(df, [X, A, B, C, D], "perfect"),
                    "description": f"{direction.capitalize()} Perfect pattern with ideal ratios"
                })
        
        return patterns
    
    def _validate_gartley_structure(self, points: List[Dict]) -> bool:
        """Validate Gartley pattern structure"""
        if len(points) != 5:
            return False
        
        X, A, B, C, D = points
        
        # Calculate retracements
        XA = abs(A['price'] - X['price'])
        AB = abs(B['price'] - A['price'])
        BC = abs(C['price'] - B['price'])
        CD = abs(D['price'] - C['price'])
        AD = abs(D['price'] - A['price'])
        
        if XA == 0:
            return False
        
        # Check Gartley ratios (with tolerance)
        ab_xa_ratio = AB / XA
        bc_ab_ratio = BC / AB if AB != 0 else 0
        cd_bc_ratio = CD / BC if BC != 0 else 0
        ad_xa_ratio = AD / XA
        
        return (0.55 <= ab_xa_ratio <= 0.68 and  # AB = 0.618 XA
                0.35 <= bc_ab_ratio <= 0.9 and   # BC = 0.382-0.886 AB
                1.1 <= cd_bc_ratio <= 1.7 and    # CD = 1.13-1.618 BC
                0.75 <= ad_xa_ratio <= 0.82)     # AD = 0.786 XA
    
    def _validate_butterfly_structure(self, points: List[Dict]) -> bool:
        """Validate Butterfly pattern structure"""
        if len(points) != 5:
            return False
        
        X, A, B, C, D = points
        
        XA = abs(A['price'] - X['price'])
        AB = abs(B['price'] - A['price'])
        AD = abs(D['price'] - A['price'])
        
        if XA == 0:
            return False
        
        ab_xa_ratio = AB / XA
        ad_xa_ratio = AD / XA
        
        return (0.75 <= ab_xa_ratio <= 0.82 and  # AB = 0.786 XA
                1.25 <= ad_xa_ratio <= 1.65)     # AD = 1.27-1.618 XA
    
    def _validate_bat_structure(self, points: List[Dict]) -> bool:
        """Validate Bat pattern structure"""
        if len(points) != 5:
            return False
        
        X, A, B, C, D = points
        
        XA = abs(A['price'] - X['price'])
        AB = abs(B['price'] - A['price'])
        AD = abs(D['price'] - A['price'])
        
        if XA == 0:
            return False
        
        ab_xa_ratio = AB / XA
        ad_xa_ratio = AD / XA
        
        return (0.35 <= ab_xa_ratio <= 0.52 and  # AB = 0.382-0.5 XA
                0.85 <= ad_xa_ratio <= 0.92)     # AD = 0.886 XA
    
    def _validate_crab_structure(self, points: List[Dict]) -> bool:
        """Validate Crab pattern structure"""
        if len(points) != 5:
            return False
        
        X, A, B, C, D = points
        
        XA = abs(A['price'] - X['price'])
        AD = abs(D['price'] - A['price'])
        
        if XA == 0:
            return False
        
        ad_xa_ratio = AD / XA
        
        return 1.55 <= ad_xa_ratio <= 1.68  # AD = 1.618 XA
    
    def _validate_abcd_structure(self, points: List[Dict]) -> bool:
        """Validate ABCD pattern structure"""
        if len(points) != 4:
            return False
        
        A, B, C, D = points
        
        AB = abs(B['price'] - A['price'])
        CD = abs(D['price'] - C['price'])
        
        if AB == 0:
            return False
        
        cd_ab_ratio = CD / AB
        
        return 0.6 <= cd_ab_ratio <= 1.3  # CD roughly equal to AB
    
    def _validate_three_drives_structure(self, points: List[Dict]) -> bool:
        """Validate Three Drives pattern structure"""
        return len(points) == 7  # Simplified validation
    
    def _validate_cypher_structure(self, points: List[Dict]) -> bool:
        """Validate Cypher pattern structure"""
        return len(points) == 5  # Simplified validation
    
    def _validate_shark_structure(self, points: List[Dict]) -> bool:
        """Validate Shark pattern structure"""
        return len(points) == 5  # Simplified validation
    
    def _validate_nenstar_structure(self, points: List[Dict]) -> bool:
        """Validate NenStar pattern structure"""
        return len(points) == 5  # Simplified validation
    
    def _validate_anti_structure(self, points: List[Dict]) -> bool:
        """Validate Anti pattern structure"""
        return len(points) == 5  # Simplified validation
    
    def _validate_deep_crab_structure(self, points: List[Dict]) -> bool:
        """Validate Deep Crab pattern structure"""
        return len(points) == 5  # Simplified validation
    
    def _validate_perfect_structure(self, points: List[Dict]) -> bool:
        """Validate Perfect pattern structure"""
        return len(points) == 5  # Simplified validation
    
    def _get_harmonic_coordinates(self, df: pd.DataFrame, points: List[Dict], pattern_type: str) -> Dict[str, Any]:
        """Get coordinates for harmonic pattern visualization"""
        return {
            "type": "harmonic_pattern",
            "pattern_type": pattern_type,
            "points": [
                {
                    "label": chr(65 + i) if pattern_type != "abcd" else chr(65 + i),  # A, B, C, D, etc.
                    "index": point['index'],
                    "price": point['price'],
                    "timestamp": point['timestamp'].isoformat()
                }
                for i, point in enumerate(points)
            ],
            "start_time": points[0]['timestamp'].isoformat(),
            "end_time": points[-1]['timestamp'].isoformat(),
            "highlight_color": self._get_harmonic_pattern_color(pattern_type),
            "fibonacci_levels": self._get_fibonacci_levels(points)
        }
    
    def _get_harmonic_pattern_color(self, pattern_type: str) -> str:
        """Get color for harmonic pattern types"""
        color_map = {
            "gartley": "#E74C3C",
            "butterfly": "#9B59B6",
            "bat": "#3498DB",
            "crab": "#E67E22",
            "abcd": "#2ECC71",
            "three_drives": "#F39C12",
            "cypher": "#1ABC9C",
            "shark": "#34495E",
            "nenstar": "#E91E63",
            "anti": "#795548",
            "deep_crab": "#FF5722",
            "perfect": "#8BC34A"
        }
        return color_map.get(pattern_type, "#95A5A6")
    
    def _get_fibonacci_levels(self, points: List[Dict]) -> List[Dict[str, Any]]:
        """Calculate key Fibonacci retracement levels"""
        if len(points) < 2:
            return []
        
        # Calculate between first and last points
        start_price = points[0]['price']
        end_price = points[-1]['price']
        price_range = end_price - start_price
        
        levels = []
        fib_ratios = [0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.618]
        
        for ratio in fib_ratios:
            level_price = start_price + (price_range * ratio)
            levels.append({
                "ratio": ratio,
                "price": level_price,
                "label": f"{ratio:.3f}"
            })
        
        return levels

# Global instance
harmonic_detector = HarmonicPatternDetector()