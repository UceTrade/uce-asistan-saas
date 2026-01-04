"""
Backtest Engine - Execute trading strategies on historical data
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
from price_action_lib import PriceActionLib


class BacktestEngine:
    """Execute and analyze trading strategies on historical data"""
    
    def __init__(self):
        self.results = None
        self.trades = []
        self.results = None
        self.trades = []
        self.equity_curve = []
        self.pa_lib = PriceActionLib()
    
    def get_historical_data(self, symbol: str, timeframe: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """
        Fetch historical data from MT5
        
        Args:
            symbol: Trading symbol (e.g., 'EURUSD')
            timeframe: Timeframe ('M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            DataFrame with OHLCV data
        """
        # Map timeframe strings to MT5 constants
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1
        }
        
        if timeframe not in timeframe_map:
            raise ValueError(f"Invalid timeframe: {timeframe}")
        
        # Initialize MT5 if not already
        if not mt5.initialize():
            raise Exception("Failed to initialize MT5")
        
        # Convert dates
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Get rates
        rates = mt5.copy_rates_range(symbol, timeframe_map[timeframe], start, end)
        
        if rates is None or len(rates) == 0:
            raise Exception(f"No data available for {symbol} {timeframe} from {start_date} to {end_date}")
        
        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df[['time', 'open', 'high', 'low', 'close', 'tick_volume']].rename(columns={'tick_volume': 'volume'})
    
    def run_backtest(self, strategy_code: str, symbol: str, timeframe: str, 
                     initial_balance: float, start_date: str, end_date: str,
                     lot_size: float = 0.01, spread_points: int = 2) -> Dict:
        """
        Run backtest with given strategy
        
        Args:
            strategy_code: Python code with strategy(data, position) function
            symbol: Trading symbol
            timeframe: Timeframe
            initial_balance: Starting balance
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            lot_size: Position size in lots
            spread_points: Spread in points (for cost calculation)
        
        Returns:
            Dictionary with backtest results
        """
        try:
            # Get historical data
            data = self.get_historical_data(symbol, timeframe, start_date, end_date)
            
            if data is None or len(data) < 20:
                return {
                    'success': False,
                    'error': 'Insufficient historical data'
                }
            
            # Pre-calculate Price Action indicators for performance
            # This turns O(N^2) per-bar calculation into O(N) one-time calculation
            try:
                data = self.pa_lib.analyze_all(data)
            except Exception as e:
                print(f"Warning: PA analysis failed: {e}")

            # Execute strategy code
            # Execute strategy code
            namespace = {
                'pd': pd, 
                'np': np,
                'pa': self.pa_lib  # Expose Price Action Library
            }
            exec(strategy_code, namespace)
            
            if 'strategy' not in namespace:
                return {
                    'success': False,
                    'error': 'Strategy function not found in code'
                }
            
            strategy_func = namespace['strategy']
            
            # Run backtest
            balance = initial_balance
            equity = initial_balance
            position = 0  # 0: no position, 1: long, -1: short
            entry_price = 0
            entry_price = 0
            entry_time = None
            sl_price = 0
            tp_price = 0
            
            self.trades = []
            self.equity_curve = []
            
            # Get point value (for forex, typically 0.0001 for most pairs)
            point_value = 0.0001 if 'JPY' not in symbol else 0.01
            
            for i in range(20, len(data)):  # Start from bar 20 to allow indicators
                current_data = data.iloc[:i+1].copy()
                current_bar = data.iloc[i]
                
                # Check SL/TP Hits (Simulate Intrabar roughly)
                if position != 0:
                    sl_hit = False
                    tp_hit = False
                    exit_price_sl_tp = 0
                    
                    if position == 1: # Long
                        if current_bar['low'] <= sl_price:
                            sl_hit = True
                            exit_price_sl_tp = sl_price
                        elif current_bar['high'] >= tp_price:
                            tp_hit = True
                            exit_price_sl_tp = tp_price
                    else: # Short
                        if current_bar['high'] >= sl_price:
                            sl_hit = True
                            exit_price_sl_tp = sl_price
                        elif current_bar['low'] <= tp_price:
                            tp_hit = True
                            exit_price_sl_tp = tp_price
                            
                    if sl_hit or tp_hit:
                        # Close Trade
                        if position == 1:
                            profit = (exit_price_sl_tp - entry_price) / point_value * lot_size * 10
                        else:
                            profit = (entry_price - exit_price_sl_tp) / point_value * lot_size * 10
                            
                        spread_cost = spread_points * lot_size * 10
                        net_profit = profit - spread_cost
                        balance += net_profit
                        
                        self.trades.append({
                            'entry_time': entry_time,
                            'exit_time': current_bar['time'],
                            'type': 'LONG' if position == 1 else 'SHORT',
                            'entry_price': entry_price,
                            'exit_price': exit_price_sl_tp,
                            'profit': net_profit,
                            'balance': balance,
                            'reason': 'TP' if tp_hit else 'SL'
                        })
                        
                        position = 0
                        equity = balance
                        # Continue to next bar (don't execute strategies on same bar we exited)
                        continue
                
                # Calculate current equity
                if position != 0:
                    current_price = current_bar['close']
                    if position == 1:  # Long
                        profit = (current_price - entry_price) / point_value * lot_size * 10
                    else:  # Short
                        profit = (entry_price - current_price) / point_value * lot_size * 10
                    
                    equity = balance + profit
                else:
                    equity = balance
                
                self.equity_curve.append({
                    'time': current_bar['time'],
                    'equity': equity,
                    'balance': balance
                })
                
                # Get strategy signal
                try:
                    signal = strategy_func(current_data, position)
                    
                    # CRITICAL FIX: Handle pandas Series returns (common AI mistake)
                    # If strategy returns a Series instead of a string, extract the last value
                    if hasattr(signal, 'iloc'):
                        signal = signal.iloc[-1] if len(signal) > 0 else 'HOLD'
                    elif isinstance(signal, (list, tuple)):
                        signal = signal[-1] if len(signal) > 0 else 'HOLD'
                    
                    # Convert to string and uppercase
                    signal = str(signal).upper().strip()
                    
                    # Validate signal
                    if signal not in ['BUY', 'SELL', 'HOLD']:
                        print(f"[WARNING] Invalid signal '{signal}' at bar {i}, treating as HOLD")
                        signal = 'HOLD'
                    
                    if signal in ['BUY', 'SELL']:
                         print(f"[DEBUG] Signal {signal} at bar {i}")
                         
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'Strategy execution error: {str(e)}\n\nHINT: Make sure your strategy function returns a STRING (\'BUY\', \'SELL\', or \'HOLD\'), not a pandas Series. Use .iloc[-1] to get the last value when checking conditions.'
                    }
                
                # Execute trades
                if signal == 'BUY' and position <= 0:
                    # Close short if exists
                    if position == -1:
                         # ... (Existing close logic) ...
                         pass # handled above/below, but we need to ensure we don't double count if we just opened.
                         # Actually the loop structure handles "Check existing" -> "Check Signal".
                         # If we close here, we update position.
                         
                         exit_price = current_bar['close']
                         profit = (entry_price - exit_price) / point_value * lot_size * 10
                         spread_cost = spread_points * lot_size * 10
                         net_profit = profit - spread_cost
                         balance += net_profit
                         self.trades.append({
                            'entry_time': entry_time,
                            'exit_time': current_bar['time'],
                            'type': 'SHORT',
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'profit': net_profit,
                            'balance': balance,
                            'reason': 'Signal'
                        })

                    # Open long
                    position = 1
                    entry_price = current_bar['close']
                    entry_time = current_bar['time']
                    
                    # AUTO SL/TP Logic - ICT Causation Style
                    # SL = Swing Low that CREATED the recent Swing High (causation low)
                    # This means: Find the highest swing high, then find the swing low
                    # that comes IMMEDIATELY before it in the swing sequence
                    # TP = 2:1 Reward
                    
                    sl_price = None
                    
                    if 'swing_high' in current_data.columns and 'swing_low' in current_data.columns:
                        # Get all swing points with their indices
                        swing_highs = current_data[current_data['swing_high'] == True]
                        swing_lows = current_data[current_data['swing_low'] == True]
                        
                        if len(swing_highs) > 0:
                            # Find the highest swing high (most significant)
                            highest_sh_idx = swing_highs['high'].idxmax()
                            highest_sh_value = swing_highs.loc[highest_sh_idx, 'high']
                            
                            # Find swing lows that come BEFORE this specific swing high
                            swing_lows_before = swing_lows[swing_lows.index < highest_sh_idx]
                            
                            if len(swing_lows_before) > 0:
                                # The LAST swing low before this high = causation low
                                causation_low_idx = swing_lows_before.index[-1]
                                causation_low = swing_lows_before.loc[causation_low_idx, 'low']
                                sl_price = causation_low - (5 * point_value)  # 5 pips buffer
                    
                    # Fallback if no valid causation found
                    if sl_price is None:
                        sl_price = current_data['low'].iloc[-30:].min()
                    
                    # Safety: If SL is too close or above entry
                    if entry_price - sl_price < 10 * point_value:
                        sl_price = entry_price - 50 * point_value  # Default 50 pips
                        
                    risk = entry_price - sl_price
                    tp_price = entry_price + (risk * 2.0)
                
                elif signal == 'SELL' and position >= 0:
                    # Close long if exists
                    if position == 1:
                         exit_price = current_bar['close']
                         profit = (exit_price - entry_price) / point_value * lot_size * 10
                         spread_cost = spread_points * lot_size * 10
                         net_profit = profit - spread_cost
                         balance += net_profit
                         self.trades.append({
                            'entry_time': entry_time,
                            'exit_time': current_bar['time'],
                            'type': 'LONG',
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'profit': net_profit,
                            'balance': balance,
                            'reason': 'Signal'
                        })

                    # Open short
                    position = -1
                    entry_price = current_bar['close']
                    entry_time = current_bar['time']
                    
                    # AUTO SL/TP Logic - ICT Causation Style
                    # SL = Swing High that CREATED the recent Swing Low (causation high)
                    # This means: Find the lowest swing low, then find the swing high
                    # that comes IMMEDIATELY before it in the swing sequence
                    # TP = 2:1 Reward
                    
                    sl_price = None
                    
                    if 'swing_low' in current_data.columns and 'swing_high' in current_data.columns:
                        # Get all swing points with their indices
                        swing_lows = current_data[current_data['swing_low'] == True]
                        swing_highs = current_data[current_data['swing_high'] == True]
                        
                        if len(swing_lows) > 0:
                            # Find the lowest swing low (most significant)
                            lowest_sl_idx = swing_lows['low'].idxmin()
                            lowest_sl_value = swing_lows.loc[lowest_sl_idx, 'low']
                            
                            # Find swing highs that come BEFORE this specific swing low
                            swing_highs_before = swing_highs[swing_highs.index < lowest_sl_idx]
                            
                            if len(swing_highs_before) > 0:
                                # The LAST swing high before this low = causation high
                                causation_high_idx = swing_highs_before.index[-1]
                                causation_high = swing_highs_before.loc[causation_high_idx, 'high']
                                sl_price = causation_high + (5 * point_value)  # 5 pips buffer
                    
                    # Fallback if no valid causation found
                    if sl_price is None:
                        sl_price = current_data['high'].iloc[-30:].max()
                    
                    # Safety check
                    if sl_price - entry_price < 10 * point_value:
                        sl_price = entry_price + 50 * point_value
                        
                    risk = sl_price - entry_price
                    tp_price = entry_price - (risk * 2.0)
            
            # Close any open position at the end
            if position != 0:
                exit_price = data.iloc[-1]['close']
                if position == 1:
                    profit = (exit_price - entry_price) / point_value * lot_size * 10
                else:
                    profit = (entry_price - exit_price) / point_value * lot_size * 10
                
                spread_cost = spread_points * lot_size * 10
                net_profit = profit - spread_cost
                balance += net_profit
                
                self.trades.append({
                    'entry_time': entry_time,
                    'exit_time': data.iloc[-1]['time'],
                    'type': 'LONG' if position == 1 else 'SHORT',
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'profit': net_profit,
                    'balance': balance
                })
            
            # Calculate metrics
            metrics = self.calculate_metrics(initial_balance, balance)
            
            # Sample price history for chart (max 500 points to keep payload small)
            price_history = []
            step = 1
            if len(data) > 500:
                step = len(data) // 500
                
            for i in range(0, len(data), step):
                row = data.iloc[i]
                price_history.append({
                    'time': row['time'],
                    'open': row['open'],
                    'high': row['high'],
                    'low': row['low'],
                    'close': row['close']
                })
                
            return {
                'success': True,
                'metrics': metrics,
                'trades': self.trades,
                'equity_curve': self.equity_curve,
                'price_history': price_history
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def calculate_metrics(self, initial_balance: float, final_balance: float) -> Dict:
        """Calculate performance metrics"""
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'total_loss': 0,
                'net_profit': 0,
                'profit_factor': 0,
                'max_drawdown': 0,
                'max_drawdown_pct': 0,
                'return_pct': 0
            }
        
        # Basic stats
        total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t['profit'] > 0]
        losing_trades = [t for t in self.trades if t['profit'] <= 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        # Profit/Loss
        total_profit = sum(t['profit'] for t in winning_trades)
        total_loss = abs(sum(t['profit'] for t in losing_trades))
        net_profit = final_balance - initial_balance
        
        profit_factor = (total_profit / total_loss) if total_loss > 0 else 0
        
        # Drawdown
        peak = initial_balance
        max_dd = 0
        
        for point in self.equity_curve:
            if point['equity'] > peak:
                peak = point['equity']
            
            dd = peak - point['equity']
            if dd > max_dd:
                max_dd = dd
        
        max_dd_pct = (max_dd / peak * 100) if peak > 0 else 0
        
        # Return
        return_pct = (net_profit / initial_balance * 100) if initial_balance > 0 else 0
        
        # Average win/loss
        avg_win = (total_profit / win_count) if win_count > 0 else 0
        avg_loss = (total_loss / loss_count) if loss_count > 0 else 0
        avg_profit = (net_profit / total_trades) if total_trades > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': win_count,
            'losing_trades': loss_count,
            'win_rate': round(win_rate, 2),
            'total_profit': round(total_profit, 2),
            'total_loss': round(total_loss, 2),
            'net_profit': round(net_profit, 2),
            'profit_factor': round(profit_factor, 2),
            'max_drawdown': round(max_dd, 2),
            'max_drawdown_pct': round(max_dd_pct, 2),
            'return_pct': round(return_pct, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'avg_profit': round(avg_profit, 2)
        }
