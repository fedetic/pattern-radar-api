# Pattern Hero - Backend API

A FastAPI-based backend for crypto pattern analysis with real-time market data integration and technical analysis capabilities.

## Overview

The Pattern Hero backend is a Python FastAPI application that provides pattern analysis endpoints for cryptocurrency trading pairs. It integrates with CoinGecko API for market data and uses technical analysis libraries for pattern detection.

## Features

- **Pattern Analysis**: Comprehensive candlestick and chart pattern detection
- **Market Data Integration**: Real-time OHLCV data from CoinGecko API
- **Technical Analysis**: Uses ta-lib for advanced pattern recognition
- **Flexible Timeframes**: Support for multiple analysis timeframes
- **Fallback Systems**: Graceful degradation when dependencies unavailable
- **CORS Enabled**: Cross-origin support for frontend integration
- **Coordinate System**: Rich pattern coordinate data for visualization

## Technology Stack

- **FastAPI** - Modern, fast web framework
- **Python 3.8+** - Programming language
- **ta-lib** - Technical analysis library
- **pandas** - Data manipulation and analysis
- **requests** - HTTP client for API calls
- **uvicorn** - ASGI server

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd pattern-hero/pattern-radar-api
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the development server**
   ```bash
   uvicorn main:app --reload
   ```

5. **Access the API**
   Navigate to `http://localhost:8000`

## API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Available Endpoints

#### Health Check
```http
GET /
```
Returns API status and health information.

**Response:**
```json
{
  "message": "Pattern Hero API is running",
  "status": "healthy"
}
```

#### Get Trading Pairs
```http
GET /pairs
```
Returns available cryptocurrency trading pairs.

**Response:**
```json
[
  {
    "symbol": "BTC-USD",
    "base": "BTC",
    "quote": "USD",
    "label": "BTC/USD",
    "name": "Bitcoin",
    "coin_id": "bitcoin",
    "status": "active"
  }
]
```

#### Get Market Data
```http
GET /market-data/{coin_id}?vs_currency=usd&days=30
```
Returns OHLCV market data for a specific coin.

**Parameters:**
- `coin_id` (path): CoinGecko coin ID (e.g., "bitcoin", "ethereum")
- `vs_currency` (query): Currency for prices (default: "usd")
- `days` (query): Number of days of data (1-365, default: 30)

**Response:**
```json
{
  "coin_id": "bitcoin",
  "vs_currency": "usd",
  "days": 30,
  "data": [
    {
      "timestamp": "2025-01-01T00:00:00",
      "open": 45000.0,
      "high": 46000.0,
      "low": 44000.0,
      "close": 45500.0
    }
  ]
}
```

#### Get Pattern Analysis
```http
GET /patterns/{coin_id}?vs_currency=usd&days=30&timeframe=1d
```
Returns comprehensive pattern analysis for a cryptocurrency.

**Parameters:**
- `coin_id` (path): CoinGecko coin ID
- `vs_currency` (query): Currency for prices (default: "usd")
- `days` (query): Number of days for analysis (7-365, default: 30)
- `timeframe` (query): Analysis timeframe (default: "1d")

**Response:**
```json
{
  "coin_id": "bitcoin",
  "vs_currency": "usd",
  "timeframe": "1d",
  "analysis_date": "2025-01-01T12:00:00",
  "patterns": [
    {
      "name": "Hammer",
      "category": "Candle",
      "confidence": 85,
      "direction": "bullish",
      "latest_occurrence": 25,
      "timestamp": "2025-01-01T12:00:00",
      "coordinates": {
        "type": "pattern_range",
        "start_index": 25,
        "end_index": 25,
        "start_time": "2025-01-01T12:00:00",
        "end_time": "2025-01-01T12:00:00",
        "pattern_high": 46000.0,
        "pattern_low": 44000.0,
        "highlight_color": "#10B981",
        "pattern_name": "Hammer"
      },
      "description": "A bullish hammer pattern detected"
    }
  ],
  "market_data": [
    {
      "timestamp": "2025-01-01T00:00:00",
      "open": 45000.0,
      "high": 46000.0,
      "low": 44000.0,
      "close": 45500.0
    }
  ],
  "strongest_pattern": {
    "name": "Hammer",
    "confidence": 85
  }
}
```

## Pattern Detection System

### Pattern Categories

#### Candlestick Patterns
Implemented using ta-lib library:
- **Doji** - Indecision pattern
- **Hammer** - Bullish reversal
- **Hanging Man** - Bearish reversal
- **Engulfing Pattern** - Reversal confirmation
- **Morning Star** - Bullish reversal
- **Evening Star** - Bearish reversal
- **Shooting Star** - Bearish reversal
- **Three Black Crows** - Strong bearish signal
- **Three White Soldiers** - Strong bullish signal
- And many more...

#### Chart Patterns
- **Support/Resistance Levels** - Key price levels
- **Trend Patterns** - Moving average analysis
- **Breakout Patterns** - Price level breaks

### Coordinate System

Pattern coordinates provide visualization data:

#### Pattern Range (`pattern_range`)
For multi-candle patterns:
```json
{
  "type": "pattern_range",
  "start_index": 23,
  "end_index": 25,
  "start_time": "2025-01-01T10:00:00",
  "end_time": "2025-01-01T12:00:00",
  "pattern_high": 46000.0,
  "pattern_low": 44000.0,
  "highlight_color": "#10B981",
  "pattern_name": "Hammer"
}
```

