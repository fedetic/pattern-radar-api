# Load environment variables first (critical for database connection)
try:
    from dotenv import load_dotenv
    load_dotenv()
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    print("Warning: python-dotenv not available")

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os

# Enhanced services with database persistence
try:
    from services.enhanced_coingecko_client import enhanced_coingecko_client
    from services.coingecko_client import coingecko_client  # Fallback
    COINGECKO_AVAILABLE = True
    DATABASE_ENHANCED = True
except ImportError as e:
    try:
        from services.coingecko_client import coingecko_client
        COINGECKO_AVAILABLE = True
        DATABASE_ENHANCED = False
        print(f"Warning: Enhanced CoinGecko client not available, using basic version: {e}")
    except ImportError as e2:
        COINGECKO_AVAILABLE = False
        DATABASE_ENHANCED = False
        print(f"Warning: CoinGecko client not available: {e2}")

try:
    from services.enhanced_pattern_detector import enhanced_pattern_detector
    from services.pattern_detector import pattern_detector  # Fallback
    PATTERN_DETECTOR_AVAILABLE = True
    ENHANCED_PATTERN_DETECTOR_AVAILABLE = True
except ImportError as e:
    try:
        from services.pattern_detector import pattern_detector
        PATTERN_DETECTOR_AVAILABLE = True
        ENHANCED_PATTERN_DETECTOR_AVAILABLE = False
        print(f"Warning: Enhanced pattern detector not available, using basic version: {e}")
    except ImportError as e2:
        PATTERN_DETECTOR_AVAILABLE = False
        ENHANCED_PATTERN_DETECTOR_AVAILABLE = False
        print(f"Warning: Pattern detector not available: {e2}")

# Database initialization (only if enhanced services haven't already initialized it)
if not DATABASE_ENHANCED:
    try:
        from database.connection import init_database
        DATABASE_AVAILABLE = True
        print("Initializing database connection...")
        init_database()
        print("Database initialized successfully")
    except ImportError as e:
        DATABASE_AVAILABLE = False
        print(f"Warning: Database not available: {e}")
    except Exception as e:
        DATABASE_AVAILABLE = False
        print(f"Warning: Database initialization failed: {e}")
else:
    # Enhanced services are available, so database should already be initialized
    DATABASE_AVAILABLE = True
    print("Database already initialized by enhanced services")

try:
    from services.ml_predictor import ml_predictor_service
    ML_PREDICTOR_AVAILABLE = True
except ImportError as e:
    ML_PREDICTOR_AVAILABLE = False
    print(f"Warning: ML predictor not available: {e}")

app = FastAPI(title="Pattern Hero API", description="Crypto pattern analysis API")

