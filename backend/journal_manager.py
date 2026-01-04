"""
Journal Manager - Handles trade history, user notes, and analysis data
"""
import json
import os
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

class JournalManager:
    """Manages trading journal data, syncing MT5 history with local notes"""
    
    def __init__(self, data_file='user_data/journal_notes.json'):
        self.data_file = data_file
        self.notes = {}
        self.ensure_data_dir()
        self.load_notes()
        
    def ensure_data_dir(self):
        """Ensure data directory exists"""
        directory = os.path.dirname(self.data_file)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
    def load_notes(self):
        """Load user notes from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.notes = json.load(f)
            except Exception as e:
                print(f"[ERROR] Failed to load journal notes: {e}")
                self.notes = {}
        else:
            self.notes = {}
            
    def save_notes(self):
        """Save user notes to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.notes, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save journal notes: {e}")
            return False

    def get_trade_history(self, days=30):
        """
        Fetch trade history from MT5 and merge with user notes
        """
        if not mt5.initialize():
            return {'error': 'MT5 not initialized'}
            
        from_date = datetime.now() - timedelta(days=days)
        to_date = datetime.now() + timedelta(days=1) # Include today
        
        # Get history deals
        deals = mt5.history_deals_get(from_date, to_date)
        
        if deals is None:
            return []
            
        trades = []
        
        # Process deals to reconstruct trades (Entry + Exit)
        # Note: This is a simplified reconstruction. In MT5, a "position" lifecycle 
        # is composed of an ENTRY deal and an EXIT deal.
        
        # We will focus on exit deals (Entry = 1) because they contain the profit info.
        # We then look for the corresponding entry deal if possible, or just use exit info.
        
        for deal in deals:
            # Entry 1 = DEAL_ENTRY_OUT (Exit/Close of a position)
            # Entry 2 = DEAL_ENTRY_INOUT (Reversal)
            if deal.entry == 1 or deal.entry == 2: 
                ticket = str(deal.ticket)
                position_id = str(deal.position_id)
                
                # Get saved note for this position
                # We use position_id as key because tickets change, but position_id links entry/exit
                note_data = self.notes.get(position_id, {})
                
                trades.append({
                    'ticket': ticket,
                    'position_id': position_id,
                    'symbol': deal.symbol,
                    'type': 'BUY' if deal.type == 0 else 'SELL', # 0=Buy, 1=Sell
                    'volume': deal.volume,
                    'price': deal.price,
                    'profit': deal.profit,
                    'commission': deal.commission,
                    'swap': deal.swap,
                    'time': datetime.fromtimestamp(deal.time).isoformat(),
                    # User annotations
                    'note': note_data.get('note', ''),
                    'tags': note_data.get('tags', []),
                    'emotion': note_data.get('emotion', 'neutral'),
                    'strategy': note_data.get('strategy', '')
                })
                
        # Sort by time descending (newest first)
        trades.sort(key=lambda x: x['time'], reverse=True)
        
        return trades

    def save_trade_note(self, position_id, data):
        """Save text note, emotion, and tags for a trade"""
        if not position_id:
            return False
            
        position_id = str(position_id)
        
        # Update or create note entry
        if position_id not in self.notes:
            self.notes[position_id] = {}
            
        # Update fields
        if 'note' in data:
            self.notes[position_id]['note'] = data['note']
        if 'tags' in data:
            self.notes[position_id]['tags'] = data['tags']
        if 'emotion' in data:
            self.notes[position_id]['emotion'] = data['emotion']
        if 'strategy' in data:
            self.notes[position_id]['strategy'] = data['strategy']
            
        return self.save_notes()

    def get_stats(self, days=30):
        """Calculate stats for the dashboard"""
        trades = self.get_trade_history(days)
        if isinstance(trades, dict) and 'error' in trades:
            return trades
            
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'net_profit': 0
            }
            
        df = pd.DataFrame(trades)
        
        total_trades = len(df)
        winning_trades = df[df['profit'] > 0]
        losing_trades = df[df['profit'] <= 0]
        
        win_count = len(winning_trades)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        gross_profit = winning_trades['profit'].sum()
        gross_loss = abs(losing_trades['profit'].sum())
        
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        net_profit = df['profit'].sum()
        
        # Best Pair
        best_pair = "N/A"
        if total_trades > 0:
            pair_stats = df.groupby('symbol')['profit'].sum()
            if not pair_stats.empty:
                best_pair = pair_stats.idxmax()
        
        return {
            'total_trades': total_trades,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'net_profit': round(net_profit, 2),
            'best_pair': best_pair,
            'avg_win': round(winning_trades['profit'].mean(), 2) if not winning_trades.empty else 0,
            'avg_loss': round(losing_trades['profit'].mean(), 2) if not losing_trades.empty else 0,
            'raw_data': trades # Useful for AI context
        }
