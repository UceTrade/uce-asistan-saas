"""
Signal Confluence Finder - Professional Implementation
Find moments when multiple trading strategies agree on the same signal
"""

import pandas as pd
import numpy as np
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Tuple
import traceback


class SignalConfluenceFinder:
    """
    Professional-grade signal confluence detection system
    
    Features:
    - Unlimited strategy support
    - Parallel execution
    - Confluence scoring
    - Strength classification
    - Performance tracking
    """
    
    def __init__(self):
        self.strategies = []
        self.results_cache = {}
        self.performance_stats = {}
    
    def add_strategy(self, name: str, code: str, metadata: Dict = None):
        """
        Add a strategy to the confluence analysis
        
        Args:
            name: Strategy identifier
            code: Python strategy code
            metadata: Optional metadata (template_id, created_date, etc.)
        """
        strategy = {
            'name': name,
            'code': code,
            'metadata': metadata or {},
            'added_at': datetime.now().isoformat()
        }
        self.strategies.append(strategy)
        print(f"[CONFLUENCE] Added strategy: {name}")
    
    def clear_strategies(self):
        """Clear all strategies"""
        self.strategies = []
        self.results_cache = {}
        print("[CONFLUENCE] All strategies cleared")
    
    def run_all_strategies(self, data: pd.DataFrame, max_workers: int = 10) -> Dict:
        """
        Run all strategies in parallel on the same data
        
        Args:
            data: OHLCV DataFrame
            max_workers: Maximum parallel threads
        
        Returns:
            {
                'signals': {timestamp: {strategy_name: signal}},
                'errors': {strategy_name: error_message},
                'execution_times': {strategy_name: seconds}
            }
        """
        print(f"[CONFLUENCE] Running {len(self.strategies)} strategies in parallel...")
        
        all_signals = {}
        errors = {}
        execution_times = {}
        
        # Parallel execution
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_strategy = {
                executor.submit(self._run_single_strategy, strategy, data): strategy
                for strategy in self.strategies
            }
            
            for future in as_completed(future_to_strategy):
                strategy = future_to_strategy[future]
                strategy_name = strategy['name']
                
                try:
                    result = future.result()
                    
                    if result['success']:
                        # Merge signals into timeline
                        for timestamp, signal in result['signals'].items():
                            if timestamp not in all_signals:
                                all_signals[timestamp] = {}
                            all_signals[timestamp][strategy_name] = signal
                        
                        execution_times[strategy_name] = result['execution_time']
                        print(f"[CONFLUENCE] ✓ {strategy_name} completed ({result['execution_time']:.2f}s)")
                    else:
                        errors[strategy_name] = result['error']
                        print(f"[CONFLUENCE] ✗ {strategy_name} failed: {result['error']}")
                
                except Exception as e:
                    errors[strategy_name] = str(e)
                    print(f"[CONFLUENCE] ✗ {strategy_name} exception: {str(e)}")
        
        return {
            'signals': all_signals,
            'errors': errors,
            'execution_times': execution_times,
            'total_strategies': len(self.strategies),
            'successful_strategies': len(self.strategies) - len(errors)
        }
    
    def _run_single_strategy(self, strategy: Dict, data: pd.DataFrame) -> Dict:
        """
        Execute a single strategy
        
        Returns:
            {
                'success': bool,
                'signals': {timestamp: 'BUY'/'SELL'/'HOLD'},
                'execution_time': float,
                'error': str (if failed)
            }
        """
        start_time = datetime.now()
        
        try:
            # Create execution environment
            exec_globals = {
                'pd': pd,
                'np': np,
                'data': data.copy()
            }
            
            # Execute strategy code
            exec(strategy['code'], exec_globals)
            
            # Get strategy function
            if 'strategy' not in exec_globals:
                return {
                    'success': False,
                    'error': 'Strategy function not found. Must define strategy(data, position)',
                    'execution_time': 0
                }
            
            strategy_func = exec_globals['strategy']
            
            # Run strategy on each bar
            signals = {}
            position = 0
            
            for i in range(len(data)):
                current_data = data.iloc[:i+1].copy()
                
                try:
                    signal = strategy_func(current_data, position)
                    
                    # Validate signal
                    if signal not in ['BUY', 'SELL', 'HOLD']:
                        signal = 'HOLD'
                    
                    timestamp = data.index[i]
                    signals[timestamp] = signal
                    
                    # Update position
                    if signal == 'BUY':
                        position = 1
                    elif signal == 'SELL':
                        position = -1
                
                except Exception as e:
                    # If strategy fails on a bar, mark as HOLD
                    timestamp = data.index[i]
                    signals[timestamp] = 'HOLD'
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                'success': True,
                'signals': signals,
                'execution_time': execution_time,
                'error': None
            }
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return {
                'success': False,
                'signals': {},
                'execution_time': execution_time,
                'error': f"{type(e).__name__}: {str(e)}"
            }
    
    def find_confluences(self, signals: Dict, min_agreement: float = 0.6) -> List[Dict]:
        """
        Find moments with high strategy agreement
        
        Args:
            signals: {timestamp: {strategy_name: signal}}
            min_agreement: Minimum agreement threshold (0.0 to 1.0)
        
        Returns:
            List of confluence moments sorted by strength
        """
        print(f"[CONFLUENCE] Analyzing confluences (min agreement: {min_agreement*100:.0f}%)...")
        
        confluences = []
        
        for timestamp, strategy_signals in signals.items():
            confluence = self._calculate_confluence(timestamp, strategy_signals, min_agreement)
            
            if confluence:
                confluences.append(confluence)
        
        # Sort by agreement (strongest first)
        confluences.sort(key=lambda x: x['agreement'], reverse=True)
        
        print(f"[CONFLUENCE] Found {len(confluences)} confluence moments")
        return confluences
    
    def _calculate_confluence(self, timestamp, strategy_signals: Dict, min_agreement: float) -> Dict:
        """
        Calculate confluence score for a single moment
        
        Returns:
            Confluence dict or None if below threshold
        """
        total = len(strategy_signals)
        
        if total == 0:
            return None
        
        # Count signals
        buy_count = sum(1 for s in strategy_signals.values() if s == 'BUY')
        sell_count = sum(1 for s in strategy_signals.values() if s == 'SELL')
        hold_count = sum(1 for s in strategy_signals.values() if s == 'HOLD')
        
        # Determine dominant signal
        max_count = max(buy_count, sell_count, hold_count)
        
        if max_count == buy_count and buy_count > 0:
            dominant_signal = 'BUY'
            agreeing_count = buy_count
        elif max_count == sell_count and sell_count > 0:
            dominant_signal = 'SELL'
            agreeing_count = sell_count
        else:
            # HOLD or mixed - skip
            return None
        
        # Calculate agreement percentage
        agreement = agreeing_count / total
        
        # Check threshold
        if agreement < min_agreement:
            return None
        
        # Get agreeing and disagreeing strategies
        agreeing = [name for name, sig in strategy_signals.items() if sig == dominant_signal]
        disagreeing = [name for name, sig in strategy_signals.items() if sig != dominant_signal]
        
        # Determine strength
        strength, strength_icon = self._get_strength_level(agreement)
        
        return {
            'timestamp': timestamp,
            'signal': dominant_signal,
            'agreement': agreement,
            'agreeing_count': agreeing_count,
            'total_count': total,
            'strategies_agreeing': agreeing,
            'strategies_disagreeing': disagreeing,
            'strength': strength,
            'strength_icon': strength_icon,
            'buy_count': buy_count,
            'sell_count': sell_count,
            'hold_count': hold_count
        }
    
    def _get_strength_level(self, agreement: float) -> Tuple[str, str]:
        """
        Classify confluence strength
        
        Returns:
            (strength_name, icon)
        """
        if agreement >= 0.95:
            return 'VERY_STRONG', '🔥'
        elif agreement >= 0.80:
            return 'STRONG', '💪'
        elif agreement >= 0.65:
            return 'MEDIUM', '👍'
        elif agreement >= 0.50:
            return 'WEAK', '🤏'
        else:
            return 'VERY_WEAK', '❌'
    
    def generate_confluence_report(self, confluences: List[Dict]) -> str:
        """
        Generate human-readable confluence report
        
        Returns:
            Formatted report string
        """
        if not confluences:
            return "No confluences found with current settings."
        
        report = f"📊 **Signal Confluence Report**\n\n"
        report += f"Total Confluences Found: {len(confluences)}\n\n"
        
        # Group by strength
        very_strong = [c for c in confluences if c['strength'] == 'VERY_STRONG']
        strong = [c for c in confluences if c['strength'] == 'STRONG']
        medium = [c for c in confluences if c['strength'] == 'MEDIUM']
        
        if very_strong:
            report += f"🔥 **VERY STRONG ({len(very_strong)}):**\n"
            for c in very_strong[:5]:  # Top 5
                report += f"  - {c['timestamp']}: {c['signal']} ({c['agreement']*100:.0f}%)\n"
            report += "\n"
        
        if strong:
            report += f"💪 **STRONG ({len(strong)}):**\n"
            for c in strong[:5]:
                report += f"  - {c['timestamp']}: {c['signal']} ({c['agreement']*100:.0f}%)\n"
            report += "\n"
        
        if medium:
            report += f"👍 **MEDIUM ({len(medium)}):**\n"
            for c in medium[:3]:
                report += f"  - {c['timestamp']}: {c['signal']} ({c['agreement']*100:.0f}%)\n"
        
        return report
    
    def get_strategy_performance(self, confluences: List[Dict]) -> Dict:
        """
        Analyze which strategies contribute most to confluences
        
        Returns:
            {
                strategy_name: {
                    'confluence_count': int,
                    'agreement_rate': float,
                    'reliability_score': float
                }
            }
        """
        performance = {}
        
        for strategy in self.strategies:
            name = strategy['name']
            
            # Count how many times this strategy was in agreement
            in_agreement = sum(1 for c in confluences if name in c['strategies_agreeing'])
            total_confluences = len(confluences)
            
            if total_confluences > 0:
                agreement_rate = in_agreement / total_confluences
            else:
                agreement_rate = 0
            
            performance[name] = {
                'confluence_count': in_agreement,
                'total_confluences': total_confluences,
                'agreement_rate': agreement_rate,
                'reliability_score': agreement_rate * 100
            }
        
        return performance


# Example usage
if __name__ == '__main__':
    # Test with sample data
    finder = SignalConfluenceFinder()
    
    # Add sample strategies
    rsi_strategy = """
def strategy(data, position):
    if len(data) < 14:
        return 'HOLD'
    
    # Simple RSI
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    if rsi.iloc[-1] < 30:
        return 'BUY'
    elif rsi.iloc[-1] > 70:
        return 'SELL'
    return 'HOLD'
"""
    
    finder.add_strategy('RSI', rsi_strategy)
    
    print("\n[OK] Signal Confluence Finder initialized")
    print(f"Strategies loaded: {len(finder.strategies)}")
