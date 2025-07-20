import pytest
import requests
import sys
import os
from typing import Dict, List, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPatternVisualization:
    """Test suite for ensuring all detected patterns have proper visualization coordinates"""
    
    BASE_URL = "http://127.0.0.1:8000"
    
    @classmethod
    def setup_class(cls):
        """Set up class-level fixtures"""
        # Verify server is running
        try:
            response = requests.get(f"{cls.BASE_URL}/", timeout=5)
            assert response.status_code == 200
        except Exception as e:
            pytest.skip(f"API server not running: {e}")
    
    def test_all_patterns_have_visualization_data(self):
        """Test that all detected patterns have coordinates or can be visualized"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            
            if len(patterns) > 0:
                print(f"\nTesting visualization for {len(patterns)} detected patterns:")
                
                patterns_without_coords = []
                patterns_with_coords = []
                
                for pattern in patterns:
                    pattern_name = pattern.get("name", "Unknown")
                    has_coordinates = "coordinates" in pattern and pattern["coordinates"]
                    
                    if has_coordinates:
                        patterns_with_coords.append(pattern)
                        print(f"✅ {pattern_name}: Has coordinates ({pattern['coordinates'].get('type', 'unknown type')})")
                    else:
                        patterns_without_coords.append(pattern)
                        print(f"⚠️  {pattern_name}: Missing coordinates - will use fallback visualization")
                
                # Verify that patterns have required fields for visualization
                for pattern in patterns:
                    self._validate_pattern_structure(pattern)
                
                print(f"\nSummary:")
                print(f"Patterns with coordinates: {len(patterns_with_coords)}")
                print(f"Patterns needing fallback: {len(patterns_without_coords)}")
                
                # At least some patterns should have coordinates
                if len(patterns) > 5:
                    coord_percentage = len(patterns_with_coords) / len(patterns) * 100
                    assert coord_percentage >= 50, f"Only {coord_percentage:.1f}% of patterns have coordinates"
    
    def _validate_pattern_structure(self, pattern: Dict[str, Any]):
        """Validate that a pattern has the minimum required structure for visualization"""
        required_fields = ["name", "confidence", "direction", "category"]
        
        for field in required_fields:
            assert field in pattern, f"Pattern missing required field: {field}"
        
        # Validate field values
        assert isinstance(pattern["confidence"], (int, float)), "Confidence must be numeric"
        assert 0 <= pattern["confidence"] <= 100, "Confidence must be between 0-100"
        assert pattern["direction"] in ["bullish", "bearish", "neutral", "continuation"], \
            f"Invalid direction: {pattern['direction']}"
        assert isinstance(pattern["name"], str) and len(pattern["name"]) > 0, "Name must be non-empty string"
        assert isinstance(pattern["category"], str) and len(pattern["category"]) > 0, "Category must be non-empty string"
    
    def test_pattern_coordinates_structure(self):
        """Test that pattern coordinates have proper structure for visualization"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            
            coord_types_found = set()
            
            for pattern in patterns:
                if "coordinates" in pattern and pattern["coordinates"]:
                    coords = pattern["coordinates"]
                    coord_type = coords.get("type", "unknown")
                    coord_types_found.add(coord_type)
                    
                    # Validate coordinate structure based on type
                    if coord_type == "pattern_range":
                        self._validate_pattern_range_coords(coords, pattern["name"])
                    elif coord_type == "volume_pattern":
                        self._validate_volume_pattern_coords(coords, pattern["name"])
                    elif coord_type == "harmonic_pattern":
                        self._validate_harmonic_pattern_coords(coords, pattern["name"])
                    elif coord_type == "statistical_pattern":
                        self._validate_statistical_pattern_coords(coords, pattern["name"])
                    elif coord_type == "horizontal_line":
                        self._validate_horizontal_line_coords(coords, pattern["name"])
                    else:
                        print(f"Warning: Unknown coordinate type '{coord_type}' for pattern '{pattern['name']}'")
            
            print(f"\nCoordinate types found: {coord_types_found}")
            
            # Should have at least some coordinate types (any valid pattern detection)
            assert len(coord_types_found) > 0, "Should detect at least some patterns with coordinates"
    
    def _validate_pattern_range_coords(self, coords: Dict[str, Any], pattern_name: str):
        """Validate pattern_range coordinate structure"""
        required_fields = ["start_time", "end_time", "pattern_high", "pattern_low"]
        
        for field in required_fields:
            assert field in coords, f"Pattern '{pattern_name}' missing {field} in coordinates"
        
        # Validate data types and ranges
        assert isinstance(coords["pattern_high"], (int, float)), f"Pattern '{pattern_name}' high must be numeric"
        assert isinstance(coords["pattern_low"], (int, float)), f"Pattern '{pattern_name}' low must be numeric"
        assert coords["pattern_high"] >= coords["pattern_low"], f"Pattern '{pattern_name}' high must be >= low"
        
        # Validate timestamps are ISO format strings
        assert isinstance(coords["start_time"], str), f"Pattern '{pattern_name}' start_time must be string"
        assert isinstance(coords["end_time"], str), f"Pattern '{pattern_name}' end_time must be string"
    
    def _validate_volume_pattern_coords(self, coords: Dict[str, Any], pattern_name: str):
        """Validate volume_pattern coordinate structure"""
        assert "timestamp" in coords, f"Volume pattern '{pattern_name}' missing timestamp"
        assert isinstance(coords["timestamp"], str), f"Volume pattern '{pattern_name}' timestamp must be string"
    
    def _validate_harmonic_pattern_coords(self, coords: Dict[str, Any], pattern_name: str):
        """Validate harmonic_pattern coordinate structure"""
        assert "points" in coords, f"Harmonic pattern '{pattern_name}' missing points"
        points = coords["points"]
        assert isinstance(points, list), f"Harmonic pattern '{pattern_name}' points must be list"
        assert len(points) >= 2, f"Harmonic pattern '{pattern_name}' must have at least 2 points"
        
        for i, point in enumerate(points):
            assert "timestamp" in point, f"Harmonic pattern '{pattern_name}' point {i} missing timestamp"
            assert "price" in point, f"Harmonic pattern '{pattern_name}' point {i} missing price"
            assert isinstance(point["price"], (int, float)), f"Harmonic pattern '{pattern_name}' point {i} price must be numeric"
    
    def _validate_statistical_pattern_coords(self, coords: Dict[str, Any], pattern_name: str):
        """Validate statistical_pattern coordinate structure"""
        # Statistical patterns can have various coordinate structures
        # At minimum should have a timestamp or time range
        has_timestamp = "timestamp" in coords
        has_time_range = "start_time" in coords and "end_time" in coords
        
        assert has_timestamp or has_time_range, \
            f"Statistical pattern '{pattern_name}' must have timestamp or time range"
    
    def _validate_horizontal_line_coords(self, coords: Dict[str, Any], pattern_name: str):
        """Validate horizontal_line coordinate structure"""
        assert "level" in coords, f"Horizontal line pattern '{pattern_name}' missing level"
        assert isinstance(coords["level"], (int, float)), f"Horizontal line pattern '{pattern_name}' level must be numeric"
    
    def test_pattern_visualization_coverage_by_category(self):
        """Test that patterns in each category have appropriate visualization"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            
            if len(patterns) > 0:
                # Group patterns by category
                patterns_by_category = {}
                for pattern in patterns:
                    category = pattern.get("category", "Unknown")
                    if category not in patterns_by_category:
                        patterns_by_category[category] = []
                    patterns_by_category[category].append(pattern)
                
                print(f"\nPattern visualization coverage by category:")
                
                for category, category_patterns in patterns_by_category.items():
                    with_coords = sum(1 for p in category_patterns if p.get("coordinates"))
                    total = len(category_patterns)
                    coverage = (with_coords / total * 100) if total > 0 else 0
                    
                    print(f"{category}: {with_coords}/{total} patterns have coordinates ({coverage:.1f}%)")
                    
                    # For categories with multiple patterns, at least some should have coordinates
                    if total >= 3:
                        assert coverage >= 30, f"Category '{category}' has low coordinate coverage: {coverage:.1f}%"
    
    def test_pattern_fallback_visualization_requirements(self):
        """Test that patterns without coordinates have sufficient data for fallback visualization"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            market_data = data.get("market_data", [])
            
            patterns_without_coords = [p for p in patterns if not p.get("coordinates")]
            
            if len(patterns_without_coords) > 0:
                print(f"\nTesting fallback visualization for {len(patterns_without_coords)} patterns:")
                
                # Ensure market data is available for fallback visualization
                assert len(market_data) >= 5, "Need at least 5 market data points for fallback visualization"
                
                for pattern in patterns_without_coords:
                    # Check that pattern has the required fields for fallback visualization
                    assert "name" in pattern, f"Pattern missing name for fallback visualization"
                    assert "direction" in pattern, f"Pattern '{pattern['name']}' missing direction for fallback"
                    assert "category" in pattern, f"Pattern '{pattern['name']}' missing category for fallback"
                    assert "confidence" in pattern, f"Pattern '{pattern['name']}' missing confidence for fallback"
                    
                    print(f"✅ {pattern['name']}: Can use fallback visualization (category: {pattern['category']})")
    
    def test_multiple_timeframes_pattern_visualization(self):
        """Test pattern visualization across different timeframes"""
        timeframes = ["1h", "4h", "1d"]
        
        for timeframe in timeframes:
            response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe={timeframe}")
            
            if response.status_code == 200:
                data = response.json()
                patterns = data.get("patterns", [])
                
                if len(patterns) > 0:
                    coord_count = sum(1 for p in patterns if p.get("coordinates"))
                    coord_percentage = (coord_count / len(patterns) * 100) if len(patterns) > 0 else 0
                    
                    print(f"Timeframe {timeframe}: {coord_count}/{len(patterns)} patterns have coordinates ({coord_percentage:.1f}%)")
                    
                    # Each timeframe should have some visualizable patterns
                    assert coord_count > 0 or len(patterns) <= 2, \
                        f"Timeframe {timeframe} has {len(patterns)} patterns but none have coordinates"
    
    def test_pattern_visualization_performance(self):
        """Test that pattern visualization data doesn't significantly impact API performance"""
        import time
        
        # Test normal patterns endpoint
        start_time = time.time()
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            
            # Verify that coordinate generation doesn't make API too slow
            assert duration < 15, f"Pattern API too slow with coordinates: {duration:.2f}s"
            
            # Verify data size is reasonable
            total_patterns = len(patterns)
            patterns_with_coords = sum(1 for p in patterns if p.get("coordinates"))
            
            print(f"Performance test: {duration:.2f}s for {total_patterns} patterns ({patterns_with_coords} with coordinates)")
            
            # Ensure we're not missing too much coordinate data
            if total_patterns >= 5:
                coord_ratio = patterns_with_coords / total_patterns
                assert coord_ratio >= 0.3, f"Too few patterns have coordinates: {coord_ratio:.1%}"


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])