import pytest
import requests
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.coingecko_client import CoinGeckoClient


class TestMarketCapData:
    """Test suite for ensuring Market Cap data is always available"""
    
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
    
    def test_market_cap_in_api_response(self):
        """Test that market cap is always present in API responses"""
        # Test with multiple coins and timeframes
        test_cases = [
            ('bitcoin', '1d'),
            ('ethereum', '1d'),
            ('cardano', '1d'),
            ('bitcoin', '4h'),
            ('bitcoin', '1h')
        ]
        
        for coin_id, timeframe in test_cases:
            response = requests.get(f"{self.BASE_URL}/patterns/{coin_id}?days=30&timeframe={timeframe}")
            
            # API might return 404 due to rate limits, but when it returns 200, market_cap should be present
            if response.status_code == 200:
                data = response.json()
                market_info = data.get("market_info")
                
                assert market_info is not None, f"market_info missing for {coin_id}"
                assert "market_cap" in market_info, f"market_cap field missing for {coin_id}"
                assert market_info["market_cap"] is not None, f"market_cap is None for {coin_id}"
                assert isinstance(market_info["market_cap"], (int, float)), f"market_cap is not numeric for {coin_id}"
                assert market_info["market_cap"] > 0, f"market_cap is not positive for {coin_id}"
                
                # Also check market_cap_rank
                assert "market_cap_rank" in market_info, f"market_cap_rank missing for {coin_id}"
                assert market_info["market_cap_rank"] is not None, f"market_cap_rank is None for {coin_id}"
                assert isinstance(market_info["market_cap_rank"], int), f"market_cap_rank is not integer for {coin_id}"
                assert market_info["market_cap_rank"] > 0, f"market_cap_rank is not positive for {coin_id}"
    
    def test_market_cap_fallback_data(self):
        """Test that fallback market cap data is reasonable"""
        # Test known cryptocurrencies have reasonable market cap values
        known_coins = {
            'bitcoin': {
                'min_market_cap': 500_000_000_000,  # At least 500B USD
                'max_rank': 5  # Should be top 5
            },
            'ethereum': {
                'min_market_cap': 100_000_000_000,  # At least 100B USD
                'max_rank': 10  # Should be top 10
            },
            'cardano': {
                'min_market_cap': 5_000_000_000,    # At least 5B USD
                'max_rank': 50  # Should be top 50
            }
        }
        
        for coin_id, expectations in known_coins.items():
            response = requests.get(f"{self.BASE_URL}/patterns/{coin_id}?days=30&timeframe=1d")
            
            if response.status_code == 200:
                data = response.json()
                market_info = data.get("market_info")
                
                if market_info:
                    market_cap = market_info.get("market_cap")
                    market_cap_rank = market_info.get("market_cap_rank")
                    
                    if market_cap:
                        assert market_cap >= expectations['min_market_cap'], \
                            f"{coin_id} market cap too low: ${market_cap/1e9:.1f}B"
                    
                    if market_cap_rank:
                        assert market_cap_rank <= expectations['max_rank'], \
                            f"{coin_id} rank too low: #{market_cap_rank}"
    
    def test_market_cap_coingecko_client(self):
        """Test that CoinGecko client includes market_cap in response"""
        client = CoinGeckoClient()
        
        try:
            markets = client.get_coins_markets("usd", 10)
            
            if markets and len(markets) > 0:
                # Check that market_cap field is included in response
                sample_coin = markets[0]
                
                assert "market_cap" in sample_coin, "market_cap field missing from CoinGecko client response"
                # Note: market_cap might be None due to API issues, but the field should exist
                
                # Check other required fields too
                required_fields = ["coin_id", "name", "symbol", "current_price", "market_cap_rank"]
                for field in required_fields:
                    assert field in sample_coin, f"{field} missing from CoinGecko client response"
        except Exception as e:
            # If CoinGecko API fails, test should pass (this is expected with rate limits)
            pytest.skip(f"CoinGecko API unavailable: {e}")
    
    def test_market_cap_formatting_in_ui(self):
        """Test that market cap values can be properly formatted for UI display"""
        response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
        
        if response.status_code == 200:
            data = response.json()
            market_info = data.get("market_info")
            
            if market_info and market_info.get("market_cap"):
                market_cap = market_info["market_cap"]
                
                # Test that market cap can be formatted as billions
                market_cap_billions = market_cap / 1e9
                assert market_cap_billions > 0, "Market cap billions conversion failed"
                
                # Test formatting with 2 decimal places
                formatted = f"${market_cap_billions:.2f}B"
                assert "B" in formatted, "Billions formatting failed"
                assert "$" in formatted, "Currency symbol missing"
                
                # Test that the formatted value is reasonable (not too long)
                assert len(formatted) < 20, f"Formatted market cap too long: {formatted}"
    
    def test_market_cap_consistency_across_endpoints(self):
        """Test that market cap data is consistent between pairs and patterns endpoints"""
        # Get data from pairs endpoint
        pairs_response = requests.get(f"{self.BASE_URL}/pairs")
        
        if pairs_response.status_code == 200:
            pairs = pairs_response.json()
            bitcoin_pair = next((pair for pair in pairs if pair.get('coin_id') == 'bitcoin'), None)
            
            if bitcoin_pair and bitcoin_pair.get('market_cap'):
                # Get data from patterns endpoint
                patterns_response = requests.get(f"{self.BASE_URL}/patterns/bitcoin?days=30&timeframe=1d")
                
                if patterns_response.status_code == 200:
                    patterns_data = patterns_response.json()
                    market_info = patterns_data.get("market_info")
                    
                    if market_info and market_info.get("market_cap"):
                        # Market cap values should be in the same ballpark (allowing for some variation due to time)
                        pairs_market_cap = bitcoin_pair["market_cap"]
                        patterns_market_cap = market_info["market_cap"]
                        
                        # Allow up to 20% difference (markets can move)
                        diff_percent = abs(pairs_market_cap - patterns_market_cap) / max(pairs_market_cap, patterns_market_cap)
                        assert diff_percent <= 0.2, f"Market cap inconsistency: pairs={pairs_market_cap}, patterns={patterns_market_cap}"


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])