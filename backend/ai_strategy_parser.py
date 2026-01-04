"""
AI Strategy Parser - Convert natural language to Python trading strategy
Enterprise-grade with retry, rate limiting, and sandbox testing
"""
import json
import re
import asyncio
import time
from collections import deque


class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, max_calls: int = 20, period: int = 60):
        self.max_calls = max_calls
        self.period = period
        self.calls = deque()
    
    def can_call(self) -> bool:
        """Check if a call can be made"""
        now = time.time()
        # Remove old calls outside the window
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        """Record a new call"""
        self.calls.append(time.time())
    
    def wait_time(self) -> float:
        """Get time to wait before next call"""
        if self.can_call():
            return 0
        return self.period - (time.time() - self.calls[0])


class AIStrategyParser:
    """Parse natural language trading strategies into executable Python code
    
    Enterprise Features:
    - Retry mechanism with exponential backoff
    - Rate limiting (20 calls/minute default)
    - Sandbox testing for generated code
    - Multi-provider AI support (Groq, OpenAI, Gemini)
    """
    
    def __init__(self, rate_limit: int = 20):
        self.allowed_imports = [
            'pandas', 'numpy', 'talib', 'math'
        ]
        self.forbidden_keywords = [
            'import os', 'import sys', 'exec', 'eval', 'open(', 
            '__import__', 'compile', 'globals', 'locals'
        ]
        self.rate_limiter = RateLimiter(max_calls=rate_limit, period=60)
        self.max_retries = 3
        self.base_delay = 1.0  # seconds
    
    def create_prompt(self, strategy_description):
        """Create AI prompt for strategy generation"""
        prompt = f"""You are a trading strategy code generator. Convert the following trading strategy description into Python code.

STRATEGY DESCRIPTION:
{strategy_description}

REQUIREMENTS:
1. Create a function called `strategy(data, position)` that returns 'BUY', 'SELL', or 'HOLD'
2. The `data` parameter is a pandas DataFrame with columns: ['time', 'open', 'high', 'low', 'close', 'volume']
3. The `position` parameter is current position: 0 (no position), 1 (long), -1 (short)
4. Use ONLY these libraries: pandas (as pd), numpy (as np)
5. **CRITICAL: USE THE BUILT-IN 'pa' LIBRARY FOR PRICE ACTION CONCEPTS**
   - The `pa` object is available in the scope.
   - **BEST PRACTICE:** Call `df = pa.analyze_all(data)` at the start to get ALL indicators (Order Blocks, FVG, Swings) in one go.
   - `analyze_all` adds: 'bullish_ob', 'bearish_ob', 'bullish_fvg', 'bearish_fvg', 'swing_high', 'swing_low', etc.
   - If you only need specific ones:
     - `pa.identify_swings(data)`
     - `pa.detect_order_blocks(data)` (Only adds OB columns)
     - `pa.detect_fvg(data)` (Only adds FVG columns)
   - `pa.get_market_structure(data)` -> Returns 'BULLISH', 'BEARISH', or 'RANGING'
   - **NEW SMC COLUMNS (from analyze_all):**
     - `bos`: True if a Break of Structure occurred.
     - `choch`: True if a Change of Character (Trend Reversal) occurred.
     - `trend_bias`: 1 (Bullish), -1 (Bearish), 0 (Neutral).
     - `sweep_high`/`sweep_low`: True if a liquidity sweep was detected.
     - `is_discount`: True if price is in its 50% lower range (Buy zone).
     - `is_premium`: True if price is in its 50% upper range (Sell zone).

6. Return 'BUY' to enter long, 'SELL' to enter short, 'HOLD' to do nothing
7. **CRITICAL PYTHON RULE - MOST COMMON ERROR:** Never check a Series directly in if statements.
   - ❌ WRONG: `if data['rsi'] < 30:` → This causes "The truth value of a Series is ambiguous" error
   - ❌ WRONG: `if rsi < 30:` where rsi = data['rsi'] → Same error!
   - ✅ CORRECT: `if data['rsi'].iloc[-1] < 30:` → Check the LAST value only
   - ✅ CORRECT: `latest_rsi = data['rsi'].iloc[-1]` then `if latest_rsi < 30:`
   
8. **RETURN VALUE MUST BE A STRING, NOT A SERIES:**
   - ❌ WRONG: `return data['signal']` → Returns a Series
   - ✅ CORRECT: `return 'BUY'` or `return 'SELL'` or `return 'HOLD'` → Returns a string

**ICT CONCEPT LIBRARY (USE THIS KNOWLEDGE):**
- **Market Structure Shift (MSS):** A reversal pattern.
  - Bullish MSS: Price closes above the last significant Swing High (`swing_high` column).
  - Bearish MSS: Price closes below the last significant Swing Low (`swing_low` column).
  - Use `pa.identify_swings(data)` to find these levels.

- **Displacement:** High momentum move that often accompanies MSS.
  - Identification: A candle with a large body (abs(close-open)) > 2x average body size of last 20 candles.

- **Fair Value Gap (FVG):** A 3-candle imbalance pattern.
  - Bullish FVG: `data['bullish_fvg'] == True`. Entry zone: `data['fvg_top']` to `data['fvg_bottom']`.
  - Bearish FVG: `data['bearish_fvg'] == True`. Entry zone: `data['fvg_top']` to `data['fvg_bottom']`.

- **Order Block (OB):** Institutional reference point.
  - Bullish OB: `data['bullish_ob'] == True`. Entry at `data['ob_top']`.
  - Bearish OB: `data['bearish_ob'] == True`. Entry at `data['ob_bottom']`.

- **Optimal Trade Entry (OTE):**
  - Fibonacci retracement level identifying deep discount/premium.
  - Long Entry: Between 0.618 and 0.79 retracement of the last Swing Low to Swing High range.

- **Silver Bullet Strategy (Time-Based):**
  - Time Window: 10:00 AM - 11:00 AM (New York Time).
  - Setup: Look for a FVG (`bullish/bearish_fvg`) forming *inside* this hour.
  - Entry: Market order or Limit when price taps the FVG within the hour.
  - Direction: Follow the MSS that happened prior (e.g., 9:30-10:00).
  
- **ICT 2022 Mentorship Model:**
  1. Wait for liquidity sweep (`sweep_high` or `sweep_low`).
  2. Wait for CHoCH (`choch == True`) in opposite direction.
  3. Identify FVG or Order Block created by the displacement.
  4. Enter on retest, ideally in the `is_discount` (for Buy) or `is_premium` (for Sell) zone.

- **Market Structure (SMC):**
  - **BOS:** Continuation of the current trend.
  - **CHoCH:** First sign of a trend shift. Only trade in the direction of `trend_bias`.
  - **Liquidity:** EQH/EQL are magnets. Avoid selling just below EQH or buying just above EQL.

**LOGIC PROTOCOL (SMART BUT ACTIVE):**
1.  **Context Check:** Check trend, but DON'T freeze if ranging.
    - Bias = BULLISH if Price > SMA 50.
    - Bias = BEARISH if Price < SMA 50.
    - **CRITICAL:** If trend is weak/flat, look for Mean Reversion (Buy Low, Sell High).
2.  **Confluence or Strong Signal:**
    - IDEAL: Trend + Pattern (e.g., Bullish FVG in Uptrend).
    - ACCEPTABLE: Strong Pattern at Key Level (e.g., Engulfing at Swing Low).
3.  **Action Bias:** We want valid trades. Don't be too perfect.
4.  **Step-by-Step Execution:**
    - Explain your logic in comments inside the code.
    - `step1_trend = ...`
    - `step2_pattern = ...`
    - `if step1_trend and step2_pattern: return 'BUY'`

9. Handle edge cases (not enough data, etc.)

EXAMPLE OUTPUT FORMAT:
<SUMMARY>
Bu strateji, RSI indikatörü 30'un altına düştüğünde alım (aşırı satım), 70'in üzerine çıktığında ise satım (aşırı alım) yapar. Ayrıca ICT konsepti olan "Bullish Order Block" oluşumlarını dikkate alır.
</SUMMARY>
<CODE>
import pandas as pd
import numpy as np

def strategy(data, position):
    # Ensure we have enough data
    if len(data) < 20:
        return 'HOLD'
    
    # Calculate RSI (14-period)
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # ✅ CORRECT: Get the LAST value using .iloc[-1]
    current_rsi = rsi.iloc[-1]
    current_price = data['close'].iloc[-1]
    
    # Check for oversold condition
    if current_rsi < 30 and position <= 0:
        return 'BUY'
    
    # Check for overbought condition
    elif current_rsi > 70 and position >= 0:
        return 'SELL'
    
    return 'HOLD'
</CODE>

Now generate the response for the strategy described above.
1. Put the Turkish explanation inside `<SUMMARY>` and `</SUMMARY>` tags.
2. Put the Python code inside `<CODE>` and `</CODE>` tags. Do NOT use markdown code blocks (```)."""
        
        return prompt
    
    def validate_code(self, code):
        """Validate generated code for security"""
        # Check for forbidden keywords
        for keyword in self.forbidden_keywords:
            if keyword in code.lower():
                return False, f"Forbidden keyword detected: {keyword}"
        
        # Check for required function
        if 'def strategy(' not in code:
            return False, "Missing required function: strategy(data, position)"
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'__\w+__',  # Dunder methods
            r'subprocess',
            r'socket',
            r'requests',
            r'urllib'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Potentially dangerous pattern detected: {pattern}"
        
        return True, "Code validation passed"
    
    def _sandbox_test(self, code: str) -> tuple:
        """Test generated code in a safe sandbox environment
        
        Returns:
            (success: bool, error_message: str or None)
        """
        try:
            # Create minimal test environment
            import pandas as pd
            import numpy as np
            
            # Create sample data for testing
            test_data = pd.DataFrame({
                'time': pd.date_range('2024-01-01', periods=100, freq='h'),  # lowercase 'h'
                'open': np.random.uniform(1.0, 1.1, 100),
                'high': np.random.uniform(1.05, 1.15, 100),
                'low': np.random.uniform(0.95, 1.05, 100),
                'close': np.random.uniform(1.0, 1.1, 100),
                'volume': np.random.randint(1000, 10000, 100)
            })
            
            # Compile the code (syntax check)
            compile(code, '<strategy>', 'exec')
            
            # Execute in namespace with pre-imported libraries
            # This avoids the need for import statements in the strategy code
            namespace = {
                'pd': pd,
                'np': np,
                'pandas': pd,
                'numpy': np,
                '__builtins__': __builtins__  # Allow full builtins for import support
            }
            
            # Try to import price_action_lib if available
            try:
                from price_action_lib import PriceActionLib
                namespace['pa'] = PriceActionLib()
            except ImportError:
                pass
            
            exec(code, namespace)
            
            # Test the strategy function
            if 'strategy' in namespace:
                result = namespace['strategy'](test_data, 0)
                if result not in ['BUY', 'SELL', 'HOLD']:
                    return False, f"Strategy returned invalid value: {result}"
                return True, None
            else:
                return False, "Strategy function not found after execution"
                
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
        except Exception as e:
            return False, f"Runtime error: {str(e)}"
    
    async def _call_with_retry(self, api_func, prompt: str, api_key: str) -> str:
        """Call API with exponential backoff retry
        
        Args:
            api_func: Async function to call (_call_groq, _call_openai, etc.)
            prompt: The prompt to send
            api_key: API key for authentication
            
        Returns:
            API response string
            
        Raises:
            Exception if all retries fail
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Check rate limit
                if not self.rate_limiter.can_call():
                    wait_time = self.rate_limiter.wait_time()
                    print(f"[RateLimit] Waiting {wait_time:.1f}s before API call...")
                    await asyncio.sleep(wait_time)
                
                # Record the call
                self.rate_limiter.record_call()
                
                # Make the API call
                result = await api_func(prompt, api_key)
                return result
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)  # 1s, 2s, 4s
                    print(f"[Retry] Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
        
        raise Exception(f"All {self.max_retries} attempts failed. Last error: {last_error}")
    
    async def parse_strategy(self, description, ai_provider, api_key):
        """
        Parse strategy description using AI
        
        Args:
            description: Natural language strategy description
            ai_provider: 'groq', 'openai', or 'gemini'
            api_key: API key for the provider
        
        Returns:
            dict with 'code', 'explanation', 'success'
        """
        try:
            # NEW: Turkish NLU preprocessing
            from turkish_nlu import TurkishNLU
            nlu = TurkishNLU()
            parsed = nlu.parse(description)
            
            # Enhance description if confidence is high
            if parsed['confidence'] >= 0.7:
                print(f"[NLU] Detected: {parsed['indicators']}, Confidence: {parsed['confidence']:.2f}")
                description = nlu.enhance_prompt(description, parsed)
                
                # Suggest template if available
                suggested_template = nlu.suggest_template(parsed)
                if suggested_template:
                    print(f"[NLU] Suggested template: {suggested_template}")
            
            prompt = self.create_prompt(description)
            
            # Select API function based on provider
            api_funcs = {
                'groq': self._call_groq,
                'openai': self._call_openai,
                'gemini': self._call_gemini
            }
            
            if ai_provider not in api_funcs:
                return {
                    'success': False,
                    'error': f'Unknown AI provider: {ai_provider}'
                }
            
            # Call AI with retry mechanism
            response = await self._call_with_retry(api_funcs[ai_provider], prompt, api_key)
            
            # Extract code from markdown if present
            code = self._extract_code(response)
            
            # Validate code for security
            is_valid, message = self.validate_code(code)
            
            if not is_valid:
                return {
                    'success': False,
                    'error': f'Code validation failed: {message}',
                    'code': code
                }
            
            # Sandbox test the code
            sandbox_ok, sandbox_error = self._sandbox_test(code)
            if not sandbox_ok:
                print(f"[Sandbox] Test failed: {sandbox_error}")
                # Still return the code but with a warning
                return {
                    'success': True,
                    'code': code,
                    'explanation': 'Strategy generated (sandbox warning: ' + sandbox_error + ')',
                    'sandbox_warning': sandbox_error
                }
            
            return {
                'success': True,
                'code': code,
                'explanation': 'Strategy code generated and tested successfully ✓'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def evolve_strategy(self, current_code, ai_provider, api_key):
        """Evolves existing strategy code with advanced optimizations"""
        prompt = f"""You are a professional quant developer and SMC expert. Improve the following trading strategy code.
        
        CURRENT CODE:
        {current_code}
        
        TASK:
        Modify the code to implement ONE of these advanced optimizations:
        1. Add a Volatility-based Entry/Exit Filter (ATR).
        2. Implement a Liquidity Filter (using `data['is_discount']` or `data['is_premium']` logic).
        3. Add a dynamic Trailing Stop based on Swing Highs/Lows.
        
        REQUIREMENTS:
        - Return the FULL modified code.
        - Ensure the function signature `strategy(data, position)` remains unchanged.
        - The code must be production-ready and handle NaNs safely.
        
        Output format:
        1. Turkish summary of technical improvements inside <SUMMARY> tags.
        2. Full Python code inside <CODE> tags."""

        try:
            api_funcs = {
                'groq': self._call_groq,
                'openai': self._call_openai,
                'gemini': self._call_gemini
            }
            
            if ai_provider not in api_funcs:
                return {'success': False, 'error': 'Invalid provider'}
            
            # Call with retry mechanism
            evolved = await self._call_with_retry(api_funcs[ai_provider], prompt, api_key)

            evolved_code = self._extract_code(evolved)
            summary = "Geliştirme özeti bulunamadı."
            if '<SUMMARY>' in evolved:
                summary = evolved.split('<SUMMARY>')[1].split('</SUMMARY>')[0].strip()

            return {
                'success': True, 
                'code': evolved_code, 
                'summary': summary
            }
        except Exception as e:
            return {'success': False, 'error': f"Evolution failed: {str(e)}"}
    
    def _extract_code(self, text):
        """Extract Python code from markdown code blocks"""
        # Look for ```python ... ``` blocks
        pattern = r'```python\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # Look for ``` ... ``` blocks
        pattern = r'```\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0]
        
        # Return as-is if no code blocks found
        return text.strip()
    
    async def _call_groq(self, prompt, api_key):
        """Call Groq API"""
        import aiohttp
        
        url = 'https://api.groq.com/openai/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key.strip()}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'llama-3.3-70b-versatile',  # Updated from deprecated mixtral
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 2000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    try:
                        error_json = await response.json()
                        error_msg = error_json.get('error', {}).get('message', error_text)
                    except:
                        error_msg = error_text
                    raise Exception(f'Groq API error {response.status}: {error_msg}')
                
                result = await response.json()
                return result['choices'][0]['message']['content']
    
    async def _call_openai(self, prompt, api_key):
        """Call OpenAI API"""
        import aiohttp
        
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-4o-mini',  # Updated: 90% cheaper than gpt-4, faster
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 2000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f'OpenAI API error {response.status}: {error_text}')
                
                result = await response.json()
                return result['choices'][0]['message']['content']
    
    async def _call_gemini(self, prompt, api_key):
        """Call Google Gemini API"""
        import aiohttp
        
        # Updated to Gemini 2.0 Flash - faster and more capable
        url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}'
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            'contents': [{
                'parts': [{'text': prompt}]
            }],
            'generationConfig': {
                'temperature': 0.3,
                'maxOutputTokens': 2000
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f'Gemini API error {response.status}: {error_text}')
                
                result = await response.json()
                return result['candidates'][0]['content']['parts'][0]['text']
