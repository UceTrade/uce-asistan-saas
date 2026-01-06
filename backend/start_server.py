"""
MT5 Auto-Connect Server - Automatically connects to active MT5 account
"""
import asyncio
import json
from mt5_proxy import mt5, MT5_AVAILABLE

if not MT5_AVAILABLE:
    print("WARNING: MetaTrader5 package not found or incompatible. Running in Simulation Mode.")

import websockets
from datetime import datetime
from config import settings, validate_settings
from ai_strategy_parser import AIStrategyParser
from backtest_engine import BacktestEngine
from journal_manager import JournalManager
from journal_analytics import JournalAnalytics
from strategy_manager import StrategyManager
from signal_confluence import SignalConfluenceFinder
from price_action_lib import PriceActionLib
from forecasting_engine import ForecastingEngine
from telegram_bot import telegram_notifier
from multi_timeframe import MultiTimeframeAnalyzer
from drawdown_planner import DrawdownRecoveryPlanner
from prop_firm_database import get_rules_for_broker, get_prop_firm_rules, get_all_prop_firms, get_risk_recommendations
from live_trader import LiveTrader
from yahoo_finance_provider import yahoo_provider
from fin_agent import FinAgent, FinanceQueryType
import pandas as pd
import numpy as np


class MT5AutoConnectServer:
    """WebSocket server that auto-connects to currently active MT5 account"""
    
    def __init__(self, host='localhost', port=8766):
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.update_interval = 1.0  # seconds
        self.current_account = None
        self.account_data = None
        self.strategy_parser = AIStrategyParser()
        self.strategy_parser = AIStrategyParser()
        self.backtest_engine = BacktestEngine()
        self.journal_manager = JournalManager()
        self.strategy_manager = StrategyManager()
        self.confluence_finder = SignalConfluenceFinder()
        self.pa_lib = PriceActionLib()
        self.forecaster = ForecastingEngine(self.pa_lib)
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.recovery_planner = DrawdownRecoveryPlanner()
        self.telegram_settings = {} # Will be loaded from connection
        self.journal_analytics = JournalAnalytics(self.journal_manager)
        self.live_trader = LiveTrader()  # Live trading engine
        
        # FinGPT Financial Agent
        self.fin_agent = FinAgent()
        
        # Telegram Notifier
        self.telegram = telegram_notifier
        self.last_risk_level = 'safe'  # Track for alert triggering
        self.telegram_settings = {'max_drawdown': 10.0, 'daily_limit': 500.0}
        
        # MTF and Recovery Planner
        self.mtf_analyzer = MultiTimeframeAnalyzer()
        self.recovery_planner = DrawdownRecoveryPlanner()
    
    def initialize_mt5(self):
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
        
        return True
    
    def get_account_data(self):
        """Get current account data"""
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
        from datetime import datetime, timedelta
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
            'name': self.current_account['name'],
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
    
    async def register_client(self, websocket):
        """Register a new WebSocket client"""
        self.connected_clients.add(websocket)
        print(f"[OK] Client connected. Total clients: {len(self.connected_clients)}")
        
        # Send initial account info
        if self.current_account:
            await websocket.send(json.dumps({
                'type': 'account_info',
                'data': self.current_account
            }))
    
    async def unregister_client(self, websocket):
        """Unregister a WebSocket client"""
        self.connected_clients.remove(websocket)
        print(f"[DISCONNECT] Client disconnected. Total clients: {len(self.connected_clients)}")

    def get_market_analysis(self, symbol):
        """Get market analysis data for a symbol (price, RSI, SMA)"""
        # 1. Get current price (Tick)
        tick = mt5.symbol_info_tick(symbol)
        
        # 2. Get recent rates for indicators
        timeframe = mt5.TIMEFRAME_H1
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 100)
        
        if rates is None or len(rates) < 50:
            # Check if symbol even exists
            si = mt5.symbol_info(symbol)
            if si is None:
                return {'error': f'{symbol} sembolü bulunamadı. Lütfen Market Watch\'a ekleyin.'}
            return {'error': f'{symbol} için yeterli veri yok (En az 50 bar H1 gerekli).'}

        # 3. Weekend Fallback
        current_price = tick.ask if tick is not None else rates[-1]['close']
        is_weekend_data = tick is None
        
        if current_price == 0:
            return {'error': f'{symbol} için fiyat verisi alınamadı.'}
            
        df = pd.DataFrame(rates)
        
        # Calculate RSI 14
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Calculate SMAs
        sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
        sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
        
        # Calculate 24h change (approx 24 bars for H1)
        price_24h_ago = df['close'].iloc[-24] if len(df) >= 24 else df['open'].iloc[0]
        change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
        
        # Determine trend
        trend = 'neutral'
        if current_price > sma_50:
            trend = 'uptrend' 
        elif current_price < sma_50:
            trend = 'downtrend'
            
        # --- NEW: Advanced SMC Analysis ---
        try:
            # Perform deep analysis
            analysis_df = self.pa_lib.analyze_all(df)
            latest = analysis_df.iloc[-1]
            
            # Extract SMC metrics
            smc_data = {
                'trend_bias': int(latest.get('trend_bias', 0)),
                'bos_detected': bool(latest.get('bos', False)),
                'choch_detected': bool(latest.get('choch', False)),
                'is_discount': bool(latest.get('is_discount', False)),
                'is_premium': bool(latest.get('is_premium', False)),
                'sweep_high': bool(latest.get('sweep_high', False)),
                'sweep_low': bool(latest.get('sweep_low', False)),
                'bullish_ob': bool(latest.get('bullish_ob', False)),
                'bearish_ob': bool(latest.get('bearish_ob', False)),
                'eqh_price': float(latest.get('eqh_price', 0)) if not np.isnan(latest.get('eqh_price', np.nan)) else 0,
                'eql_price': float(latest.get('eql_price', 0)) if not np.isnan(latest.get('eql_price', np.nan)) else 0,
                'bos_count': int(analysis_df['bos'].sum()),
                'choch_count': int(analysis_df['choch'].sum()),
                'confluence_score': float(latest.get('confluence_score', 0)),
                'session_info': self._get_session_info(),
                'coach_advice': self._generate_coach_advice(latest, analysis_df, is_weekend_data)
            }
        except Exception as e:
            print(f"[ERROR] SMC analysis failed: {e}")
            smc_data = {}
            
        return {
            'symbol': symbol,
            'price': current_price,
            'change_24h': round(change_24h, 2),
            'rsi_14': round(current_rsi, 2),
            'sma_20': round(sma_20, 5),
            'sma_50': round(sma_50, 5),
            'trend': trend,
            'smc': smc_data,
            'forecast': self.forecaster.project_paths(analysis_df),
            'off_market': is_weekend_data,
            'timestamp': datetime.now().isoformat()
        }

    
    async def handle_message(self, websocket, message):
        """Handle incoming messages from clients"""
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'get_account_data':
                # Get current account data
                account_data = self.get_account_data()
                
                response = {
                    'type': 'account_data',
                    'data': account_data
                }
                
                await websocket.send(json.dumps(response))
            
            elif action == 'get_portfolio':
                # For single account, portfolio = account data
                account_data = self.get_account_data()
                
                response = {
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
                
                await websocket.send(json.dumps(response))
            
            elif action == 'parse_strategy':
                try:
                    # Parse strategy description with AI
                    description = data.get('description')
                    ai_provider = data.get('ai_provider', 'groq')
                    api_key = data.get('api_key')
                    
                    result = await self.strategy_parser.parse_strategy(description, ai_provider, api_key)
                    
                    # Check if result contains split markers
                    if result.get('success'):
                        raw_code = result.get('code', '')
                        summary = "Özet bulunamadı."
                        code_content = raw_code
                        
                        # XML Style Parsing
                        if '<SUMMARY>' in raw_code or '<CODE>' in raw_code:
                            try:
                                # Extract Summary
                                if '<SUMMARY>' in raw_code and '</SUMMARY>' in raw_code:
                                    summary = raw_code.split('<SUMMARY>')[1].split('</SUMMARY>')[0].strip()
                                
                                # Extract Code
                                if '<CODE>' in raw_code and '</CODE>' in raw_code:
                                    code_content = raw_code.split('<CODE>')[1].split('</CODE>')[0].strip()
                                else:
                                    # Fallback if only summary tags exist
                                    code_content = raw_code.split('</SUMMARY>')[-1].strip()
                                    
                            except Exception as e:
                                print(f"Parsing error: {e}")
                                
                        elif '---SUMMARY---' in raw_code:
                             # Backward compatibility
                            parts = raw_code.split('---CODE---')
                            if len(parts) > 1:
                                summary_part = parts[0].replace('---SUMMARY---', '').strip()
                                code_part = parts[1].strip()
                                
                                summary = summary_part
                                code_content = code_part
                        
                        # Clean markdown code blocks if present (just in case AI wraps CODE in backticks)
                        if code_content.startswith('```python'):
                            code_content = code_content.replace('```python', '', 1)
                        if code_content.startswith('```'):
                             code_content = code_content.replace('```', '', 1)
                        if code_content.endswith('```'):
                            code_content = code_content[:-3]
                            
                        result['code'] = code_content.strip()
                        result['summary'] = summary

                    response = {
                        'type': 'strategy_parsed',
                        'data': result
                    }
                    
                    await websocket.send(json.dumps(response))
                    
                except OSError as e:
                    # Catch broken pipe / connection reset (WinError 64)
                    print(f"[ERROR] Client disconnected during strategy parsing: {e}")
                except Exception as e:
                    print(f"[ERROR] Error in parse_strategy handler: {e}")
                    try:
                        # Try to send error to client if still connected
                        await websocket.send(json.dumps({
                            'type': 'strategy_parsed',
                            'data': {'success': False, 'error': str(e)}
                        }))
                    except:
                        pass
            
            elif action == 'run_backtest':
                # Run backtest with strategy code
                strategy_code = data.get('strategy_code')
                symbol = data.get('symbol', 'EURUSD')
                timeframe = data.get('timeframe', 'H1')
                initial_balance = data.get('initial_balance', 10000)
                start_date = data.get('start_date')
                end_date = data.get('end_date')
                lot_size = data.get('lot_size', 0.01)
                spread_points = data.get('spread_points', 2)
                
                result = self.backtest_engine.run_backtest(
                    strategy_code, symbol, timeframe, initial_balance,
                    start_date, end_date, lot_size, spread_points
                )
                
                print(f"[DEBUG] Backtest executed. Result keys: {list(result.keys())}")
                if 'price_history' in result:
                    print(f"[DEBUG] Price history count: {len(result['price_history'])}")
                else:
                    print("[ERROR] 'price_history' NOT FOUND in result from backtest_engine!")
                
                # Convert datetime objects to strings for JSON
                if result.get('success'):
                    for trade in result.get('trades', []):
                        trade['entry_time'] = trade['entry_time'].isoformat()
                        trade['exit_time'] = trade['exit_time'].isoformat()
                    
                    for point in result.get('equity_curve', []):
                        point['time'] = point['time'].isoformat()
                        
                    for candle in result.get('price_history', []):
                        candle['time'] = candle['time'].isoformat()
                
                response = {
                    'type': 'backtest_result',
                    'data': result
                }
                
                await websocket.send(json.dumps(response))
            
            elif action == 'get_market_analysis':
                # Get market analysis data
                symbol = data.get('symbol', 'EURUSD')
                analysis = self.get_market_analysis(symbol)
                
                response = {
                    'type': 'get_market_analysis_response',
                    'data': analysis
                }
                
                await websocket.send(json.dumps(response))
            
            elif action == 'run_global_scan':
                # Scan multiple symbols for confluence
                symbols = data.get('symbols', ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD'])
                results = []
                
                for sym in symbols:
                    try:
                        analysis = self.get_market_analysis(sym)
                        if 'error' not in analysis:
                            results.append({
                                'symbol': sym,
                                'score': analysis['smc']['confluence_score'],
                                'bias': analysis['trend'],
                                'price': analysis['price']
                            })
                    except:
                        continue
                
                # Sort by score descending
                results.sort(key=lambda x: x['score'], reverse=True)
                print(f"[RADAR] Scan complete. Found {len(results)} opportunities.")
                
                await websocket.send(json.dumps({
                    'type': 'run_global_scan_response',
                    'data': {'results': results}
                }))

            elif action == 'evolve_strategy':
                # Mutate/Optimize existing strategy code
                current_code = data.get('code')
                ai_provider = data.get('ai_provider', 'groq')
                api_key = data.get('api_key')
                
                result = await self.strategy_parser.evolve_strategy(current_code, ai_provider, api_key)
                
                await websocket.send(json.dumps({
                    'type': 'evolve_strategy_response',
                    'data': result
                }))

            elif action == 'get_journal_data':
                # Get journal history and stats
                days = data.get('days', 30)
                history = self.journal_manager.get_trade_history(days)
                stats = self.journal_manager.get_stats(days)
                
                response = {
                    'type': 'journal_data',
                    'data': {
                        'history': history,
                        'stats': stats
                    }
                }
                await websocket.send(json.dumps(response))
            
            elif action == 'get_journal_analytics':
                # Get advanced journal analytics
                days = data.get('days', 30)
                analytics = self.journal_analytics.get_full_analytics(days)
                
                await websocket.send(json.dumps({
                    'type': 'journal_analytics',
                    'data': analytics
                }))
            
            elif action == 'get_market_analysis':
                # Market Terminal: Get single symbol analysis
                symbol = data.get('symbol', 'EURUSD')
                try:
                    analysis = self.get_market_analysis(symbol)
                    await websocket.send(json.dumps({
                        'type': 'market_analysis_response',
                        **analysis  # Spread analysis data directly
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'market_analysis_response',
                        'error': str(e),
                        'symbol': symbol
                    }))
            
            elif action == 'get_yahoo_quote':
                # Yahoo Finance: Get single symbol quote
                symbol = data.get('symbol', 'EURUSD')
                try:
                    quote = yahoo_provider.get_quote(symbol)
                    await websocket.send(json.dumps({
                        'type': 'get_yahoo_quote_response',
                        **quote
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'get_yahoo_quote_response',
                        'error': str(e),
                        'symbol': symbol
                    }))
            
            elif action == 'get_yahoo_all':
                # Yahoo Finance: Get all terminal data
                try:
                    all_data = yahoo_provider.get_all_terminal_data()
                    await websocket.send(json.dumps({
                        'type': 'get_yahoo_all_response',
                        'data': all_data
                    }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'get_yahoo_all_response',
                        'error': str(e)
                    }))
            
            elif action == 'mtf_analysis':
                # Multi-Timeframe Analysis
                symbol = data.get('symbol', 'EURUSD')
                preset = data.get('preset', 'intraday')
                custom_tfs = data.get('custom_timeframes')
                
                result = self.mtf_analyzer.analyze(symbol, preset, custom_tfs)
                
                await websocket.send(json.dumps({
                    'type': 'mtf_analysis_result',
                    'data': result
                }))
            
            elif action == 'get_recovery_plan':
                # Drawdown Recovery Planner
                account_data = self.get_account_data()
                if account_data:
                    balance = account_data.get('balance', 10000)
                    equity = account_data.get('equity', balance)
                    
                    # Use balance as initial (prop firm assumption) or get from settings
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
                    
                    await websocket.send(json.dumps({
                        'type': 'recovery_plan',
                        'data': plan
                    }))
                else:
                    await websocket.send(json.dumps({
                        'type': 'recovery_plan',
                        'data': {'error': 'Account data not available'}
                    }))
                
            elif action == 'save_trade_note':
                # Save note for a trade
                position_id = data.get('position_id')
                note_data = data.get('data') # {note, emotion, tags, strategy}
                
                success = self.journal_manager.save_trade_note(position_id, note_data)
                
                response = {
                    'type': 'note_saved',
                    'success': success,
                    'position_id': position_id
                }
                await websocket.send(json.dumps(response))

            elif action == 'save_strategy':
                name = data.get('name')
                code = data.get('code')
                summary = data.get('summary')
                timeframe = data.get('timeframe')
                
                success = self.strategy_manager.save_strategy(name, code, summary, timeframe)
                
                await websocket.send(json.dumps({
                    'type': 'strategy_saved',
                    'success': success
                }))
                
            elif action == 'get_strategies' or action == 'list_strategies':
                strategies = self.strategy_manager.get_strategies()
                await websocket.send(json.dumps({
                    'type': 'strategies_list',
                    'data': strategies
                }))
                
            elif action == 'delete_strategy':
                strategy_id = data.get('id')
                success = self.strategy_manager.delete_strategy(strategy_id)
                await websocket.send(json.dumps({
                    'type': 'strategy_deleted',
                    'success': success
                }))
            
            # User Template CRUD handlers
            elif action == 'save_user_template':
                import os
                import uuid
                template_file = os.path.join(os.path.dirname(__file__), 'user_templates.json')
                
                # Load existing templates
                templates = []
                if os.path.exists(template_file):
                    with open(template_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                
                # Create new template
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
                
                # Save to file
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, ensure_ascii=False, indent=2)
                
                print(f"[TEMPLATE] Saved user template: {new_template['name']}")
                
                await websocket.send(json.dumps({
                    'type': 'save_user_template_response',
                    'success': True,
                    'template_id': new_template['id']
                }))
            
            elif action == 'get_user_templates':
                import os
                template_file = os.path.join(os.path.dirname(__file__), 'user_templates.json')
                
                templates = []
                if os.path.exists(template_file):
                    with open(template_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                
                await websocket.send(json.dumps({
                    'type': 'get_user_templates_response',
                    'data': templates
                }))
            
            elif action == 'delete_user_template':
                import os
                template_id = data.get('template_id')
                template_file = os.path.join(os.path.dirname(__file__), 'user_templates.json')
                
                templates = []
                if os.path.exists(template_file):
                    with open(template_file, 'r', encoding='utf-8') as f:
                        templates = json.load(f)
                
                # Filter out the template to delete
                templates = [t for t in templates if t['id'] != template_id]
                
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(templates, f, ensure_ascii=False, indent=2)
                
                print(f"[TEMPLATE] Deleted template: {template_id}")
                
                await websocket.send(json.dumps({
                    'type': 'delete_user_template_response',
                    'success': True
                }))
            
            elif action == 'get_mt5_symbols':
                # Get visible symbols from MT5
                symbols = mt5.symbols_get()
                visible_symbols = []
                
                if symbols:
                    # Get only visible symbols (in Market Watch)
                    for s in symbols:
                        if s.visible:
                            visible_symbols.append(s.name)
                
                # If no visible symbols, return defaults
                if not visible_symbols:
                    visible_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']
                
                await websocket.send(json.dumps({
                    'type': 'mt5_symbols',
                    'data': visible_symbols[:30]  # Limit to 30 symbols
                }))
            
            # Built-in Template handlers
            elif action == 'get_templates':
                from strategy_templates import StrategyTemplates
                templates = StrategyTemplates()
                await websocket.send(json.dumps({
                    'type': 'templates_list',
                    'data': templates.list_templates()
                }))
            
            elif action == 'load_template':
                try:
                    from strategy_templates import StrategyTemplates
                    template_id = data.get('template_id')
                    params = data.get('params', {})
                    
                    print(f"[DEBUG] Loading template: {template_id}")
                    
                    templates = StrategyTemplates()
                    result = templates.customize_template(template_id, params)
                    
                    print(f"[DEBUG] Template result: {result.get('success', False)}")
                    
                    await websocket.send(json.dumps({
                        'type': 'template_loaded',
                        'data': result
                    }))
                except Exception as e:
                    print(f"[ERROR] Template loading failed: {e}")
                    import traceback
                    traceback.print_exc()
                    await websocket.send(json.dumps({
                        'type': 'template_loaded',
                        'data': {'success': False, 'error': str(e)}
                    }))
            
            # NEW: Conversation Wizard handlers
            elif action == 'start_conversation':
                from conversation_manager import ConversationManager
                if not hasattr(self, 'conv_manager'):
                    self.conv_manager = ConversationManager()
                
                session_id = data.get('session_id')
                description = data.get('description')
                question = self.conv_manager.start_conversation(session_id, description)
                
                await websocket.send(json.dumps({
                    'type': 'conversation_question',
                    'data': {'question': question}
                }))
            
            elif action == 'answer_question':
                session_id = data.get('session_id')
                question_id = data.get('question_id')
                answer = data.get('answer')
                
                self.conv_manager.process_answer(session_id, question_id, answer)
                next_question = self.conv_manager.get_next_question(session_id)
                
                if next_question:
                    await websocket.send(json.dumps({
                        'type': 'conversation_question',
                        'data': {'question': next_question}
                    }))
                else:
                    await websocket.send(json.dumps({
                        'type': 'conversation_complete',
                        'data': {}
                    }))
            
            elif action == 'generate_final_prompt':
                session_id = data.get('session_id')
                prompt = self.conv_manager.generate_final_prompt(session_id)
                
                await websocket.send(json.dumps({
                    'type': 'final_prompt',
                    'data': {'prompt': prompt}
                }))
            
            # NEW: Optimizer handler
            elif action == 'optimize_strategy':
                from strategy_optimizer import StrategyOptimizer
                optimizer = StrategyOptimizer()
                
                strategy_code = data.get('strategy_code')
                backtest_results = data.get('backtest_results')
                
                suggestions = optimizer.analyze_backtest(strategy_code, backtest_results)
                
                await websocket.send(json.dumps({
                    'type': 'optimization_suggestions',
                    'data': {'suggestions': suggestions}
                }))
                
            elif action == 'start_auto_trade':
                strategy_code = data.get('code')
                symbol = data.get('symbol')
                timeframe = data.get('timeframe')
                rr_ratio = data.get('rr_ratio', 2.0)
                lot_size = data.get('lot_size', 0.01)
                
                success, msg = self.live_trader.start(strategy_code, symbol, timeframe, rr_ratio, lot_size)
                
                await websocket.send(json.dumps({
                    'type': 'auto_trade_started',
                    'success': success,
                    'message': msg
                }))
                
            elif action == 'stop_auto_trade':
                success, msg = self.live_trader.stop()
                
                await websocket.send(json.dumps({
                    'type': 'auto_trade_stopped',
                    'success': success,
                    'message': msg
                }))
            
            elif action == 'start_live_trading':
                # Start live trading with strategy (from frontend "Canlıya Al" button)
                strategy_code = data.get('strategy_code')
                symbol = data.get('symbol', 'EURUSD')
                timeframe = data.get('timeframe', 'H1')
                lot_size = data.get('lot_size', 0.01)
                rr_ratio = data.get('rr_ratio', 2.0)
                
                print(f"[LIVE TRADER] Starting live trading on {symbol} {timeframe}...")
                
                success, msg = self.live_trader.start(strategy_code, symbol, timeframe, rr_ratio, lot_size)
                
                if success:
                    print(f"[LIVE TRADER] ✅ Successfully started!")
                else:
                    print(f"[LIVE TRADER] ❌ Failed: {msg}")
                
                await websocket.send(json.dumps({
                    'type': 'live_trading_started',
                    'success': success,
                    'message': msg
                }))

            # ========== FinGPT Financial Agent Handlers ==========
            elif action == 'fin_agent_query':
                # Main FinAgent query endpoint
                try:
                    query = data.get('query')
                    context = data.get('context', {})
                    api_keys = data.get('api_keys', {})
                    
                    # Set API keys if provided (in priority order: free first)
                    if api_keys.get('groq_api_key'):
                        self.fin_agent.groq_api_key = api_keys['groq_api_key']
                    if api_keys.get('openrouter_api_key'):
                        self.fin_agent.openrouter_api_key = api_keys['openrouter_api_key']
                    if api_keys.get('together_api_key'):
                        self.fin_agent.together_api_key = api_keys['together_api_key']
                    if api_keys.get('fireworks_api_key'):
                        self.fin_agent.fireworks_api_key = api_keys['fireworks_api_key']
                    
                    # Add account context if available
                    account_data = self.get_account_data()
                    if account_data:
                        context['account_balance'] = account_data.get('balance')
                        context['open_positions'] = account_data.get('positions', [])
                        context['daily_pnl'] = account_data.get('daily_profit')
                    
                    # Run analysis
                    result = await self.fin_agent.analyze(query, context)
                    
                    print(f"[FIN_AGENT] Query: {query[:50]}... → Type: {result.get('query_type', 'unknown')}")
                    
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_response',
                        'data': result
                    }))
                    
                except Exception as e:
                    print(f"[FIN_AGENT] Error: {e}")
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_response',
                        'data': {'error': True, 'message': str(e)}
                    }))
            
            elif action == 'fin_agent_sentiment':
                # Quick sentiment analysis
                try:
                    symbol = data.get('symbol', 'EURUSD')
                    news = data.get('news', [])
                    api_keys = data.get('api_keys', {})
                    
                    if api_keys.get('together_api_key'):
                        self.fin_agent.together_api_key = api_keys['together_api_key']
                    
                    result = await self.fin_agent.get_sentiment(symbol, news)
                    
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_sentiment_response',
                        'data': result
                    }))
                    
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_sentiment_response',
                        'data': {'error': True, 'message': str(e)}
                    }))
            
            elif action == 'fin_agent_trade_signal':
                # Get trading decision
                try:
                    symbol = data.get('symbol', 'EURUSD')
                    api_keys = data.get('api_keys', {})
                    
                    if api_keys.get('together_api_key'):
                        self.fin_agent.together_api_key = api_keys['together_api_key']
                    
                    # Get market data for context
                    market_analysis = self.get_market_analysis(symbol)
                    market_data = {}
                    if 'error' not in market_analysis:
                        market_data = {
                            'price': market_analysis.get('price'),
                            'rsi': market_analysis.get('rsi_14'),
                            'trend': market_analysis.get('trend'),
                            'sma_20': market_analysis.get('sma_20'),
                            'sma_50': market_analysis.get('sma_50')
                        }
                        if market_analysis.get('smc'):
                            market_data['confluence_score'] = market_analysis['smc'].get('confluence_score')
                    
                    result = await self.fin_agent.get_trade_signal(symbol, market_data)
                    
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_trade_signal_response',
                        'data': result
                    }))
                    
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_trade_signal_response',
                        'data': {'error': True, 'message': str(e)}
                    }))
            
            elif action == 'fin_agent_risk':
                # Risk assessment
                try:
                    symbol = data.get('symbol', 'EURUSD')
                    planned_lot = data.get('lot_size', 0.01)
                    api_keys = data.get('api_keys', {})
                    
                    if api_keys.get('together_api_key'):
                        self.fin_agent.together_api_key = api_keys['together_api_key']
                    
                    # Get account balance
                    account_data = self.get_account_data()
                    balance = account_data.get('balance', 10000) if account_data else 10000
                    
                    result = await self.fin_agent.assess_risk(symbol, balance, planned_lot)
                    
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_risk_response',
                        'data': result
                    }))
                    
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_risk_response',
                        'data': {'error': True, 'message': str(e)}
                    }))
            
            elif action == 'fin_agent_analyze_market':
                # Full market analysis
                try:
                    symbol = data.get('symbol', 'EURUSD')
                    timeframe = data.get('timeframe', 'H1')
                    api_keys = data.get('api_keys', {})
                    
                    if api_keys.get('together_api_key'):
                        self.fin_agent.together_api_key = api_keys['together_api_key']
                    
                    result = await self.fin_agent.analyze_market(symbol, timeframe)
                    
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_market_analysis_response',
                        'data': result
                    }))
                    
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'fin_agent_market_analysis_response',
                        'data': {'error': True, 'message': str(e)}
                    }))
            
            elif action == 'fin_agent_set_keys':
                # Set API keys for FinAgent
                together_key = data.get('together_api_key')
                fireworks_key = data.get('fireworks_api_key')
                
                if together_key:
                    self.fin_agent.together_api_key = together_key
                if fireworks_key:
                    self.fin_agent.fireworks_api_key = fireworks_key
                
                await websocket.send(json.dumps({
                    'type': 'fin_agent_keys_set',
                    'success': True
                }))

            elif action == 'find_confluences':
                # Signal Confluence Detection
                try:
                    strategies = data.get('strategies', [])
                    min_agreement = data.get('min_agreement', 0.6)
                    symbol = data.get('symbol', 'EURUSD')
                    timeframe_str = data.get('timeframe', 'H1')
                    bars = data.get('bars', 500)
                    
                    print(f"[CONFLUENCE] Finding confluences for {len(strategies)} strategies...")
                    
                    # Clear previous strategies
                    self.confluence_finder.clear_strategies()
                    
                    # Load strategies
                    for strategy in strategies:
                        strategy_type = strategy.get('type')  # 'template' or 'saved'
                        strategy_id = strategy.get('id')
                        
                        if strategy_type == 'template':
                            # Load from template library
                            from strategy_templates import StrategyTemplates
                            templates = StrategyTemplates()
                            template = templates.get_template(strategy_id)
                            
                            if template:
                                self.confluence_finder.add_strategy(
                                    template['name'],
                                    template['code'],
                                    {'type': 'template', 'id': strategy_id}
                                )
                        
                        elif strategy_type == 'saved':
                            # Load from saved strategies
                            saved_strategy = self.strategy_manager.get_strategy(strategy_id)
                            
                            if saved_strategy:
                                self.confluence_finder.add_strategy(
                                    saved_strategy['name'],
                                    saved_strategy['code'],
                                    {'type': 'saved', 'id': strategy_id}
                                )
                    
                    # Get market data
                    timeframe_map = {
                        'M1': mt5.TIMEFRAME_M1,
                        'M5': mt5.TIMEFRAME_M5,
                        'M15': mt5.TIMEFRAME_M15,
                        'M30': mt5.TIMEFRAME_M30,
                        'H1': mt5.TIMEFRAME_H1,
                        'H4': mt5.TIMEFRAME_H4,
                        'D1': mt5.TIMEFRAME_D1
                    }
                    
                    timeframe = timeframe_map.get(timeframe_str, mt5.TIMEFRAME_H1)
                    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
                    
                    if rates is None or len(rates) == 0:
                        await websocket.send(json.dumps({
                            'type': 'confluence_error',
                            'error': f'Failed to get data for {symbol}'
                        }))
                        return
                    
                    # Convert to DataFrame
                    import pandas as pd
                    data_df = pd.DataFrame(rates)
                    data_df['time'] = pd.to_datetime(data_df['time'], unit='s')
                    data_df.set_index('time', inplace=True)
                    
                    # Run all strategies
                    results = self.confluence_finder.run_all_strategies(data_df)
                    
                    # Find confluences
                    confluences = self.confluence_finder.find_confluences(
                        results['signals'],
                        min_agreement
                    )
                    
                    # Generate report
                    report = self.confluence_finder.generate_confluence_report(confluences)
                    
                    # Get strategy performance
                    performance = self.confluence_finder.get_strategy_performance(confluences)
                    
                    # Send response
                    await websocket.send(json.dumps({
                        'type': 'confluences_found',
                        'confluences': [
                            {
                                **conf,
                                'timestamp': conf['timestamp'].isoformat() if hasattr(conf['timestamp'], 'isoformat') else str(conf['timestamp'])
                            }
                            for conf in confluences
                        ],
                        'report': report,
                        'performance': performance,
                        'execution_summary': {
                            'total_strategies': results['total_strategies'],
                            'successful': results['successful_strategies'],
                            'errors': results['errors'],
                            'execution_times': results['execution_times']
                        }
                    }))
                    

                    # NOTIFY TELEGRAM FOR STRONG CONFLUENCES
                    try:
                        strong_confluences = [c for c in confluences if c['agreement'] >= 0.8]
                        if strong_confluences:
                            conf = strong_confluences[0] # Notify top one
                            import asyncio
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            strategies_names = conf.get('strategies_agreeing', [])
                            
                            loop.run_until_complete(self.telegram.notify_confluence_detected(
                                symbol=symbol,
                                direction=conf['signal'],
                                strength=conf['agreement']*100,
                                strategies=strategies_names
                            ))
                            loop.close()
                            print(f"[Telegram] Confluence notification sent for {symbol}")
                    except Exception as e:
                        print(f"[Telegram Error] {e}")
                    
                    print(f"[CONFLUENCE] Found {len(confluences)} confluences")
                
                except Exception as e:
                    import traceback
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    print(f"[CONFLUENCE ERROR] {error_msg}")
                    print(traceback.format_exc())
                    
                    await websocket.send(json.dumps({
                        'type': 'confluence_error',
                        'error': error_msg
                    }))

            elif action == 'configure_telegram':
                # Configure Telegram Bot
                bot_token = data.get('bot_token')
                chat_id = data.get('chat_id')
                max_drawdown = data.get('max_drawdown', 10.0)
                daily_limit = data.get('daily_limit', 500.0)
                
                self.telegram.configure(bot_token, chat_id)
                self.telegram_settings = {
                    'max_drawdown': max_drawdown,
                    'daily_limit': daily_limit
                }
                
                # Test connection
                result = await self.telegram.test_connection()
                
                await websocket.send(json.dumps({
                    'type': 'telegram_configured',
                    'success': result.get('success', False),
                    'bot_name': result.get('bot_name', ''),
                    'error': result.get('error', '')
                }))
                
                if result.get('success'):
                    print(f"[Telegram] Configured: @{result.get('bot_username')}")
            
            elif action == 'test_telegram':
                # Send test message
                result = await self.telegram.send_message(
                    "🤖 <b>Test Mesajı</b>\n\n"
                    "AI Trading Coach Telegram bildirimleri başarıyla yapılandırıldı!\n\n"
                    "Artık şu bildirimleri alacaksınız:\n"
                    "• ⚠️ Risk uyarıları\n"
                    "• 🎯 Confluence tespitleri\n"
                    "• 📈 İşlem bildirimleri"
                )
                
                await websocket.send(json.dumps({
                    'type': 'telegram_test_result',
                    'success': result
                }))
            
            elif action == 'get_prop_firm_rules':
                # Auto-detect prop firm from MT5 broker name and return rules
                try:
                    account_info = mt5.account_info()
                    if account_info:
                        broker_name = account_info.company if hasattr(account_info, 'company') else ''
                        server_name = account_info.server if hasattr(account_info, 'server') else ''
                        
                        # Optional manual override from client
                        manual_firm = data.get('firm_key')
                        
                        if manual_firm:
                            # Use manually specified firm
                            rules = get_prop_firm_rules(manual_firm)
                            if rules:
                                result = {
                                    'detected': True,
                                    'firm_key': manual_firm,
                                    'firm_name': rules.firm_name,
                                    'rules': {
                                        'max_drawdown': rules.max_drawdown,
                                        'daily_drawdown': rules.daily_drawdown,
                                        'news_trading_allowed': rules.news_trading_allowed,
                                        'news_buffer_minutes': rules.news_buffer_minutes,
                                        'weekend_holding_allowed': rules.weekend_holding_allowed,
                                        'consistency_rule': rules.consistency_rule,
                                        'min_trading_days': rules.min_trading_days,
                                        'profit_split': rules.profit_split,
                                        'special_rules': rules.special_rules
                                    },
                                    'ai_summary': rules.ai_summary,
                                    'warnings': []
                                }
                            else:
                                result = {'detected': False, 'supported_firms': get_all_prop_firms()}
                        else:
                            # Auto-detect from broker name
                            result = get_rules_for_broker(broker_name, server_name)
                        
                        result['broker_name'] = broker_name
                        result['server_name'] = server_name
                        
                        print(f"[PROP FIRM] Broker: {broker_name}, Server: {server_name}")
                        if result.get('detected'):
                            print(f"[PROP FIRM] Detected: {result.get('firm_name')}")
                        else:
                            print(f"[PROP FIRM] No match found")
                    else:
                        result = {'detected': False, 'error': 'MT5 account not connected'}
                    
                    await websocket.send(json.dumps({
                        'type': 'prop_firm_rules',
                        'data': result
                    }))
                    
                except Exception as e:
                    print(f"[PROP FIRM ERROR] {e}")
                    await websocket.send(json.dumps({
                        'type': 'prop_firm_rules',
                        'data': {'detected': False, 'error': str(e)}
                    }))
            
            elif action == 'get_supported_prop_firms':
                # Return list of all supported prop firms
                await websocket.send(json.dumps({
                    'type': 'supported_prop_firms',
                    'data': get_all_prop_firms()
                }))
            
            elif action == 'get_risk_advice':
                # Get personalized risk advice based on current state and prop firm rules
                try:
                    firm_key = data.get('firm_key')
                    current_drawdown = float(data.get('current_drawdown', 0))
                    daily_loss = float(data.get('daily_loss', 0))
                    
                    rules = get_prop_firm_rules(firm_key)
                    if rules:
                        advice = get_risk_recommendations(rules, current_drawdown, daily_loss)
                        await websocket.send(json.dumps({
                            'type': 'risk_advice',
                            'data': advice
                        }))
                    else:
                        await websocket.send(json.dumps({
                            'type': 'risk_advice',
                            'data': {'error': 'Prop firm not found'}
                        }))
                except Exception as e:
                    await websocket.send(json.dumps({
                        'type': 'risk_advice',
                        'data': {'error': str(e)}
                    }))
            
            
            elif action == 'execute_complex_trade':
                # Execute Complex Trade from AI Chat
                print(f"[TRADE] Complex Trade Request: {data}")
                
                try:
                    symbol = data.get('symbol')
                    trade_type = data.get('trade_action') # BUY or SELL
                    volume = float(data.get('volume', 0.01))
                    sl_percent = float(data.get('sl_percent', 0.5)) 
                    rr = float(data.get('rr', 1.5))
                    
                    if trade_type == 'CLOSE_ALL':
                        target_symbol = data.get('symbol', 'ALL')
                        print(f"[TRADE] Closing positions for: {target_symbol}")
                        
                        if target_symbol and target_symbol != 'ALL':
                            positions = mt5.positions_get(symbol=target_symbol)
                        else:
                            positions = mt5.positions_get() # Close EVERYTHING
                        
                        closed_count = 0
                        
                        if positions:
                            for pos in positions:
                                # Determine close type
                                tick = mt5.symbol_info_tick(pos.symbol)
                                price = tick.bid if pos.type == 0 else tick.ask
                                type_close = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
                                
                                request = {
                                    "action": mt5.TRADE_ACTION_DEAL,
                                    "symbol": pos.symbol,
                                    "volume": pos.volume,
                                    "type": type_close,
                                    "position": pos.ticket,
                                    "price": price,
                                    "deviation": 20,
                                    "magic": 112233,
                                    "comment": "AI Close All",
                                    "type_time": mt5.ORDER_TIME_GTC,
                                    "type_filling": mt5.ORDER_FILLING_FOK,
                                }
                                
                                res = mt5.order_send(request)
                                if res.retcode == mt5.TRADE_RETCODE_DONE:
                                    closed_count += 1
                                    
                        response_type = 'success'
                        response_msg = f"Closed {closed_count} positions for {target_symbol}."
                        print(f"[TRADE] {response_msg}")
                        
                        # Notify Telegram
                        try:
                            from telegram_bot import telegram_notifier
                            import asyncio
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(telegram_notifier.send_message(f"🚨 <b>POZİSYONLAR KAPATILDI</b>\n\nSembol: {target_symbol}\nKapatılan Adet: {closed_count}"))
                            loop.close()
                        except:
                            pass
                            
                        # Early return for CLOSE_ALL
                        data = {
                            'type': 'trade_result',
                            'status': response_type,
                            'message': response_msg
                        }
                        await websocket.send(json.dumps(data))
                        return
                    
                    if trade_type == 'CLOSE_PARTIAL':
                        percent = float(data.get('percent', 50))
                        print(f"[TRADE] Partial Close Request: {symbol} {percent}%")
                        
                        positions = mt5.positions_get(symbol=symbol)
                        if not positions:
                             raise ValueError(f"No open positions for {symbol}")
                        
                        total_closed_vol = 0
                        
                        for pos in positions:
                            # Calculate volume to close
                            vol_to_close = round(pos.volume * (percent / 100.0), 2)
                            if vol_to_close < 0.01: 
                                vol_to_close = 0.01 # Minimum
                            
                            if vol_to_close > pos.volume:
                                vol_to_close = pos.volume
                                
                            # Execute Close
                            tick = mt5.symbol_info_tick(pos.symbol)
                            price = tick.bid if pos.type == 0 else tick.ask
                            type_close = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
                            
                            request = {
                                "action": mt5.TRADE_ACTION_DEAL,
                                "symbol": pos.symbol,
                                "volume": vol_to_close,
                                "type": type_close,
                                "position": pos.ticket,
                                "price": price,
                                "deviation": 20,
                                "magic": 112233,
                                "comment": f"Partial {percent}%",
                                "type_time": mt5.ORDER_TIME_GTC,
                                "type_filling": mt5.ORDER_FILLING_FOK,
                            }
                            
                            res = mt5.order_send(request)
                            if res.retcode == mt5.TRADE_RETCODE_DONE:
                                total_closed_vol += vol_to_close
                                
                        response_type = 'success'
                        response_msg = f"Closed {total_closed_vol} lots ({percent}%) of {symbol}"
                        print(f"[TRADE] {response_msg}")
                        
                        # Notify Telegram
                        try:
                            from telegram_bot import telegram_notifier
                            import asyncio
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(telegram_notifier.send_message(f"✂️ <b>KISMİ KÂR ALINDI</b>\n\n{symbol}: {total_closed_vol} lot (%{percent}) kapatıldı."))
                            loop.close()
                        except:
                            pass
                            
                        # Early return
                        data = {
                            'type': 'trade_result',
                            'status': response_type,
                            'message': response_msg
                        }
                        await websocket.send(json.dumps(data))
                        return

                    if not symbol:
                        raise ValueError("Symbol is required")
                        
                    # Get current price
                    tick = mt5.symbol_info_tick(symbol)
                    if not tick:
                        raise ValueError(f"Symbol {symbol} not found")
                        
                    point = mt5.symbol_info(symbol).point
                    
                    price = tick.ask if trade_type == 'BUY' else tick.bid
                    order_type = mt5.ORDER_TYPE_BUY if trade_type == 'BUY' else mt5.ORDER_TYPE_SELL
                    
                    # Calculate SL/TP
                    sl_price = 0.0
                    tp_price = 0.0
                    
                    if trade_type == 'BUY':
                        # SL below price
                        sl_dist = price * (sl_percent / 100.0)
                        sl_price = price - sl_dist
                        
                        # TP above price (Risk * RR)
                        risk = price - sl_price
                        tp_price = price + (risk * rr)
                        
                    else:
                        # SL above price
                        sl_dist = price * (sl_percent / 100.0)
                        sl_price = price + sl_dist
                        
                        # TP below price
                        risk = sl_price - price
                        tp_price = price - (risk * rr)
                    
                    # Send Order
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": volume,
                        "type": order_type,
                        "price": price,
                        "sl": float(sl_price),
                        "tp": float(tp_price),
                        "deviation": 20,
                        "magic": 112233, 
                        "comment": "AI Chat Trade",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_FOK, # Defaulting to FOK as per test
                    }
                    
                    result = mt5.order_send(request)
                    
                    response_type = 'success'
                    response_msg = f"Trade Executed! Ticket: {getattr(result, 'order', 'Unknown')}"
                    
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        response_type = 'error'
                        response_msg = f"Trade Failed: {result.comment} ({result.retcode})"
                        
                        # Notify frontend of failure directly via toast? 
                        # Or just let the generic error handler catch it?
                        # Let's send a generic result message
                    
                    # Log
                    print(f"[TRADE] Result: {response_msg}")
                    
                    # Send feedback via Telegram automatically
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                         # Notify Telegram
                        try:
                            from telegram_bot import telegram_notifier
                            import asyncio
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(telegram_notifier.notify_trade_opened(
                                symbol=symbol.upper(),
                                direction=trade_type,
                                lot_size=volume,
                                entry_price=price,
                                sl=sl_price,
                                tp=tp_price
                            ))
                            loop.close()
                        except Exception as e:
                            print(f"[Telegram Error] {e}")

                except Exception as e:
                    print(f"[TRADE ERROR] {e}")
                    # Optionally notify frontend
            
            elif action == 'get_telegram_status':
                # Get current Telegram configuration status
                await websocket.send(json.dumps({
                    'type': 'telegram_status',
                    'enabled': self.telegram.enabled,
                    'settings': self.telegram_settings
                }))

            elif action == 'health':
                # Health check for cloud deployments (Koyeb, Railway, etc.)
                response = {
                    'type': 'health_check',
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'mt5_connected': mt5.terminal_info() is not None,
                    'version': '2.2'
                }
                await websocket.send(json.dumps(response))
            
            elif action == 'ping':
                # Heartbeat
                response = {
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }
                
                await websocket.send(json.dumps(response))
        
        except json.JSONDecodeError:
            error_response = {
                'type': 'error',
                'message': 'Invalid JSON'
            }
            await websocket.send(json.dumps(error_response))
        
        except Exception as e:
            error_response = {
                'type': 'error',
                'message': str(e)
            }
            await websocket.send(json.dumps(error_response))
    
    async def broadcast_updates(self):
        """Broadcast real-time updates to all connected clients"""
        while True:
            if self.connected_clients:
                # Get account data
                account_data = self.get_account_data()
                
                if account_data:
                    # Check risk levels and send Telegram alerts
                    await self._check_and_notify_risk(account_data)
                    
                    # Broadcast to all clients
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
                    
                    # Send to all connected clients
                    disconnected_clients = set()
                    for client in self.connected_clients:
                        try:
                            await client.send(message)
                        except websockets.exceptions.ConnectionClosed:
                            disconnected_clients.add(client)
                    
                    # Remove disconnected clients
                    for client in disconnected_clients:
                        await self.unregister_client(client)
            
            await asyncio.sleep(self.update_interval)
    
    async def _check_and_notify_risk(self, account_data):
        """Check risk levels and send Telegram notifications if needed"""
        if not self.telegram.enabled:
            return
        
        current_dd = account_data.get('current_drawdown', 0)
        max_dd = self.telegram_settings.get('max_drawdown', 10.0)
        daily_loss = abs(account_data.get('daily_profit', 0)) if account_data.get('daily_profit', 0) < 0 else 0
        daily_limit = self.telegram_settings.get('daily_limit', 500.0)
        
        # Calculate risk level
        dd_pct = (current_dd / max_dd * 100) if max_dd > 0 else 0
        daily_pct = (daily_loss / daily_limit * 100) if daily_limit > 0 else 0
        
        # Determine new risk level
        if dd_pct >= 80 or daily_pct >= 80:
            new_level = 'critical'
        elif dd_pct >= 60 or daily_pct >= 60:
            new_level = 'warning'
        else:
            new_level = 'safe'
        
        # Only notify if risk level increased
        if new_level != self.last_risk_level and new_level != 'safe':
            await self.telegram.notify_risk_warning(
                current_dd, max_dd, daily_loss, daily_limit
            )
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
    
    def _get_session_info(self):
        """Identify current ICT/Global trading session (UTC based)"""
        from datetime import datetime, time
        now_utc = datetime.utcnow().time()
        
        # ICT Killzones (Simplified UTC)
        if time(0, 0) <= now_utc < time(6, 0):
            return {"name": "ASYAKONSOLİDASYONU", "status": "LİKİDİTE BİRİKİMİ", "color": "#00d2ff"}
        elif time(7, 0) <= now_utc < time(10, 0):
            return {"name": "LONDRAAÇILIŞI", "status": "VOLATİLİTE YÜKSEK", "color": "#38ef7d"}
        elif time(12, 0) <= now_utc < time(15, 0):
            return {"name": "NEW YORK OPEN", "status": "KURUMSAL HACİM", "color": "#ff0080"}
        elif time(15, 0) <= now_utc < time(17, 0):
            return {"name": "LONDON CLOSE", "status": "TREND SONU / REVERSAL", "color": "#f45c43"}
        else:
            return {"name": "OFF-PEAK", "status": "DÜŞÜK HACİM", "color": "rgba(255,255,255,0.5)"}

    def _generate_coach_advice(self, latest, df, is_weekend):
        """Generate human-like trading advice based on SMC data"""
        if is_weekend:
             return "Haftasonu piyasalar kapalı. Pazartesi Londra açılışında likidite süpürmesini bekle."
        
        bias = latest.get('trend_bias', 0)
        is_discount = bool(latest.get('is_discount', False))
        is_premium = bool(latest.get('is_premium', False))
        has_choch = bool(latest.get('choch', False))
        
        if bias == 1: # Bullish
            if is_discount:
                return "Bias BULLISH ve İndirim bölgesindeyiz. Bullish Order Block retesti için alım fırsatı kolla."
            else:
                return "Bias BULLISH ama fiyat Pahalı (Premium) bölgede. Geri çekilme (retracement) beklemeden girme."
        elif bias == -1: # Bearish
            if is_premium:
                return "Bias BEARISH ve Premium (Satış) bölgesindeyiz. Bearish OB veya FVG girişleri için yerleş."
            else:
                return "Bias BEARISH ama fiyat İndirimli bölgede. Satış için düzeltme hareketini bekle."
        
        if has_choch:
            return "Trend dönüşü (CHoCH) saptandı. Piyasa yapısı değişiyor, yeni bias onayını bekle."
            
        return "Piyasa şu an karar aşamasında (Equilibrium). Net bir BOS veya Swings kırılımı bekle."

    async def start(self):
        """Start the WebSocket server"""
        # Start broadcast task
        broadcast_task = asyncio.create_task(self.broadcast_updates())
        
        # Start WebSocket server
        async with websockets.serve(self.handler, self.host, self.port):
            print(f"[START] MT5 WebSocket Server started on ws://{self.host}:{self.port}")
            print("[WAIT] Waiting for connections...")
            await asyncio.Future()  # Run forever


def main():
    """Main entry point"""
    print("=" * 60)
    print("AI Trading Coach - MT5 Auto-Connect Server")
    print("Version: 2.2 (Config Module Enabled)")
    print("=" * 60)
    
    # Validate settings and show warnings
    warnings = validate_settings()
    for warning in warnings:
        print(warning)
    
    if settings.DEBUG:
        print(f"[DEBUG] Debug mode enabled")
        print(f"[DEBUG] Host: {settings.HOST}, Port: {settings.PORT}")
    
    # Create server with config
    server = MT5AutoConnectServer(host=settings.HOST, port=settings.PORT)
    
    # Initialize MT5
    if not server.initialize_mt5():
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
        mt5.shutdown()
        print("[CLOSE] MT5 connection closed")


if __name__ == "__main__":
    main()
