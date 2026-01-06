"""
UceAsistan WebSocket Server - Modular Architecture
This is the new entry point that uses the refactored service modules

Migration from monolithic start_server.py to modular architecture:
- MT5 operations -> services/mt5_service.py
- Market analysis -> services/market_service.py  
- Message handlers -> core/handlers.py
- Server logic -> this file (core/server.py)
"""
import asyncio
import json
import websockets
from datetime import datetime
from typing import Set

# Import services
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import get_mt5_service, get_market_service
from config import settings, validate_settings

# Import existing modules (will be gradually refactored)
from ai_strategy_parser import AIStrategyParser
from backtest_engine import BacktestEngine
from journal_manager import JournalManager
from journal_analytics import JournalAnalytics
from strategy_manager import StrategyManager
from signal_confluence import SignalConfluenceFinder
from multi_timeframe import MultiTimeframeAnalyzer
from drawdown_planner import DrawdownRecoveryPlanner
from telegram_bot import telegram_notifier
from live_trader import LiveTrader
from yahoo_finance_provider import yahoo_provider


class UceAsistanServer:
    """
    Modular WebSocket server for UceAsistan Trading Platform
    
    This replaces the monolithic MT5AutoConnectServer with a cleaner architecture:
    - Uses service classes for MT5 and market operations
    - Modular message handling
    - Clean separation of concerns
    """
    
    def __init__(self, host: str = 'localhost', port: int = 8766):
        self.host = host
        self.port = port
        self.connected_clients: Set = set()
        self.update_interval = 1.0
        
        # Initialize services
        self.mt5_service = get_mt5_service()
        self.market_service = get_market_service()
        
        # Legacy modules (will be refactored to services later)
        self.strategy_parser = AIStrategyParser()
        self.backtest_engine = BacktestEngine()
        self.journal_manager = JournalManager()
        self.journal_analytics = JournalAnalytics(self.journal_manager)
        self.strategy_manager = StrategyManager()
        self.confluence_finder = SignalConfluenceFinder()
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.recovery_planner = DrawdownRecoveryPlanner()
        self.live_trader = LiveTrader()
        
        # Telegram settings
        self.telegram = telegram_notifier
        self.last_risk_level = 'safe'
        self.telegram_settings = {'max_drawdown': 10.0, 'daily_limit': 500.0}
    
    def initialize(self) -> bool:
        """Initialize the server and MT5 connection"""
        return self.mt5_service.initialize()
    
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.connected_clients.add(websocket)
        print(f"[OK] Client connected. Total clients: {len(self.connected_clients)}")
        
        # Send initial account info
        if self.mt5_service.current_account:
            await websocket.send(json.dumps({
                'type': 'account_info',
                'data': self.mt5_service.current_account
            }))
    
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.connected_clients.discard(websocket)
        print(f"[DISCONNECT] Client disconnected. Total clients: {len(self.connected_clients)}")
    
    async def handle_message(self, websocket, message: str):
        """Route incoming messages to appropriate handlers"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            # Account handlers
            if action == 'get_account_data':
                response = await self._handle_get_account_data(data)
            elif action == 'get_portfolio':
                response = await self._handle_get_portfolio(data)
            
            # Market handlers
            elif action == 'get_market_analysis':
                response = await self._handle_get_market_analysis(data)
            elif action == 'run_global_scan':
                response = await self._handle_run_global_scan(data)
            elif action == 'get_mt5_symbols':
                response = await self._handle_get_mt5_symbols(data)
            elif action == 'get_yahoo_quote':
                response = await self._handle_get_yahoo_quote(data)
            elif action == 'get_yahoo_all':
                response = await self._handle_get_yahoo_all(data)
            
            # Strategy handlers
            elif action == 'parse_strategy':
                response = await self._handle_parse_strategy(data)
            elif action == 'run_backtest':
                response = await self._handle_run_backtest(data)
            elif action == 'save_strategy':
                response = await self._handle_save_strategy(data)
            elif action in ('get_strategies', 'list_strategies'):
                response = await self._handle_get_strategies(data)
            elif action == 'delete_strategy':
                response = await self._handle_delete_strategy(data)
            elif action == 'evolve_strategy':
                response = await self._handle_evolve_strategy(data)
            
            # Template handlers
            elif action == 'get_templates':
                response = await self._handle_get_templates(data)
            elif action == 'load_template':
                response = await self._handle_load_template(data)
            elif action == 'save_user_template':
                response = await self._handle_save_user_template(data)
            elif action == 'get_user_templates':
                response = await self._handle_get_user_templates(data)
            elif action == 'delete_user_template':
                response = await self._handle_delete_user_template(data)
            
            # Journal handlers
            elif action == 'get_journal_data':
                response = await self._handle_get_journal_data(data)
            elif action == 'get_journal_analytics':
                response = await self._handle_get_journal_analytics(data)
            elif action == 'save_trade_note':
                response = await self._handle_save_trade_note(data)
            
            # Advanced analysis handlers
            elif action == 'mtf_analysis':
                response = await self._handle_mtf_analysis(data)
            elif action == 'get_recovery_plan':
                response = await self._handle_get_recovery_plan(data)
            
            # Config handlers
            elif action == 'set_telegram_settings':
                response = await self._handle_set_telegram_settings(data)
            
            # Live trading handlers
            elif action == 'start_live_trader':
                response = await self._handle_start_live_trader(data)
            elif action == 'stop_live_trader':
                response = await self._handle_stop_live_trader(data)
            elif action == 'get_live_trader_status':
                response = await self._handle_get_live_trader_status(data)
            elif action == 'execute_trade':
                response = await self._handle_execute_trade(data)
            
            else:
                response = {'type': 'error', 'message': f'Unknown action: {action}'}
            
            await websocket.send(json.dumps(response))
            
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            print(f"[ERROR] Message handling failed: {e}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    # ========== Account Handlers ==========
    
    async def _handle_get_account_data(self, data: dict) -> dict:
        account_data = self.mt5_service.get_account_data()
        return {'type': 'account_data', 'data': account_data}
    
    async def _handle_get_portfolio(self, data: dict) -> dict:
        account_data = self.mt5_service.get_account_data()
        return {
            'type': 'portfolio_data',
            'data': {
                'total_balance': account_data['balance'] if account_data else 0,
                'total_equity': account_data['equity'] if account_data else 0,
                'total_profit': account_data['profit'] if account_data else 0,
                'total_daily_profit': account_data['daily_profit'] if account_data else 0,
                'total_positions': account_data['positions_count'] if account_data else 0,
                'accounts_count': 1 if account_data else 0,
                'avg_drawdown': account_data['current_drawdown'] if account_data else 0,
                'accounts': [account_data] if account_data else []
            }
        }
    
    # ========== Market Handlers ==========
    
    async def _handle_get_market_analysis(self, data: dict) -> dict:
        symbol = data.get('symbol', 'EURUSD')
        analysis = self.market_service.get_market_analysis(symbol)
        return {'type': 'get_market_analysis_response', 'data': analysis}
    
    async def _handle_run_global_scan(self, data: dict) -> dict:
        symbols = data.get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD'])
        results = self.market_service.run_global_scan(symbols)
        return {'type': 'run_global_scan_response', 'data': {'results': results}}
    
    async def _handle_get_mt5_symbols(self, data: dict) -> dict:
        symbols = self.mt5_service.get_visible_symbols(30)
        return {'type': 'mt5_symbols', 'data': symbols}
    
    async def _handle_get_yahoo_quote(self, data: dict) -> dict:
        symbol = data.get('symbol', 'EURUSD')
        try:
            quote = yahoo_provider.get_quote(symbol)
            return {'type': 'get_yahoo_quote_response', **quote}
        except Exception as e:
            return {'type': 'get_yahoo_quote_response', 'error': str(e), 'symbol': symbol}
    
    async def _handle_get_yahoo_all(self, data: dict) -> dict:
        try:
            all_data = yahoo_provider.get_all_terminal_data()
            return {'type': 'get_yahoo_all_response', 'data': all_data}
        except Exception as e:
            return {'type': 'get_yahoo_all_response', 'error': str(e)}
    
    # ========== Strategy Handlers ==========
    
    async def _handle_parse_strategy(self, data: dict) -> dict:
        try:
            description = data.get('description')
            ai_provider = data.get('ai_provider', 'groq')
            api_key = data.get('api_key')
            
            result = await self.strategy_parser.parse_strategy(description, ai_provider, api_key)
            
            if result.get('success'):
                raw_code = result.get('code', '')
                summary = "Özet bulunamadı."
                code_content = raw_code
                
                # XML Style Parsing
                if '<SUMMARY>' in raw_code:
                    try:
                        if '</SUMMARY>' in raw_code:
                            summary = raw_code.split('<SUMMARY>')[1].split('</SUMMARY>')[0].strip()
                        if '<CODE>' in raw_code and '</CODE>' in raw_code:
                            code_content = raw_code.split('<CODE>')[1].split('</CODE>')[0].strip()
                    except Exception:
                        pass
                
                # Clean code blocks
                for marker in ['```python', '```']:
                    if code_content.startswith(marker):
                        code_content = code_content[len(marker):]
                if code_content.endswith('```'):
                    code_content = code_content[:-3]
                
                result['code'] = code_content.strip()
                result['summary'] = summary
            
            return {'type': 'strategy_parsed', 'data': result}
        except Exception as e:
            return {'type': 'strategy_parsed', 'data': {'success': False, 'error': str(e)}}
    
    async def _handle_run_backtest(self, data: dict) -> dict:
        result = self.backtest_engine.run_backtest(
            data.get('strategy_code'),
            data.get('symbol', 'EURUSD'),
            data.get('timeframe', 'H1'),
            data.get('initial_balance', 10000),
            data.get('start_date'),
            data.get('end_date'),
            data.get('lot_size', 0.01),
            data.get('spread_points', 2)
        )
        
        if result.get('success'):
            for trade in result.get('trades', []):
                trade['entry_time'] = trade['entry_time'].isoformat()
                trade['exit_time'] = trade['exit_time'].isoformat()
            for point in result.get('equity_curve', []):
                point['time'] = point['time'].isoformat()
            for candle in result.get('price_history', []):
                candle['time'] = candle['time'].isoformat()
        
        return {'type': 'backtest_result', 'data': result}
    
    async def _handle_save_strategy(self, data: dict) -> dict:
        success = self.strategy_manager.save_strategy(
            data.get('name'),
            data.get('code'),
            data.get('summary'),
            data.get('timeframe')
        )
        return {'type': 'strategy_saved', 'success': success}
    
    async def _handle_get_strategies(self, data: dict) -> dict:
        strategies = self.strategy_manager.get_strategies()
        return {'type': 'strategies_list', 'data': strategies}
    
    async def _handle_delete_strategy(self, data: dict) -> dict:
        success = self.strategy_manager.delete_strategy(data.get('id'))
        return {'type': 'strategy_deleted', 'success': success}
    
    async def _handle_evolve_strategy(self, data: dict) -> dict:
        result = await self.strategy_parser.evolve_strategy(
            data.get('code'),
            data.get('ai_provider', 'groq'),
            data.get('api_key')
        )
        return {'type': 'evolve_strategy_response', 'data': result}
    
    # ========== Template Handlers ==========
    
    async def _handle_get_templates(self, data: dict) -> dict:
        from strategy_templates import StrategyTemplates
        templates = StrategyTemplates()
        return {'type': 'templates_list', 'data': templates.list_templates()}
    
    async def _handle_load_template(self, data: dict) -> dict:
        from strategy_templates import StrategyTemplates
        templates = StrategyTemplates()
        result = templates.customize_template(
            data.get('template_id'),
            data.get('params', {})
        )
        return {'type': 'template_loaded', 'data': result}
    
    async def _handle_save_user_template(self, data: dict) -> dict:
        import uuid
        template_file = os.path.join(os.path.dirname(__file__), '..', 'user_templates.json')
        
        templates = []
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        
        new_template = {
            'id': f"user_{uuid.uuid4().hex[:8]}",
            'name': data.get('name'),
            'description': data.get('description', ''),
            'code': data.get('code'),
            'timeframe': data.get('timeframe', 'H1'),
            'category': 'Kullanıcı',
            'created_at': datetime.now().isoformat()
        }
        templates.append(new_template)
        
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        return {'type': 'save_user_template_response', 'success': True, 'template_id': new_template['id']}
    
    async def _handle_get_user_templates(self, data: dict) -> dict:
        template_file = os.path.join(os.path.dirname(__file__), '..', 'user_templates.json')
        templates = []
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        return {'type': 'get_user_templates_response', 'data': templates}
    
    async def _handle_delete_user_template(self, data: dict) -> dict:
        template_file = os.path.join(os.path.dirname(__file__), '..', 'user_templates.json')
        template_id = data.get('template_id')
        
        templates = []
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        
        templates = [t for t in templates if t['id'] != template_id]
        
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        return {'type': 'delete_user_template_response', 'success': True}
    
    # ========== Journal Handlers ==========
    
    async def _handle_get_journal_data(self, data: dict) -> dict:
        days = data.get('days', 30)
        history = self.journal_manager.get_trade_history(days)
        stats = self.journal_manager.get_stats(days)
        return {'type': 'journal_data', 'data': {'history': history, 'stats': stats}}
    
    async def _handle_get_journal_analytics(self, data: dict) -> dict:
        days = data.get('days', 30)
        analytics = self.journal_analytics.get_full_analytics(days)
        return {'type': 'journal_analytics', 'data': analytics}
    
    async def _handle_save_trade_note(self, data: dict) -> dict:
        position_id = data.get('position_id')
        note_data = data.get('data')
        success = self.journal_manager.save_trade_note(position_id, note_data)
        return {'type': 'note_saved', 'success': success, 'position_id': position_id}
    
    # ========== Analysis Handlers ==========
    
    async def _handle_mtf_analysis(self, data: dict) -> dict:
        symbol = data.get('symbol', 'EURUSD')
        preset = data.get('preset', 'intraday')
        custom_tfs = data.get('custom_timeframes')
        result = self.mtf_analyzer.analyze(symbol, preset, custom_tfs)
        return {'type': 'mtf_analysis_result', 'data': result}
    
    async def _handle_get_recovery_plan(self, data: dict) -> dict:
        account_data = self.mt5_service.get_account_data()
        if not account_data:
            return {'type': 'recovery_plan', 'data': {'error': 'Account data not available'}}
        
        balance = account_data.get('balance', 10000)
        equity = account_data.get('equity', balance)
        initial_balance = data.get('initial_balance', balance)
        peak_balance = data.get('peak_balance', max(balance, equity))
        
        plan = self.recovery_planner.calculate_recovery_plan(
            current_balance=equity,
            peak_balance=peak_balance,
            initial_balance=initial_balance,
            max_allowed_dd=self.telegram_settings.get('max_drawdown', 10.0),
            daily_loss_limit=self.telegram_settings.get('daily_limit', 5.0),
            target_win_rate=data.get('win_rate', 55),
            average_rr=data.get('rr_ratio', 1.5)
        )
        return {'type': 'recovery_plan', 'data': plan}
    
    # ========== Config Handlers ==========
    
    async def _handle_set_telegram_settings(self, data: dict) -> dict:
        self.telegram_settings = {
            'max_drawdown': data.get('max_drawdown', 10.0),
            'daily_limit': data.get('daily_limit', 500.0)
        }
        return {'type': 'telegram_settings_saved', 'success': True}
    
    # ========== Live Trading Handlers ==========
    
    async def _handle_start_live_trader(self, data: dict) -> dict:
        strategy_code = data.get('strategy_code')
        symbol = data.get('symbol', 'EURUSD')
        timeframe = data.get('timeframe', 'H1')
        lot_size = data.get('lot_size', 0.01)
        
        success = self.live_trader.start(strategy_code, symbol, timeframe, lot_size)
        return {'type': 'live_trader_started', 'success': success}
    
    async def _handle_stop_live_trader(self, data: dict) -> dict:
        success = self.live_trader.stop()
        return {'type': 'live_trader_stopped', 'success': success}
    
    async def _handle_get_live_trader_status(self, data: dict) -> dict:
        status = self.live_trader.get_status()
        return {'type': 'live_trader_status', 'data': status}
    
    async def _handle_execute_trade(self, data: dict) -> dict:
        result = self.live_trader.execute_trade(
            symbol=data.get('symbol'),
            action=data.get('action'),
            volume=data.get('volume', 0.01),
            sl_pct=data.get('sl_pct'),
            rr_ratio=data.get('rr_ratio')
        )
        return {'type': 'trade_executed', 'data': result}
    
    # ========== Broadcasting ==========
    
    async def broadcast_updates(self):
        """Broadcast real-time updates to all connected clients"""
        while True:
            if self.connected_clients:
                account_data = self.mt5_service.get_account_data()
                
                if account_data:
                    # Check risk and notify
                    await self._check_and_notify_risk(account_data)
                    
                    message = json.dumps({
                        'type': 'realtime_update',
                        'data': {
                            'total_balance': account_data['balance'],
                            'total_equity': account_data['equity'],
                            'total_profit': account_data['profit'],
                            'total_daily_profit': account_data['daily_profit'],
                            'total_positions': account_data['positions_count'],
                            'accounts_count': 1,
                            'avg_drawdown': account_data['current_drawdown'],
                            'accounts': [account_data]
                        },
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    disconnected = set()
                    for client in self.connected_clients:
                        try:
                            await client.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected.add(client)
                    
                    for client in disconnected:
                        await self.unregister_client(client)
            
            await asyncio.sleep(self.update_interval)
    
    async def _check_and_notify_risk(self, account_data: dict):
        """Check risk levels and send Telegram notifications"""
        if not self.telegram.enabled:
            return
        
        current_dd = account_data.get('current_drawdown', 0)
        max_dd = self.telegram_settings.get('max_drawdown', 10.0)
        daily_loss = abs(account_data.get('daily_profit', 0)) if account_data.get('daily_profit', 0) < 0 else 0
        daily_limit = self.telegram_settings.get('daily_limit', 500.0)
        
        dd_pct = (current_dd / max_dd * 100) if max_dd > 0 else 0
        daily_pct = (daily_loss / daily_limit * 100) if daily_limit > 0 else 0
        
        if dd_pct >= 80 or daily_pct >= 80:
            new_level = 'critical'
        elif dd_pct >= 60 or daily_pct >= 60:
            new_level = 'warning'
        else:
            new_level = 'safe'
        
        if new_level != self.last_risk_level and new_level != 'safe':
            await self.telegram.notify_risk_warning(current_dd, max_dd, daily_loss, daily_limit)
            self.last_risk_level = new_level
    
    async def handler(self, websocket):
        """Main WebSocket handler"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)
    
    async def start(self):
        """Start the WebSocket server"""
        broadcast_task = asyncio.create_task(self.broadcast_updates())
        
        async with websockets.serve(self.handler, self.host, self.port):
            print(f"[START] UceAsistan Server started on ws://{self.host}:{self.port}")
            print("[WAIT] Waiting for connections...")
            await asyncio.Future()


def main():
    """Main entry point for the modular server"""
    print("=" * 60)
    print("UceAsistan Trading Platform - Modular Architecture")
    print("Version: 3.0 (Refactored)")
    print("=" * 60)
    
    warnings = validate_settings()
    for warning in warnings:
        print(warning)
    
    if settings.DEBUG:
        print(f"[DEBUG] Debug mode enabled")
        print(f"[DEBUG] Host: {settings.HOST}, Port: {settings.PORT}")
    
    server = UceAsistanServer(host=settings.HOST, port=settings.PORT)
    
    if not server.initialize():
        print("\n[ERROR] Failed to initialize. Please:")
        print("   1. Make sure MetaTrader 5 is running")
        print("   2. Login to an MT5 account")
        print("   3. Run this script again")
        input("\nPress Enter to exit...")
        return
    
    print("\n" + "=" * 60)
    print("[OK] Server ready! Open the web application to start trading.")
    print("=" * 60 + "\n")
    
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\n\n[STOP] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Server error: {e}")
    finally:
        server.mt5_service.shutdown()


if __name__ == "__main__":
    main()
