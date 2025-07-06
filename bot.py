# --- IMPORTS ---
import pandas as pd
import joblib
import os
import asyncio
from dotenv import load_dotenv
from pytz import timezone
from datetime import datetime, timedelta
import telegram
import ccxt
import asyncio
from ccxt.base.errors import OrderNotFound


# --- CONFIGURATION ---
MODEL_FILE = 'master_model.joblib'
PREDICTION_THRESHOLD = 0.45
FEATURE_COLUMNS = ['return_1', 'return_5', 'return_10', 'volume_change_1', 'volume_change_5', 'candle_range', 'volatility_10']
MARKET_SYMBOL = 'BTCUSDT'
TIMEFRAME = '15m'

# --- CCXT HYPERLIQUID SETUP ---
MARKET_SYMBOL_CCXT = 'BTC/USDC:USDC'
exchange = ccxt.hyperliquid({'enableRateLimit': True})

# --- PORTFOLIO & RISK MANAGEMENT ---
portfolio = {
    "balance": 100.0,
    "open_trades": [],
    "max_open_trades": 2,
    "risk_per_trade_percent": 0.02,
    "rr_ratio": 3.0,
    "fee_percent": 0.0005,
    "wins": 0,
    "losses": 0,
    "total_trades": 0,
    "start_time": datetime.utcnow()
}

# --- TELEGRAM BOT CLASS ---
class TelegramBot:
    def __init__(self):
        load_dotenv()
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.bot = telegram.Bot(token=self.token) if self.token and self.chat_id else None

    async def send_message(self, text):
        if self.bot:
            try:
                await self.bot.send_message(chat_id=self.chat_id, text=text, parse_mode='Markdown')
            except Exception as e:
                print(f"Error sending Telegram message: {e}")

# --- FEATURE CALCULATION ---
def calculate_features(df):
    df['return_1'] = df['close'].pct_change(1)
    df['return_5'] = df['close'].pct_change(5)
    df['return_10'] = df['close'].pct_change(10)
    df['volume_change_1'] = df['volume'].pct_change(1)
    df['volume_change_5'] = df['volume'].pct_change(5)
    df['candle_range'] = (df['high'] - df['low']) / df['close']
    df['volatility_10'] = df['return_1'].rolling(window=10).std()
    df.dropna(inplace=True)
    return df


async def get_hyperliquid_candles(symbol, timeframe, limit=25):
    """
    Fetches the latest k-line/candle data from Hyperliquid via CCXT.
    """
    try:
        ohlcv = await asyncio.to_thread(exchange.fetch_ohlcv, MARKET_SYMBOL_CCXT, timeframe, None, limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"Hyperliquid Fetch Error: {e}")
        return None

# --- TRADE SIMULATION & P&L ---
async def check_and_close_trades(current_price, telegram_bot):
    global portfolio
    trades_to_remove = []
    for trade in portfolio["open_trades"]:
        pnl, closed, status = 0, False, ""
        if trade['side'] == 'buy':
            if current_price >= trade['tp_price']:
                pnl, closed, status, portfolio['wins'] = (trade['tp_price'] - trade['entry_price']) * trade['size'], True, "✅ TP HIT", portfolio['wins'] + 1
            elif current_price <= trade['sl_price']:
                pnl, closed, status, portfolio['losses'] = (trade['sl_price'] - trade['entry_price']) * trade['size'], True, "❌ SL HIT", portfolio['losses'] + 1
        elif trade['side'] == 'sell':
            if current_price <= trade['tp_price']:
                pnl, closed, status, portfolio['wins'] = (trade['entry_price'] - trade['tp_price']) * trade['size'], True, "✅ TP HIT", portfolio['wins'] + 1
            elif current_price >= trade['sl_price']:
                pnl, closed, status, portfolio['losses'] = (trade['entry_price'] - trade['sl_price']) * trade['size'], True, "❌ SL HIT", portfolio['losses'] + 1
        
        if closed:
            # Close position on Hyperliquid (market order to reverse side)
            close_side = 'sell' if trade['side'] == 'buy' else 'buy'
            try:
                await asyncio.to_thread(exchange.create_order, MARKET_SYMBOL_CCXT, 'market', close_side, trade['size'])
            except OrderNotFound:
                print(f"Order {trade['order_id']} already closed.")
            except Exception as e:
                print(f"Error closing order: {e}")

            fees = (trade['entry_price'] * trade['size'] + current_price * trade['size']) * portfolio['fee_percent']
            net_pnl = pnl - fees
            portfolio['balance'] += net_pnl
            trades_to_remove.append(trade)
            message = f"*{status}*\n\nSide: {trade['side'].upper()}\nNet P&L: `${net_pnl:.2f}` (incl. `${fees:.2f}` fees)\n*New Balance: `${portfolio['balance']:.2f}`*"
            await telegram_bot.send_message(message)
    
    portfolio['open_trades'] = [t for t in portfolio['open_trades'] if t not in trades_to_remove]

