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
    from services.pattern_orchestrator import pattern_orchestrator
    PATTERN_ORCHESTRATOR_AVAILABLE = True
except ImportError as e:
    PATTERN_ORCHESTRATOR_AVAILABLE = False
    print(f"Warning: Pattern orchestrator not available: {e}")

app = FastAPI(
    title="Pattern Hero API", 
    description="Crypto pattern analysis API with modular architecture",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """API health check with service status"""
    status = {
        "message": "Pattern Hero API is running",
        "status": "healthy",
        "version": "2.0.0 (Refactored)",
        "services": {
            "coingecko": COINGECKO_AVAILABLE,
            "pattern_detection": PATTERN_ORCHESTRATOR_AVAILABLE
        }
    }
    
    if PATTERN_ORCHESTRATOR_AVAILABLE:
        status["pattern_services"] = pattern_orchestrator.get_service_status()
    
    return status

@app.get("/pairs")
async def get_pairs():
    """Get available crypto trading pairs from CoinGecko"""
    if not COINGECKO_AVAILABLE:
        return _get_fallback_pairs()
    
    try:
        pairs = coingecko_client.get_coins_markets(vs_currency="usd", limit=50)
        
        if not pairs:
            return _get_fallback_pairs()
        
        return pairs
        
    except Exception as e:
        print(f"Error fetching pairs: {e}")
        return _get_fallback_pairs()

@app.get("/patterns/{coin_id}")
async def get_patterns(
    coin_id: str,
    vs_currency: str = "usd",
    days: int = Query(30, ge=7, le=365, description="Number of days for analysis"),
    timeframe: Optional[str] = Query("1d", description="Analysis timeframe")
):
    """Analyze patterns for a specific coin using the new orchestrator"""
    return await _analyze_patterns_internal(coin_id, vs_currency, days, timeframe)

@app.get("/patterns/{coin_id}/filtered")
async def get_filtered_patterns(
    coin_id: str,
    start_time: str = Query(..., description="Start time for analysis (ISO format)"),
    end_time: str = Query(..., description="End time for analysis (ISO format)"),
    vs_currency: str = "usd",
    timeframe: Optional[str] = Query("1d", description="Analysis timeframe")
):
    """Analyze patterns for a specific coin within a time range"""
    return await _analyze_patterns_internal(coin_id, vs_currency, None, timeframe, start_time, end_time)

@app.get("/services/status")
async def get_service_status():
    """Get detailed status of all services"""
    status = {
        "core_services": {
            "coingecko": COINGECKO_AVAILABLE,
            "pattern_orchestrator": PATTERN_ORCHESTRATOR_AVAILABLE
        }
    }
    
    if PATTERN_ORCHESTRATOR_AVAILABLE:
        status["pattern_services"] = pattern_orchestrator.get_service_status()
    
    return status

async def _analyze_patterns_internal(
    coin_id: str, 
    vs_currency: str = "usd", 
    days: Optional[int] = None, 
    timeframe: str = "1d",
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
):
    """Internal pattern analysis with improved error handling and fallbacks"""
    
    # Early validation
    if not COINGECKO_AVAILABLE:
        return _get_fallback_analysis_response(coin_id, vs_currency, timeframe)
    
    if not PATTERN_ORCHESTRATOR_AVAILABLE:
        return _get_legacy_analysis_response(coin_id, vs_currency, timeframe)
    
    try:
        print(f"Analyzing patterns for {coin_id} ({'filtered' if start_time else 'standard'})")
        
        # Resolve coin_id from symbol if needed
        actual_coin_id = _resolve_coin_id(coin_id)
        
        # Fetch market data with robust fallback handling
        df = await _fetch_market_data_with_fallbacks(
            actual_coin_id, vs_currency, days, timeframe, start_time, end_time
        )
        
        if df is None or df.empty:
            raise HTTPException(
                status_code=500, 
                detail=f"Unable to fetch market data for {coin_id}. Please try again later."
            )
        
        # Filter data by time range if specified
        if start_time and end_time:
            df = _filter_dataframe_by_time(df, start_time, end_time)
        
        print(f"Analyzing {len(df)} data points with pattern orchestrator")
        
        # Use the new pattern orchestrator
        analysis_result = pattern_orchestrator.analyze_patterns(df)
        
        # Get market info
        market_info = await _get_market_info(actual_coin_id, vs_currency)
        
        return {
            "coin_id": actual_coin_id,
            "vs_currency": vs_currency,
            "timeframe": timeframe,
            "analysis_date": df.index[-1].isoformat(),
            "market_info": market_info,
            **analysis_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in patterns endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error analyzing patterns: {str(e)}")

def _get_fallback_pairs():
    """Get fallback trading pairs when API is unavailable"""
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

def _get_fallback_analysis_response(coin_id: str, vs_currency: str, timeframe: str):
    """Get fallback analysis when services are unavailable"""
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
        },
        "service_status": "degraded"
    }

