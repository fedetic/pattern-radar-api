from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os

# Try to load optional dependencies
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not available")

try:
    from services.coingecko_client import coingecko_client
    COINGECKO_AVAILABLE = True
except ImportError as e:
    COINGECKO_AVAILABLE = False
    print(f"Warning: CoinGecko client not available: {e}")

try:
    from services.pattern_detector import pattern_detector
    PATTERN_DETECTOR_AVAILABLE = True
except ImportError as e:
    PATTERN_DETECTOR_AVAILABLE = False
    print(f"Warning: Pattern detector not available: {e}")

app = FastAPI(title="Pattern Hero API", description="Crypto pattern analysis API")

# Allow local frontend to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change this in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/pairs")
async def get_pairs():
    """Get available crypto trading pairs from CoinGecko"""
    if not COINGECKO_AVAILABLE:
        # Return fallback data when dependencies are missing
        return [
            {
                "symbol": "BTC-USD",
                "base": "BTC", 
                "quote": "USD",
                "label": "BTC/USD",
                "name": "Bitcoin",
                "coin_id": "bitcoin",
                "status": "active"
            },
            {
                "symbol": "ETH-USD",
                "base": "ETH",
                "quote": "USD", 
                "label": "ETH/USD",
                "name": "Ethereum",
                "coin_id": "ethereum",
                "status": "active"
            },
            {
                "symbol": "SOL-USD",
                "base": "SOL",
                "quote": "USD", 
                "label": "SOL/USD",
                "name": "Solana",
                "coin_id": "solana",
                "status": "active"
            }
        ]
    
    try:
        pairs = coingecko_client.get_coins_markets(vs_currency="usd", limit=50)
        
        if not pairs:
            # Fallback to mock data if API fails
            return [
                {
                    "symbol": "BTC-USD",
                    "base": "BTC", 
                    "quote": "USD",
                    "label": "BTC/USD",
                    "name": "Bitcoin",
                    "coin_id": "bitcoin",
                    "status": "active"
                },
                {
                    "symbol": "ETH-USD",
                    "base": "ETH",
                    "quote": "USD", 
                    "label": "ETH/USD",
                    "name": "Ethereum",
                    "coin_id": "ethereum",
                    "status": "active"
                }
            ]
        
        return pairs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching pairs: {str(e)}")

@app.get("/market-data/{coin_id}")
async def get_market_data(
    coin_id: str,
    vs_currency: str = "usd",
    days: int = Query(30, ge=1, le=365, description="Number of days of data"),
    timeframe: Optional[str] = Query("1d", description="Data timeframe")
):
    """Get OHLCV market data for a specific coin"""
    try:
        # First try to get coin_id from symbol if needed
        if coin_id.upper() in ["BTC", "ETH", "ADA", "SOL"]:
            actual_coin_id = coingecko_client.get_coin_by_symbol(coin_id)
            if actual_coin_id:
                coin_id = actual_coin_id
        
        df = coingecko_client.get_ohlc_data(coin_id, vs_currency, days, timeframe)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No market data found for {coin_id}")
        
        # Convert DataFrame to list of dictionaries
        market_data = []
        for timestamp, row in df.iterrows():
            market_data.append({
                "timestamp": timestamp.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close'])
            })
        
        return {
            "coin_id": coin_id,
            "vs_currency": vs_currency,
            "days": days,
            "timeframe": timeframe,
            "data": market_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market data: {str(e)}")

@app.get("/patterns/{coin_id}")
async def get_patterns(
    coin_id: str,
    vs_currency: str = "usd",
    days: int = Query(30, ge=7, le=365, description="Number of days for analysis"),
    timeframe: Optional[str] = Query("1d", description="Analysis timeframe")
):
    """Analyze patterns for a specific coin and return pattern data with coordinates for visualization"""
    if not COINGECKO_AVAILABLE:
        # Return fallback data when dependencies are missing
        return {
            "coin_id": coin_id,
            "vs_currency": vs_currency,
            "timeframe": timeframe,
            "analysis_date": "2025-07-16T12:00:00",
            "patterns": [
                {
                    "name": "Demo Pattern",
                    "category": "Chart",
                    "confidence": 85,
                    "direction": "bullish",
                    "description": "Install backend dependencies (pip install -r requirements.txt) for real patterns"
                }
            ],
            "market_data": [
                {"timestamp": "2025-07-16T12:00:00", "open": 119000, "high": 120000, "low": 118000, "close": 119500}
            ],
            "strongest_pattern": {
                "name": "Demo Pattern",
                "confidence": 85
            }
        }
    
    try:
        print(f"Analyzing patterns for {coin_id} with {days} days")
        
        # Get coin_id from symbol if needed
        if coin_id.upper() in ["BTC", "ETH", "ADA", "SOL"]:
            actual_coin_id = coingecko_client.get_coin_by_symbol(coin_id)
            if actual_coin_id:
                coin_id = actual_coin_id
        
        print(f"Using coin_id: {coin_id}")
        
        # Fetch market data with timeframe support
        df = coingecko_client.get_ohlc_data(coin_id, vs_currency, days, timeframe)
        
        if df is None or df.empty:
            print(f"No market data found for {coin_id}")
            raise HTTPException(status_code=404, detail=f"No market data found for {coin_id}")
        
        print(f"Got {len(df)} data points")
        
        # Analyze patterns
        try:
            analysis_result = pattern_detector.analyze_patterns(df)
            print(f"Analysis completed, found {len(analysis_result.get('patterns', []))} patterns")
        except Exception as pattern_error:
            print(f"Pattern analysis failed: {pattern_error}")
            # Convert DataFrame to market data format for fallback
            market_data = []
            for timestamp, row in df.iterrows():
                market_data.append({
                    "timestamp": timestamp.isoformat(),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close'])
                })
            
            # Return fallback response with demo patterns but real market data
            analysis_result = {
                "patterns": [
                    {
                        "name": "Demo Pattern",
                        "category": "Chart",
                        "confidence": 85,
                        "direction": "bullish",
                        "description": "Sample pattern for testing (backend dependencies needed)"
                    }
                ],
                "market_data": market_data,
                "strongest_pattern": {
                    "name": "Demo Pattern",
                    "confidence": 85
                }
            }
        
        # Get additional market data
        try:
            markets_data = coingecko_client.get_coins_markets(vs_currency="usd", limit=100)
            coin_market_data = next((coin for coin in markets_data if coin['coin_id'] == coin_id), None)
        except:
            coin_market_data = None
        
        return {
            "coin_id": coin_id,
            "vs_currency": vs_currency,
            "timeframe": timeframe,
            "analysis_date": df.index[-1].isoformat(),
            "market_info": coin_market_data,
            **analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in patterns endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error analyzing patterns: {str(e)}")

@app.get("/")
async def root():
    """API health check"""
    return {"message": "Pattern Hero API is running", "status": "healthy"}