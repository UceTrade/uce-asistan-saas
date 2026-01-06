from mt5_proxy import mt5
import pandas as pd

def check_positions():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    positions = mt5.positions_get()
    if positions is None:
        print("No positions or error")
    elif len(positions) == 0:
        print("No open positions")
    else:
        print(f"Open Positions: {len(positions)}")
        for pos in positions:
            print(f"Ticket: {pos.ticket} | {pos.symbol} {pos.type} (0=Buy,1=Sell) | Vol: {pos.volume} | Open: {pos.price_open} | SL: {pos.sl} | TP: {pos.tp}")

    mt5.shutdown()

if __name__ == "__main__":
    check_positions()
