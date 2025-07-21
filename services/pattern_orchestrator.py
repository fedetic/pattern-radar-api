"""
Pattern Detection Orchestrator - Coordinates multiple pattern detection services
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import asyncio

# Import pattern services
from .candlestick_service import CandlestickPatternService
from .chart_patterns_service import ChartPatternsService

# Import optional services with error handling
try:
    from .volume_patterns import volume_detector
    VOLUME_PATTERNS_AVAILABLE = True
except ImportError:
    VOLUME_PATTERNS_AVAILABLE = False

try:
    from .harmonic_patterns import harmonic_detector
    HARMONIC_PATTERNS_AVAILABLE = True
except ImportError:
    HARMONIC_PATTERNS_AVAILABLE = False

try:
    from .statistical_patterns import statistical_detector
    STATISTICAL_PATTERNS_AVAILABLE = True
except ImportError:
    STATISTICAL_PATTERNS_AVAILABLE = False

class PatternOrchestrator:
    """Orchestrates pattern detection across multiple specialized services"""
    
    def __init__(self):
        # Initialize core services
        self.candlestick_service = CandlestickPatternService()
        self.chart_service = ChartPatternsService()
        
        # Track available services
        self.services = {
            'candlestick': self.candlestick_service,
            'chart': self.chart_service
        }
        
        print("Pattern Orchestrator initialized with services:", list(self.services.keys()))
    
    async def analyze_patterns_async(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns asynchronously using multiple services"""
        if df is None or df.empty:
            return {"patterns": [], "market_data": []}
        
        print(f"Starting comprehensive pattern analysis on {len(df)} data points...")
        
        # Run pattern detection in parallel
        all_patterns = await self._run_parallel_detection(df)
        
        # Sort patterns by confidence
        all_patterns.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"Total patterns detected: {len(all_patterns)}")
        
        # Convert DataFrame to market data format
        market_data = self._convert_to_market_data(df)
        
        # Calculate pattern statistics
        pattern_stats = self._calculate_pattern_stats(all_patterns)
        
        return {
            "patterns": all_patterns[:50],  # Limit to top 50 patterns for performance
            "market_data": market_data,
            "strongest_pattern": all_patterns[0] if all_patterns else None,
            "pattern_statistics": pattern_stats,
            "total_patterns_detected": len(all_patterns),
            "services_used": list(self.services.keys())
        }
    
    def analyze_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Synchronous version of pattern analysis"""
        if df is None or df.empty:
            return {"patterns": [], "market_data": []}
        
        print(f"Starting comprehensive pattern analysis on {len(df)} data points...")
        
        all_patterns = []
        
        # 1. Candlestick patterns
        try:
            candlestick_patterns = self.candlestick_service.detect_patterns(df)
            all_patterns.extend(candlestick_patterns)
        except Exception as e:
            print(f"Error in candlestick detection: {e}")
        
        # 2. Chart patterns
        try:
            chart_patterns = self.chart_service.detect_patterns(df)
            all_patterns.extend(chart_patterns)
        except Exception as e:
            print(f"Error in chart pattern detection: {e}")
        
        # 3. Volume patterns (if available)
        if VOLUME_PATTERNS_AVAILABLE:
            try:
                volume_patterns = volume_detector.detect_volume_patterns(df)
                all_patterns.extend(volume_patterns)
                print(f"Detected {len(volume_patterns)} volume patterns")
            except Exception as e:
                print(f"Error detecting volume patterns: {e}")
        
        # 4. Harmonic patterns (if available)
        if HARMONIC_PATTERNS_AVAILABLE:
            try:
                harmonic_patterns = harmonic_detector.detect_harmonic_patterns(df)
                all_patterns.extend(harmonic_patterns)
                print(f"Detected {len(harmonic_patterns)} harmonic patterns")
            except Exception as e:
                print(f"Error detecting harmonic patterns: {e}")
        
        # 5. Statistical patterns (if available)
        if STATISTICAL_PATTERNS_AVAILABLE:
            try:
                statistical_patterns = statistical_detector.detect_statistical_patterns(df)
                all_patterns.extend(statistical_patterns)
                print(f"Detected {len(statistical_patterns)} statistical patterns")
            except Exception as e:
                print(f"Error detecting statistical patterns: {e}")
        
        # Sort by confidence
        all_patterns.sort(key=lambda x: x['confidence'], reverse=True)
        
        print(f"Total patterns detected: {len(all_patterns)}")
        
        # Convert DataFrame to market data format
        market_data = self._convert_to_market_data(df)
        
        # Calculate pattern statistics
        pattern_stats = self._calculate_pattern_stats(all_patterns)
        
        return {
            "patterns": all_patterns[:50],  # Limit to top 50 patterns for performance
            "market_data": market_data,
            "strongest_pattern": all_patterns[0] if all_patterns else None,
            "pattern_statistics": pattern_stats,
            "total_patterns_detected": len(all_patterns),
            "analysis_modules": {
                "candlestick": True,
                "chart": True,
                "volume": VOLUME_PATTERNS_AVAILABLE,
                "harmonic": HARMONIC_PATTERNS_AVAILABLE,
                "statistical": STATISTICAL_PATTERNS_AVAILABLE
            }
        }
    
    async def _run_parallel_detection(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Run pattern detection services in parallel"""
        loop = asyncio.get_event_loop()
        all_patterns = []
        
        # Create tasks for each service
        tasks = []
        
        # Core services
        for service_name, service in self.services.items():
            task = loop.run_in_executor(None, service.detect_patterns, df)
            tasks.append((service_name, task))
        
        # Optional services
        if VOLUME_PATTERNS_AVAILABLE:
            task = loop.run_in_executor(None, volume_detector.detect_volume_patterns, df)
            tasks.append(('volume', task))
        
        if HARMONIC_PATTERNS_AVAILABLE:
            task = loop.run_in_executor(None, harmonic_detector.detect_harmonic_patterns, df)
            tasks.append(('harmonic', task))
        
        if STATISTICAL_PATTERNS_AVAILABLE:
            task = loop.run_in_executor(None, statistical_detector.detect_statistical_patterns, df)
            tasks.append(('statistical', task))
        
        # Wait for all tasks to complete
        for service_name, task in tasks:
            try:
                patterns = await task
                all_patterns.extend(patterns)
                print(f"{service_name} service: Detected {len(patterns)} patterns")
            except Exception as e:
                print(f"Error in {service_name} service: {e}")
        
        return all_patterns
    
    def _convert_to_market_data(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to market data format"""
        market_data = []
        
        for timestamp, row in df.iterrows():
            market_data.append({
                "timestamp": timestamp.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row.get('volume', 0))  # Include volume if available
            })
        
        return market_data
    
    def _calculate_pattern_stats(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics about detected patterns"""
        if not patterns:
            return {}
        
        # Count by category
        category_counts = {}
        direction_counts = {"bullish": 0, "bearish": 0, "neutral": 0, "continuation": 0}
        confidence_levels = {"high": 0, "medium": 0, "low": 0}
        service_counts = {}
        
        for pattern in patterns:
            # Category stats
            category = pattern.get('category', 'Unknown')
            category_counts[category] = category_counts.get(category, 0) + 1
            
            # Direction stats
            direction = pattern.get('direction', 'neutral')
            direction_counts[direction] = direction_counts.get(direction, 0) + 1
            
            # Confidence stats
            confidence = pattern.get('confidence', 0)
            if confidence >= 80:
                confidence_levels["high"] += 1
            elif confidence >= 60:
                confidence_levels["medium"] += 1
            else:
                confidence_levels["low"] += 1
            
            # Service stats
            service = pattern.get('service', 'Unknown')
            service_counts[service] = service_counts.get(service, 0) + 1
        
        avg_confidence = sum(p.get('confidence', 0) for p in patterns) / len(patterns)
        
        return {
            "total_patterns": len(patterns),
            "by_category": category_counts,
            "by_direction": direction_counts,
            "by_confidence_level": confidence_levels,
            "by_service": service_counts,
            "average_confidence": round(avg_confidence, 2),
            "highest_confidence": max(p.get('confidence', 0) for p in patterns),
            "pattern_types": len(set(p.get('name', '') for p in patterns))
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all available services"""
        return {
            "core_services": list(self.services.keys()),
            "optional_services": {
                "volume": VOLUME_PATTERNS_AVAILABLE,
                "harmonic": HARMONIC_PATTERNS_AVAILABLE, 
                "statistical": STATISTICAL_PATTERNS_AVAILABLE
            },
            "total_services": len(self.services) + sum([
                VOLUME_PATTERNS_AVAILABLE,
                HARMONIC_PATTERNS_AVAILABLE,
                STATISTICAL_PATTERNS_AVAILABLE
            ])
        }

# Global orchestrator instance
pattern_orchestrator = PatternOrchestrator()