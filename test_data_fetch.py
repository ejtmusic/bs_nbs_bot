import asyncio
import pandas as pd

# --- IMPORTS FOR THE NEWEST SDK VERSION ---
from pyinjective.core.network import Network
from pyinjective.async_client import AsyncClient

TARGET_SYMBOL = "BTC/USDT PERP"
TIMEFRAME = '15m'

async def main():
    print(f"Attempting to fetch {TIMEFRAME} candles for {TARGET_SYMBOL} using the new Chronos API...")

    try:
        network = Network.mainnet()
        client = AsyncClient(network)

        # --- STEP 1: Get Market ID ---
        response_dict = await client.fetch_derivative_markets()
        market_id = None
        for market in response_dict['markets']:
            if market['ticker'] == TARGET_SYMBOL:
                market_id = market['marketId']
                break
        
        if not market_id:
            print(f"❌ FAILED: Could not find market ID.")
            return
        print(f"✅ Found Market ID: {market_id}")

        # --- STEP 2: Fetch candles via SDK ---
        resolutions = {'1m': 60, '5m': 300, '15m': 900, '1h': 3600, '4h': 14400, '1d': 86400}
        
        # CORRECT METHOD NAME: fetch_derivative_candles
        candles_response = await client.fetch_derivative_candles(
            market_id=market_id,
            resolution=resolutions[TIMEFRAME],
            limit=25
        )
        candles_list = candles_response.candles
        
        # --- STEP 3: Format into DataFrame (already in chronological order) ---
        df = pd.DataFrame([
            {
                'timestamp': pd.to_datetime(int(candle.start_time), unit='s'),
                'open': float(candle.open),
                'high': float(candle.high),
                'low': float(candle.low),
                'close': float(candle.close),
                'volume': float(candle.volume)
            } for candle in candles_list
        ])

        print("\n✅ SUCCESS! Latest candle data:")
        print(df.tail())

    except Exception as e:
        print(f"\n🚨 An unexpected error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())