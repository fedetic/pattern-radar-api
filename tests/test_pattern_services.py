"""
Test cases for pattern detection services
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import services to test
from services.base_pattern_service import BasePatternService
from services.candlestick_service import CandlestickPatternService
from services.chart_patterns_service import ChartPatternsService
from services.pattern_orchestrator import PatternOrchestrator

class TestBasePatternService:
    """Test the base pattern service functionality"""
    
    def test_validate_dataframe_valid(self):
        """Test DataFrame validation with valid data"""
        service = BasePatternService.__new__(BasePatternService)  # Create instance without calling __init__
        service.__init__()
        
        # Create valid test data
        dates = pd.date_range(start='2023-01-01', periods=10, freq='D')
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104, 105, 104, 103, 102, 101],
            'high': [105, 106, 107, 108, 109, 110, 109, 108, 107, 106],
            'low': [95, 96, 97, 98, 99, 100, 99, 98, 97, 96],
            'close': [104, 105, 106, 107, 108, 109, 108, 107, 106, 105]
        }, index=dates)
        
        assert service._validate_dataframe(df) == True
    
    def test_validate_dataframe_invalid(self):
        """Test DataFrame validation with invalid data"""
        service = BasePatternService.__new__(BasePatternService)
        service.__init__()
        
        # Test empty DataFrame
        empty_df = pd.DataFrame()
        assert service._validate_dataframe(empty_df) == False
        
        # Test None
        assert service._validate_dataframe(None) == False
        
        # Test missing columns
        incomplete_df = pd.DataFrame({'open': [100, 101], 'high': [105, 106]})
        assert service._validate_dataframe(incomplete_df) == False
        
        # Test insufficient length
        short_df = pd.DataFrame({
            'open': [100], 'high': [105], 'low': [95], 'close': [104]
        })
        assert service._validate_dataframe(short_df, min_length=5) == False
    
    def test_get_pattern_color(self):
        """Test pattern color assignment"""
        service = BasePatternService.__new__(BasePatternService)
        service.__init__()
        
        assert service._get_pattern_color('bullish') == '#10B981'
        assert service._get_pattern_color('bearish') == '#EF4444'
        assert service._get_pattern_color('neutral') == '#F59E0B'
        assert service._get_pattern_color('unknown') == '#6B7280'
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        service = BasePatternService.__new__(BasePatternService)
        service.__init__()
        
        # Test normal case
        factors = [0.8, 0.7, 0.9]
        confidence = service._calculate_confidence(factors)
        assert 10 <= confidence <= 100
        
        # Test empty factors
        confidence = service._calculate_confidence([])
        assert confidence == 50
        
        # Test extreme values
        confidence = service._calculate_confidence([2.0])  # Should cap at 100
        assert confidence == 100

class TestCandlestickPatternService:
    """Test candlestick pattern detection"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLC data for testing"""
        dates = pd.date_range(start='2023-01-01', periods=20, freq='D')
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic OHLC data
        prices = []
        base_price = 100
        
        for i in range(20):
            open_price = base_price + np.random.normal(0, 2)
            close_price = open_price + np.random.normal(0, 3)
            high_price = max(open_price, close_price) + np.random.uniform(0.5, 2)
            low_price = min(open_price, close_price) - np.random.uniform(0.5, 2)
            
            prices.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price
            })
            base_price = close_price
        
        return pd.DataFrame(prices, index=dates)
    
    def test_pattern_detection(self, sample_data):
        """Test basic pattern detection functionality"""
        service = CandlestickPatternService()
        patterns = service.detect_patterns(sample_data)
        
        # Should return a list
        assert isinstance(patterns, list)
        
        # Each pattern should have required fields
        for pattern in patterns:
            assert 'name' in pattern
            assert 'category' in pattern
            assert 'confidence' in pattern
            assert 'direction' in pattern
            assert 'description' in pattern
            assert pattern['category'] == 'Candle'
    
    def test_pattern_detection_empty_data(self):
        """Test pattern detection with empty/invalid data"""
        service = CandlestickPatternService()
        
        # Test with empty DataFrame
        patterns = service.detect_patterns(pd.DataFrame())
        assert patterns == []
        
        # Test with None
        patterns = service.detect_patterns(None)
        assert patterns == []

