"""
MetaTrader5 Proxy - Handles potential missing MetaTrader5 package
Allows the system to run in Simulation Mode even if MT5 is not installed.
"""

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except (ImportError, Exception):
    MT5_AVAILABLE = False
    
    # Create a mock object that doesn't crash on attribute access
    class MockMT5:
        def __getattr__(self, name):
            # Return dummy values for common constants
            if name.startswith('TIMEFRAME_'):
                return 0
            if name.startswith('ORDER_'):
                return 0
            if name.startswith('POSITION_'):
                return 0
            if name.startswith('SYMBOL_'):
                return 0
            
            # Dummy methods
            def dummy_func(*args, **kwargs):
                return None
            return dummy_func
            
        def initialize(self, *args, **kwargs):
            return True
            
        def account_info(self):
            class MockAccount:
                login = 123456
                server = "UceAsistan-Simulation"
                name = "Simulasyon Kullanicisi"
                balance = 10000.0
                equity = 10000.0
                margin = 0.0
                margin_free = 10000.0
                profit = 0.0
                currency = "USD"
            return MockAccount()
            
    mt5 = MockMT5()
    print("MT5_PROXY: MetaTrader5 package not available. Using Mock implementation.")

# Export both for use in other modules
__all__ = ['mt5', 'MT5_AVAILABLE']
