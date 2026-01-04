"""
Live Trader - Execute Generated Strategies in Real-Time
"""
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import time
import threading
import traceback
from datetime import datetime
from datetime import datetime
from price_action_lib import PriceActionLib
from telegram_bot import telegram_notifier
import asyncio

class LiveTrader:
    def __init__(self):
        self.active = False
        self.strategy_code = None
        self.symbol = None
        self.timeframe = None
        self.rr_ratio = 2.0
        self.lot_size = 0.01
        self.thread = None
        self.logs = []
        self.pa_lib = PriceActionLib()
        
    def log(self, message):
        """Add log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.logs.append(log_entry)
        if len(self.logs) > 100:
            self.logs.pop(0)
            
    def start(self, strategy_code, symbol, timeframe_str, rr_ratio, lot_size):
        """Start auto-trading strategy"""
        if self.active:
            return False, "Strategy already running"
            
        self.strategy_code = strategy_code
        self.symbol = symbol
        self.timeframe_str = timeframe_str
        self.rr_ratio = float(rr_ratio)
        self.lot_size = float(lot_size)
        
        # Map timeframe string to MT5 constant
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1, 'M5': mt5.TIMEFRAME_M5, 'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30, 'H1': mt5.TIMEFRAME_H1, 'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1
        }
        
        self.timeframe = timeframe_map.get(timeframe_str)
        if not self.timeframe:
            return False, "Invalid timeframe"
            
        self.active = True
        self.thread = threading.Thread(target=self._run_loop)
        self.thread.daemon = True
        self.thread.start()
        
        self.log(f"Started strategy on {symbol} {timeframe_str}")
        return True, "Strategy started"
        
    def stop(self):
        """Stop auto-trading"""
        if not self.active:
            return False, "No strategy running"
            
        self.active = False
        if self.thread:
            self.thread.join(timeout=2.0)
            
        self.log("Strategy stopped")
        return True, "Strategy stopped"
        
    def _run_loop(self):
        """Main execution loop"""
        last_candle_time = 0
        
        while self.active:
            try:
                # 1. Check for connection
                if not mt5.initialize():
                    self.log("MT5 Connection failed, retrying...")
                    time.sleep(5)
                    continue

                # 2. Get latest candle time to check for new bar
                # We only trade on bar close
                rates = mt5.copy_rates_from(self.symbol, self.timeframe, datetime.now(), 1)
                if rates is None or len(rates) == 0:
                    time.sleep(1)
                    continue
                    
                current_candle_time = rates[0]['time']
                
                # Check if we have processed this bar already
                if current_candle_time <= last_candle_time:
                    time.sleep(1)
                    continue
                    
                # NEW BAR DETECTED
                last_candle_time = current_candle_time
                self.log(f"New bar detected: {datetime.fromtimestamp(current_candle_time)}")
                
                # 3. Get History for Analysis (last 200 bars)
                history = mt5.copy_rates_from_pos(self.symbol, self.timeframe, 0, 200)
                if history is None:
                    continue
                    
                df = pd.DataFrame(history)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df = df[['time', 'open', 'high', 'low', 'close', 'tick_volume']].rename(columns={'tick_volume': 'volume'})
                
                # 4. Check Open Positions
                positions = mt5.positions_get(symbol=self.symbol)
                position_state = 0
                if positions and len(positions) > 0:
                    # Determine direction of existing position
                    # 0=Buy, 1=Sell in MT5
                    if positions[0].type == 0: 
                        position_state = 1 # Long
                    elif positions[0].type == 1:
                        position_state = -1 # Short
                        
                # 5. Execute Strategy
                namespace = {
                    'pd': pd, 
                    'np': np,
                    'pa': self.pa_lib
                }
                
                # Inject logic to prevent future peeking? No need for live code.
                exec(self.strategy_code, namespace)
                
                signal = 'HOLD'
                if 'strategy' in namespace:
                    signal = namespace['strategy'](df, position_state)
                    
                self.log(f"Signal: {signal}")
                
                # 6. Execute Signal
                if signal == 'BUY' and position_state == 0:
                    self._execute_trade(mt5.ORDER_TYPE_BUY, df)
                elif signal == 'SELL' and position_state == 0:
                    self._execute_trade(mt5.ORDER_TYPE_SELL, df)
                elif signal == 'SELL' and position_state == 1:
                    # Close Long
                    self._close_position(positions[0])
                elif signal == 'BUY' and position_state == -1:
                    # Close Short
                    self._close_position(positions[0])
                    
            except Exception as e:
                self.log(f"Error in loop: {str(e)}")
                traceback.print_exc()
                
            time.sleep(1)
            
    def _execute_trade(self, order_type, df):
        """Execute trade with auto SL/TP"""
        # Calculate SL based on PA
        # Use simple swing detection from last 20 candles
        last_20 = df.tail(20)
        current_price = mt5.symbol_info_tick(self.symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(self.symbol).bid
        
        sl_price = 0.0
        tp_price = 0.0
        
        # SL Calculation Logic
        if order_type == mt5.ORDER_TYPE_BUY:
            # SL = Lowest Low of last 10 bars
            sl_price = last_20['low'].min()
            # Ensure a minimum distance (e.g. 5 pips)
            point = mt5.symbol_info(self.symbol).point
            min_dist = 50 * point # 5 pips
            if (current_price - sl_price) < min_dist:
                sl_price = current_price - min_dist
                
            # TP = Entry + (Entry - SL) * RR
            risk = current_price - sl_price
            tp_price = current_price + (risk * self.rr_ratio)
            
        else: # SELL
            # SL = Highest High
            sl_price = last_20['high'].max()
            point = mt5.symbol_info(self.symbol).point
            min_dist = 50 * point
            if (sl_price - current_price) < min_dist:
                sl_price = current_price + min_dist
                
            # TP
            risk = sl_price - current_price
            tp_price = current_price - (risk * self.rr_ratio)
            
        # Get symbol info and determine filling mode
        symbol_info = mt5.symbol_info(self.symbol)
        filling_mode = mt5.ORDER_FILLING_IOC  # Default
        
        if symbol_info is not None:
            # Check supported filling modes
            if symbol_info.filling_mode & mt5.SYMBOL_FILLING_FOK:
                filling_mode = mt5.ORDER_FILLING_FOK
            elif symbol_info.filling_mode & mt5.SYMBOL_FILLING_IOC:
                filling_mode = mt5.ORDER_FILLING_IOC
            else:
                filling_mode = mt5.ORDER_FILLING_RETURN
        
        # Send Order
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot_size,
            "type": order_type,
            "price": current_price,
            "sl": float(sl_price),
            "tp": float(tp_price),
            "deviation": 20,
            "magic": 234000,
            "comment": "AI AutoTrade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log(f"Order failed: {result.comment}")
        else:
            self.log(f"Order executed! Ticket: {result.order}")
            
            # NOTIFY TELEGRAM
            try:
                # Run async task in thread
                async def send_notify():
                    await telegram_notifier.notify_trade_opened(
                        symbol=self.symbol,
                        direction='BUY' if order_type == mt5.ORDER_TYPE_BUY else 'SELL',
                        lot_size=self.lot_size,
                        entry_price=float(current_price),
                        sl=float(sl_price),
                        tp=float(tp_price)
                    )
                
                # New loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_notify())
                loop.close()
            except Exception as e:
                print(f"[Telegram Error] {e}")
            
    def _close_position(self, position):
        """Close existing position"""
        tick = mt5.symbol_info_tick(position.symbol)
        price = tick.bid if position.type == 0 else tick.ask
        type_close = mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY
        
        # Get symbol info and determine filling mode
        symbol_info = mt5.symbol_info(position.symbol)
        filling_mode = mt5.ORDER_FILLING_IOC  # Default
        
        if symbol_info is not None:
            if symbol_info.filling_mode & mt5.SYMBOL_FILLING_FOK:
                filling_mode = mt5.ORDER_FILLING_FOK
            elif symbol_info.filling_mode & mt5.SYMBOL_FILLING_IOC:
                filling_mode = mt5.ORDER_FILLING_IOC
            else:
                filling_mode = mt5.ORDER_FILLING_RETURN
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": type_close,
            "position": position.ticket,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "AI Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": filling_mode,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log(f"Close failed: {result.comment}")
        else:
            self.log(f"Position closed: {position.ticket}")
            
            # NOTIFY TELEGRAM
            try:
                async def send_close_notify():
                    await telegram_notifier.notify_trade_closed(
                        symbol=position.symbol,
                        direction='BUY' if position.type == 0 else 'SELL',
                        profit=position.profit,
                        duration="Auto"
                    )
                    
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_close_notify())
                loop.close()
            except Exception as e:
                print(f"[Telegram Error] {e}")
            
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(telegram_notifier.notify_trade_closed(
                    symbol=position.symbol,
                    direction='BUY' if position.type == 0 else 'SELL',
                    profit=position.profit, # This might be initial profit, ideally we get deal info
                    duration="Auto-Close"
                ))
                loop.close()
            except Exception as e:
                print(f"[Telegram Error] {e}")
