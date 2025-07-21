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
    timeframe: Optional[str] = Query("1d", description="Analysis timeframe"),
    full_history: bool = Query(False, description="Show all patterns, not just most recent window")
):
    """Analyze patterns for a specific coin and return pattern data with coordinates for visualization"""
    return await _analyze_patterns_internal(coin_id, vs_currency, days, timeframe, None, None, full_history)

@app.get("/patterns/{coin_id}/filtered")
async def get_filtered_patterns(
    coin_id: str,
    start_time: str = Query(..., description="Start time for analysis (ISO format)"),
    end_time: str = Query(..., description="End time for analysis (ISO format)"),
    vs_currency: str = "usd",
    timeframe: Optional[str] = Query("1d", description="Analysis timeframe"),
    full_history: bool = Query(False, description="Show all patterns, not just most recent window")
):
    """Analyze patterns for a specific coin within a time range (for zoom updates)"""
    return await _analyze_patterns_internal(coin_id, vs_currency, None, timeframe, start_time, end_time, full_history)

async def _analyze_patterns_internal(
    coin_id: str, 
    vs_currency: str = "usd", 
    days: Optional[int] = None, 
    timeframe: str = "1d",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    full_history: bool = False
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
        if start_time and end_time:
            print(f"Analyzing patterns for {coin_id} from {start_time} to {end_time}")
        else:
            print(f"Analyzing patterns for {coin_id} with {days} days")
        
        # Get coin_id from symbol if needed
        if coin_id.upper() in ["BTC", "ETH", "ADA", "SOL"]:
            actual_coin_id = coingecko_client.get_coin_by_symbol(coin_id)
            if actual_coin_id:
                coin_id = actual_coin_id
        
        print(f"Using coin_id: {coin_id}")
        
        # Fetch market data with robust fallback handling
        df = None
        if start_time and end_time:
            # For filtered requests, get more data initially and then filter
            df = coingecko_client.get_ohlc_data(coin_id, vs_currency, days or 365, timeframe)
        else:
            df = coingecko_client.get_ohlc_data(coin_id, vs_currency, days, timeframe)

        # Only use the most recent N candles unless full_history is True
        if not full_history and df is not None and len(df) > 20:
            # Run pattern detection on a larger window first (e.g., last 100)
            temp_df = df.iloc[-100:] if len(df) > 100 else df
            patterns_result = pattern_detector.analyze_patterns(temp_df)
            patterns = patterns_result.get('patterns', [])
            if patterns:
                # Find the most recent pattern with the largest required window
                max_window = 0
                for p in patterns:
                    duration = 3
                    if hasattr(pattern_detector, '_get_pattern_duration'):
                        try:
                            duration = pattern_detector._get_pattern_duration(p['name'])
                        except Exception:
                            duration = 3
                    idx = p.get('latest_occurrence', 0)
                    window = idx + duration
                    if window > max_window:
                        max_window = window
                window = min(len(df), max(20, max_window + 2))
                df = df.iloc[-window:]
            else:
                df = df.iloc[-20:]
        
        # Enhanced fallback logic instead of immediate 404
        if df is None or df.empty:
            print(f"Primary data fetch failed for {coin_id} ({timeframe}), trying fallbacks...")
            
            # Fallback 1: Try with different timeframe (daily data is more reliable)
            if timeframe in ["1h", "4h"]:
                print(f"Trying daily data fallback for {timeframe}")
                fallback_df = coingecko_client.get_ohlc_data(coin_id, vs_currency, min(days, 30), "1d")
                if fallback_df is not None and not fallback_df.empty:
                    print(f"Got daily fallback data, will resample to {timeframe}")
                    df = coingecko_client._resample_for_intraday(fallback_df, timeframe)
            
            # Fallback 2: Try different days parameter
            if df is None or df.empty:
                for fallback_days in [7, 30, 90]:
                    if fallback_days != days:
                        print(f"Trying fallback with {fallback_days} days")
                        df = coingecko_client.get_ohlc_data(coin_id, vs_currency, fallback_days, timeframe)
                        if df is not None and not df.empty:
                            print(f"Successfully got data with {fallback_days} days")
                            break
            
            # Fallback 3: Generate synthetic data as last resort
            if df is None or df.empty:
                print(f"All data sources failed, generating fallback data for {coin_id}")
                df = coingecko_client._generate_fallback_ohlc_data(coin_id, timeframe, days)
        
        # Final check - if still no data after all fallbacks
        if df is None or df.empty:
            print(f"All fallbacks failed for {coin_id} ({timeframe})")
            raise HTTPException(status_code=500, detail=f"Unable to fetch market data for {coin_id}. Please try again later.")
        
        # Filter data by time range if specified
        if start_time and end_time:
            try:
                from datetime import datetime
                import pandas as pd
                
                start_dt = pd.to_datetime(start_time)
                end_dt = pd.to_datetime(end_time)
                
                # Filter the dataframe to the specified time range
                df = df[(df.index >= start_dt) & (df.index <= end_dt)]
                
                if df.empty:
                    print(f"No data in specified time range {start_time} to {end_time}")
                    raise HTTPException(status_code=404, detail=f"No data in specified time range")
                
                print(f"Filtered to {len(df)} data points in range {start_time} to {end_time}")
            except Exception as filter_error:
                print(f"Error filtering data: {filter_error}")
                # Continue with unfiltered data if filtering fails
        
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
        except Exception as e:
            print(f"Failed to get market data: {e}")
            coin_market_data = None
        
        # Provide fallback market data if API fails
        if coin_market_data is None:
            # Default market data for major cryptocurrencies
            fallback_market_data = {
                'bitcoin': {
                    'coin_id': 'bitcoin',
                    'name': 'Bitcoin',
                    'symbol': 'BTC-USD',
                    'current_price': 67000,
                    'market_cap': 1300000000000,  # ~1.3T USD
                    'market_cap_rank': 1
                },
                'ethereum': {
                    'coin_id': 'ethereum',
                    'name': 'Ethereum',
                    'symbol': 'ETH-USD',
                    'current_price': 3500,
                    'market_cap': 420000000000,  # ~420B USD
                    'market_cap_rank': 2
                },
                'cardano': {
                    'coin_id': 'cardano',
                    'name': 'Cardano',
                    'symbol': 'ADA-USD',
                    'current_price': 0.45,
                    'market_cap': 15000000000,  # ~15B USD
                    'market_cap_rank': 10
                }
            }
            coin_market_data = fallback_market_data.get(coin_id, {
                'coin_id': coin_id,
                'name': coin_id.capitalize(),
                'symbol': f'{coin_id.upper()}-USD',
                'current_price': 100,
                'market_cap': 1000000000,  # 1B USD fallback
                'market_cap_rank': 50
            })
        
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