def _get_legacy_analysis_response(coin_id: str, vs_currency: str, timeframe: str):
    """Get response using legacy pattern detection if orchestrator unavailable"""
    try:
        # Try to use the old pattern detector as fallback
        from services.pattern_detector import pattern_detector
        
        # This would need to be implemented with the old logic
        # For now, return fallback response
        return _get_fallback_analysis_response(coin_id, vs_currency, timeframe)
        
    except ImportError:
        return _get_fallback_analysis_response(coin_id, vs_currency, timeframe)

def _resolve_coin_id(coin_id: str) -> str:
    """Resolve coin ID from symbol"""
    if COINGECKO_AVAILABLE and coin_id.upper() in ["BTC", "ETH", "ADA", "SOL"]:
        actual_coin_id = coingecko_client.get_coin_by_symbol(coin_id)
        if actual_coin_id:
            return actual_coin_id
    return coin_id

async def _fetch_market_data_with_fallbacks(
    coin_id: str, vs_currency: str, days: Optional[int], 
    timeframe: str, start_time: Optional[str], end_time: Optional[str]
):
    """Fetch market data with comprehensive fallback handling"""
    if not COINGECKO_AVAILABLE:
        return None
    
    try:
        if start_time and end_time:
            # For filtered requests, get more data initially
            df = coingecko_client.get_ohlc_data(coin_id, vs_currency, days or 365, timeframe)
        else:
            df = coingecko_client.get_ohlc_data(coin_id, vs_currency, days, timeframe)
        
        # Apply fallback logic if initial fetch fails
        if df is None or df.empty:
            print(f"Primary data fetch failed, trying fallbacks...")
            
            # Try with different timeframe
            if timeframe in ["1h", "4h"]:
                fallback_df = coingecko_client.get_ohlc_data(coin_id, vs_currency, min(days or 30, 30), "1d")
                if fallback_df is not None and not fallback_df.empty:
                    df = coingecko_client._resample_for_intraday(fallback_df, timeframe)
            
            # Try different days parameter
            if df is None or df.empty:
                for fallback_days in [7, 30, 90]:
                    if fallback_days != days:
                        df = coingecko_client.get_ohlc_data(coin_id, vs_currency, fallback_days, timeframe)
                        if df is not None and not df.empty:
                            break
            
            # Generate synthetic data as last resort
            if df is None or df.empty:
                df = coingecko_client._generate_fallback_ohlc_data(coin_id, timeframe, days or 30)
        
        return df
        
    except Exception as e:
        print(f"Error fetching market data: {e}")
        return None

def _filter_dataframe_by_time(df, start_time: str, end_time: str):
    """Filter dataframe by time range"""
    try:
        import pandas as pd
        
        start_dt = pd.to_datetime(start_time)
        end_dt = pd.to_datetime(end_time)
        
        filtered_df = df[(df.index >= start_dt) & (df.index <= end_dt)]
        
        if filtered_df.empty:
            print(f"No data in specified time range {start_time} to {end_time}")
            return df  # Return original data if filtering results in empty set
        
        print(f"Filtered to {len(filtered_df)} data points in range")
        return filtered_df
        
    except Exception as e:
        print(f"Error filtering data by time: {e}")
        return df

async def _get_market_info(coin_id: str, vs_currency: str):
    """Get market information for the coin"""
    if not COINGECKO_AVAILABLE:
        return _get_fallback_market_info(coin_id)
    
    try:
        markets_data = coingecko_client.get_coins_markets(vs_currency=vs_currency, limit=100)
        market_info = next((coin for coin in markets_data if coin['coin_id'] == coin_id), None)
        
        if market_info:
            return market_info
        else:
            return _get_fallback_market_info(coin_id)
            
    except Exception as e:
        print(f"Failed to get market data: {e}")
        return _get_fallback_market_info(coin_id)

def _get_fallback_market_info(coin_id: str):
    """Get fallback market information"""
    fallback_data = {
        'bitcoin': {
            'coin_id': 'bitcoin',
            'name': 'Bitcoin',
            'symbol': 'BTC-USD',
            'current_price': 67000,
            'market_cap': 1300000000000,
            'market_cap_rank': 1
        },
        'ethereum': {
            'coin_id': 'ethereum',
            'name': 'Ethereum', 
            'symbol': 'ETH-USD',
            'current_price': 3500,
            'market_cap': 420000000000,
            'market_cap_rank': 2
        }
    }
    
    return fallback_data.get(coin_id, {
        'coin_id': coin_id,
        'name': coin_id.capitalize(),
        'symbol': f'{coin_id.upper()}-USD',
        'current_price': 100,
        'market_cap': 1000000000,
        'market_cap_rank': 50
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)