# Allow local frontend to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change this in prod
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/pairs")
async def get_pairs(force_refresh: bool = Query(False, description="Force refresh from API")):
    """Get available crypto trading pairs with database caching"""
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
        # Use enhanced client with database persistence if available
        if DATABASE_ENHANCED and DATABASE_AVAILABLE:
            pairs = enhanced_coingecko_client.get_coins_markets_with_persistence(
                vs_currency="usd", limit=50, force_refresh=force_refresh
            )
        else:
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
    timeframe: Optional[str] = Query("1d", description="Data timeframe (currently only '1d' supported)"),
    force_refresh: bool = Query(False, description="Force refresh from API")
):
    """Get OHLCV market data for a specific coin"""
    
    # Validate timeframe - currently only support 1d
    supported_timeframes = ["1d"]  # Easily extendible list
    if timeframe not in supported_timeframes:
        raise HTTPException(
            status_code=400, 
            detail=f"Timeframe '{timeframe}' not supported. Currently supported: {supported_timeframes}"
        )
    
    try:
        # First try to get coin_id from symbol if needed
        if coin_id.upper() in ["BTC", "ETH", "ADA", "SOL"]:
            if DATABASE_ENHANCED and DATABASE_AVAILABLE:
                actual_coin_id = enhanced_coingecko_client.get_coin_by_symbol(coin_id)
            else:
                actual_coin_id = coingecko_client.get_coin_by_symbol(coin_id)
            if actual_coin_id:
                coin_id = actual_coin_id
        
        # Use enhanced client with database persistence if available
        if DATABASE_ENHANCED and DATABASE_AVAILABLE:
            df = enhanced_coingecko_client.get_ohlc_data_with_persistence(
                coin_id, vs_currency, days, timeframe, force_refresh=force_refresh
            )
        else:
            df = coingecko_client.get_ohlc_data(coin_id, vs_currency, days, timeframe)
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No market data found for {coin_id}")
        
        # Convert DataFrame to list of dictionaries
        market_data = []
        for i, (timestamp, row) in enumerate(df.iterrows()):
            # Temporary: Add test volume data to verify frontend display
            test_volume = float(row.get('volume', 0))
            if test_volume == 0:
                # Generate test volume proportional to price movement
                price_range = float(row['high']) - float(row['low'])
                base_volume = price_range * float(row['close']) * 0.1
                test_volume = base_volume * (1 + 0.5 * (i % 10) / 10)  # Add variation
            
            market_data.append({
                "timestamp": timestamp.isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": test_volume  # Include volume data with test values
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
    timeframe: Optional[str] = Query("1d", description="Analysis timeframe (currently only '1d' supported)"),
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
    timeframe: Optional[str] = Query("1d", description="Analysis timeframe (currently only '1d' supported)"),
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
    
    # Validate timeframe - currently only support 1d
    # Keep this validation simple to make it easy to extend later
    supported_timeframes = ["1d"]  # Easily extendible list
    if timeframe not in supported_timeframes:
        raise HTTPException(
            status_code=400, 
            detail=f"Timeframe '{timeframe}' not supported. Currently supported: {supported_timeframes}"
        )
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

        # Keep full dataframe for market data, create separate dataframe for pattern analysis
        full_df = df.copy()  # Keep full data for chart display
        pattern_analysis_df = df  # Default to full data
        
        # Simplified logic: directly control pattern analysis scope based on full_history
        if not full_history and df is not None and len(df) > 50:
            # When full_history=False (toggle ON - "recent only"), use a fixed recent window
            recent_window = 50  # Fixed window for recent analysis
            pattern_analysis_df = df.iloc[-recent_window:]
        
        # Enhanced fallback logic instead of immediate 404
        if df is None or df.empty:
            print(f"Primary data fetch failed for {coin_id} ({timeframe}), trying fallbacks...")
            
            # Since we only support 1d now, no timeframe fallback needed
            # This block is kept for future extensibility when other timeframes are re-added
            
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
        
        # Analyze patterns using the appropriate dataframe scope with database persistence
        try:
            if ENHANCED_PATTERN_DETECTOR_AVAILABLE and DATABASE_AVAILABLE:
                analysis_result = enhanced_pattern_detector.analyze_patterns_with_persistence(
                    pattern_analysis_df, coin_id, timeframe, save_to_db=True
                )
            else:
                analysis_result = pattern_detector.analyze_patterns(pattern_analysis_df)
            print(f"Analysis completed, found {len(analysis_result.get('patterns', []))} patterns")
            
            # Override market_data in analysis_result with full dataframe data
            market_data = []
            for i, (timestamp, row) in enumerate(full_df.iterrows()):
                # Temporary: Add test volume data to verify frontend display
                test_volume = float(row.get('volume', 0))
                if test_volume == 0:
                    # Generate test volume proportional to price movement
                    price_range = float(row['high']) - float(row['low'])
                    base_volume = price_range * float(row['close']) * 0.1
                    test_volume = base_volume * (1 + 0.5 * (i % 10) / 10)  # Add variation
                
                market_data.append({
                    "timestamp": timestamp.isoformat(),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": test_volume  # Include volume data with test values
                })
            analysis_result['market_data'] = market_data
        except Exception as pattern_error:
            print(f"Pattern analysis failed: {pattern_error}")
            # Convert full DataFrame to market data format for fallback
            market_data = []
            for i, (timestamp, row) in enumerate(full_df.iterrows()):
                # Temporary: Add test volume data to verify frontend display
                test_volume = float(row.get('volume', 0))
                if test_volume == 0:
                    # Generate test volume proportional to price movement
                    price_range = float(row['high']) - float(row['low'])
                    base_volume = price_range * float(row['close']) * 0.1
                    test_volume = base_volume * (1 + 0.5 * (i % 10) / 10)  # Add variation
                
                market_data.append({
                    "timestamp": timestamp.isoformat(),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": test_volume  # Include volume data with test values
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
            if DATABASE_ENHANCED and DATABASE_AVAILABLE:
                markets_data = enhanced_coingecko_client.get_coins_markets_with_persistence(vs_currency="usd", limit=100)
            else:
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
            "analysis_date": full_df.index[-1].isoformat(),
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

@app.get("/predictions/{coin_id}")
async def get_ml_predictions(
    coin_id: str,
    vs_currency: str = "usd",
    days: int = Query(30, ge=7, le=365, description="Number of days for analysis")
):
    """Get ML-based predictions for a specific coin"""
    
    try:
        # Get coin_id from symbol if needed
        if COINGECKO_AVAILABLE and coin_id.upper() in ["BTC", "ETH", "ADA", "SOL"]:
            actual_coin_id = coingecko_client.get_coin_by_symbol(coin_id)
            if actual_coin_id:
                coin_id = actual_coin_id
        
        # Fetch market data
        df = None
        if COINGECKO_AVAILABLE:
            df = coingecko_client.get_ohlc_data(coin_id, vs_currency, days, "1d")
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No market data found for {coin_id}")
        
        # Get ML prediction
        prediction = ml_predictor_service.get_prediction(coin_id, df)
        
        if prediction is None:
            raise HTTPException(
                status_code=503, 
                detail=f"ML models not available for {coin_id}. Please train models first using pattern-data-ingest."
            )
        
        return prediction
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in predictions endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting predictions: {str(e)}")

@app.get("/recommendations/{coin_id}")
async def get_trading_recommendations(
    coin_id: str,
    vs_currency: str = "usd",
    days: int = Query(30, ge=7, le=365, description="Number of days for analysis"),
    include_patterns: bool = Query(True, description="Include pattern analysis in recommendation")
):
    """Get trading recommendations based on ML predictions and pattern analysis"""
    
    try:
        # Get coin_id from symbol if needed
        if COINGECKO_AVAILABLE and coin_id.upper() in ["BTC", "ETH", "ADA", "SOL"]:
            actual_coin_id = coingecko_client.get_coin_by_symbol(coin_id)
            if actual_coin_id:
                coin_id = actual_coin_id
        
        # Fetch market data
        df = None
        if COINGECKO_AVAILABLE:
            df = coingecko_client.get_ohlc_data(coin_id, vs_currency, days, "1d")
        
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No market data found for {coin_id}")
        
        # Get pattern strength if requested
        pattern_strength = 0
        if include_patterns and PATTERN_DETECTOR_AVAILABLE:
            try:
                if ENHANCED_PATTERN_DETECTOR_AVAILABLE and DATABASE_AVAILABLE:
                    pattern_analysis = enhanced_pattern_detector.analyze_patterns_with_persistence(
                        df, coin_id, "1d", save_to_db=True
                    )
                else:
                    pattern_analysis = pattern_detector.analyze_patterns(df)
                if pattern_analysis.get('strongest_pattern'):
                    pattern_strength = pattern_analysis['strongest_pattern'].get('confidence', 0)
            except Exception as e:
                print(f"Error getting pattern strength: {e}")
        
        # Get recommendation
        recommendation = ml_predictor_service.get_recommendation(coin_id, df, pattern_strength)
        
        if recommendation is None:
            raise HTTPException(
                status_code=503, 
                detail=f"ML models not available for {coin_id}. Please train models first using pattern-data-ingest."
            )
        
        return recommendation
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in recommendations endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@app.get("/")
async def root():
    """API health check"""
    status_info = {
        "message": "Pattern Hero API is running", 
        "status": "healthy",
        "features": {
            "coingecko_available": COINGECKO_AVAILABLE,
            "pattern_detector_available": PATTERN_DETECTOR_AVAILABLE,
            "ml_predictor_available": ML_PREDICTOR_AVAILABLE,
            "database_available": DATABASE_AVAILABLE,
            "database_enhanced": DATABASE_ENHANCED,
            "enhanced_pattern_detector": ENHANCED_PATTERN_DETECTOR_AVAILABLE
        }
    }
    return status_info

# Database-specific endpoints
@app.get("/db/stats")
async def get_database_stats():
    """Get database statistics"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        if DATABASE_ENHANCED:
            stats = enhanced_coingecko_client.get_database_stats()
            pattern_stats = enhanced_pattern_detector.get_database_pattern_summary()
            stats.update(pattern_stats)
            return stats
        else:
            return {"error": "Enhanced database features not available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting database stats: {str(e)}")

@app.get("/db/pattern-statistics")
async def get_pattern_statistics(days: int = Query(30, ge=1, le=365, description="Days to analyze")):
    """Get pattern detection statistics"""
    if not DATABASE_AVAILABLE or not ENHANCED_PATTERN_DETECTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced pattern detection not available")
    
    try:
        stats = enhanced_pattern_detector.get_pattern_statistics(days)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pattern statistics: {str(e)}")

@app.get("/db/high-confidence-patterns")
async def get_high_confidence_patterns(
    min_confidence: int = Query(80, ge=50, le=100, description="Minimum confidence level"),
    days: int = Query(7, ge=1, le=90, description="Days to look back")
):
    """Get high confidence patterns from database"""
    if not DATABASE_AVAILABLE or not ENHANCED_PATTERN_DETECTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced pattern detection not available")
    
    try:
        patterns = enhanced_pattern_detector.get_high_confidence_patterns(min_confidence, days)
        return {
            "patterns": patterns,
            "total_count": len(patterns),
            "min_confidence": min_confidence,
            "days_analyzed": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting high confidence patterns: {str(e)}")

@app.get("/db/patterns/by-direction/{direction}")
async def get_patterns_by_direction(
    direction: str,
    days: int = Query(7, ge=1, le=90, description="Days to look back")
):
    """Get patterns by direction (bullish, bearish, neutral)"""
    if not DATABASE_AVAILABLE or not ENHANCED_PATTERN_DETECTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced pattern detection not available")
    
    if direction not in ["bullish", "bearish", "neutral", "continuation"]:
        raise HTTPException(status_code=400, detail="Direction must be one of: bullish, bearish, neutral, continuation")
    
    try:
        patterns = enhanced_pattern_detector.get_patterns_by_direction(direction, days)
        return {
            "direction": direction,
            "patterns": patterns,
            "total_count": len(patterns),
            "days_analyzed": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting patterns by direction: {str(e)}")

@app.post("/db/sync-pairs")
async def sync_trading_pairs(limit: int = Query(100, ge=10, le=500, description="Number of pairs to sync")):
    """Synchronize trading pairs with CoinGecko API"""
    if not DATABASE_AVAILABLE or not DATABASE_ENHANCED:
        raise HTTPException(status_code=503, detail="Enhanced database features not available")
    
    try:
        updated_count = enhanced_coingecko_client.sync_trading_pairs(limit)
        return {
            "message": f"Synchronized {updated_count} trading pairs",
            "updated_count": updated_count,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error syncing trading pairs: {str(e)}")

@app.post("/db/backfill-ohlcv/{coin_id}")
async def backfill_ohlcv_data(
    coin_id: str,
    days: int = Query(90, ge=1, le=365, description="Days to backfill"),
    timeframe: str = Query("1d", description="Timeframe to backfill")
):
    """Backfill missing OHLCV data for a coin"""
    if not DATABASE_AVAILABLE or not DATABASE_ENHANCED:
        raise HTTPException(status_code=503, detail="Enhanced database features not available")
    
    try:
        filled_count = enhanced_coingecko_client.backfill_ohlcv_data(coin_id, timeframe, days)
        return {
            "message": f"Backfilled {filled_count} records for {coin_id}",
            "coin_id": coin_id,
            "filled_count": filled_count,
            "days": days,
            "timeframe": timeframe
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error backfilling OHLCV data: {str(e)}")

@app.delete("/db/cleanup-old-patterns")
async def cleanup_old_patterns(days_to_keep: int = Query(90, ge=30, le=365, description="Days of patterns to keep")):
    """Clean up old detected patterns"""
    if not DATABASE_AVAILABLE or not ENHANCED_PATTERN_DETECTOR_AVAILABLE:
        raise HTTPException(status_code=503, detail="Enhanced pattern detection not available")
    
    try:
        deleted_count = enhanced_pattern_detector.cleanup_old_patterns(days_to_keep)
        return {
            "message": f"Cleaned up {deleted_count} old patterns",
            "deleted_count": deleted_count,
            "days_kept": days_to_keep
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up old patterns: {str(e)}")