async def open_trade(side, entry_price, telegram_bot):
    global portfolio
    risk_amount_usd = portfolio['balance'] * portfolio['risk_per_trade_percent']
    
    if side == 'buy':
        sl_price = entry_price * (1 - portfolio['risk_per_trade_percent'])
        tp_price = entry_price * (1 + (portfolio['risk_per_trade_percent'] * portfolio['rr_ratio']))
    else:  # 'sell'
        sl_price = entry_price * (1 + portfolio['risk_per_trade_percent'])
        tp_price = entry_price * (1 - (portfolio['risk_per_trade_percent'] * portfolio['rr_ratio']))
    
    position_value = risk_amount_usd / portfolio['risk_per_trade_percent']
    size_coin = position_value / entry_price

    # Place market order on Hyperliquid
    try:
        order = await asyncio.to_thread(exchange.create_order, MARKET_SYMBOL_CCXT, 'market', side, size_coin)
        order_id = order.get('id')
    except Exception as e:
        print(f"Order placement error: {e}")
        return

    portfolio['open_trades'].append({
        'side': side,
        'entry_price': entry_price,
        'sl_price': sl_price,
        'tp_price': tp_price,
        'size': size_coin,
        'order_id': order_id
    })
    portfolio['total_trades'] += 1
    message = f"🔔 *NEW TRADE OPENED*\n\nSide: {side.upper()}\nEntry: `${entry_price:,.2f}`\nTP: `${tp_price:,.2f}`\nSL: `${sl_price:,.2f}`"
    await telegram_bot.send_message(message)

# --- REPORTING FUNCTION ---
async def send_report(telegram_bot):
    global portfolio
    uptime = datetime.utcnow() - portfolio['start_time']
    win_rate = (portfolio['wins'] / portfolio['total_trades'] * 100) if portfolio['total_trades'] > 0 else 0
    pnl = portfolio['balance'] - 100.0
    
    message = (
        f"📊 *Periodic Report*\n\n"
        f"Bot Uptime: {str(uptime).split('.')[0]}\n"
        f"----------------------\n"
        f"Current Balance: `${portfolio['balance']:.2f}`\n"
        f"Total P&L: `${pnl:.2f}`\n"
        f"----------------------\n"
        f"Total Trades: {portfolio['total_trades']}\n"
        f"Wins: {portfolio['wins']}\n"
        f"Losses: {portfolio['losses']}\n"
        f"Win Rate: {win_rate:.2f}%\n"
        f"Open Trades: {len(portfolio['open_trades'])}"
    )
    await telegram_bot.send_message(message)

# --- MAIN BOT LOOP ---
async def main():
    print("Bot starting up in LIVE MAINNET PAPER TRADING MODE using ccxt Hyperliquid integration...")
    model = joblib.load(MODEL_FILE)
    telegram_bot = TelegramBot()
    await telegram_bot.send_message("🤖 *Bot is now online (Hyperliquid Paper‑Trading via ccxt).*")
    
    last_report_time = datetime.utcnow()

    while True:
        try:
            ny_time = pd.to_datetime('now').tz_localize('UTC').tz_convert('America/New_York')
            print(f"\n--- Cycle Start: {ny_time.strftime('%Y-%m-%d %H:%M:%S')} (NY Time) ---")
            
            candles_df = await get_hyperliquid_candles(symbol=MARKET_SYMBOL_CCXT, timeframe=TIMEFRAME)
            if candles_df is None or candles_df.empty:
                print("Could not fetch data, sleeping for 60 seconds...")
                await asyncio.sleep(60)
                continue

            current_price = candles_df.iloc[-1]['close']
            await check_and_close_trades(current_price, telegram_bot)

            if len(portfolio['open_trades']) < portfolio['max_open_trades']:
                features_df = calculate_features(candles_df.copy())
                if not features_df.empty:
                    latest_features = features_df.iloc[-1:][FEATURE_COLUMNS]
                    
                    buy_prob = model.predict_proba(latest_features)[0][1]
                    if buy_prob >= PREDICTION_THRESHOLD:
                        await open_trade('buy', current_price, telegram_bot)
                    else:
                        sell_features = latest_features.copy()
                        directional_features = ['return_1', 'return_5', 'return_10']
                        for col in directional_features:
                            sell_features[col] = sell_features[col] * -1
                        sell_prob = model.predict_proba(sell_features)[0][1]
                        if sell_prob >= PREDICTION_THRESHOLD:
                            await open_trade('sell', current_price, telegram_bot)

            if datetime.utcnow() - last_report_time >= timedelta(hours=12):
                await send_report(telegram_bot)
                last_report_time = datetime.utcnow()

            print(f"Current Price (BTC): ${current_price:,.2f}")
            print(f"Current Balance: ${portfolio['balance']:.2f}, Open Trades: {len(portfolio['open_trades'])}")
            print("Waiting 60 seconds...")
            await asyncio.sleep(60)

        except Exception as e:
            print(f"An error occurred in the main loop: {e}")
            await telegram_bot.send_message(f"🚨 *CRITICAL ERROR*: Bot loop failed with error: {e}")
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())