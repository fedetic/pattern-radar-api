import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.coingecko_client import CoinGeckoClient


class TestCoinGeckoClient:
    """Test suite for CoinGecko client OHLC data generation"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = CoinGeckoClient()
    
    def test_fallback_ohlc_data_generation(self):
        """Test that fallback OHLC data is generated correctly"""
        # Test daily fallback
        df = self.client._generate_fallback_ohlc_data('bitcoin', '1d', 30)
        
        assert df is not None
        assert not df.empty
        assert len(df) <= 30  # Should not exceed requested days
        assert len(df) >= 5   # Should have minimum data points
        
        # Check required columns
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            assert col in df.columns
        
        # Check OHLC relationships for each candle
        for idx, row in df.iterrows():
            assert row['low'] <= row['open'] <= row['high'], f"Invalid open price at {idx}"
            assert row['low'] <= row['close'] <= row['high'], f"Invalid close price at {idx}"
            assert row['high'] >= row['low'], f"High < Low at {idx}"
            assert row['volume'] > 0, f"Volume should be positive at {idx}"
    
    def test_fallback_weekly_data(self):
        """Test weekly fallback data generation"""
        df = self.client._generate_fallback_ohlc_data('bitcoin', '1w', 365)
        
        assert df is not None
        assert not df.empty
        assert len(df) <= 52  # Max 52 weeks
        
        # Check that we get weekly frequency data
        if len(df) > 1:
            time_diff = df.index[1] - df.index[0]
            assert time_diff.days >= 6  # Should be roughly 7 days apart
    
    def test_fallback_monthly_data(self):
        """Test monthly fallback data generation"""
        df = self.client._generate_fallback_ohlc_data('bitcoin', '1m', 365)
        
        assert df is not None
        assert not df.empty
        assert len(df) <= 12  # Max 12 months
        
        # Check that we get monthly frequency data
        if len(df) > 1:
            time_diff = df.index[1] - df.index[0]
            assert time_diff.days >= 28  # Should be roughly 30 days apart
    
    def test_price_ranges_realistic(self):
        """Test that generated prices are realistic"""
        df = self.client._generate_fallback_ohlc_data('bitcoin', '1d', 30)
        
        # Bitcoin prices should be reasonable (assuming base price ~67000)
        for idx, row in df.iterrows():
            assert 30000 <= row['close'] <= 150000, f"Unrealistic BTC price: {row['close']}"
            
            # Daily volatility should be reasonable (< 20% per day)
            daily_range = (row['high'] - row['low']) / row['close']
            assert daily_range <= 0.2, f"Excessive daily volatility: {daily_range*100:.1f}%"
    
    def test_different_coin_base_prices(self):
        """Test that different coins get appropriate base prices"""
        coins_to_test = ['bitcoin', 'ethereum', 'cardano', 'unknown_coin']
        
        for coin in coins_to_test:
            df = self.client._generate_fallback_ohlc_data(coin, '1d', 10)
            
            assert df is not None
            assert not df.empty
            
            # Check that prices are in reasonable ranges for each coin
            avg_price = df['close'].mean()
            if coin == 'bitcoin':
                assert 30000 <= avg_price <= 150000
            elif coin == 'ethereum':
                assert 1000 <= avg_price <= 10000
            elif coin == 'cardano':
                assert 0.1 <= avg_price <= 2.0
            elif coin == 'unknown_coin':
                assert 50 <= avg_price <= 200  # Default fallback price range
    
    @patch('services.coingecko_client.CoinGeckoClient.get_market_chart')
    def test_get_ohlc_data_with_api_failure(self, mock_get_market_chart):
        """Test that get_ohlc_data falls back to generated data when API fails"""
        # Mock API failure
        mock_get_market_chart.return_value = None
        
        # Test daily data (should not use fallback for small timeframes)
        df = self.client.get_ohlc_data('bitcoin', 'usd', 30, '1d')
        assert df is not None
        
        # Test weekly data (should use fallback when API fails)
        df = self.client.get_ohlc_data('bitcoin', 'usd', 90, '1w')
        assert df is not None
        assert not df.empty
    
    @patch('services.coingecko_client.CoinGeckoClient.get_market_chart')
    def test_market_chart_fallback_on_exception(self, mock_get_market_chart):
        """Test fallback when market chart raises exception"""
        # Mock exception
        mock_get_market_chart.side_effect = Exception("API Error")
        
        df = self.client._get_ohlc_from_market_chart('bitcoin', 'usd', 90, '1w')
        
        assert df is not None
        assert not df.empty
        assert len(df) > 0
    
    def test_timeframe_specific_periods(self):
        """Test that different timeframes generate appropriate number of periods"""
        test_cases = [
            ('1h', 7, 168),    # 7 days * 24 hours = 168 max
            ('4h', 7, 42),     # 7 days * 6 periods = 42 max  
            ('1d', 30, 30),    # 30 days
            ('1w', 365, 52),   # ~52 weeks max
            ('1m', 365, 12),   # 12 months max
        ]
        
        for timeframe, days, expected_max in test_cases:
            df = self.client._generate_fallback_ohlc_data('bitcoin', timeframe, days)
            assert len(df) <= expected_max, f"Too many periods for {timeframe}: {len(df)} > {expected_max}"
            assert len(df) > 0, f"No data generated for {timeframe}"
    
    def test_ohlc_mathematical_consistency(self):
        """Test mathematical consistency of OHLC data"""
        df = self.client._generate_fallback_ohlc_data('bitcoin', '1d', 50)
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Basic OHLC relationships
            assert row['low'] <= row['high'], f"Low > High at index {i}"
            assert row['low'] <= row['open'] <= row['high'], f"Open outside range at index {i}"
            assert row['low'] <= row['close'] <= row['high'], f"Close outside range at index {i}"
            
            # Volume should be positive
            assert row['volume'] > 0, f"Non-positive volume at index {i}"
            
            # Prices should be positive
            for price_col in ['open', 'high', 'low', 'close']:
                assert row[price_col] > 0, f"Non-positive {price_col} at index {i}"
    
    def test_consecutive_candles_continuity(self):
        """Test that consecutive candles have reasonable price continuity"""
        df = self.client._generate_fallback_ohlc_data('bitcoin', '1d', 30)
        
        if len(df) < 2:
            return  # Skip if insufficient data
        
        for i in range(1, len(df)):
            prev_close = df.iloc[i-1]['close']
            curr_open = df.iloc[i]['open']
            
            # Gap between previous close and current open should be reasonable (<10%)
            gap_percent = abs(curr_open - prev_close) / prev_close
            assert gap_percent <= 0.1, f"Excessive gap at index {i}: {gap_percent*100:.1f}%"


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])