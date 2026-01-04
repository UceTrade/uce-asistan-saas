"""
Turkish Natural Language Understanding for Trading Strategies
Extracts indicators, conditions, and parameters from Turkish descriptions
"""
import re


class TurkishNLU:
    """Parse Turkish trading strategy descriptions"""
    
    def __init__(self):
        # Indicator keywords (Turkish and English)
        self.indicators = {
            'rsi': ['rsi', 'göreceli güç', 'relative strength', 'rsi indikatörü'],
            'sma': ['sma', 'basit hareketli ortalama', 'simple moving average', 'hareketli ortalama'],
            'ema': ['ema', 'üstel hareketli ortalama', 'exponential moving average'],
            'macd': ['macd', 'macd indikatörü'],
            'bollinger': ['bollinger', 'bollinger bands', 'bollinger bantları'],
            'stochastic': ['stochastic', 'stokastik'],
            'atr': ['atr', 'average true range'],
            'fvg': ['fvg', 'fair value gap', 'boşluk'],
            'order_block': ['order block', 'ob', 'sipariş bloğu']
        }
        
        # Action keywords
        self.actions = {
            'buy': ['al', 'alış', 'long', 'buy', 'satın al', 'gir'],
            'sell': ['sat', 'satış', 'short', 'sell', 'kısa', 'çık']
        }
        
        # Condition keywords
        self.conditions = {
            'above': ['üstünde', 'üzerinde', 'above', 'over', 'yukarı', 'yukarıda'],
            'below': ['altında', 'below', 'under', 'aşağı', 'aşağıda'],
            'cross_up': ['yukarı kesme', 'yukarı kes', 'cross up', 'yukarı geç'],
            'cross_down': ['aşağı kesme', 'aşağı kes', 'cross down', 'aşağı geç'],
            'equal': ['eşit', 'equal', '='],
            'greater': ['büyük', 'greater', '>'],
            'less': ['küçük', 'less', '<']
        }
        
        # Number patterns
        self.number_pattern = r'\d+(?:\.\d+)?'
    
    def parse(self, text):
        """
        Parse Turkish trading description
        
        Returns:
            dict with indicators, conditions, actions, parameters, confidence
        """
        text_lower = text.lower()
        
        result = {
            'indicators': [],
            'conditions': [],
            'actions': [],
            'parameters': {},
            'confidence': 0.0,
            'original_text': text
        }
        
        # Extract indicators
        for indicator, keywords in self.indicators.items():
            for keyword in keywords:
                if keyword in text_lower:
                    result['indicators'].append(indicator)
                    break
        
        # Extract actions
        for action, keywords in self.actions.items():
            for keyword in keywords:
                if keyword in text_lower:
                    result['actions'].append(action)
                    break
        
        # Extract conditions
        for condition, keywords in self.conditions.items():
            for keyword in keywords:
                if keyword in text_lower:
                    result['conditions'].append(condition)
                    break
        
        # Extract numbers (potential thresholds)
        numbers = re.findall(self.number_pattern, text)
        if numbers:
            result['parameters']['thresholds'] = [float(n) for n in numbers]
        
        # Calculate confidence
        confidence = 0.0
        if result['indicators']:
            confidence += 0.4
        if result['actions']:
            confidence += 0.3
        if result['conditions']:
            confidence += 0.2
        if result['parameters']:
            confidence += 0.1
        
        result['confidence'] = min(confidence, 1.0)
        
        return result
    
    def enhance_prompt(self, original_description, parsed_data):
        """
        Enhance AI prompt with extracted parameters
        
        Args:
            original_description: Original user input
            parsed_data: Parsed NLU data
        
        Returns:
            Enhanced description string
        """
        if parsed_data['confidence'] < 0.5:
            # Low confidence, return original
            return original_description
        
        # Build enhanced description
        enhanced = original_description + "\n\n**Detected Parameters:**\n"
        
        if parsed_data['indicators']:
            enhanced += f"- Indicators: {', '.join(parsed_data['indicators']).upper()}\n"
        
        if parsed_data['actions']:
            actions_str = ', '.join([a.upper() for a in parsed_data['actions']])
            enhanced += f"- Actions: {actions_str}\n"
        
        if parsed_data['conditions']:
            conditions_str = ', '.join(parsed_data['conditions'])
            enhanced += f"- Conditions: {conditions_str}\n"
        
        if 'thresholds' in parsed_data['parameters']:
            thresholds_str = ', '.join([str(t) for t in parsed_data['parameters']['thresholds']])
            enhanced += f"- Threshold values: {thresholds_str}\n"
        
        return enhanced
    
    def suggest_template(self, parsed_data):
        """
        Suggest a template based on parsed data
        
        Returns:
            template_id or None
        """
        indicators = set(parsed_data['indicators'])
        
        # RSI template
        if 'rsi' in indicators:
            return 'rsi_oversold'
        
        # SMA Crossover
        if 'sma' in indicators and len(parsed_data['parameters'].get('thresholds', [])) >= 2:
            return 'sma_crossover'
        
        # ICT FVG
        if 'fvg' in indicators or 'order_block' in indicators:
            return 'ict_fvg'
        
        # Bollinger Bands
        if 'bollinger' in indicators:
            return 'mean_reversion'
        
        return None


# Example usage
if __name__ == '__main__':
    nlu = TurkishNLU()
    
    # Test cases
    tests = [
        "RSI 30'un altında al, 70'in üstünde sat",
        "SMA 50, SMA 200'ü yukarı keserse al",
        "Fiyat Bollinger bandının alt bandına değerse alış yap",
        "Fair Value Gap oluştuğunda trade al"
    ]
    
    for test in tests:
        print(f"\nInput: {test}")
        result = nlu.parse(test)
        print(f"Indicators: {result['indicators']}")
        print(f"Actions: {result['actions']}")
        print(f"Conditions: {result['conditions']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Suggested template: {nlu.suggest_template(result)}")
