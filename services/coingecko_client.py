import requests
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

class CoinGeckoClient:
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")
        self.base_url = "https://api.coingecko.com/api/v3"
        self.headers = {
            "x-cg-demo-api-key": self.api_key
        } if self.api_key else {}
    
    def get_coins_markets(self, vs_currency: str = "usd", limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch available crypto pairs from CoinGecko markets endpoint"""
        try:
            url = f"{self.base_url}/coins/markets"
            params = {
                "vs_currency": vs_currency,
                "order": "market_cap_desc",
                "per_page": limit,
                "page": 1,
                "sparkline": False,
                "price_change_percentage": "24h"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            markets_data = response.json()
            
            # Transform to our expected format
            pairs = []
            for coin in markets_data:
                pairs.append({
                    "symbol": f"{coin['symbol'].upper()}-{vs_currency.upper()}",
                    "base": coin['symbol'].upper(),
                    "quote": vs_currency.upper(),
                    "label": f"{coin['symbol'].upper()}/{vs_currency.upper()}",
                    "name": coin['name'],
                    "coin_id": coin['id'],
                    "status": "active",
                    "current_price": coin.get('current_price'),
                    "market_cap_rank": coin.get('market_cap_rank')
                })
            
            return pairs
            
        except requests.RequestException as e:
            print(f"Error fetching coins markets: {e}")
            return []
    
    def get_ohlc_data(self, coin_id: str, vs_currency: str = "usd", days: int = 30, timeframe: str = "1d") -> Optional[pd.DataFrame]:
        """Fetch OHLC data for a specific coin with proper timeframe support"""
        try:
            # For weekly and monthly timeframes, use market_chart endpoint for better data aggregation
            if timeframe in ["1w", "1m"] or days > 90:
                return self._get_ohlc_from_market_chart(coin_id, vs_currency, days, timeframe)
            
            # Use OHLC endpoint for shorter timeframes
            url = f"{self.base_url}/coins/{coin_id}/ohlc"
            params = {
                "vs_currency": vs_currency,
                "days": days
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            ohlc_data = response.json()
            
            if not ohlc_data:
                return None
            
            # Convert to pandas DataFrame
            df = pd.DataFrame(ohlc_data, columns=['timestamp', 'open', 'high', 'low', 'close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Convert to numeric types
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col])
            
            return df
            
        except requests.RequestException as e:
            print(f"Error fetching OHLC data for {coin_id}: {e}")
            return None
    
    def get_market_chart(self, coin_id: str, vs_currency: str = "usd", days: int = 30) -> Optional[Dict[str, Any]]:
        """Fetch market chart data including price, market cap, and volume"""
        try:
            url = f"{self.base_url}/coins/{coin_id}/market_chart"
            
            # Determine appropriate interval based on days
            if days <= 1:
                interval = "minutely"
            elif days <= 90:
                interval = "hourly"
            else:
                interval = "daily"
            
            params = {
                "vs_currency": vs_currency,
                "days": days,
                "interval": interval
            }
            
            print(f"Fetching market chart for {coin_id}: {days} days, {interval} interval")
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Debug logging
            if data:
                print(f"Market chart response for {coin_id}:")
                print(f"  - Prices: {len(data.get('prices', []))} points")
                print(f"  - Volumes: {len(data.get('total_volumes', []))} points")
                if data.get('prices'):
                    first_price = data['prices'][0]
                    last_price = data['prices'][-1]
                    print(f"  - Date range: {pd.to_datetime(first_price[0], unit='ms')} to {pd.to_datetime(last_price[0], unit='ms')}")
            
            return data
            
        except requests.RequestException as e:
            print(f"Error fetching market chart for {coin_id}: {e}")
            return None
    
    def get_coin_by_symbol(self, symbol: str) -> Optional[str]:
        """Get coin ID by symbol for API calls"""
        # Common mappings for major coins
        symbol_to_id = {
            "BTC": "bitcoin",
            "ETH": "ethereum", 
            "ADA": "cardano",
            "SOL": "solana",
            "XRP": "ripple",
            "DOT": "polkadot",
            "DOGE": "dogecoin",
            "AVAX": "avalanche-2",
            "LINK": "chainlink",
            "UNI": "uniswap",
            "LTC": "litecoin",
            "BCH": "bitcoin-cash",
            "ALGO": "algorand",
            "VET": "vechain",
            "FTM": "fantom",
            "MATIC": "matic-network"
        }
        
        return symbol_to_id.get(symbol.upper())
    
    def _get_ohlc_from_market_chart(self, coin_id: str, vs_currency: str = "usd", days: int = 30, timeframe: str = "1d") -> Optional[pd.DataFrame]:
        """Convert market chart data to OHLC format with proper timeframe aggregation"""
        try:
            # Adjust days based on timeframe for better data coverage
            if timeframe == "1w":
                days = min(days * 7, 730)  # Up to 2 years for weekly
            elif timeframe == "1m":
                days = min(days * 30, 1095)  # Up to 3 years for monthly
            
            # Get market chart data
            market_data = self.get_market_chart(coin_id, vs_currency, days)
            
            if not market_data or 'prices' not in market_data:
                return None
            
            # Convert price data to DataFrame
            prices = market_data['prices']
            df = pd.DataFrame(prices, columns=['timestamp', 'price'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            df['price'] = pd.to_numeric(df['price'])
            
            # Add volume data if available
            if 'total_volumes' in market_data:
                volumes = market_data['total_volumes']
                volume_df = pd.DataFrame(volumes, columns=['timestamp', 'volume'])
                volume_df['timestamp'] = pd.to_datetime(volume_df['timestamp'], unit='ms')
                volume_df.set_index('timestamp', inplace=True)
                volume_df['volume'] = pd.to_numeric(volume_df['volume'])
                df = df.join(volume_df, how='left')
            
            # Convert to OHLC based on timeframe
            if timeframe == "1h":
                freq = "1H"
            elif timeframe == "4h":
                freq = "4H"
            elif timeframe == "1d":
                freq = "1D"
            elif timeframe == "1w":
                freq = "1W"
            elif timeframe == "1m":
                freq = "1M"
            else:
                freq = "1D"  # Default to daily
            
            # Resample price data to create OHLC
            ohlc_data = df['price'].resample(freq).ohlc()
            
            # Add volume if available
            if 'volume' in df.columns:
                volume_data = df['volume'].resample(freq).sum()
                ohlc_data = ohlc_data.join(volume_data, how='left')
                # Fill missing volume with 0
                ohlc_data['volume'] = ohlc_data['volume'].fillna(0)
            else:
                # Add default volume column if not available
                ohlc_data['volume'] = 0
            
            # Remove any rows with NaN values in OHLC data but keep volume
            ohlc_data = ohlc_data.dropna(subset=['open', 'high', 'low', 'close'])
            
            # Debug logging
            print(f"Market chart conversion for {coin_id} ({timeframe}):")
            print(f"  - Input data points: {len(df)}")
            print(f"  - Output OHLC points: {len(ohlc_data)}")
            print(f"  - Date range: {ohlc_data.index.min()} to {ohlc_data.index.max()}")
            print(f"  - Sample data: {ohlc_data.head(2).to_dict()}")
            
            # Ensure we have reasonable amount of data
            if len(ohlc_data) < 5:
                print(f"Insufficient OHLC data points ({len(ohlc_data)}) for {coin_id}")
                return None
            
            return ohlc_data
            
        except Exception as e:
            print(f"Error converting market chart to OHLC for {coin_id}: {e}")
            return None

# Global client instance
coingecko_client = CoinGeckoClient()