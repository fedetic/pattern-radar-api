-- Create the patternapp schema
CREATE SCHEMA IF NOT EXISTS patternapp;

-- Set search path to use the schema
SET search_path TO patternapp, public;

-- 1. Trading Pairs Entity Table
CREATE TABLE IF NOT EXISTS patternapp.trading_pairs (
    id SERIAL PRIMARY KEY,
    coin_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'bitcoin'
    symbol VARCHAR(20) NOT NULL,          -- e.g., 'BTC-USD'
    base_currency VARCHAR(10) NOT NULL,   -- e.g., 'BTC'
    quote_currency VARCHAR(10) NOT NULL,  -- e.g., 'USD'
    name VARCHAR(100) NOT NULL,           -- e.g., 'Bitcoin'
    market_cap BIGINT,
    market_cap_rank INTEGER,
    current_price DECIMAL(20,8),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for trading_pairs
CREATE INDEX IF NOT EXISTS idx_trading_pairs_coin_id ON patternapp.trading_pairs(coin_id);
CREATE INDEX IF NOT EXISTS idx_trading_pairs_symbol ON patternapp.trading_pairs(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_pairs_market_cap_rank ON patternapp.trading_pairs(market_cap_rank);

-- 2. OHLCV Transaction Table
CREATE TABLE IF NOT EXISTS patternapp.ohlcv_data (
    id SERIAL PRIMARY KEY,
    pair_id INTEGER NOT NULL REFERENCES patternapp.trading_pairs(id) ON DELETE CASCADE,
    timestamp TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,       -- '1d', '4h', '1h', etc.
    open_price DECIMAL(20,8) NOT NULL,
    high_price DECIMAL(20,8) NOT NULL,
    low_price DECIMAL(20,8) NOT NULL,
    close_price DECIMAL(20,8) NOT NULL,
    volume DECIMAL(30,8) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_ohlcv_entry UNIQUE(pair_id, timestamp, timeframe)
);

-- Create indexes for ohlcv_data
CREATE INDEX IF NOT EXISTS idx_ohlcv_pair_timestamp ON patternapp.ohlcv_data(pair_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_timestamp ON patternapp.ohlcv_data(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_timeframe ON patternapp.ohlcv_data(timeframe);

-- 3. Pattern Types Entity Table
CREATE TABLE IF NOT EXISTS patternapp.pattern_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,    -- e.g., 'Doji', 'Hammer'
    category VARCHAR(50) NOT NULL,        -- 'Candle', 'Chart', 'Volume-Based', etc.
    pattern_type VARCHAR(50) NOT NULL,    -- 'candlestick', 'harmonic', 'statistical'
    typical_duration INTEGER DEFAULT 1,   -- Duration in candles
    description TEXT,
    reliability_score INTEGER,            -- 1-100 general reliability
    is_reversal BOOLEAN DEFAULT FALSE,
    is_continuation BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for pattern_types
CREATE INDEX IF NOT EXISTS idx_pattern_types_category ON patternapp.pattern_types(category);
CREATE INDEX IF NOT EXISTS idx_pattern_types_pattern_type ON patternapp.pattern_types(pattern_type);
CREATE INDEX IF NOT EXISTS idx_pattern_types_reliability ON patternapp.pattern_types(reliability_score DESC);

-- 4. Detected Patterns Transaction Table
CREATE TABLE IF NOT EXISTS patternapp.detected_patterns (
    id SERIAL PRIMARY KEY,
    pair_id INTEGER NOT NULL REFERENCES patternapp.trading_pairs(id) ON DELETE CASCADE,
    pattern_type_id INTEGER NOT NULL REFERENCES patternapp.pattern_types(id) ON DELETE CASCADE,
    confidence_level INTEGER NOT NULL CHECK (confidence_level >= 0 AND confidence_level <= 100),
    direction VARCHAR(20) NOT NULL CHECK (direction IN ('bullish', 'bearish', 'neutral', 'continuation')),
    detection_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    pattern_start_time TIMESTAMP NOT NULL,
    pattern_end_time TIMESTAMP NOT NULL,
    timeframe VARCHAR(10) NOT NULL,
    coordinates JSONB,                    -- Store pattern coordinates for visualization
    pattern_high DECIMAL(20,8),
    pattern_low DECIMAL(20,8),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for detected_patterns
CREATE INDEX IF NOT EXISTS idx_detected_patterns_pair_detection ON patternapp.detected_patterns(pair_id, detection_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_detected_patterns_pattern_confidence ON patternapp.detected_patterns(pattern_type_id, confidence_level DESC);
CREATE INDEX IF NOT EXISTS idx_detected_patterns_detection_timestamp ON patternapp.detected_patterns(detection_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_detected_patterns_direction ON patternapp.detected_patterns(direction);
CREATE INDEX IF NOT EXISTS idx_detected_patterns_timeframe ON patternapp.detected_patterns(timeframe);
CREATE INDEX IF NOT EXISTS idx_detected_patterns_pattern_time_range ON patternapp.detected_patterns(pattern_start_time, pattern_end_time);

-- Create composite index for common queries
CREATE INDEX IF NOT EXISTS idx_detected_patterns_pair_time_confidence 
ON patternapp.detected_patterns(pair_id, detection_timestamp DESC, confidence_level DESC);

-- Update trigger for trading_pairs
CREATE OR REPLACE FUNCTION patternapp.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER update_trading_pairs_updated_at 
    BEFORE UPDATE ON patternapp.trading_pairs 
    FOR EACH ROW EXECUTE FUNCTION patternapp.update_updated_at_column();

-- Views for common queries
CREATE OR REPLACE VIEW patternapp.latest_patterns AS
SELECT 
    dp.id,
    tp.coin_id,
    tp.symbol,
    tp.name as pair_name,
    pt.name as pattern_name,
    pt.category,
    dp.confidence_level,
    dp.direction,
    dp.detection_timestamp,
    dp.pattern_start_time,
    dp.pattern_end_time,
    dp.timeframe,
    dp.coordinates,
    pt.reliability_score
FROM patternapp.detected_patterns dp
JOIN patternapp.trading_pairs tp ON dp.pair_id = tp.id
JOIN patternapp.pattern_types pt ON dp.pattern_type_id = pt.id
WHERE dp.detection_timestamp >= NOW() - INTERVAL '7 days'
ORDER BY dp.detection_timestamp DESC, dp.confidence_level DESC;

-- Pattern statistics view
CREATE OR REPLACE VIEW patternapp.pattern_statistics AS
SELECT 
    pt.name as pattern_name,
    pt.category,
    COUNT(*) as detection_count,
    AVG(dp.confidence_level) as avg_confidence,
    COUNT(CASE WHEN dp.direction = 'bullish' THEN 1 END) as bullish_count,
    COUNT(CASE WHEN dp.direction = 'bearish' THEN 1 END) as bearish_count,
    COUNT(CASE WHEN dp.direction = 'neutral' THEN 1 END) as neutral_count,
    MAX(dp.detection_timestamp) as last_detected
FROM patternapp.pattern_types pt
LEFT JOIN patternapp.detected_patterns dp ON pt.id = dp.pattern_type_id
WHERE dp.detection_timestamp >= NOW() - INTERVAL '30 days' OR dp.detection_timestamp IS NULL
GROUP BY pt.id, pt.name, pt.category
ORDER BY detection_count DESC, avg_confidence DESC;

-- Comments for documentation
COMMENT ON SCHEMA patternapp IS 'Pattern analysis application database schema';
COMMENT ON TABLE patternapp.trading_pairs IS 'Available cryptocurrency trading pairs';
COMMENT ON TABLE patternapp.ohlcv_data IS 'OHLCV market data for trading pairs';
COMMENT ON TABLE patternapp.pattern_types IS 'Master table of all pattern types and their metadata';
COMMENT ON TABLE patternapp.detected_patterns IS 'Historical record of detected patterns';
COMMENT ON VIEW patternapp.latest_patterns IS 'Recent pattern detections with full metadata';
COMMENT ON VIEW patternapp.pattern_statistics IS 'Pattern detection statistics over the last 30 days';