"""
Enhanced CoinGecko client with database persistence
Extends the original client to save data to database
"""

import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .coingecko_client import CoinGeckoClient
from database.connection import get_database_manager
from database.repositories.trading_pairs_repository import TradingPairsRepository
from database.repositories.ohlcv_repository import OHLCVRepository

logger = logging.getLogger(__name__)

class EnhancedCoinGeckoClient(CoinGeckoClient):
    """Enhanced CoinGecko client with database persistence"""
    
    def __init__(self):
        super().__init__()
        self.db_manager = get_database_manager()
    
    def get_coins_markets_with_persistence(self, vs_currency: str = "usd", limit: int = 100, 
                                         force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Get coins markets with database caching"""
        try:
            with self.db_manager.get_db_session() as session:
                pairs_repo = TradingPairsRepository(session)
                
                # Check if we have recent data in database
                if not force_refresh:
                    existing_pairs = pairs_repo.get_active_pairs(limit=limit)
                    if existing_pairs:
                        # Check if data is recent (less than 1 hour old)
                        latest_update = max([pair.updated_at for pair in existing_pairs if pair.updated_at])
                        if latest_update and (datetime.now() - latest_update).total_seconds() < 3600:
                            logger.info(f"Using cached trading pairs data ({len(existing_pairs)} pairs)")
                            return [pair.to_dict() for pair in existing_pairs]
                
                # Fetch fresh data from API
                logger.info("Fetching fresh trading pairs data from CoinGecko API")
                api_pairs = super().get_coins_markets(vs_currency, limit)
                
                if api_pairs:
                    # Save to database
                    updated_count = pairs_repo.bulk_upsert_pairs(api_pairs)
                    logger.info(f"Updated {updated_count} trading pairs in database")
                    
                    return api_pairs
                else:
                    # Fallback to database if API fails
                    logger.warning("API failed, falling back to database")
                    existing_pairs = pairs_repo.get_active_pairs(limit=limit)
                    return [pair.to_dict() for pair in existing_pairs]
                    
        except Exception as e:
            logger.error(f"Error in get_coins_markets_with_persistence: {e}")
            # Fallback to original API method
            return super().get_coins_markets(vs_currency, limit)
    
    def get_ohlc_data_with_persistence(self, coin_id: str, vs_currency: str = "usd", 
                                     days: int = 30, timeframe: str = "1d", 
                                     force_refresh: bool = False) -> Optional[pd.DataFrame]:
        """Get OHLC data with database caching"""
        try:
            with self.db_manager.get_db_session() as session:
                pairs_repo = TradingPairsRepository(session)
                ohlcv_repo = OHLCVRepository(session)
                
                # Get or create trading pair
                trading_pair = pairs_repo.get_by_coin_id(coin_id)
                if not trading_pair:
                    # Try to create from API data
                    api_pairs = super().get_coins_markets(vs_currency, 1)
                    for pair_data in api_pairs:
                        if pair_data.get('coin_id') == coin_id:
                            trading_pair = pairs_repo.upsert_pair(pair_data)
                            break
                    
                    if not trading_pair:
                        logger.error(f"Could not find or create trading pair for {coin_id}")
                        return super().get_ohlc_data(coin_id, vs_currency, days, timeframe)
                
                # Check for existing data in database
                start_date = datetime.now() - timedelta(days=days)
                
                if not force_refresh:
                    existing_data = ohlcv_repo.get_by_pair_and_timeframe(
                        trading_pair.id, timeframe, start_date, limit=days
                    )
                    
                    if existing_data and len(existing_data) >= days * 0.8:  # Have at least 80% of expected data
                        logger.info(f"Using cached OHLCV data for {coin_id} ({len(existing_data)} records)")
                        df = ohlcv_repo.to_dataframe(existing_data)
                        return df.sort_index()
                
                # Fetch fresh data from API
                logger.info(f"Fetching fresh OHLCV data for {coin_id} from API")
                df = super().get_ohlc_data(coin_id, vs_currency, days, timeframe)
                
                if df is not None and not df.empty:
                    # Save to database
                    ohlcv_records = []
                    for timestamp, row in df.iterrows():
                        ohlcv_records.append({
                            'pair_id': trading_pair.id,
                            'timestamp': timestamp,
                            'timeframe': timeframe,
                            'open_price': float(row['open']),
                            'high_price': float(row['high']),
                            'low_price': float(row['low']),
                            'close_price': float(row['close']),
                            'volume': float(row.get('volume', 0))
                        })
                    
                    saved_count = ohlcv_repo.bulk_insert_ohlcv(ohlcv_records)
                    logger.info(f"Saved {saved_count} new OHLCV records for {coin_id}")
                    
                    return df
                else:
                    # Fallback to database if API fails
                    logger.warning(f"API failed for {coin_id}, falling back to database")
                    existing_data = ohlcv_repo.get_by_pair_and_timeframe(
                        trading_pair.id, timeframe, start_date, limit=days
                    )
                    if existing_data:
                        return ohlcv_repo.to_dataframe(existing_data).sort_index()
                    return None
                    
        except Exception as e:
            logger.error(f"Error in get_ohlc_data_with_persistence for {coin_id}: {e}")
            # Fallback to original API method
            return super().get_ohlc_data(coin_id, vs_currency, days, timeframe)
    
    def sync_trading_pairs(self, limit: int = 100) -> int:
        """Synchronize trading pairs with CoinGecko API"""
        try:
            logger.info(f"Synchronizing {limit} trading pairs from CoinGecko")
            api_pairs = super().get_coins_markets("usd", limit)
            
            if not api_pairs:
                logger.warning("No pairs returned from API")
                return 0
            
            with self.db_manager.get_db_session() as session:
                pairs_repo = TradingPairsRepository(session)
                updated_count = pairs_repo.bulk_upsert_pairs(api_pairs)
                logger.info(f"Synchronized {updated_count} trading pairs")
                return updated_count
                
        except Exception as e:
            logger.error(f"Error synchronizing trading pairs: {e}")
            return 0
    
    def update_market_data_for_pair(self, coin_id: str) -> bool:
        """Update market data for a specific pair"""
        try:
            # Get latest market data from API
            api_pairs = super().get_coins_markets("usd", 100)
            
            for pair_data in api_pairs:
                if pair_data.get('coin_id') == coin_id:
                    with self.db_manager.get_db_session() as session:
                        pairs_repo = TradingPairsRepository(session)
                        updated_pair = pairs_repo.upsert_pair(pair_data)
                        
                        if updated_pair:
                            logger.info(f"Updated market data for {coin_id}")
                            return True
                        break
            
            logger.warning(f"Could not find {coin_id} in API response")
            return False
            
        except Exception as e:
            logger.error(f"Error updating market data for {coin_id}: {e}")
            return False
    
    def get_missing_ohlcv_data(self, coin_id: str, timeframe: str = "1d", 
                              max_days: int = 90) -> List[tuple]:
        """Find missing OHLCV data ranges for a coin"""
        try:
            with self.db_manager.get_db_session() as session:
                pairs_repo = TradingPairsRepository(session)
                ohlcv_repo = OHLCVRepository(session)
                
                trading_pair = pairs_repo.get_by_coin_id(coin_id)
                if not trading_pair:
                    return []
                
                start_date = datetime.now() - timedelta(days=max_days)
                end_date = datetime.now()
                
                return ohlcv_repo.get_missing_data_ranges(
                    trading_pair.id, timeframe, start_date, end_date
                )
                
        except Exception as e:
            logger.error(f"Error finding missing OHLCV data for {coin_id}: {e}")
            return []
    
    def backfill_ohlcv_data(self, coin_id: str, timeframe: str = "1d", 
                           days: int = 90) -> int:
        """Backfill missing OHLCV data for a coin"""
        try:
            missing_ranges = self.get_missing_ohlcv_data(coin_id, timeframe, days)
            
            if not missing_ranges:
                logger.info(f"No missing data found for {coin_id}")
                return 0
            
            total_filled = 0
            
            for start_date, end_date in missing_ranges:
                days_to_fetch = (end_date - start_date).days
                if days_to_fetch > 0:
                    logger.info(f"Backfilling {days_to_fetch} days for {coin_id} from {start_date} to {end_date}")
                    
                    # Fetch data for this range
                    df = super().get_ohlc_data(coin_id, "usd", days_to_fetch, timeframe)
                    
                    if df is not None and not df.empty:
                        # Filter to the specific date range
                        df = df[(df.index >= start_date) & (df.index <= end_date)]
                        
                        if not df.empty:
                            # Save to database
                            with self.db_manager.get_db_session() as session:
                                pairs_repo = TradingPairsRepository(session)
                                ohlcv_repo = OHLCVRepository(session)
                                
                                trading_pair = pairs_repo.get_by_coin_id(coin_id)
                                if trading_pair:
                                    ohlcv_records = []
                                    for timestamp, row in df.iterrows():
                                        ohlcv_records.append({
                                            'pair_id': trading_pair.id,
                                            'timestamp': timestamp,
                                            'timeframe': timeframe,
                                            'open_price': float(row['open']),
                                            'high_price': float(row['high']),
                                            'low_price': float(row['low']),
                                            'close_price': float(row['close']),
                                            'volume': float(row.get('volume', 0))
                                        })
                                    
                                    saved_count = ohlcv_repo.bulk_insert_ohlcv(ohlcv_records)
                                    total_filled += saved_count
                                    logger.info(f"Backfilled {saved_count} records for range {start_date} to {end_date}")
            
            logger.info(f"Total backfilled records for {coin_id}: {total_filled}")
            return total_filled
            
        except Exception as e:
            logger.error(f"Error backfilling OHLCV data for {coin_id}: {e}")
            return 0
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.db_manager.get_db_session() as session:
                pairs_repo = TradingPairsRepository(session)
                ohlcv_repo = OHLCVRepository(session)
                
                return {
                    'trading_pairs_count': pairs_repo.count(),
                    'ohlcv_records_count': ohlcv_repo.count(),
                    'top_pairs_by_market_cap': [
                        pair.to_dict() for pair in pairs_repo.get_top_by_market_cap(10)
                    ]
                }
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}

# Global enhanced client instance
enhanced_coingecko_client = EnhancedCoinGeckoClient()