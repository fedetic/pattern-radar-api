"""
ML Predictor Service for Pattern Hero API

This service interfaces with the trained ML models from pattern-data-ingest
to provide price direction predictions and buy/hold/sell recommendations.
"""

import os
import sys
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import logging

# Add pattern-data-ingest to path for imports
pattern_data_ingest_path = os.path.join(os.path.dirname(__file__), '..', '..', 'pattern-data-ingest')
sys.path.append(pattern_data_ingest_path)

try:
    from feature_engineering.processor import FeatureEngineeringProcessor
    from ml_models.correction_predictor import CorrectionPredictor
    FEATURE_ENGINEERING_AVAILABLE = True
except ImportError as e:
    FEATURE_ENGINEERING_AVAILABLE = False
    FeatureEngineeringProcessor = None
    CorrectionPredictor = None
    print(f"Error: ML dependencies not found: {e}")
    print("Please install pattern-data-ingest dependencies to enable ML predictions")

try:
    import xgboost as xgb
    from sklearn.preprocessing import RobustScaler
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: XGBoost not available, using mock predictions")

class MLPredictorService:
    """
    Service to provide ML-based predictions and recommendations for trading pairs.
    """
    
    def __init__(self, model_dir: str = None):
        """
        Initialize the ML predictor service.
        
        Args:
            model_dir: Directory containing trained models
        """
        if model_dir is None:
            self.model_dir = os.path.join(pattern_data_ingest_path, 'trained_models')
        else:
            self.model_dir = model_dir
            
        self.feature_processor = None
        self.loaded_models = {}  # Cache for loaded models
        self.logger = logging.getLogger(__name__)
        
        # Initialize feature processor if available
        if FEATURE_ENGINEERING_AVAILABLE:
            try:
                self.feature_processor = FeatureEngineeringProcessor()
                print("Feature engineering processor initialized")
            except Exception as e:
                print(f"Error initializing feature processor: {e}")
                self.feature_processor = None
    
    def get_prediction(self, coin_id: str, market_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Get ML predictions for a trading pair.
        
        Args:
            coin_id: Trading pair identifier (e.g., 'bitcoin')
            market_data: DataFrame with OHLCV data
            
        Returns:
            Dictionary containing ML predictions and confidence scores, or None if ML not available
        """
        try:
            # Only use real ML models - no fallbacks
            if not FEATURE_ENGINEERING_AVAILABLE or not XGBOOST_AVAILABLE:
                self.logger.warning(f"ML dependencies not available for {coin_id}")
                return None
            
            # Generate features from market data
            enriched_data = self._generate_features(market_data)
            if not enriched_data:
                self.logger.warning(f"Could not generate features for {coin_id}")
                return None
            
            # Load or get cached model
            model_path = self._find_model_for_pair(coin_id)
            if not model_path:
                self.logger.warning(f"No trained model found for {coin_id}")
                return None
            
            predictor = self._load_model(model_path)
            if not predictor:
                self.logger.warning(f"Could not load model for {coin_id}")
                return None
            
            # Prepare features for prediction
            X = self._prepare_features_for_prediction(enriched_data, predictor.feature_names)
            if X is None or X.size == 0:
                self.logger.warning(f"Could not prepare features for {coin_id}")
                return None
            
            # Make prediction
            prediction = predictor.predict(X)
            correction_probability = float(prediction[-1]) if len(prediction) > 0 else 0.5
            
            # Generate market direction assessment
            market_direction = self._assess_market_direction(enriched_data)
            
            # Calculate confidence
            confidence = self._calculate_confidence(correction_probability, market_direction)
            
            return {
                "coin_id": coin_id,
                "timestamp": datetime.now().isoformat(),
                "correction_probability_5d": correction_probability,
                "market_direction": market_direction,
                "bull_market_strength": self._calculate_bull_strength(enriched_data),
                "confidence": confidence,
                "prediction_horizon": "5 days",
                "model_available": True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting prediction for {coin_id}: {e}")
            return None
    
    
    def get_recommendation(self, coin_id: str, market_data: pd.DataFrame, 
                          pattern_strength: float = 0) -> Optional[Dict[str, Any]]:
        """
        Generate buy/hold/sell recommendation based on ML predictions and patterns.
        
        Args:
            coin_id: Trading pair identifier
            market_data: DataFrame with OHLCV data
            pattern_strength: Strength of detected patterns (0-100)
            
        Returns:
            Dictionary containing recommendation and reasoning
        """
        try:
            # Get ML prediction (now always returns something)
            prediction = self.get_prediction(coin_id, market_data)
            
            if prediction is None:
                return None
            
            correction_prob = prediction.get('correction_probability_5d', 0.5)
            market_direction = prediction.get('market_direction', 'sideways')
            confidence = prediction.get('confidence', 0.5)
            
            # Generate recommendation
            recommendation = self._generate_recommendation(
                correction_prob, pattern_strength, market_direction, confidence
            )
            
            return {
                "coin_id": coin_id,
                "timestamp": datetime.now().isoformat(),
                "recommendation": recommendation["action"],
                "confidence": recommendation["confidence"],
                "reasoning": recommendation["reasoning"],
                "risk_level": recommendation["risk_level"],
                "ml_prediction": prediction,
                "pattern_strength": pattern_strength,
                "factors": {
                    "correction_probability": correction_prob,
                    "market_direction": market_direction,
                    "pattern_strength": pattern_strength,
                    "overall_confidence": confidence
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation for {coin_id}: {e}")
            return None
    
    def _generate_features(self, market_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """Generate ML features from market data."""
        try:
            if not self.feature_processor or market_data.empty:
                return None
            
            # Ensure minimum data length
            if len(market_data) < 50:
                return None
            
            # Process features
            enriched_data = self.feature_processor.process_features(market_data)
            return enriched_data
            
        except Exception as e:
            self.logger.error(f"Error generating features: {e}")
            return None
    
    def _find_model_for_pair(self, coin_id: str) -> Optional[str]:
        """Find the latest trained model for a trading pair."""
        try:
            if not os.path.exists(self.model_dir):
                self.logger.error(f"Model directory does not exist: {self.model_dir}")
                print(f"ML Model directory not found: {self.model_dir}")
                print("Please create trained models by running:")
                print(f"  cd pattern-data-ingest")
                print(f"  python scripts/train_correction_model.py --pair {coin_id.upper()}/USD")
                return None
            
            # Look for models matching the coin_id
            model_files = []
            for filename in os.listdir(self.model_dir):
                if filename.startswith(f"correction_model_{coin_id}") and filename.endswith('.pkl'):
                    model_path = os.path.join(self.model_dir, filename)
                    model_files.append((filename, model_path))
            
            if not model_files:
                # Try with common symbol mappings
                symbol_mappings = {
                    'bitcoin': 'BTC_USD',
                    'ethereum': 'ETH_USD',
                    'solana': 'SOL_USD',
                    'cardano': 'ADA_USD'
                }
                
                if coin_id in symbol_mappings:
                    symbol = symbol_mappings[coin_id]
                    self.logger.info(f"Trying symbol mapping: {coin_id} -> {symbol}")
                    for filename in os.listdir(self.model_dir):
                        if filename.startswith(f"correction_model_{symbol}") and filename.endswith('.pkl'):
                            model_path = os.path.join(self.model_dir, filename)
                            model_files.append((filename, model_path))
            
            if model_files:
                # Return the most recent model
                model_files.sort(reverse=True)
                selected_model = model_files[0][1]
                self.logger.info(f"Found model for {coin_id}: {model_files[0][0]}")
                return selected_model
            
            # Log specific error about missing models
            available_models = [f for f in os.listdir(self.model_dir) if f.endswith('.pkl')]
            self.logger.error(f"No trained model found for {coin_id}")
            print(f"No trained model found for {coin_id}")
            print(f"Available models in {self.model_dir}:")
            if available_models:
                for model in available_models:
                    print(f"  - {model}")
                print(f"\nTo train a model for {coin_id}:")
                print(f"  cd pattern-data-ingest")
                print(f"  python scripts/train_correction_model.py --pair {coin_id.upper()}/USD")
            else:
                print("  (No models found)")
                print("Please train models first:")
                print("  cd pattern-data-ingest")
                print("  python scripts/ingest_multi_pairs.py --pair BTC/USD --days 365")
                print("  python scripts/feature_engineering.py --pair BTC/USD")
                print("  python scripts/train_correction_model.py --pair BTC/USD")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding model for {coin_id}: {e}")
            return None
    
    def _load_model(self, model_path: str) -> Optional[CorrectionPredictor]:
        """Load a trained model from file."""
        try:
            if model_path in self.loaded_models:
                self.logger.info(f"Using cached model: {os.path.basename(model_path)}")
                return self.loaded_models[model_path]
            
            if not FEATURE_ENGINEERING_AVAILABLE:
                self.logger.error("Feature engineering not available - cannot load model")
                print("Error: Missing ML dependencies")
                print("Please install required packages:")
                print("  pip install xgboost scikit-learn pandas ta-lib")
                return None
            
            if not os.path.exists(model_path):
                self.logger.error(f"Model file does not exist: {model_path}")
                print(f"Error: Model file not found: {model_path}")
                return None
            
            self.logger.info(f"Loading model from: {os.path.basename(model_path)}")
            print(f"Loading ML model: {os.path.basename(model_path)}")
            
            predictor = CorrectionPredictor()
            predictor.load_model(model_path)
            
            # Cache the loaded model
            self.loaded_models[model_path] = predictor
            print(f"Successfully loaded model with {len(predictor.feature_names)} features")
            return predictor
            
        except FileNotFoundError:
            self.logger.error(f"Model file not found: {model_path}")
            print(f"Error: Model file not found: {model_path}")
            return None
        except Exception as e:
            self.logger.error(f"Error loading model from {model_path}: {e}")
            print(f"Error loading model: {e}")
            print("The model file may be corrupted or incompatible.")
            print("Try retraining the model:")
            print("  cd pattern-data-ingest")
            print("  python scripts/train_correction_model.py --pair BTC/USD")
            return None
    
    def _prepare_features_for_prediction(self, enriched_data: Dict[str, Any], 
                                       feature_names: List[str]) -> Optional[np.ndarray]:
        """Prepare features for model prediction."""
        try:
            feature_values = []
            
            for feature_name in feature_names:
                if feature_name in enriched_data:
                    values = enriched_data[feature_name]
                    if isinstance(values, (list, np.ndarray)) and len(values) > 0:
                        # Use the latest value
                        latest_value = values[-1] if not np.isnan(values[-1]) else 0.0
                        feature_values.append(latest_value)
                    else:
                        feature_values.append(0.0)
                else:
                    feature_values.append(0.0)
            
            if not feature_values:
                return None
            
            # Return as 2D array for single prediction
            return np.array([feature_values])
            
        except Exception as e:
            self.logger.error(f"Error preparing features: {e}")
            return None
    
    def _assess_market_direction(self, enriched_data: Dict[str, Any]) -> str:
        """Assess current market direction from features."""
        try:
            if 'market_direction' in enriched_data:
                direction_values = enriched_data['market_direction']
                if isinstance(direction_values, (list, np.ndarray)) and len(direction_values) > 0:
                    latest_direction = direction_values[-1]
                    if latest_direction == 1:
                        return "bull"
                    elif latest_direction == -1:
                        return "bear"
                    else:
                        return "sideways"
            
            # Fallback: use moving averages
            if 'sma_20' in enriched_data and 'sma_50' in enriched_data and 'close' in enriched_data:
                sma_20 = enriched_data['sma_20'][-1] if len(enriched_data['sma_20']) > 0 else 0
                sma_50 = enriched_data['sma_50'][-1] if len(enriched_data['sma_50']) > 0 else 0
                close = enriched_data['close'][-1] if len(enriched_data['close']) > 0 else 0
                
                if close > sma_20 > sma_50:
                    return "bull"
                elif close < sma_20 < sma_50:
                    return "bear"
            
            return "sideways"
            
        except Exception as e:
            self.logger.error(f"Error assessing market direction: {e}")
            return "sideways"
    
    def _calculate_bull_strength(self, enriched_data: Dict[str, Any]) -> float:
        """Calculate bull market strength (0.0 to 1.0)."""
        try:
            if 'bull_strength' in enriched_data:
                values = enriched_data['bull_strength']
                if isinstance(values, (list, np.ndarray)) and len(values) > 0:
                    return max(0.0, min(1.0, float(values[-1])))
            
            # Fallback calculation
            strength_factors = []
            
            # RSI factor
            if 'rsi_14' in enriched_data:
                rsi = enriched_data['rsi_14'][-1] if len(enriched_data['rsi_14']) > 0 else 50
                strength_factors.append((rsi - 50) / 50)  # -1 to 1 scale
            
            # Moving average factor
            if 'sma_20' in enriched_data and 'sma_50' in enriched_data:
                sma_20 = enriched_data['sma_20'][-1] if len(enriched_data['sma_20']) > 0 else 0
                sma_50 = enriched_data['sma_50'][-1] if len(enriched_data['sma_50']) > 0 else 0
                if sma_50 > 0:
                    ma_factor = (sma_20 - sma_50) / sma_50
                    strength_factors.append(max(-1, min(1, ma_factor)))
            
            if strength_factors:
                avg_strength = np.mean(strength_factors)
                return max(0.0, min(1.0, (avg_strength + 1) / 2))  # Convert to 0-1 scale
            
            return 0.5
            
        except Exception as e:
            self.logger.error(f"Error calculating bull strength: {e}")
            return 0.5
    
    def _calculate_confidence(self, correction_prob: float, market_direction: str) -> float:
        """Calculate overall prediction confidence."""
        try:
            base_confidence = 0.5
            
            # Higher confidence for extreme probabilities
            if correction_prob > 0.8 or correction_prob < 0.2:
                base_confidence += 0.2
            elif correction_prob > 0.7 or correction_prob < 0.3:
                base_confidence += 0.1
            
            # Adjust based on market direction clarity
            if market_direction in ["bull", "bear"]:
                base_confidence += 0.1
            
            return max(0.0, min(1.0, base_confidence))
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}")
            return 0.5
    
    def _generate_recommendation(self, correction_prob: float, pattern_strength: float, 
                               market_direction: str, confidence: float) -> Dict[str, Any]:
        """Generate buy/hold/sell recommendation based on inputs."""
        try:
            # Normalize pattern strength to 0-1 scale
            pattern_strength_norm = pattern_strength / 100.0
            
            # Recommendation logic
            if market_direction == "bull":
                if correction_prob > 0.7:
                    # High correction risk in bull market -> SELL
                    return {
                        "action": "SELL",
                        "confidence": min(0.9, confidence + 0.2),
                        "reasoning": f"High correction probability ({correction_prob:.1%}) detected in bull market. Consider taking profits.",
                        "risk_level": "HIGH"
                    }
                elif correction_prob < 0.3 and pattern_strength_norm > 0.7:
                    # Low correction risk + strong patterns -> BUY
                    return {
                        "action": "BUY", 
                        "confidence": min(0.9, confidence + 0.1),
                        "reasoning": f"Low correction risk ({correction_prob:.1%}) with strong bullish patterns ({pattern_strength:.0f}%). Good entry opportunity.",
                        "risk_level": "LOW"
                    }
                elif correction_prob < 0.4:
                    # Moderate buy signal
                    return {
                        "action": "BUY",
                        "confidence": confidence,
                        "reasoning": f"Bull market with moderate correction risk ({correction_prob:.1%}). Consider buying.",
                        "risk_level": "MEDIUM"
                    }
            
            elif market_direction == "bear":
                if correction_prob > 0.6:
                    # Bear market with high correction risk -> SELL
                    return {
                        "action": "SELL",
                        "confidence": min(0.9, confidence + 0.1),
                        "reasoning": f"Bear market with high correction probability ({correction_prob:.1%}). Avoid long positions.",
                        "risk_level": "HIGH"
                    }
                elif pattern_strength_norm > 0.8:
                    # Strong patterns in bear market might indicate reversal
                    return {
                        "action": "HOLD",
                        "confidence": confidence,
                        "reasoning": f"Bear market but strong patterns detected. Wait for confirmation.",
                        "risk_level": "MEDIUM"
                    }
            
            # Default case: HOLD
            return {
                "action": "HOLD",
                "confidence": confidence,
                "reasoning": f"Mixed signals: {market_direction} market, {correction_prob:.1%} correction risk. Hold current position.",
                "risk_level": "MEDIUM"
            }
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {e}")
            return {
                "action": "HOLD",
                "confidence": 0.5,
                "reasoning": "Unable to analyze market conditions. Hold current position.",
                "risk_level": "MEDIUM"
            }
    

# Global service instance
ml_predictor_service = MLPredictorService()