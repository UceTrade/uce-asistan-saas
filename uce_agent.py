import sys
import os
import json
import asyncio
import websockets
import MetaTrader5 as mt5
import colorama
from colorama import Fore, Style

colorama.init()

VERSION = "1.0.0"

class UceAsistanAgent:
    def __init__(self, port=8001):
        self.port = port
        self.connected_clients = set()
        
    def print_banner(self):
        print(f"{Fore.MAGENTA}{Style.BRIGHT}")
        print("   __  __              _     _     _              ")
        print("  |  ||  |            / \   / \   / \             ")
        print("  |  ||  |  ____ ___ / _ \ / _ \ / _ \   ___ _ __ ")
        print("  |  ||  | / ___/ _ \ /_\ / /_\ / /_\ \ / __| '__|")
        print("  |  ||  || (__|  __/  _  |  _  |  _  | \__ \ |   ")
        print("  \______/ \___|\___|_| |_|_| |_|_| |_|_|___/_|   ")
        print(f"{Style.RESET_ALL}")
        print(f"{Fore.CYAN}UceAsistan Client Bridge - v{VERSION}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Local Server: ws://localhost:{self.port}{Style.RESET_ALL}")
        print("-" * 50)

    async def handle_client(self, websocket, path):
        print(f"{Fore.GREEN}[+] Yeni bağlantı sağlandı: {websocket.remote_address}{Style.RESET_ALL}")
        self.connected_clients.add(websocket)
        try:
            async for message in websocket:
                data = json.loads(message)
                action = data.get('action')
                
                # Forward to MT5 or handle local logic
                response = await self.process_mt5_action(data)
                await websocket.send(json.dumps(response))
                
        except websockets.exceptions.ConnectionClosed:
            print(f"{Fore.RED}[-] Bağlantı koptu: {websocket.remote_address}{Style.RESET_ALL}")
        finally:
            self.connected_clients.remove(websocket)

    async def process_mt5_action(self, data):
        action = data.get('action')
        
        # Ensure MT5 is active
        if not mt5.initialize():
            return {"error": "MT5 terminaline bağlanılamadı. Lütfen terminalin açık olduğunu kontrol edin."}
            
        try:
            if action == 'get_account_info':
                return await self._get_account_info()
            elif action == 'get_market_analysis':
                symbol = data.get('symbol', 'EURUSD')
                return await self._get_market_analysis(symbol)
            elif action == 'run_global_scan':
                symbols = data.get('symbols', [])
                return await self._run_global_scan(symbols)
            elif action == 'get_journal_data':
                return await self._get_journal_data()
            else:
                return {"error": f"Bilinmeyen komut: {action}"}
        except Exception as e:
            print(f"{Fore.RED}[!] İşlem Hatası: {str(e)}{Style.RESET_ALL}")
            return {"error": str(e)}

    async def _get_account_info(self):
        info = mt5.account_info()
        if info:
            return {
                "type": "account_info",
                "login": info.login,
                "name": info.name,
                "server": info.server,
                "balance": info.balance,
                "equity": info.equity,
                "margin": info.margin,
                "margin_free": info.margin_free,
                "currency": info.currency
            }
        return {"error": "Hesap bilgisi alınamadı"}

    async def _get_market_analysis(self, symbol):
        # We can reuse the logic from the main server
        # For professional SaaS, we will wrap this into a library call
        print(f"{Fore.YELLOW}[i] Analiz yapılıyor: {symbol}{Style.RESET_ALL}")
        # (Internal logic will be imported here)
        return {"type": "get_market_analysis_response", "symbol": symbol, "data": {"status": "success"}}

    async def _run_global_scan(self, symbols):
        # Batch analysis logic
        return {"type": "run_global_scan_response", "results": []}

    async def _get_journal_data(self):
        return {"type": "journal_data", "trades": []}

    async def start(self):
        self.print_banner()
        
        if not mt5.initialize():
            print(f"{Fore.RED}[!] HATA: MetaTrader 5 terminali bulunamadı!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[i] Lütfen MT5'in yüklü ve açık olduğundan emin olun.{Style.RESET_ALL}")
            return

        print(f"{Fore.GREEN}[✓] MetaTrader 5 Bağlantısı Aktif.{Style.RESET_ALL}")
        
        async with websockets.serve(self.handle_client, "localhost", self.port):
            print(f"{Fore.BLUE}[i] UceAsistan Cloud bağlantısı bekleniyor...{Style.RESET_ALL}")
            await asyncio.Future()  # run forever

if __name__ == "__main__":
    agent = UceAsistanAgent()
    try:
        asyncio.run(agent.start())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[!] Kapatılıyor...{Style.RESET_ALL}")
        mt5.shutdown()
        sys.exit(0)
