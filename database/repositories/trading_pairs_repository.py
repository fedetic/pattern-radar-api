from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import desc, asc
from typing import List, Optional, Dict, Any
import logging

from ..models import TradingPair
from .base_repository import BaseRepository

logger = logging.getLogger(__name__)

class TradingPairsRepository(BaseRepository[TradingPair]):
    """Repository for trading pairs operations"""
    
    def __init__(self, session: Session):
        super().__init__(session, TradingPair)
    
    def get_by_coin_id(self, coin_id: str) -> Optional[TradingPair]:
        """Get trading pair by coin_id"""
        try:
            return self.session.query(TradingPair).filter(
                TradingPair.coin_id == coin_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting trading pair by coin_id {coin_id}: {e}")
            return None
    
    def get_by_symbol(self, symbol: str) -> Optional[TradingPair]:
        """Get trading pair by symbol"""
        try:
            return self.session.query(TradingPair).filter(
                TradingPair.symbol == symbol
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Error getting trading pair by symbol {symbol}: {e}")
            return None
    
    def get_active_pairs(self, limit: Optional[int] = None) -> List[TradingPair]:
        """Get all active trading pairs"""
        try:
            query = self.session.query(TradingPair).filter(
                TradingPair.status == 'active'
            ).order_by(asc(TradingPair.market_cap_rank))
            
            if limit:
                query = query.limit(limit)
            
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting active trading pairs: {e}")
            return []
    
    def get_top_by_market_cap(self, limit: int = 50) -> List[TradingPair]:
        """Get top trading pairs by market cap rank"""
        try:
            return self.session.query(TradingPair).filter(
                TradingPair.status == 'active',
                TradingPair.market_cap_rank.isnot(None)
            ).order_by(asc(TradingPair.market_cap_rank)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error getting top trading pairs by market cap: {e}")
            return []
    
    def search_pairs(self, search_term: str, limit: int = 20) -> List[TradingPair]:
        """Search trading pairs by name, symbol, or coin_id"""
        try:
            search_pattern = f"%{search_term.lower()}%"
            return self.session.query(TradingPair).filter(
                TradingPair.status == 'active'
            ).filter(
                (TradingPair.name.ilike(search_pattern)) |
                (TradingPair.symbol.ilike(search_pattern)) |
                (TradingPair.coin_id.ilike(search_pattern))
            ).order_by(asc(TradingPair.market_cap_rank)).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching trading pairs with term '{search_term}': {e}")
            return []
    
    def upsert_pair(self, pair_data: Dict[str, Any]) -> Optional[TradingPair]:
        """Insert or update a trading pair"""
        try:
            # Map API fields to database model fields
            mapped_data = self._map_api_data_to_model(pair_data)
            
            # Try to find existing pair by coin_id
            existing_pair = self.get_by_coin_id(mapped_data.get('coin_id'))
            
            if existing_pair:
                # Update existing pair
                for key, value in mapped_data.items():
                    if hasattr(existing_pair, key) and key != 'id':
                        setattr(existing_pair, key, value)
                self.session.flush()
                logger.info(f"Updated trading pair: {existing_pair.coin_id}")
                return existing_pair
            else:
                # Create new pair
                new_pair = self.create(**mapped_data)
                logger.info(f"Created new trading pair: {new_pair.coin_id if new_pair else 'Failed'}")
                return new_pair
                
        except SQLAlchemyError as e:
            logger.error(f"Error upserting trading pair {pair_data.get('coin_id', 'unknown')}: {e}")
            self.session.rollback()
            return None
    
    def bulk_upsert_pairs(self, pairs_data: List[Dict[str, Any]]) -> int:
        """Bulk insert or update trading pairs"""
        try:
            updated_count = 0
            created_count = 0
            
            for pair_data in pairs_data:
                # Map API fields to database model fields
                mapped_data = self._map_api_data_to_model(pair_data)
                
                existing_pair = self.get_by_coin_id(mapped_data.get('coin_id'))
                
                if existing_pair:
                    # Update existing
                    for key, value in mapped_data.items():
                        if hasattr(existing_pair, key) and key != 'id':
                            setattr(existing_pair, key, value)
                    updated_count += 1
                else:
                    # Create new
                    new_pair = TradingPair(**mapped_data)
                    self.session.add(new_pair)
                    created_count += 1
            
            self.session.flush()
            logger.info(f"Bulk upsert completed: {created_count} created, {updated_count} updated")
            return created_count + updated_count
            
        except SQLAlchemyError as e:
            logger.error(f"Error in bulk upsert trading pairs: {e}")
            self.session.rollback()
            return 0
    
    def _map_api_data_to_model(self, api_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map API field names to database model field names"""
        mapped_data = {}
        
        # Direct field mappings
        field_mappings = {
            'coin_id': 'coin_id',
            'symbol': 'symbol', 
            'name': 'name',
            'current_price': 'current_price',
            'market_cap': 'market_cap',
            'market_cap_rank': 'market_cap_rank',
            'status': 'status'
        }
        
        # Map base and quote to base_currency and quote_currency
        if 'base' in api_data:
            mapped_data['base_currency'] = api_data['base']
        if 'quote' in api_data:
            mapped_data['quote_currency'] = api_data['quote']
        
        # Apply direct mappings
        for api_field, model_field in field_mappings.items():
            if api_field in api_data:
                mapped_data[model_field] = api_data[api_field]
        
        return mapped_data
    
    def get_pairs_with_recent_data(self, hours: int = 24) -> List[TradingPair]:
        """Get pairs that have recent OHLCV data"""
        try:
            from sqlalchemy import text
            
            query = text("""
                SELECT DISTINCT tp.*
                FROM patternapp.trading_pairs tp
                JOIN patternapp.ohlcv_data od ON tp.id = od.pair_id
                WHERE tp.status = 'active'
                AND od.timestamp >= NOW() - INTERVAL ':hours hours'
                ORDER BY tp.market_cap_rank ASC NULLS LAST
            """)
            
            result = self.session.execute(query, {'hours': hours})
            pairs = []
            for row in result:
                pair = TradingPair()
                for key, value in row._mapping.items():
                    setattr(pair, key, value)
                pairs.append(pair)
            
            return pairs
        except SQLAlchemyError as e:
            logger.error(f"Error getting pairs with recent data: {e}")
            return []
    
    def get_pairs_needing_update(self, hours: int = 1) -> List[TradingPair]:
        """Get pairs that need price/market cap updates"""
        try:
            from sqlalchemy import text
            
            query = text("""
                SELECT * FROM patternapp.trading_pairs
                WHERE status = 'active'
                AND (updated_at IS NULL OR updated_at < NOW() - INTERVAL ':hours hours')
                ORDER BY market_cap_rank ASC NULLS LAST
                LIMIT 100
            """)
            
            result = self.session.execute(query, {'hours': hours})
            pairs = []
            for row in result:
                pair = TradingPair()
                for key, value in row._mapping.items():
                    setattr(pair, key, value)
                pairs.append(pair)
            
            return pairs
        except SQLAlchemyError as e:
            logger.error(f"Error getting pairs needing update: {e}")
            return []
    
    def update_market_data(self, coin_id: str, market_cap: int = None, 
                          current_price: float = None, market_cap_rank: int = None) -> Optional[TradingPair]:
        """Update market data for a trading pair"""
        try:
            pair = self.get_by_coin_id(coin_id)
            if pair:
                if market_cap is not None:
                    pair.market_cap = market_cap
                if current_price is not None:
                    pair.current_price = current_price
                if market_cap_rank is not None:
                    pair.market_cap_rank = market_cap_rank
                
                self.session.flush()
                return pair
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error updating market data for {coin_id}: {e}")
            self.session.rollback()
            return None