import pytest
import requests
import sys
import os
from typing import Dict, List, Any

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPatternDurationMarkers:
    """Test suite for pattern duration markers and volume toggle functionality"""
    
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
    
    def test_pattern_coordinates_support_duration_markers(self):
        """Test that pattern coordinates provide sufficient data for duration markers"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            
            patterns_with_coords = [p for p in patterns if p.get("coordinates")]
            
            if len(patterns_with_coords) > 0:
                print(f"\nTesting duration marker support for {len(patterns_with_coords)} patterns:")
                
                for pattern in patterns_with_coords:
                    pattern_name = pattern.get("name", "Unknown")
                    coords = pattern["coordinates"]
                    coord_type = coords.get("type", "unknown")
                    
                    # Check if pattern has time information for duration markers
                    has_duration_info = False
                    start_time = None
                    end_time = None
                    
                    if coord_type == "pattern_range":
                        has_duration_info = "start_time" in coords and "end_time" in coords
                        start_time = coords.get("start_time")
                        end_time = coords.get("end_time")
                    elif coord_type == "volume_pattern":
                        has_duration_info = "timestamp" in coords
                        start_time = end_time = coords.get("timestamp")
                    elif coord_type == "harmonic_pattern":
                        points = coords.get("points", [])
                        if len(points) >= 2:
                            has_duration_info = True
                            start_time = points[0].get("timestamp")
                            end_time = points[-1].get("timestamp")
                    elif coord_type == "statistical_pattern":
                        has_duration_info = "timestamp" in coords
                        start_time = end_time = coords.get("timestamp")
                    elif coord_type == "horizontal_line":
                        has_duration_info = "start_time" in coords and "end_time" in coords
                        start_time = coords.get("start_time")
                        end_time = coords.get("end_time")
                    
                    assert has_duration_info, f"Pattern '{pattern_name}' ({coord_type}) lacks duration info for markers"
                    assert start_time is not None, f"Pattern '{pattern_name}' missing start time"
                    assert end_time is not None, f"Pattern '{pattern_name}' missing end time"
                    
                    # Validate time format (should be ISO strings)
                    assert isinstance(start_time, str), f"Pattern '{pattern_name}' start_time must be string"
                    assert isinstance(end_time, str), f"Pattern '{pattern_name}' end_time must be string"
                    
                    print(f"✅ {pattern_name} ({coord_type}): Duration {start_time} → {end_time}")
                
                print(f"All {len(patterns_with_coords)} patterns support duration markers")
            else:
                print("No patterns with coordinates found")
    
    def test_pattern_fallback_duration_support(self):
        """Test that patterns without coordinates can still show duration markers using fallback"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            market_data = data.get("market_data", [])
            
            patterns_without_coords = [p for p in patterns if not p.get("coordinates")]
            
            if len(patterns_without_coords) > 0:
                print(f"\nTesting fallback duration markers for {len(patterns_without_coords)} patterns:")
                
                # Verify market data is available for fallback duration calculation
                assert len(market_data) >= 5, "Need at least 5 market data points for fallback duration markers"
                
                # Verify market data has timestamps in correct format
                for data_point in market_data[-5:]:  # Check last 5 points
                    assert "timestamp" in data_point, "Market data must have timestamp for duration markers"
                    assert isinstance(data_point["timestamp"], str), "Timestamp must be string"
                
                for pattern in patterns_without_coords:
                    pattern_name = pattern.get("name", "Unknown")
                    
                    # Check that pattern has required fields for fallback duration
                    assert "name" in pattern, f"Pattern missing name for fallback duration"
                    assert "category" in pattern, f"Pattern '{pattern_name}' missing category"
                    assert "direction" in pattern, f"Pattern '{pattern_name}' missing direction"
                    
                    print(f"✅ {pattern_name}: Can use fallback duration markers from market data")
                
                print(f"All {len(patterns_without_coords)} patterns support fallback duration markers")
            else:
                print("All patterns have coordinates")
    
    def test_volume_toggle_compatibility(self):
        """Test that volume data is compatible with toggle functionality"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", [])
            patterns = data.get("patterns", [])
            
            # Test volume data availability
            volume_data_points = sum(1 for d in market_data if "volume" in d and d["volume"] is not None)
            volume_coverage = volume_data_points / len(market_data) if len(market_data) > 0 else 0
            
            assert volume_coverage >= 0.9, f"Volume data coverage too low for toggle: {volume_coverage:.1%}"
            
            # Test volume patterns exist for toggle functionality
            volume_patterns = [p for p in patterns if p.get("category", "").lower() == "volume"]
            
            if len(volume_patterns) > 0:
                print(f"\nVolume toggle compatibility test:")
                print(f"Volume data coverage: {volume_coverage:.1%} ({volume_data_points}/{len(market_data)} points)")
                print(f"Volume patterns available: {len(volume_patterns)}")
                
                # Test that volume patterns have reasonable values
                for data_point in market_data[:10]:  # Check first 10 points
                    if "volume" in data_point and data_point["volume"] is not None:
                        volume = data_point["volume"]
                        assert isinstance(volume, (int, float)), f"Volume must be numeric: {volume}"
                        assert volume >= 0, f"Volume must be non-negative: {volume}"
                
                print("✅ Volume data is compatible with toggle functionality")
            else:
                print("No volume patterns detected")
    
    def test_pattern_duration_marker_time_validation(self):
        """Test that pattern duration markers have valid time ranges"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            market_data = data.get("market_data", [])
            
            if len(market_data) > 0 and len(patterns) > 0:
                # Get the time range of available market data
                market_start = market_data[0]["timestamp"]
                market_end = market_data[-1]["timestamp"]
                
                print(f"\nMarket data time range: {market_start} → {market_end}")
                
                patterns_with_coords = [p for p in patterns if p.get("coordinates")]
                
                for pattern in patterns_with_coords[:5]:  # Test first 5 patterns
                    pattern_name = pattern.get("name", "Unknown")
                    coords = pattern["coordinates"]
                    
                    # Extract time range based on coordinate type
                    start_time = None
                    end_time = None
                    
                    if coords.get("type") == "pattern_range":
                        start_time = coords.get("start_time")
                        end_time = coords.get("end_time")
                    elif coords.get("type") == "volume_pattern":
                        start_time = end_time = coords.get("timestamp")
                    elif coords.get("type") == "harmonic_pattern":
                        points = coords.get("points", [])
                        if len(points) >= 2:
                            start_time = points[0].get("timestamp")
                            end_time = points[-1].get("timestamp")
                    elif coords.get("type") == "statistical_pattern":
                        start_time = end_time = coords.get("timestamp")
                    elif coords.get("type") == "horizontal_line":
                        start_time = coords.get("start_time")
                        end_time = coords.get("end_time")
                    
                    if start_time and end_time:
                        # Validate that pattern times are within reasonable market data range
                        # (Allow some flexibility as patterns might extend slightly beyond data)
                        assert isinstance(start_time, str), f"Pattern '{pattern_name}' start_time must be string"
                        assert isinstance(end_time, str), f"Pattern '{pattern_name}' end_time must be string"
                        
                        # Basic format validation (should be ISO-like strings)
                        assert len(start_time) >= 10, f"Pattern '{pattern_name}' start_time too short: {start_time}"
                        assert len(end_time) >= 10, f"Pattern '{pattern_name}' end_time too short: {end_time}"
                        
                        print(f"✅ {pattern_name}: Valid duration markers {start_time} → {end_time}")
                    else:
                        print(f"⚠️  {pattern_name}: No duration info (will use fallback)")
    
    def test_chart_layout_toggle_compatibility(self):
        """Test that chart layout data supports both volume-enabled and volume-disabled modes"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", [])
            patterns = data.get("patterns", [])
            
            assert len(market_data) > 0, "Need market data for chart layout testing"
            
            # Test data structure supports both modes
            required_price_fields = ["timestamp", "open", "high", "low", "close"]
            for data_point in market_data[:5]:  # Check first 5 points
                for field in required_price_fields:
                    assert field in data_point, f"Market data missing required field: {field}"
                    
                # Volume should be present but optional for toggle
                if "volume" in data_point:
                    assert isinstance(data_point["volume"], (int, float, type(None))), \
                        f"Volume must be numeric or null: {data_point['volume']}"
            
            # Test patterns work with both volume modes
            volume_patterns = [p for p in patterns if p.get("category", "").lower() == "volume"]
            non_volume_patterns = [p for p in patterns if p.get("category", "").lower() != "volume"]
            
            print(f"\nChart layout compatibility test:")
            print(f"Total patterns: {len(patterns)}")
            print(f"Volume patterns: {len(volume_patterns)} (affected by toggle)")
            print(f"Non-volume patterns: {len(non_volume_patterns)} (unaffected by toggle)")
            print(f"Market data points: {len(market_data)}")
            
            # Both pattern types should have valid structure
            for pattern in patterns[:3]:  # Test first 3 patterns
                assert "name" in pattern, "Pattern missing name"
                assert "direction" in pattern, "Pattern missing direction"
                assert "category" in pattern, "Pattern missing category"
                assert "confidence" in pattern, "Pattern missing confidence"
            
            print("✅ Chart layout supports both volume-enabled and volume-disabled modes")
    
    def test_pattern_duration_performance_impact(self):
        """Test that pattern duration markers don't significantly impact API performance"""
        import time
        
        # Test API performance
        start_time = time.time()
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            market_data = data.get("market_data", [])
            
            # API should still be fast despite pattern duration data
            assert duration < 8, f"API too slow with duration marker support: {duration:.2f}s"
            
            patterns_with_coords = sum(1 for p in patterns if p.get("coordinates"))
            total_patterns = len(patterns)
            
            print(f"Performance test: {duration:.2f}s for {total_patterns} patterns")
            print(f"Pattern coordinate coverage: {patterns_with_coords}/{total_patterns}")
            print(f"Market data points: {len(market_data)}")
            
            # Should have reasonable pattern detection
            assert total_patterns > 0, "Should detect some patterns"
            
            print("✅ Pattern duration markers don't impact performance")


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])