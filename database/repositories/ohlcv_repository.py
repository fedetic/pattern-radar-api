from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, asc, and_, func
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
import pandas as pd

from ..models import OHLCVData, TradingPair
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)

class OHLCVRepository(BaseRepository[OHLCVData]):
    """Repository for OHLCV data operations"""
    
    def __init__(self, session: Session):
        super().__init__(session, OHLCVData)
    
    def get_by_pair_and_timeframe(self, pair_id: int, timeframe: str, 
                                 start_time: Optional[datetime] = None,
                                 end_time: Optional[datetime] = None,
                                 limit: Optional[int] = None) -> List[OHLCVData]:
        """Get OHLCV data for a specific pair and timeframe"""
        try:
            query = self.session.query(OHLCVData).filter(
                OHLCVData.pair_id == pair_id,
                OHLCVData.timeframe == timeframe
            )
            
            if start_time:
                query = query.filter(OHLCVData.timestamp >= start_time)
            if end_time:
                query = query.filter(OHLCVData.timestamp <= end_time)
            
            query = query.order_by(desc(OHLCVData.timestamp))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting OHLCV data for pair {pair_id}, timeframe {timeframe}: {e}")
            return []
    
    def get_latest_by_pair(self, pair_id: int, timeframe: str = '1d', limit: int = 100) -> List[OHLCVData]:
        """Get latest OHLCV data for a pair"""
        return self.get_by_pair_and_timeframe(pair_id, timeframe, limit=limit)
    
    def get_by_coin_id(self, coin_id: str, timeframe: str = '1d', 
                      days: int = 30, limit: Optional[int] = None) -> List[OHLCVData]:
        """Get OHLCV data by coin_id"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            query = self.session.query(OHLCVData).join(TradingPair).filter(
                TradingPair.coin_id == coin_id,
                OHLCVData.timeframe == timeframe,
                OHLCVData.timestamp >= start_time
            ).order_by(asc(OHLCVData.timestamp))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting OHLCV data for coin {coin_id}: {e}")
            return []
    
    def bulk_insert_ohlcv(self, ohlcv_data: List[Dict[str, Any]]) -> int:
        """Bulk insert OHLCV data with conflict handling"""
        try:
            inserted_count = 0
            for data in ohlcv_data:
                # Check if record already exists
                existing = self.session.query(OHLCVData).filter(
                    OHLCVData.pair_id == data['pair_id'],
                    OHLCVData.timestamp == data['timestamp'],
                    OHLCVData.timeframe == data['timeframe']
                ).first()
                
                if not existing:
                    ohlcv_record = OHLCVData(**data)
                    self.session.add(ohlcv_record)
                    inserted_count += 1
                else:
                    # Update existing record if prices are different
                    if (existing.close_price != data.get('close_price') or
                        existing.volume != data.get('volume', 0)):
                        for key, value in data.items():
                            if hasattr(existing, key) and key not in ['id', 'created_at']:
                                setattr(existing, key, value)
            
            self.session.flush()
            logger.info(f"Bulk inserted {inserted_count} OHLCV records")
            return inserted_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error in bulk insert OHLCV data: {e}")
            self.session.rollback()
            return 0
    
    def upsert_ohlcv_record(self, pair_id: int, timestamp: datetime, timeframe: str,
                           open_price: float, high_price: float, low_price: float,
                           close_price: float, volume: float = 0) -> Optional[OHLCVData]:
        """Insert or update a single OHLCV record"""
        try:
            existing = self.session.query(OHLCVData).filter(
                OHLCVData.pair_id == pair_id,
                OHLCVData.timestamp == timestamp,
                OHLCVData.timeframe == timeframe
            ).first()
            
            if existing:
                # Update existing record
                existing.open_price = open_price
                existing.high_price = high_price
                existing.low_price = low_price
                existing.close_price = close_price
                existing.volume = volume
                self.session.flush()
                return existing
            else:
                # Create new record
                new_record = OHLCVData(
                    pair_id=pair_id,
                    timestamp=timestamp,
                    timeframe=timeframe,
                    open_price=open_price,
                    high_price=high_price,
                    low_price=low_price,
                    close_price=close_price,
                    volume=volume
                )
                self.session.add(new_record)
                self.session.flush()
                return new_record
                
        except SQLAlchemyError as e:
            logger.error(f"Error upserting OHLCV record: {e}")
            self.session.rollback()
            return None
    
    def get_missing_data_ranges(self, pair_id: int, timeframe: str, 
                               start_date: datetime, end_date: datetime) -> List[tuple]:
        """Find missing data ranges for a pair and timeframe"""
        try:
            # Get all existing timestamps in the range
            existing_timestamps = self.session.query(OHLCVData.timestamp).filter(
                OHLCVData.pair_id == pair_id,
                OHLCVData.timeframe == timeframe,
                OHLCVData.timestamp >= start_date,
                OHLCVData.timestamp <= end_date
            ).order_by(OHLCVData.timestamp).all()
            
            if not existing_timestamps:
                return [(start_date, end_date)]
            
            # Find gaps in the data
            gaps = []
            existing_dates = [ts[0] for ts in existing_timestamps]
            
            # Check gap before first record
            if existing_dates[0] > start_date:
                gaps.append((start_date, existing_dates[0]))
            
            # Check gaps between records
            for i in range(len(existing_dates) - 1):
                current_date = existing_dates[i]
                next_date = existing_dates[i + 1]
                
                # Calculate expected next timestamp based on timeframe
                if timeframe == '1d':
                    expected_next = current_date + timedelta(days=1)
                elif timeframe == '1h':
                    expected_next = current_date + timedelta(hours=1)
                elif timeframe == '4h':
                    expected_next = current_date + timedelta(hours=4)
                else:
                    expected_next = current_date + timedelta(days=1)
                
                if next_date > expected_next:
                    gaps.append((expected_next, next_date))
            
            # Check gap after last record
            if existing_dates[-1] < end_date:
                gaps.append((existing_dates[-1], end_date))
            
            return gaps
            
        except SQLAlchemyError as e:
            logger.error(f"Error finding missing data ranges: {e}")
            return []
    
    def to_dataframe(self, ohlcv_data: List[OHLCVData]) -> pd.DataFrame:
        """Convert OHLCV data to pandas DataFrame"""
        if not ohlcv_data:
            return pd.DataFrame()
        
        data = []
        for record in ohlcv_data:
            data.append({
                'timestamp': record.timestamp,
                'open': float(record.open_price),
                'high': float(record.high_price),
                'low': float(record.low_price),
                'close': float(record.close_price),
                'volume': float(record.volume) if record.volume else 0
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        return df
    
    def get_latest_timestamp(self, pair_id: int, timeframe: str) -> Optional[datetime]:
        """Get the latest timestamp for a pair and timeframe"""
        try:
            result = self.session.query(func.max(OHLCVData.timestamp)).filter(
                OHLCVData.pair_id == pair_id,
                OHLCVData.timeframe == timeframe
            ).scalar()
            return result
        except SQLAlchemyError as e:
            logger.error(f"Error getting latest timestamp for pair {pair_id}: {e}")
            return None
    
    def get_price_stats(self, pair_id: int, timeframe: str, days: int = 30) -> Dict[str, float]:
        """Get price statistics for a pair"""
        try:
            start_time = datetime.now() - timedelta(days=days)
            
            result = self.session.query(
                func.min(OHLCVData.low_price).label('min_price'),
                func.max(OHLCVData.high_price).label('max_price'),
                func.avg(OHLCVData.close_price).label('avg_price'),
                func.sum(OHLCVData.volume).label('total_volume'),
                func.count(OHLCVData.id).label('data_points')
            ).filter(
                OHLCVData.pair_id == pair_id,
                OHLCVData.timeframe == timeframe,
                OHLCVData.timestamp >= start_time
            ).first()
            
            if result:
                return {
                    'min_price': float(result.min_price) if result.min_price else 0,
                    'max_price': float(result.max_price) if result.max_price else 0,
                    'avg_price': float(result.avg_price) if result.avg_price else 0,
                    'total_volume': float(result.total_volume) if result.total_volume else 0,
                    'data_points': result.data_points or 0
                }
            return {}
        except SQLAlchemyError as e:
            logger.error(f"Error getting price stats for pair {pair_id}: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """Remove OHLCV data older than specified days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            deleted_count = self.session.query(OHLCVData).filter(
                OHLCVData.timestamp < cutoff_date
            ).delete()
            
            self.session.flush()
            logger.info(f"Cleaned up {deleted_count} old OHLCV records")
            return deleted_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error cleaning up old OHLCV data: {e}")
            self.session.rollback()
            return 0