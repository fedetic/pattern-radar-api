from sqlalchemy import Column, Integer, BigInteger, String, DECIMAL, TIMESTAMP, Boolean, Text, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()

class TradingPair(Base):
    """Trading pairs entity table"""
    __tablename__ = 'trading_pairs'
    __table_args__ = {'schema': 'patternapp'}

    id = Column(Integer, primary_key=True)
    coin_id = Column(String(50), unique=True, nullable=False)
    symbol = Column(String(20), nullable=False)
    base_currency = Column(String(10), nullable=False)
    quote_currency = Column(String(10), nullable=False)
    name = Column(String(100), nullable=False)
    market_cap = Column(BigInteger)
    market_cap_rank = Column(Integer)
    current_price = Column(DECIMAL(20, 8))
    status = Column(String(20), default='active')
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())

    # Relationships
    ohlcv_data = relationship("OHLCVData", back_populates="trading_pair", cascade="all, delete-orphan")
    detected_patterns = relationship("DetectedPattern", back_populates="trading_pair", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TradingPair(coin_id='{self.coin_id}', symbol='{self.symbol}', name='{self.name}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'coin_id': self.coin_id,
            'symbol': self.symbol,
            'base': self.base_currency,
            'quote': self.quote_currency,
            'label': f"{self.base_currency}/{self.quote_currency}",
            'name': self.name,
            'market_cap': self.market_cap,
            'market_cap_rank': self.market_cap_rank,
            'current_price': float(self.current_price) if self.current_price else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class OHLCVData(Base):
    """OHLCV market data transaction table"""
    __tablename__ = 'ohlcv_data'
    __table_args__ = (
        UniqueConstraint('pair_id', 'timestamp', 'timeframe', name='unique_ohlcv_entry'),
        {'schema': 'patternapp'}
    )

    id = Column(Integer, primary_key=True)
    pair_id = Column(Integer, ForeignKey('patternapp.trading_pairs.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(TIMESTAMP, nullable=False)
    timeframe = Column(String(10), nullable=False)
    open_price = Column(DECIMAL(20, 8), nullable=False)
    high_price = Column(DECIMAL(20, 8), nullable=False)
    low_price = Column(DECIMAL(20, 8), nullable=False)
    close_price = Column(DECIMAL(20, 8), nullable=False)
    volume = Column(DECIMAL(30, 8), default=0)
    created_at = Column(TIMESTAMP, default=func.now())

    # Relationships
    trading_pair = relationship("TradingPair", back_populates="ohlcv_data")

    def __repr__(self):
        return f"<OHLCVData(pair_id={self.pair_id}, timestamp='{self.timestamp}', timeframe='{self.timeframe}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'pair_id': self.pair_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'timeframe': self.timeframe,
            'open': float(self.open_price),
            'high': float(self.high_price),
            'low': float(self.low_price),
            'close': float(self.close_price),
            'volume': float(self.volume) if self.volume else 0
        }

class PatternType(Base):
    """Pattern types entity table"""
    __tablename__ = 'pattern_types'
    __table_args__ = {'schema': 'patternapp'}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(50), nullable=False)
    pattern_type = Column(String(50), nullable=False)
    typical_duration = Column(Integer, default=1)
    description = Column(Text)
    reliability_score = Column(Integer)
    is_reversal = Column(Boolean, default=False)
    is_continuation = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=func.now())

    # Relationships
    detected_patterns = relationship("DetectedPattern", back_populates="pattern_type", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PatternType(name='{self.name}', category='{self.category}', type='{self.pattern_type}')>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'pattern_type': self.pattern_type,
            'typical_duration': self.typical_duration,
            'description': self.description,
            'reliability_score': self.reliability_score,
            'is_reversal': self.is_reversal,
            'is_continuation': self.is_continuation,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DetectedPattern(Base):
    """Detected patterns transaction table"""
    __tablename__ = 'detected_patterns'
    __table_args__ = (
        CheckConstraint('confidence_level >= 0 AND confidence_level <= 100', name='valid_confidence_level'),
        CheckConstraint("direction IN ('bullish', 'bearish', 'neutral', 'continuation')", name='valid_direction'),
        Index('idx_detected_patterns_pair_detection', 'pair_id', 'detection_timestamp'),
        Index('idx_detected_patterns_pattern_confidence', 'pattern_type_id', 'confidence_level'),
        Index('idx_detected_patterns_pair_time_confidence', 'pair_id', 'detection_timestamp', 'confidence_level'),
        {'schema': 'patternapp'}
    )

    id = Column(Integer, primary_key=True)
    pair_id = Column(Integer, ForeignKey('patternapp.trading_pairs.id', ondelete='CASCADE'), nullable=False)
    pattern_type_id = Column(Integer, ForeignKey('patternapp.pattern_types.id', ondelete='CASCADE'), nullable=False)
    confidence_level = Column(Integer, nullable=False)
    direction = Column(String(20), nullable=False)
    detection_timestamp = Column(TIMESTAMP, nullable=False, default=func.now())
    pattern_start_time = Column(TIMESTAMP, nullable=False)
    pattern_end_time = Column(TIMESTAMP, nullable=False)
    timeframe = Column(String(10), nullable=False)
    coordinates = Column(JSONB)
    pattern_high = Column(DECIMAL(20, 8))
    pattern_low = Column(DECIMAL(20, 8))
    created_at = Column(TIMESTAMP, default=func.now())

    # Relationships
    trading_pair = relationship("TradingPair", back_populates="detected_patterns")
    pattern_type = relationship("PatternType", back_populates="detected_patterns")

    def __repr__(self):
        return f"<DetectedPattern(pair_id={self.pair_id}, pattern='{self.pattern_type.name if self.pattern_type else 'Unknown'}', confidence={self.confidence_level})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'pair_id': self.pair_id,
            'pattern_type_id': self.pattern_type_id,
            'name': self.pattern_type.name if self.pattern_type else None,
            'category': self.pattern_type.category if self.pattern_type else None,
            'confidence': self.confidence_level,
            'direction': self.direction,
            'detection_timestamp': self.detection_timestamp.isoformat() if self.detection_timestamp else None,
            'pattern_start_time': self.pattern_start_time.isoformat() if self.pattern_start_time else None,
            'pattern_end_time': self.pattern_end_time.isoformat() if self.pattern_end_time else None,
            'timestamp': self.pattern_start_time.isoformat() if self.pattern_start_time else None,  # For compatibility
            'timeframe': self.timeframe,
            'coordinates': self.coordinates,
            'pattern_high': float(self.pattern_high) if self.pattern_high else None,
            'pattern_low': float(self.pattern_low) if self.pattern_low else None,
            'description': self.pattern_type.description if self.pattern_type else None
        }

# Index definitions for better query performance
Index('idx_trading_pairs_coin_id', TradingPair.coin_id)
Index('idx_trading_pairs_symbol', TradingPair.symbol)
Index('idx_trading_pairs_market_cap_rank', TradingPair.market_cap_rank)

Index('idx_ohlcv_pair_timestamp', OHLCVData.pair_id, OHLCVData.timestamp.desc())
Index('idx_ohlcv_timestamp', OHLCVData.timestamp.desc())
Index('idx_ohlcv_timeframe', OHLCVData.timeframe)

Index('idx_pattern_types_category', PatternType.category)
Index('idx_pattern_types_pattern_type', PatternType.pattern_type)
Index('idx_pattern_types_reliability', PatternType.reliability_score.desc())

Index('idx_detected_patterns_detection_timestamp', DetectedPattern.detection_timestamp.desc())
Index('idx_detected_patterns_direction', DetectedPattern.direction)
Index('idx_detected_patterns_timeframe', DetectedPattern.timeframe)
Index('idx_detected_patterns_pattern_time_range', DetectedPattern.pattern_start_time, DetectedPattern.pattern_end_time)

# Export all models for easy importing
__all__ = ['Base', 'TradingPair', 'OHLCVData', 'PatternType', 'DetectedPattern']