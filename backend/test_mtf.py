from mt5_proxy import mt5
import sys
sys.stdout.reconfigure(encoding='utf-8')

mt5.initialize()
from multi_timeframe import MultiTimeframeAnalyzer
a = MultiTimeframeAnalyzer()
r = a.analyze('EURUSD', 'intraday')
print("SUCCESS" if r and 'error' not in r else f"FAILED: {r.get('error', 'Unknown')}")
mt5.shutdown()
