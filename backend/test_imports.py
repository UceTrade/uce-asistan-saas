"""
Test script to verify all backend modules can be imported
"""
import sys
import traceback
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    os.system('chcp 65001 > nul')

def test_import(module_name, description):
    """Test importing a module"""
    try:
        __import__(module_name)
        print(f"[OK] {description}")
        return True
    except Exception as e:
        print(f"[FAIL] {description}")
        print(f"       Error: {str(e)}")
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("AI Trading Coach - Backend Import Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Core dependencies
    print("Core Dependencies:")
    results.append(test_import("MetaTrader5", "MetaTrader5"))
    results.append(test_import("websockets", "WebSockets"))
    results.append(test_import("pandas", "Pandas"))
    results.append(test_import("numpy", "NumPy"))
    results.append(test_import("aiohttp", "AioHTTP"))
    print()
    
    # Backend modules
    print("Backend Modules:")
    results.append(test_import("start_server", "Main Server"))
    results.append(test_import("ai_strategy_parser", "AI Strategy Parser"))
    results.append(test_import("backtest_engine", "Backtest Engine"))
    results.append(test_import("journal_manager", "Journal Manager"))
    results.append(test_import("strategy_manager", "Strategy Manager"))
    results.append(test_import("live_trader", "Live Trader"))
    results.append(test_import("signal_confluence", "Signal Confluence"))
    results.append(test_import("conversation_manager", "Conversation Manager"))
    results.append(test_import("turkish_nlu", "Turkish NLU"))
    results.append(test_import("price_action_lib", "Price Action Library"))
    results.append(test_import("strategy_optimizer", "Strategy Optimizer"))
    results.append(test_import("strategy_templates", "Strategy Templates"))
    print()
    
    # Summary
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Test Summary: {passed}/{total} passed")
    
    if passed == total:
        print("SUCCESS: All imports successful!")
        return 0
    else:
        print(f"WARNING: {total - passed} imports failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