class TestChartPatternsService:
    """Test chart pattern detection"""
    
    @pytest.fixture
    def trending_data(self):
        """Create trending price data for testing"""
        dates = pd.date_range(start='2023-01-01', periods=60, freq='D')
        
        # Create upward trending data
        base_prices = np.linspace(100, 150, 60)
        noise = np.random.normal(0, 2, 60)
        
        prices = []
        for i, (base_price, noise_val) in enumerate(zip(base_prices, noise)):
            open_price = base_price + noise_val
            close_price = base_price + noise_val + np.random.normal(0, 1)
            high_price = max(open_price, close_price) + abs(np.random.normal(0, 1))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, 1))
            
            prices.append({
                'open': open_price,
                'high': high_price, 
                'low': low_price,
                'close': close_price,
                'volume': np.random.uniform(1000, 5000)
            })
        
        return pd.DataFrame(prices, index=dates)
    
    def test_trend_detection(self, trending_data):
        """Test trend pattern detection"""
        service = ChartPatternsService()
        patterns = service.detect_patterns(trending_data)
        
        # Should detect some patterns
        assert len(patterns) > 0
        
        # Check for trend patterns
        trend_patterns = [p for p in patterns if 'Trend' in p['name']]
        assert len(trend_patterns) > 0
        
        # Verify pattern structure
        for pattern in patterns:
            assert pattern['category'] in ['Chart', 'Price Action']
            assert 'coordinates' in pattern
    
    def test_support_resistance_detection(self):
        """Test support/resistance level detection"""
        # Create data that bounces between levels
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        prices = []
        
        for i in range(30):
            # Oscillate between 95-105 range
            base = 100 + 5 * np.sin(i * 0.5)
            open_price = base + np.random.normal(0, 1)
            close_price = base + np.random.normal(0, 1) 
            high_price = max(open_price, close_price) + abs(np.random.normal(0, 0.5))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, 0.5))
            
            prices.append({
                'open': open_price,
                'high': high_price,
                'low': low_price, 
                'close': close_price
            })
        
        df = pd.DataFrame(prices, index=dates)
        
        service = ChartPatternsService()
        patterns = service.detect_patterns(df)
        
        # Should return valid patterns
        assert isinstance(patterns, list)
        
        # Check pattern structure
        for pattern in patterns:
            assert 'coordinates' in pattern
            if pattern['coordinates'].get('type') == 'horizontal_line':
                assert 'level' in pattern['coordinates']

class TestPatternOrchestrator:
    """Test the pattern orchestrator"""
    
    @pytest.fixture
    def comprehensive_data(self):
        """Create comprehensive test data"""
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        
        prices = []
        base_price = 100
        
        for i in range(100):
            # Add some patterns and trends
            trend = 0.1 * i  # Slight upward trend
            cycle = 10 * np.sin(i * 0.1)  # Cyclical pattern
            noise = np.random.normal(0, 2)
            
            base_price = 100 + trend + cycle + noise
            
            open_price = base_price + np.random.normal(0, 1)
            close_price = base_price + np.random.normal(0, 1)
            high_price = max(open_price, close_price) + abs(np.random.normal(0, 1))
            low_price = min(open_price, close_price) - abs(np.random.normal(0, 1))
            
            prices.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': np.random.uniform(1000, 10000)
            })
        
        return pd.DataFrame(prices, index=dates)
    
    def test_orchestrator_analysis(self, comprehensive_data):
        """Test the full orchestrator analysis"""
        orchestrator = PatternOrchestrator()
        result = orchestrator.analyze_patterns(comprehensive_data)
        
        # Check result structure
        assert isinstance(result, dict)
        assert 'patterns' in result
        assert 'market_data' in result
        assert 'pattern_statistics' in result
        assert 'services_used' in result
        
        # Check patterns
        patterns = result['patterns']
        assert isinstance(patterns, list)
        
        for pattern in patterns[:5]:  # Check first 5 patterns
            assert 'name' in pattern
            assert 'category' in pattern
            assert 'confidence' in pattern
            assert 'direction' in pattern
            assert isinstance(pattern['confidence'], int)
            assert 0 <= pattern['confidence'] <= 100
        
        # Check market data
        market_data = result['market_data']
        assert len(market_data) == len(comprehensive_data)
        
        for data_point in market_data[:3]:  # Check first 3 points
            assert 'timestamp' in data_point
            assert 'open' in data_point
            assert 'high' in data_point
            assert 'low' in data_point
            assert 'close' in data_point
        
        # Check statistics
        stats = result['pattern_statistics']
        assert 'total_patterns' in stats
        assert 'by_category' in stats
        assert 'by_direction' in stats
    
    def test_service_status(self):
        """Test service status reporting"""
        orchestrator = PatternOrchestrator()
        status = orchestrator.get_service_status()
        
        assert isinstance(status, dict)
        assert 'core_services' in status
        assert 'optional_services' in status
        assert 'total_services' in status
        
        # Core services should include candlestick and chart
        core_services = status['core_services']
        assert 'candlestick' in core_services
        assert 'chart' in core_services

# Utility functions for test data generation
def create_hammer_pattern():
    """Create data with a clear hammer pattern"""
    dates = pd.date_range(start='2023-01-01', periods=5, freq='D')
    
    # Regular candles followed by hammer
    data = [
        {'open': 100, 'high': 105, 'low': 95, 'close': 98},
        {'open': 98, 'high': 103, 'low': 93, 'close': 95},
        {'open': 95, 'high': 100, 'low': 90, 'close': 92},
        {'open': 92, 'high': 97, 'low': 85, 'close': 94},  # Hammer pattern
        {'open': 94, 'high': 99, 'low': 89, 'close': 96}
    ]
    
    return pd.DataFrame(data, index=dates)

def create_doji_pattern():
    """Create data with a doji pattern"""
    dates = pd.date_range(start='2023-01-01', periods=5, freq='D') 
    
    data = [
        {'open': 100, 'high': 105, 'low': 95, 'close': 102},
        {'open': 102, 'high': 107, 'low': 97, 'close': 100},
        {'open': 100, 'high': 105, 'low': 95, 'close': 100.1},  # Doji pattern
        {'open': 100, 'high': 105, 'low': 95, 'close': 103},
        {'open': 103, 'high': 108, 'low': 98, 'close': 105}
    ]
    
    return pd.DataFrame(data, index=dates)

if __name__ == "__main__":
    pytest.main([__file__])