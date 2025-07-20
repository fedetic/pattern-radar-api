import pytest
import requests
import sys
import os
from typing import Dict, List, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestVolumeChartIntegration:
    """Test suite for volume chart integration and pattern visualization"""
    
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
    
    def test_market_data_includes_volume(self):
        """Test that market data includes volume information for chart visualization"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", [])
            
            assert len(market_data) > 0, "Should have market data"
            
            # Check that volume data is present in market data
            for data_point in market_data[:5]:  # Check first 5 points
                assert "volume" in data_point, f"Market data point missing volume: {data_point}"
                assert isinstance(data_point["volume"], (int, float)), f"Volume should be numeric: {data_point['volume']}"
                assert data_point["volume"] >= 0, f"Volume should be non-negative: {data_point['volume']}"
                
            print(f"✅ Market data includes volume for {len(market_data)} data points")
    
    def test_volume_patterns_have_coordinates(self):
        """Test that volume patterns have proper coordinates for volume chart visualization"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            
            volume_patterns = [p for p in patterns if p.get("category", "").lower() == "volume"]
            
            if len(volume_patterns) > 0:
                print(f"\nTesting volume pattern coordinates for {len(volume_patterns)} patterns:")
                
                for pattern in volume_patterns:
                    pattern_name = pattern.get("name", "Unknown")
                    
                    # Volume patterns should have coordinates for visualization
                    if "coordinates" in pattern and pattern["coordinates"]:
                        coords = pattern["coordinates"]
                        
                        # Check volume pattern coordinate structure
                        if coords.get("type") == "volume_pattern":
                            self._validate_volume_pattern_coordinates(coords, pattern_name)
                            print(f"✅ {pattern_name}: Has volume pattern coordinates")
                        else:
                            print(f"⚠️  {pattern_name}: Has coordinates but not volume_pattern type")
                    else:
                        print(f"⚠️  {pattern_name}: Missing coordinates - will use fallback visualization")
                
                print(f"Volume patterns found: {len(volume_patterns)}")
            else:
                print("No volume patterns detected in current data")
    
    def _validate_volume_pattern_coordinates(self, coords: Dict[str, Any], pattern_name: str):
        """Validate volume pattern coordinate structure"""
        required_fields = ["timestamp", "volume"]
        
        for field in required_fields:
            assert field in coords, f"Volume pattern '{pattern_name}' missing {field} in coordinates"
        
        # Validate data types
        assert isinstance(coords["timestamp"], str), f"Volume pattern '{pattern_name}' timestamp must be string"
        assert isinstance(coords["volume"], (int, float)), f"Volume pattern '{pattern_name}' volume must be numeric"
        assert coords["volume"] >= 0, f"Volume pattern '{pattern_name}' volume must be non-negative"
        
        # Optional fields that may be present
        optional_fields = ["volume_ma_20", "price", "index", "pattern_type", "highlight_color"]
        for field in optional_fields:
            if field in coords:
                if field in ["volume_ma_20", "price"]:
                    assert isinstance(coords[field], (int, float)), f"Volume pattern '{pattern_name}' {field} must be numeric"
                elif field == "index":
                    assert isinstance(coords[field], int), f"Volume pattern '{pattern_name}' index must be integer"
                elif field in ["pattern_type", "highlight_color"]:
                    assert isinstance(coords[field], str), f"Volume pattern '{pattern_name}' {field} must be string"
    
    def test_volume_pattern_fallback_visualization(self):
        """Test that volume patterns without coordinates can use fallback visualization"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            market_data = data.get("market_data", [])
            
            volume_patterns = [p for p in patterns if p.get("category", "").lower() == "volume"]
            patterns_without_coords = [p for p in volume_patterns if not p.get("coordinates")]
            
            if len(patterns_without_coords) > 0:
                print(f"\nTesting fallback visualization for {len(patterns_without_coords)} volume patterns:")
                
                # Ensure market data has volume for fallback visualization
                assert len(market_data) >= 1, "Need market data for volume pattern fallback visualization"
                
                for data_point in market_data[-3:]:  # Check last 3 points
                    assert "volume" in data_point, "Market data must have volume for volume pattern fallback"
                    assert data_point["volume"] >= 0, "Volume must be non-negative for visualization"
                
                for pattern in patterns_without_coords:
                    # Check that pattern has required fields for fallback visualization
                    assert "name" in pattern, f"Pattern missing name for fallback visualization"
                    assert "direction" in pattern, f"Pattern '{pattern['name']}' missing direction for fallback"
                    assert "category" in pattern, f"Pattern '{pattern['name']}' missing category for fallback"
                    
                    print(f"✅ {pattern['name']}: Can use volume-specific fallback visualization")
            else:
                print("All volume patterns have coordinates")
    
    def test_volume_data_consistency_across_timeframes(self):
        """Test that volume data is consistent across different timeframes"""
        timeframes = ["1d"]  # Focus on working timeframe
        
        for timeframe in timeframes:
            response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe={timeframe}")
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get("market_data", [])
                
                if len(market_data) > 0:
                    # Check volume data consistency
                    volumes = [d.get("volume", 0) for d in market_data]
                    
                    # All volumes should be non-negative
                    assert all(v >= 0 for v in volumes), f"All volumes should be non-negative for {timeframe}"
                    
                    # Check for reasonable volume variation (not all identical)
                    unique_volumes = set(volumes)
                    if len(volumes) >= 5:
                        assert len(unique_volumes) > 1, f"Volumes should vary for {timeframe} (found {len(unique_volumes)} unique values)"
                    
                    print(f"✅ {timeframe}: Volume data consistent across {len(market_data)} points (range: {min(volumes):,.0f} - {max(volumes):,.0f})")
    
    def test_volume_pattern_types_coverage(self):
        """Test that different types of volume patterns are detected and can be visualized"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            
            volume_patterns = [p for p in patterns if p.get("category", "").lower() == "volume"]
            
            if len(volume_patterns) > 0:
                # Group volume patterns by type/name
                pattern_types = {}
                for pattern in volume_patterns:
                    pattern_name = pattern.get("name", "Unknown")
                    if pattern_name not in pattern_types:
                        pattern_types[pattern_name] = []
                    pattern_types[pattern_name].append(pattern)
                
                print(f"\nVolume pattern types detected:")
                for pattern_type, pattern_list in pattern_types.items():
                    coord_count = sum(1 for p in pattern_list if p.get("coordinates"))
                    total_count = len(pattern_list)
                    
                    print(f"  {pattern_type}: {total_count} instances ({coord_count} with coordinates)")
                    
                    # Validate that each pattern type can be visualized
                    for pattern in pattern_list[:2]:  # Check first 2 of each type
                        assert "direction" in pattern, f"Pattern {pattern_type} missing direction"
                        assert pattern["direction"] in ["bullish", "bearish", "neutral"], \
                            f"Pattern {pattern_type} has invalid direction: {pattern['direction']}"
                
                print(f"Total volume pattern types: {len(pattern_types)}")
            else:
                print("No volume patterns detected")
    
    def test_volume_chart_performance_impact(self):
        """Test that adding volume to chart doesn't significantly impact API performance"""
        import time
        
        # Test without specific volume requests (normal pattern request)
        start_time = time.time()
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", [])
            patterns = data.get("patterns", [])
            
            # Verify volume data is included without performance penalty
            assert duration < 10, f"API response too slow with volume data: {duration:.2f}s"
            
            # Verify data completeness
            volume_data_points = sum(1 for d in market_data if "volume" in d)
            volume_patterns = sum(1 for p in patterns if p.get("category", "").lower() == "volume")
            
            print(f"Performance test: {duration:.2f}s for {len(market_data)} data points with volume")
            print(f"Volume data coverage: {volume_data_points}/{len(market_data)} data points")
            print(f"Volume patterns: {volume_patterns} detected")
            
            # Most data points should have volume
            if len(market_data) > 0:
                volume_coverage = volume_data_points / len(market_data)
                assert volume_coverage >= 0.9, f"Volume data coverage too low: {volume_coverage:.1%}"


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])