#### Candlestick Highlight (`candlestick_highlight`)
For single candle patterns:
```json
{
  "type": "candlestick_highlight",
  "index": 25,
  "timestamp": "2025-01-01T12:00:00",
  "open": 45000.0,
  "high": 46000.0,
  "low": 44000.0,
  "close": 45500.0
}
```

#### Horizontal Line (`horizontal_line`)
For support/resistance:
```json
{
  "type": "horizontal_line",
  "level": 45000.0,
  "start_time": "2025-01-01T00:00:00",
  "end_time": "2025-01-01T12:00:00"
}
```

#### Trend Lines (`trend_lines`)
For moving averages:
```json
{
  "type": "trend_lines",
  "sma_20": 45200.0,
  "sma_50": 44800.0,
  "start_time": "2025-01-01T00:00:00",
  "end_time": "2025-01-01T12:00:00"
}
```

## Project Structure

```
pattern-radar-api/
├── main.py                    # FastAPI application entry point
├── services/
│   ├── coingecko_client.py   # CoinGecko API integration
│   ├── pattern_detector.py   # Pattern detection logic
│   └── __init__.py
├── requirements.txt           # Python dependencies
├── venv/                     # Virtual environment
├── README.md                 # This file
└── .env                      # Environment variables (optional)
```

## Configuration

### Environment Variables
Create a `.env` file (optional):
```env
# CoinGecko API configuration
COINGECKO_API_KEY=your-api-key-here

# CORS settings
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Development settings
DEBUG=true
```

### CORS Configuration
Current CORS settings allow all origins for development:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this in production
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Development

### Running Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Adding New Patterns

1. **Add to PatternDetector class**
   ```python
   def detect_new_pattern(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
       # Implementation here
       pass
   ```

2. **Update pattern categories**
   ```python
   self.candlestick_patterns = {
       'NEW_PATTERN': 'New Pattern Name',
       # ... existing patterns
   }
   ```

3. **Define coordinate generation**
   ```python
   def _get_new_pattern_coordinates(self, df: pd.DataFrame, index: int) -> Dict[str, Any]:
       # Return appropriate coordinate structure
       pass
   ```

## Dependencies

### Core Dependencies
- `fastapi>=0.68.0` - Web framework
- `uvicorn>=0.15.0` - ASGI server
- `pandas>=1.3.0` - Data manipulation
- `requests>=2.25.0` - HTTP client

### Optional Dependencies
- `ta-lib` - Technical analysis (requires separate installation)
- `python-dotenv` - Environment variable management

### Installing ta-lib
ta-lib requires separate installation:

**Windows:**
```bash
pip install TA-Lib
```

**macOS:**
```bash
brew install ta-lib
pip install TA-Lib
```

**Linux:**
```bash
sudo apt-get install libta-lib-dev
pip install TA-Lib
```

## Deployment

### Production Setup
1. **Update CORS settings**
   ```python
   allow_origins=["https://your-frontend-domain.com"]
   ```

2. **Configure environment variables**
   ```bash
   export CORS_ORIGINS="https://your-frontend-domain.com"
   ```

3. **Use production ASGI server**
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Error Handling

### Graceful Degradation
- Falls back to mock data when dependencies unavailable
- Handles CoinGecko API rate limits
- Provides meaningful error messages

### Common Issues
- **ta-lib not installed**: Falls back to simple pattern detection
- **CoinGecko API errors**: Returns cached or mock data
- **Invalid coin IDs**: Returns appropriate error messages

## Performance Optimization

### Current Optimizations
- Efficient pandas operations
- Minimal API calls to CoinGecko
- Fast pattern detection algorithms

### Future Improvements
- Caching for market data
- Async processing for multiple timeframes
- Database integration for historical data
- WebSocket support for real-time updates

## Testing

### Test Structure
```bash
tests/
├── test_main.py              # API endpoint tests
├── test_pattern_detector.py  # Pattern detection tests
├── test_coingecko_client.py  # API integration tests
└── conftest.py               # Test configuration
```

### Running Tests
```bash
pytest tests/ -v
```

## API Limits

### CoinGecko API Limits
- Free tier: 50 calls/minute
- Paid tier: Higher limits available

### Rate Limiting
Consider implementing rate limiting for production:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

## Contributing

### Development Setup
1. Fork the repository
2. Create virtual environment
3. Install dependencies
4. Make changes
5. Run tests
6. Submit pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for functions
- Maintain consistent naming

## Security

### Current Security Measures
- CORS configuration
- Input validation
- Error handling

### Production Security
- Implement authentication
- Rate limiting
- Input sanitization
- HTTPS enforcement

## Monitoring

### Health Checks
- API status endpoint
- Dependency availability checks
- Performance metrics

### Logging
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## Support

For issues, feature requests, or questions:
1. Check API documentation
2. Review error messages
3. Consult pattern detection logic
4. Create detailed issue reports

## License

[Add your license information here]

## Changelog

### Latest Updates
- Enhanced pattern coordinate system
- Improved error handling
- Added comprehensive API documentation
- Optimized pattern detection algorithms
- Added support for multiple timeframes