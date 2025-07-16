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
    
    def get_ohlc_data(self, coin_id: str, vs_currency: str = "usd", days: int = 30) -> Optional[pd.DataFrame]:
        """Fetch OHLC data for a specific coin"""
        try:
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
            params = {
                "vs_currency": vs_currency,
                "days": days,
                "interval": "daily" if days > 90 else "hourly"
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
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

# Global client instance
coingecko_client = CoinGeckoClient()