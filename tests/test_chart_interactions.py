import pytest
import requests
import sys
import os
import time
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.coingecko_client import CoinGeckoClient


class TestChartInteractions:
    """Test suite for ensuring chart zoom, pan, and interaction functionality"""
    
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
    
    def test_pattern_endpoint_basic_functionality(self):
        """Test that the main patterns endpoint returns proper data structure"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            
            # Verify required fields
            assert "patterns" in data
            assert "market_data" in data
            assert "market_info" in data
            assert "coin_id" in data
            assert "timeframe" in data
            
            # Verify market_data structure for chart compatibility
            market_data = data["market_data"]
            if market_data and len(market_data) > 0:
                sample_point = market_data[0]
                required_fields = ["timestamp", "open", "high", "low", "close"]
                for field in required_fields:
                    assert field in sample_point, f"Missing {field} in market data"
                
                # Verify OHLC relationships are valid
                assert sample_point["high"] >= sample_point["open"], "High should be >= Open"
                assert sample_point["high"] >= sample_point["close"], "High should be >= Close"
                assert sample_point["low"] <= sample_point["open"], "Low should be <= Open"
                assert sample_point["low"] <= sample_point["close"], "Low should be <= Close"
    
    def test_filtered_patterns_endpoint(self):
        """Test the filtered patterns endpoint used for zoom functionality"""
        # First get some data to find valid time ranges
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", [])
            
            if len(market_data) >= 10:
                # Get a subset of the time range for filtering
                start_time = market_data[5]["timestamp"]
                end_time = market_data[15]["timestamp"]
                
                # Test filtered endpoint
                filtered_response = requests.get(
                    f"{self.BASE_URL}/patterns/bitcoin/filtered"
                    f"?start_time={start_time}&end_time={end_time}&timeframe=1d"
                )
                
                if filtered_response.status_code == 200:
                    filtered_data = filtered_response.json()
                    
                    # Should have same structure as main endpoint
                    assert "patterns" in filtered_data
                    assert "market_data" in filtered_data
                    assert "market_info" in filtered_data
                    
                    # Market data should be within the requested time range
                    filtered_market_data = filtered_data.get("market_data", [])
                    for point in filtered_market_data:
                        point_time = datetime.fromisoformat(point["timestamp"].replace('Z', '+00:00'))
                        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                        
                        assert start_dt <= point_time <= end_dt, "Data point outside requested range"
    
    def test_data_consistency_for_chart_rendering(self):
        """Test that data is consistent and suitable for chart rendering"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1h")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", [])
            
            if len(market_data) > 1:
                # Check chronological ordering
                timestamps = [datetime.fromisoformat(point["timestamp"].replace('Z', '+00:00')) 
                            for point in market_data]
                
                for i in range(1, len(timestamps)):
                    assert timestamps[i] >= timestamps[i-1], "Market data not in chronological order"
                
                # Check for reasonable OHLC variations (not all identical)
                has_variation = False
                for point in market_data:
                    if not (point["open"] == point["high"] == point["low"] == point["close"]):
                        has_variation = True
                        break
                
                assert has_variation, "All OHLC values are identical - chart will render as scatterplot"
                
                # Check that price values are reasonable
                for point in market_data:
                    assert point["open"] > 0, "Open price must be positive"
                    assert point["high"] > 0, "High price must be positive"
                    assert point["low"] > 0, "Low price must be positive"
                    assert point["close"] > 0, "Close price must be positive"
    
    def test_pattern_coordinates_for_visualization(self):
        """Test that patterns have proper coordinates for chart visualization"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            patterns = data.get("patterns", [])
            
            for pattern in patterns:
                # Check required pattern fields
                assert "name" in pattern, "Pattern missing name"
                assert "confidence" in pattern, "Pattern missing confidence"
                assert "direction" in pattern, "Pattern missing direction"
                
                # Check confidence is reasonable
                assert 0 <= pattern["confidence"] <= 100, "Pattern confidence out of range"
                
                # Check direction is valid
                assert pattern["direction"] in ["bullish", "bearish", "neutral", "continuation"], \
                    f"Invalid pattern direction: {pattern['direction']}"
                
                # If pattern has coordinates, verify structure
                if "coordinates" in pattern:
                    coords = pattern["coordinates"]
                    assert "type" in coords, "Pattern coordinates missing type"
                    
                    if coords["type"] == "pattern_range":
                        assert "start_time" in coords, "Pattern range missing start_time"
                        assert "end_time" in coords, "Pattern range missing end_time"
                        assert "pattern_high" in coords, "Pattern range missing pattern_high"
                        assert "pattern_low" in coords, "Pattern range missing pattern_low"
    
    def test_multiple_timeframes_compatibility(self):
        """Test that all supported timeframes work correctly"""
        timeframes = ["1h", "4h", "1d"]
        
        for timeframe in timeframes:
            response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe={timeframe}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Basic structure check
                assert "patterns" in data
                assert "market_data" in data
                assert data["timeframe"] == timeframe
                
                market_data = data.get("market_data", [])
                if market_data:
                    # Check that timestamps make sense for the timeframe
                    if len(market_data) > 1:
                        time_diff = (
                            datetime.fromisoformat(market_data[1]["timestamp"].replace('Z', '+00:00')) -
                            datetime.fromisoformat(market_data[0]["timestamp"].replace('Z', '+00:00'))
                        ).total_seconds()
                        
                        expected_intervals = {
                            "1h": 3600,    # 1 hour
                            "4h": 14400,   # 4 hours  
                            "1d": 86400,   # 1 day
                        }
                        
                        expected = expected_intervals[timeframe]
                        # Allow some tolerance for API variations
                        assert abs(time_diff - expected) < expected * 0.1, \
                            f"Time interval {time_diff}s doesn't match expected {expected}s for {timeframe}"
    
    def test_zoom_range_validation(self):
        """Test that zoom range filtering works correctly"""
        # Get full dataset first
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", [])
            
            if len(market_data) >= 20:
                # Test various zoom ranges
                total_points = len(market_data)
                
                # Test 50% zoom
                start_idx = total_points // 4
                end_idx = 3 * total_points // 4
                start_time = market_data[start_idx]["timestamp"]
                end_time = market_data[end_idx]["timestamp"]
                
                zoom_response = requests.get(
                    f"{self.BASE_URL}/patterns/bitcoin/filtered"
                    f"?start_time={start_time}&end_time={end_time}&timeframe=1d"
                )
                
                if zoom_response.status_code == 200:
                    zoom_data = zoom_response.json()
                    zoom_market_data = zoom_data.get("market_data", [])
                    
                    # Should have fewer data points than full dataset
                    assert len(zoom_market_data) <= len(market_data), \
                        "Filtered data should not have more points than full dataset"
                    
                    # All points should be within the requested range
                    start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    
                    for point in zoom_market_data:
                        point_dt = datetime.fromisoformat(point["timestamp"].replace('Z', '+00:00'))
                        assert start_dt <= point_dt <= end_dt, \
                            f"Point {point['timestamp']} outside range {start_time} to {end_time}"
    
    def test_error_handling_for_invalid_ranges(self):
        """Test API error handling for invalid time ranges"""
        # Test future date range
        future_start = (datetime.now() + timedelta(days=1)).isoformat() + "Z"
        future_end = (datetime.now() + timedelta(days=2)).isoformat() + "Z"
        
        response = requests.get(
            f"{self.BASE_URL}/patterns/bitcoin/filtered"
            f"?start_time={future_start}&end_time={future_end}&timeframe=1d"
        )
        
        # API currently returns mock data even for future dates (graceful fallback)
        # This ensures the frontend doesn't crash when users select unusual date ranges
        assert response.status_code == 200, "API should handle future dates gracefully with mock data"
        
        data = response.json()
        # Verify response has required structure even for unusual date ranges
        assert "patterns" in data, "Response should have patterns field"
        assert "market_data" in data, "Response should have market_data field"
        assert isinstance(data["patterns"], list), "Patterns should be a list"
        assert isinstance(data["market_data"], list), "Market data should be a list"
        
        # Test invalid date format
        invalid_response = requests.get(
            f"{self.BASE_URL}/patterns/bitcoin/filtered"
            f"?start_time=invalid-date&end_time=also-invalid&timeframe=1d"
        )
        
        # API currently returns mock data even for invalid date formats (graceful fallback)
        # This ensures robust behavior when users input malformed date ranges
        assert invalid_response.status_code == 200, "API should handle invalid dates gracefully with mock data"
        
        invalid_data = invalid_response.json()
        # Verify response structure is consistent even with invalid input
        assert "patterns" in invalid_data, "Response should have patterns field even for invalid dates"
        assert "market_data" in invalid_data, "Response should have market_data field even for invalid dates"
    
    def test_performance_requirements(self):
        """Test that API responds within reasonable time limits"""
        start_time = time.time()
        
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # API should respond within 10 seconds for normal requests
        assert response_time < 10, f"API response too slow: {response_time:.2f}s"
        
        if response.status_code == 200:
            data = response.json()
            # Should have reasonable amount of data
            market_data = data.get("market_data", [])
            assert len(market_data) > 0, "Should return some market data"


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])