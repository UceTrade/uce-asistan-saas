"""
MT5 Service Module - Handles all MetaTrader 5 connection and data operations
Refactored from start_server.py for better modularity
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from mt5_proxy import mt5, MT5_AVAILABLE


class MT5Service:
    """Service class for MetaTrader 5 operations"""
    
    def __init__(self):
        self.current_account: Optional[Dict] = None
        self.is_initialized = False
    
    def initialize(self) -> bool:
        """Initialize MT5 and get current account info"""
        if not mt5.initialize():
            if MT5_AVAILABLE:
                print("[ERROR] Failed to initialize MT5")
                print("Make sure MetaTrader 5 is installed and running")
                return False
            else:
                print("[INFO] Simulation Mode Initialized (Mock MT5)")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            if MT5_AVAILABLE:
                print("[ERROR] No active MT5 account found")
                print("Please login to an MT5 account first")
                mt5.shutdown()
                return False
            else:
                print("[INFO] No mock account info available, but continuing in simulation.")
                self.current_account = {'login': 0, 'server': 'Simulation', 'name': 'Sim User'}
                self.is_initialized = True
                return True
        
        self.current_account = {
            'login': account_info.login,
            'server': account_info.server,
            'name': account_info.name or f"Account {account_info.login}"
        }
        
        print(f"[OK] Connected to MT5 Account:")
        print(f"   Login: {self.current_account['login']}")
        print(f"   Server: {self.current_account['server']}")
        print(f"   Name: {self.current_account['name']}")
        
        self.is_initialized = True
        return True
    
    def shutdown(self):
        """Shutdown MT5 connection"""
        mt5.shutdown()
        self.is_initialized = False
        print("[CLOSE] MT5 connection closed")
    
    def get_account_data(self) -> Optional[Dict[str, Any]]:
        """Get current account data including positions and statistics"""
        account_info = mt5.account_info()
        if account_info is None:
            return None
        
        # Get positions
        positions = mt5.positions_get()
        positions_data = []
        if positions:
            for pos in positions:
                positions_data.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'price_open': pos.price_open,
                    'price_current': pos.price_current,
                    'profit': pos.profit,
                    'sl': pos.sl,
                    'tp': pos.tp
                })
        
        # Get today's deals for daily P/L
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        deals = mt5.history_deals_get(today, datetime.now())
        daily_profit = 0
        if deals:
            for deal in deals:
                if deal.entry == 1:  # Entry out (closed position)
                    daily_profit += deal.profit
        
        # Calculate drawdown
        balance = account_info.balance
        equity = account_info.equity
        
        # Get historical data for max drawdown
        history_deals = mt5.history_deals_get(datetime.now() - timedelta(days=30), datetime.now())
        max_balance = balance
        max_drawdown = 0
        
        if history_deals:
            running_balance = balance
            for deal in reversed(list(history_deals)):
                if deal.entry == 1:
                    running_balance -= deal.profit
                    max_balance = max(max_balance, running_balance)
            
            if max_balance > 0:
                max_drawdown = ((max_balance - equity) / max_balance) * 100
        
        current_drawdown = ((balance - equity) / balance * 100) if balance > 0 else 0
        
        return {
            'account_id': f"account_{account_info.login}",
            'login': account_info.login,
            'server': account_info.server,
            'name': self.current_account['name'] if self.current_account else f"Account {account_info.login}",
            'balance': account_info.balance,
            'equity': account_info.equity,
            'margin': account_info.margin,
            'margin_free': account_info.margin_free,
            'margin_level': account_info.margin_level if account_info.margin > 0 else 0,
            'profit': account_info.profit,
            'daily_profit': daily_profit,
            'current_drawdown': current_drawdown,
            'max_drawdown': max_drawdown,
            'positions': positions_data,
            'positions_count': len(positions_data),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_symbol_tick(self, symbol: str) -> Optional[Any]:
        """Get current tick for a symbol"""
        return mt5.symbol_info_tick(symbol)
    
    def get_symbol_info(self, symbol: str) -> Optional[Any]:
        """Get symbol information"""
        return mt5.symbol_info(symbol)
    
    def get_rates(self, symbol: str, timeframe: int = None, count: int = 100) -> Optional[Any]:
        """Get historical rates for a symbol"""
        if timeframe is None:
            timeframe = mt5.TIMEFRAME_H1
        return mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    
    def get_visible_symbols(self, limit: int = 30) -> List[str]:
        """Get list of visible symbols from Market Watch"""
        symbols = mt5.symbols_get()
        visible_symbols = []
        
        if symbols:
            for s in symbols:
                if s.visible:
                    visible_symbols.append(s.name)
        
        # If no visible symbols, return defaults
        if not visible_symbols:
            visible_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']
        
        return visible_symbols[:limit]
    
    @property
    def timeframes(self) -> Dict[str, int]:
        """Get MT5 timeframe constants mapping"""
        return {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1,
        }


# Singleton instance
_mt5_service: Optional[MT5Service] = None


def get_mt5_service() -> MT5Service:
    """Get or create the MT5 service singleton"""
    global _mt5_service
    if _mt5_service is None:
        _mt5_service = MT5Service()
    return _mt5_service
