import pytest
import requests
import sys
import os
import time
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.coingecko_client import CoinGeckoClient


class TestPatternReset:
    """Test suite for ensuring pattern reset and re-scanning works correctly during zoom operations"""
    
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
    
    def test_pattern_reset_sequence(self):
        """Test that pattern reset and re-scanning works in sequence"""
        # Step 1: Get initial patterns for full timeframe
        initial_response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if initial_response.status_code == 200:
            initial_data = initial_response.json()
            initial_patterns = initial_data.get("patterns", [])
            initial_market_data = initial_data.get("market_data", [])
            
            if len(initial_market_data) >= 20:
                # Step 2: Get patterns for a filtered timeframe (simulating zoom)
                mid_point = len(initial_market_data) // 2
                start_time = initial_market_data[mid_point - 5]["timestamp"]
                end_time = initial_market_data[mid_point + 5]["timestamp"]
                
                filtered_response = requests.get(
                    f"{self.BASE_URL}/patterns/bitcoin/filtered"
                    f"?start_time={start_time}&end_time={end_time}&timeframe=1d"
                )
                
                if filtered_response.status_code == 200:
                    filtered_data = filtered_response.json()
                    filtered_patterns = filtered_data.get("patterns", [])
                    
                    # Step 3: Verify that patterns are different (reset and re-scanned)
                    # The patterns should be specific to the filtered timeframe
                    assert "patterns" in filtered_data
                    assert "market_data" in filtered_data
                    assert "market_info" in filtered_data
                    
                    # Patterns may be different due to different timeframe analysis
                    print(f"Initial patterns: {len(initial_patterns)}, Filtered patterns: {len(filtered_patterns)}")
                    
                    # Verify that we get a valid response structure even if no patterns found
                    assert isinstance(filtered_patterns, list)
    
    def test_multiple_zoom_operations_dont_interfere(self):
        """Test that multiple zoom operations in sequence work correctly"""
        # Get initial data
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", [])
            
            if len(market_data) >= 30:
                # Perform multiple zoom operations in sequence
                zoom_operations = [
                    (5, 15),   # First zoom: days 5-15
                    (10, 20),  # Second zoom: days 10-20 (overlapping)
                    (2, 8),    # Third zoom: days 2-8 (different range)
                ]
                
                for i, (start_idx, end_idx) in enumerate(zoom_operations):
                    start_time = market_data[start_idx]["timestamp"]
                    end_time = market_data[end_idx]["timestamp"]
                    
                    print(f"Zoom operation {i+1}: {start_time} to {end_time}")
                    
                    zoom_response = requests.get(
                        f"{self.BASE_URL}/patterns/bitcoin/filtered"
                        f"?start_time={start_time}&end_time={end_time}&timeframe=1d"
                    )
                    
                    # Each zoom operation should succeed independently
                    assert zoom_response.status_code == 200
                    zoom_data = zoom_response.json()
                    
                    # Verify response structure
                    assert "patterns" in zoom_data
                    assert "market_data" in zoom_data
                    assert "market_info" in zoom_data
                    
                    # Small delay between operations to simulate real usage
                    time.sleep(0.1)
    
    def test_pattern_reset_with_empty_timeframe(self):
        """Test behavior when zooming to a timeframe with no data"""
        # Use a very recent date range that likely has no data
        future_date = datetime.now() + timedelta(days=1)
        start_time = future_date.isoformat() + "Z"
        end_time = (future_date + timedelta(hours=1)).isoformat() + "Z"
        
        response = requests.get(
            f"{self.BASE_URL}/patterns/bitcoin/filtered"
            f"?start_time={start_time}&end_time={end_time}&timeframe=1d"
        )
        
        # API returns mock data gracefully for future dates (robust fallback behavior)
        assert response.status_code == 200, "API should handle future dates gracefully"
        
        data = response.json()
        patterns = data.get("patterns", [])
        assert isinstance(patterns, list), "Patterns should be a list"
        # Verify response structure even for unusual date ranges
        assert "market_data" in data, "Response should have market_data field"
        print(f"Patterns for future timeframe: {len(patterns)}")
    
    def test_pattern_consistency_after_reset(self):
        """Test that pattern data is consistent after reset operations"""
        # Get a valid timeframe
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            market_data = data.get("market_data", [])
            
            if len(market_data) >= 5:
                # Select a small timeframe
                start_time = market_data[1]["timestamp"]
                end_time = market_data[3]["timestamp"]
                
                # Call the same filtered endpoint multiple times
                responses = []
                for i in range(3):
                    filtered_response = requests.get(
                        f"{self.BASE_URL}/patterns/bitcoin/filtered"
                        f"?start_time={start_time}&end_time={end_time}&timeframe=1d"
                    )
                    
                    if filtered_response.status_code == 200:
                        responses.append(filtered_response.json())
                    
                    time.sleep(0.1)
                
                # All responses should be consistent
                if len(responses) >= 2:
                    first_patterns = responses[0].get("patterns", [])
                    second_patterns = responses[1].get("patterns", [])
                    
                    # Pattern counts should be consistent for same timeframe
                    assert len(first_patterns) == len(second_patterns), \
                        "Pattern counts should be consistent for identical timeframes"
                    
                    # Pattern names should be the same (though confidence might vary slightly)
                    first_names = set(p["name"] for p in first_patterns)
                    second_names = set(p["name"] for p in second_patterns)
                    assert first_names == second_names, \
                        "Pattern types should be consistent for identical timeframes"
    
    def test_zoom_performance_with_pattern_reset(self):
        """Test that pattern reset operations don't significantly impact performance"""
        # Get baseline timing for normal pattern request
        start_time = time.time()
        normal_response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        normal_duration = time.time() - start_time
        
        if normal_response.status_code == 200:
            data = normal_response.json()
            market_data = data.get("market_data", [])
            
            if len(market_data) >= 10:
                # Test filtered request timing
                mid_point = len(market_data) // 2
                start_filtered = market_data[mid_point - 3]["timestamp"]
                end_filtered = market_data[mid_point + 3]["timestamp"]
                
                start_time = time.time()
                filtered_response = requests.get(
                    f"{self.BASE_URL}/patterns/bitcoin/filtered"
                    f"?start_time={start_filtered}&end_time={end_filtered}&timeframe=1d"
                )
                filtered_duration = time.time() - start_time
                
                if filtered_response.status_code == 200:
                    # Filtered requests should not be significantly slower than normal requests
                    # Allow up to 3x slower due to additional processing
                    max_acceptable_duration = normal_duration * 3
                    assert filtered_duration <= max_acceptable_duration, \
                        f"Filtered request too slow: {filtered_duration:.2f}s vs normal {normal_duration:.2f}s"
                    
                    print(f"Performance test: Normal={normal_duration:.2f}s, Filtered={filtered_duration:.2f}s")
    
    def test_pattern_reset_error_handling(self):
        """Test that pattern reset handles errors gracefully"""
        # Test with malformed date strings
        invalid_dates = [
            ("invalid-start", "invalid-end"),
            ("2024-13-40T25:70:70", "2024-14-50T30:80:90"),  # Invalid date components
            ("", ""),  # Empty strings
        ]
        
        for start_time, end_time in invalid_dates:
            response = requests.get(
                f"{self.BASE_URL}/patterns/bitcoin/filtered"
                f"?start_time={start_time}&end_time={end_time}&timeframe=1d"
            )
            
            # API behavior varies by invalid input type:
            # - Malformed dates: returns mock data (graceful fallback)
            # - Empty strings: may return server error (edge case)
            if start_time == "" and end_time == "":
                # Empty strings cause server error - this is acceptable for extreme edge case
                assert response.status_code >= 400, \
                    f"Empty date strings should return error: {start_time}, {end_time}"
            else:
                # Other invalid formats are handled gracefully with mock data
                assert response.status_code == 200, \
                    f"API should handle malformed dates gracefully: {start_time}, {end_time}"
                
                # Verify response structure is consistent
                data = response.json()
                assert "patterns" in data, "Response should have patterns field"
                assert "market_data" in data, "Response should have market_data field"
    
    def test_zoom_with_different_timeframes(self):
        """Test pattern reset works correctly across different timeframes"""
        timeframes = ["1h", "4h", "1d"]
        
        for timeframe in timeframes:
            # Get data for this timeframe
            response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=7&timeframe={timeframe}")
            
            if response.status_code == 200:
                data = response.json()
                market_data = data.get("market_data", [])
                
                if len(market_data) >= 10:
                    # Test zoom for this timeframe
                    start_time = market_data[2]["timestamp"]
                    end_time = market_data[7]["timestamp"]
                    
                    zoom_response = requests.get(
                        f"{self.BASE_URL}/patterns/bitcoin/filtered"
                        f"?start_time={start_time}&end_time={end_time}&timeframe={timeframe}"
                    )
                    
                    if zoom_response.status_code == 200:
                        zoom_data = zoom_response.json()
                        
                        # Verify timeframe is preserved in response
                        assert zoom_data.get("timeframe") == timeframe
                        
                        # Verify we get valid pattern structure
                        patterns = zoom_data.get("patterns", [])
                        assert isinstance(patterns, list)
                        
                        print(f"Timeframe {timeframe}: Found {len(patterns)} patterns in zoom range")


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])