from mt5_proxy import mt5
import sys

def open_trade():
    print("Connecting to MT5...")
    if not mt5.initialize():
        print("MT5 initialize() failed")
        mt5.shutdown()
        return

    symbol = "EURUSD"
    lot = 0.1
    
    # Check symbol
    info = mt5.symbol_info(symbol)
    if not info:
        print(f"Symbol {symbol} not found")
        return
        
    if not info.visible:
        print(f"Symbol {symbol} is not visible, trying to select...")
        if not mt5.symbol_select(symbol, True):
             print(f"symbol_select({symbol}) failed")
             return

    point = info.point
    price = mt5.symbol_info_tick(symbol).ask
    deviation = 20
    
    # Determine filling mode
    filling_mode = mt5.ORDER_FILLING_FOK
    
    # Check what the symbol supports
    # 1=FOK, 2=IOC
    if info.filling_mode == 1:
        filling_mode = mt5.ORDER_FILLING_FOK
    elif info.filling_mode == 2:
        filling_mode = mt5.ORDER_FILLING_IOC
    elif info.filling_mode == 3: # Both
        filling_mode = mt5.ORDER_FILLING_FOK
    
    # For some brokers, we might need ORDER_FILLING_RETURN or 0 if nothing works, 
    # but let's try FOK as IOC failed.
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": price,
        "sl": 0.0,
        "tp": 0.0,
        "deviation": deviation,
        "magic": 999888,
        "comment": "UceAsistan Manual",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": filling_mode, 
    }

    print(f"Sending BUY {lot} {symbol} at {price}...")
    result = mt5.order_send(request)
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order failed: {result.comment} (Retcode: {result.retcode})")
        if result.retcode == 10009: # TRADE_RETCODE_DONE
            print("Wait, it says DONE but logic fell here? Double check.")
    else:
        print(f"SUCCESS! Order executed. Ticket: {result.order}")
        
    mt5.shutdown()

if __name__ == "__main__":
    open_trade()
