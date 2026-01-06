"""
WebSocket Message Handlers - Modular message routing and handling
Refactored from start_server.py for better maintainability
"""
import json
from typing import Dict, Any, Callable, Awaitable
from datetime import datetime


class MessageHandler:
    """Base class for WebSocket message handlers"""
    
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
    
    def register(self, action: str, handler: Callable[[Any, Dict], Awaitable[Dict]]):
        """Register a handler for a specific action"""
        self._handlers[action] = handler
    
    async def handle(self, websocket, message: str) -> bool:
        """Handle a message and return True if handled"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action in self._handlers:
                result = await self._handlers[action](websocket, data)
                if result:
                    await websocket.send(json.dumps(result))
                return True
            return False
            
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
            return True
        except Exception as e:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': str(e)
            }))
            return True


class AccountHandlers:
    """Handlers for account-related actions"""
    
    def __init__(self, mt5_service):
        self.mt5 = mt5_service
    
    async def get_account_data(self, websocket, data: Dict) -> Dict:
        """Handle get_account_data action"""
        account_data = self.mt5.get_account_data()
        return {
            'type': 'account_data',
            'data': account_data
        }
    
    async def get_portfolio(self, websocket, data: Dict) -> Dict:
        """Handle get_portfolio action"""
        account_data = self.mt5.get_account_data()
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


class MarketHandlers:
    """Handlers for market analysis actions"""
    
    def __init__(self, market_service, mt5_service):
        self.market = market_service
        self.mt5 = mt5_service
    
    async def get_market_analysis(self, websocket, data: Dict) -> Dict:
        """Handle get_market_analysis action"""
        symbol = data.get('symbol', 'EURUSD')
        analysis = self.market.get_market_analysis(symbol)
        return {
            'type': 'get_market_analysis_response',
            'data': analysis
        }
    
    async def run_global_scan(self, websocket, data: Dict) -> Dict:
        """Handle run_global_scan action"""
        symbols = data.get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD'])
        results = self.market.run_global_scan(symbols)
        return {
            'type': 'run_global_scan_response',
            'data': {'results': results}
        }
    
    async def get_mt5_symbols(self, websocket, data: Dict) -> Dict:
        """Handle get_mt5_symbols action"""
        symbols = self.mt5.get_visible_symbols(30)
        return {
            'type': 'mt5_symbols',
            'data': symbols
        }


class StrategyHandlers:
    """Handlers for strategy-related actions"""
    
    def __init__(self, strategy_parser, strategy_manager, backtest_engine):
        self.parser = strategy_parser
        self.manager = strategy_manager
        self.backtest = backtest_engine
    
    async def parse_strategy(self, websocket, data: Dict) -> Dict:
        """Handle parse_strategy action"""
        try:
            description = data.get('description')
            ai_provider = data.get('ai_provider', 'groq')
            api_key = data.get('api_key')
            
            result = await self.parser.parse_strategy(description, ai_provider, api_key)
            
            # Process result to extract summary and code
            if result.get('success'):
                raw_code = result.get('code', '')
                summary = "Özet bulunamadı."
                code_content = raw_code
                
                # XML Style Parsing
                if '<SUMMARY>' in raw_code or '<CODE>' in raw_code:
                    try:
                        if '<SUMMARY>' in raw_code and '</SUMMARY>' in raw_code:
                            summary = raw_code.split('<SUMMARY>')[1].split('</SUMMARY>')[0].strip()
                        if '<CODE>' in raw_code and '</CODE>' in raw_code:
                            code_content = raw_code.split('<CODE>')[1].split('</CODE>')[0].strip()
                        else:
                            code_content = raw_code.split('</SUMMARY>')[-1].strip()
                    except Exception:
                        pass
                
                # Clean markdown code blocks
                code_content = self._clean_code_blocks(code_content)
                result['code'] = code_content.strip()
                result['summary'] = summary
            
            return {
                'type': 'strategy_parsed',
                'data': result
            }
        except Exception as e:
            return {
                'type': 'strategy_parsed',
                'data': {'success': False, 'error': str(e)}
            }
    
    def _clean_code_blocks(self, code: str) -> str:
        """Remove markdown code block markers"""
        if code.startswith('```python'):
            code = code.replace('```python', '', 1)
        if code.startswith('```'):
            code = code.replace('```', '', 1)
        if code.endswith('```'):
            code = code[:-3]
        return code
    
    async def run_backtest(self, websocket, data: Dict) -> Dict:
        """Handle run_backtest action"""
        strategy_code = data.get('strategy_code')
        symbol = data.get('symbol', 'EURUSD')
        timeframe = data.get('timeframe', 'H1')
        initial_balance = data.get('initial_balance', 10000)
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        lot_size = data.get('lot_size', 0.01)
        spread_points = data.get('spread_points', 2)
        
        result = self.backtest.run_backtest(
            strategy_code, symbol, timeframe, initial_balance,
            start_date, end_date, lot_size, spread_points
        )
        
        # Convert datetime objects to strings
        if result.get('success'):
            for trade in result.get('trades', []):
                trade['entry_time'] = trade['entry_time'].isoformat()
                trade['exit_time'] = trade['exit_time'].isoformat()
            
            for point in result.get('equity_curve', []):
                point['time'] = point['time'].isoformat()
                
            for candle in result.get('price_history', []):
                candle['time'] = candle['time'].isoformat()
        
        return {
            'type': 'backtest_result',
            'data': result
        }
    
    async def save_strategy(self, websocket, data: Dict) -> Dict:
        """Handle save_strategy action"""
        name = data.get('name')
        code = data.get('code')
        summary = data.get('summary')
        timeframe = data.get('timeframe')
        
        success = self.manager.save_strategy(name, code, summary, timeframe)
        return {
            'type': 'strategy_saved',
            'success': success
        }
    
    async def get_strategies(self, websocket, data: Dict) -> Dict:
        """Handle get_strategies/list_strategies action"""
        strategies = self.manager.get_strategies()
        return {
            'type': 'strategies_list',
            'data': strategies
        }
    
    async def delete_strategy(self, websocket, data: Dict) -> Dict:
        """Handle delete_strategy action"""
        strategy_id = data.get('id')
        success = self.manager.delete_strategy(strategy_id)
        return {
            'type': 'strategy_deleted',
            'success': success
        }
