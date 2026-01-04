"""
Strategy Manager - Save and Load User Strategies
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Optional

class StrategyManager:
    def __init__(self, data_dir='user_data'):
        self.data_dir = data_dir
        self.strategies_file = os.path.join(data_dir, 'strategies.json')
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        if not os.path.exists(self.strategies_file):
            with open(self.strategies_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
                
    def get_strategies(self) -> List[Dict]:
        """Get all saved strategies"""
        try:
            with open(self.strategies_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading strategies: {e}")
            return []
            
    def save_strategy(self, name: str, code: str, summary: str, timeframe: str) -> bool:
        """Save a new strategy"""
        try:
            strategies = self.get_strategies()
            
            # Create new strategy object
            new_strategy = {
                'id': int(datetime.now().timestamp()), # Simple ID from timestamp
                'name': name,
                'code': code,
                'summary': summary,
                'timeframe': timeframe,
                'created_at': datetime.now().isoformat()
            }
            
            strategies.append(new_strategy)
            
            with open(self.strategies_file, 'w', encoding='utf-8') as f:
                json.dump(strategies, f, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Error saving strategy: {e}")
            return False
            
    def delete_strategy(self, strategy_id: int) -> bool:
        """Delete a strategy by ID"""
        try:
            strategies = self.get_strategies()
            strategies = [s for s in strategies if s['id'] != strategy_id]
            
            with open(self.strategies_file, 'w', encoding='utf-8') as f:
                json.dump(strategies, f, indent=4, ensure_ascii=False)
                
            return True
        except Exception as e:
            print(f"Error deleting strategy: {e}")
            return False
            
    def get_strategy(self, strategy_id: int) -> Optional[Dict]:
        """Get single strategy by ID"""
        strategies = self.get_strategies()
        for s in strategies:
            if s['id'] == strategy_id:
                return s
        return None
    
    def analyze_patterns(self):
        """
        Analyze user's strategy patterns (Phase 4: Context-Aware Learning)
        
        Returns:
            dict with favorite indicators, timeframes, complexity
        """
        strategies = self.get_strategies()
        
        if not strategies:
            return {
                'favorite_indicators': [],
                'favorite_timeframes': [],
                'avg_complexity': 'medium',
                'total_strategies': 0
            }
        
        # Extract patterns
        indicators = {}
        timeframes = {}
        
        for s in strategies:
            code = s.get('code', '')
            
            # Count indicator usage
            if 'rsi' in code.lower():
                indicators['RSI'] = indicators.get('RSI', 0) + 1
            if 'sma' in code.lower() or 'moving average' in code.lower():
                indicators['SMA'] = indicators.get('SMA', 0) + 1
            if 'ema' in code.lower():
                indicators['EMA'] = indicators.get('EMA', 0) + 1
            if 'macd' in code.lower():
                indicators['MACD'] = indicators.get('MACD', 0) + 1
            if 'bollinger' in code.lower():
                indicators['Bollinger'] = indicators.get('Bollinger', 0) + 1
            
            # Count timeframe usage
            tf = s.get('timeframe', 'H1')
            timeframes[tf] = timeframes.get(tf, 0) + 1
        
        # Sort by frequency
        sorted_indicators = sorted(indicators.items(), key=lambda x: x[1], reverse=True)
        sorted_timeframes = sorted(timeframes.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'favorite_indicators': [ind for ind, _ in sorted_indicators[:3]],
            'favorite_timeframes': [tf for tf, _ in sorted_timeframes[:2]],
            'avg_complexity': 'medium',  # Could calculate based on code length
            'total_strategies': len(strategies)
        }
    
    def get_similar_strategies(self, description):
        """
        Find similar past strategies based on description
        
        Returns:
            list of similar strategies
        """
        strategies = self.get_strategies()
        similar = []
        
        desc_lower = description.lower()
        keywords = desc_lower.split()
        
        for s in strategies:
            # Simple keyword matching
            s_summary = s.get('summary', '').lower()
            s_code = s.get('code', '').lower()
            
            match_count = sum(1 for kw in keywords if kw in s_summary or kw in s_code)
            
            if match_count > 0:
                similar.append({
                    'strategy': s,
                    'match_score': match_count / len(keywords)
                })
        
        # Sort by match score
        similar.sort(key=lambda x: x['match_score'], reverse=True)
        
        return [s['strategy'] for s in similar[:3]]  # Top 3
