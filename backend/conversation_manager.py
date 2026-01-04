"""
Conversation Manager - Multi-step interactive strategy creation
"""
import json
from datetime import datetime


class ConversationManager:
    """Manage multi-step conversations for strategy creation"""
    
    def __init__(self):
        self.sessions = {}  # session_id -> conversation_state
    
    def start_conversation(self, session_id, initial_description):
        """
        Start new conversation
        
        Returns:
            First question or None if no questions needed
        """
        self.sessions[session_id] = {
            'state': 'initial',
            'description': initial_description,
            'parameters': {},
            'questions_asked': [],
            'answers': {},
            'created_at': datetime.now().isoformat()
        }
        
        return self.get_next_question(session_id)
    
    def get_next_question(self, session_id):
        """
        Get next clarifying question
        
        Returns:
            dict with question, type, options or None if complete
        """
        if session_id not in self.sessions:
            return None
        
        state = self.sessions[session_id]
        params = state['parameters']
        asked = state['questions_asked']
        
        # Question 1: Timeframe
        if 'timeframe' not in params and 'timeframe' not in asked:
            state['questions_asked'].append('timeframe')
            return {
                'id': 'timeframe',
                'question': 'Hangi zaman diliminde çalışmasını istersin?',
                'type': 'select',
                'options': [
                    {'value': 'M5', 'label': 'M5 (5 Dakika) - Scalping'},
                    {'value': 'M15', 'label': 'M15 (15 Dakika) - Kısa Vade'},
                    {'value': 'H1', 'label': 'H1 (1 Saat) - Orta Vade'},
                    {'value': 'H4', 'label': 'H4 (4 Saat) - Swing'},
                    {'value': 'D1', 'label': 'D1 (Günlük) - Uzun Vade'}
                ]
            }
        
        # Question 2: Risk Level
        if 'risk_level' not in params and 'risk_level' not in asked:
            state['questions_asked'].append('risk_level')
            return {
                'id': 'risk_level',
                'question': 'Risk seviyesi nasıl olsun?',
                'type': 'select',
                'options': [
                    {'value': 'low', 'label': 'Düşük - Muhafazakar (Win rate > %60)'},
                    {'value': 'medium', 'label': 'Orta - Dengeli (Win rate ~%50)'},
                    {'value': 'high', 'label': 'Yüksek - Agresif (Büyük R:R)'}
                ]
            }
        
        # Question 3: Stop Loss Profile
        if 'stop_loss_profile' not in params and 'stop_loss_profile' not in asked:
            state['questions_asked'].append('stop_loss_profile')
            return {
                'id': 'stop_loss_profile',
                'question': 'Stop Loss profili nasıl olsun? (ATR bazlı)',
                'type': 'select',
                'options': [
                    {'value': 'hard', 'label': '🔴 Hard Stop - Sıkı (0.5x ATR) - Hızlı kes'},
                    {'value': 'mid', 'label': '🟡 Mid Stop - Dengeli (1x ATR) - Standart'},
                    {'value': 'low', 'label': '🟢 Low Stop - Geniş (2x ATR) - Nefes ver'}
                ]
            }

        # Question 4: Trading Style
        if 'trading_style' not in params and 'trading_style' not in asked:
            state['questions_asked'].append('trading_style')
            return {
                'id': 'trading_style',
                'question': 'Hangi tarz trading yapmak istersin?',
                'type': 'select',
                'options': [
                    {'value': 'trend', 'label': 'Trend Takibi - Trendle git'},
                    {'value': 'reversal', 'label': 'Reversal - Dönüş noktalarını yakala'},
                    {'value': 'breakout', 'label': 'Breakout - Kırılımları yakala'},
                    {'value': 'range', 'label': 'Range Trading - Yatay piyasada al-sat'}
                ]
            }
        
        # All questions answered
        return None
    
    def process_answer(self, session_id, question_id, answer):
        """
        Process user answer and update state
        
        Returns:
            True if answer accepted
        """
        if session_id not in self.sessions:
            return False
        
        state = self.sessions[session_id]
        state['parameters'][question_id] = answer
        state['answers'][question_id] = answer
        
        return True
    
    def generate_final_prompt(self, session_id):
        """
        Generate enhanced prompt from conversation
        
        Returns:
            Enhanced description string
        """
        if session_id not in self.sessions:
            return None
        
        state = self.sessions[session_id]
        """Generate enhanced prompt from collected answers"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        answers = session['answers']
        
        # Map answers to descriptions
        risk_map = {
            'low': 'Conservative (high win rate, tight stops)',
            'medium': 'Balanced (moderate risk-reward)',
            'high': 'Aggressive (high risk-reward ratio)'
        }
        
        style_map = {
            'trend': 'Trend following - use moving averages and trend indicators',
            'reversal': 'Reversal trading - look for overbought/oversold conditions',
            'breakout': 'Breakout trading - detect range breakouts',
            'range': 'Range trading - buy support, sell resistance'
        }
        
        stop_loss_map = {
            'hard': '0.5x ATR (tight stop, quick exit)',
            'mid': '1x ATR (standard stop)',
            'low': '2x ATR (wide stop, room to breathe)'
        }
        
        # Get stop loss multiplier
        sl_profile = answers.get('stop_loss_profile', 'mid')
        sl_multiplier = '0.5' if sl_profile == 'hard' else '1' if sl_profile == 'mid' else '2'
        
        enhanced_prompt = f"""{session['description']}

**User Preferences:**
- Timeframe: {answers.get('timeframe', 'H1')}
- Risk Level: {risk_map.get(answers.get('risk_level'), 'Balanced')}
- Stop Loss Profile: {stop_loss_map.get(sl_profile, 'Standard')}
- Trading Style: {style_map.get(answers.get('trading_style'), 'Trend following')}

**CRITICAL - ATR-Based Stop Loss Implementation:**
You MUST implement ATR-based stop loss with these exact specifications:
1. Calculate ATR(14): atr = (data['high'] - data['low']).rolling(14).mean()
2. Stop Loss Distance: {sl_multiplier} * ATR
3. In your strategy function, add these lines:
   - atr = (data['high'] - data['low']).rolling(14).mean()
   - stop_distance = {sl_multiplier} * atr.iloc[-1]
   - For LONG: stop_loss = entry_price - stop_distance
   - For SHORT: stop_loss = entry_price + stop_distance

Generate a complete strategy with ATR-based stop loss included in the code."""
        
        return enhanced_prompt
    
    def get_session_state(self, session_id):
        """Get current session state"""
        return self.sessions.get(session_id)
    
    def end_session(self, session_id):
        """End and cleanup session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False


# Example usage
if __name__ == '__main__':
    manager = ConversationManager()
    
    # Simulate conversation
    session_id = 'test_session_1'
    
    # Start
    question = manager.start_conversation(session_id, "RSI stratejisi istiyorum")
    print(f"Q1: {question['question']}")
    print(f"Options: {[opt['label'] for opt in question['options']]}")
    
    # Answer 1
    manager.process_answer(session_id, 'timeframe', 'H1')
    question = manager.get_next_question(session_id)
    print(f"\nQ2: {question['question']}")
    
    # Answer 2
    manager.process_answer(session_id, 'risk_level', 'medium')
    question = manager.get_next_question(session_id)
    print(f"\nQ3: {question['question']}")
    
    # Answer 3
    manager.process_answer(session_id, 'trading_style', 'trend')
    question = manager.get_next_question(session_id)
    print(f"\nNext question: {question}")
    
    # Generate final prompt
    final_prompt = manager.generate_final_prompt(session_id)
    print(f"\nFinal Prompt:\n{final_prompt}")
