"""
FinGPT Financial Agent - Finance-specialized AI for trading decisions
Integrates FinGPT model for sentiment analysis, market decisions, and financial reasoning
"""

import aiohttp
import asyncio
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum


class FinanceQueryType(Enum):
    """Types of financial queries"""
    SENTIMENT = "sentiment"           # News/market sentiment
    TRADE_DECISION = "trade_decision" # Buy/Sell/Hold decision
    RISK_ASSESSMENT = "risk"          # Risk analysis
    MARKET_ANALYSIS = "analysis"      # General market analysis
    NEWS_SUMMARY = "news"             # Financial news summary
    GENERAL = "general"               # General chat (route to GPT)


class FinAgent:
    """
    Finance-specialized AI Agent using FinGPT
    
    Features:
    - Sentiment analysis for forex, crypto, commodities
    - Trading decision support with confidence scores
    - Risk assessment and position sizing
    - News impact analysis
    - Hybrid routing: Finance → FinGPT, General → GPT
    
    Supported Providers (in priority order):
    1. Groq - FREE, no credit card required
    2. OpenRouter - 50 free requests/day
    3. Together AI - Paid
    4. Fireworks AI - Paid
    """
    
    # API Endpoints
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
    FIREWORKS_API_URL = "https://api.fireworks.ai/inference/v1/chat/completions"
    
    # Models for each provider
    GROQ_MODELS = {
        "primary": "llama-3.3-70b-versatile",  # Best for finance, FREE
        "fast": "llama-3.1-8b-instant",         # Faster, still good
    }
    
    OPENROUTER_MODELS = {
        "primary": "meta-llama/llama-3.3-70b-instruct",
        "fast": "meta-llama/llama-3.1-8b-instruct"
    }
    
    # FinGPT-optimized models (for paid providers)
    FINANCE_MODELS = {
        "primary": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "fast": "meta-llama/Llama-3.1-8B-Instruct-Turbo",
        "reasoning": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B"
    }
    
    # Financial system prompts for different tasks
    FINANCE_PROMPTS = {
        "sentiment": """Sen profesyonel bir finansal analist yapay zekasısın. Görevin piyasa sentiment analizi yapmak.

GÖREV: Verilen bilgiyi analiz et ve sentiment belirle.

ÇIKTI FORMATI (JSON):
{
    "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
    "confidence": 0.0-1.0,
    "key_factors": ["faktör1", "faktör2"],
    "impact_level": "HIGH" | "MEDIUM" | "LOW",
    "timeframe": "SHORT" | "MEDIUM" | "LONG",
    "summary_tr": "Türkçe özet"
}

Sadece JSON döndür, başka bir şey yazma.""",

        "trade_decision": """Sen deneyimli bir forex/kripto trader yapay zekasısın. Görevin trading kararı vermek.

KURALLAR:
1. Risk/Reward oranı minimum 1:2 olmalı
2. Trend yönünde işlem tercih et
3. Belirsizlikte HOLD öner
4. Her zaman stop-loss belirt

ÇIKTI FORMATI (JSON):
{
    "decision": "BUY" | "SELL" | "HOLD",
    "confidence": 0.0-1.0,
    "entry_zone": {"min": 0.0, "max": 0.0},
    "stop_loss": 0.0,
    "take_profit": [{"level": 0.0, "ratio": "1:2"}, {"level": 0.0, "ratio": "1:3"}],
    "risk_reward": "1:X",
    "reasoning": ["sebep1", "sebep2"],
    "warnings": ["uyarı1"],
    "summary_tr": "Türkçe özet"
}

Sadece JSON döndür.""",

        "risk": """Sen bir risk yönetimi uzmanı yapay zekasısın. Görevin pozisyon riski analiz etmek.

ÇIKTI FORMATI (JSON):
{
    "risk_level": "LOW" | "MEDIUM" | "HIGH" | "EXTREME",
    "risk_score": 0-100,
    "max_position_size": 0.0,
    "recommended_lot": 0.0,
    "risk_factors": ["risk1", "risk2"],
    "mitigation": ["önlem1", "önlem2"],
    "summary_tr": "Türkçe özet"
}

Sadece JSON döndür.""",

        "analysis": """Sen profesyonel bir piyasa analisti yapay zekasısın. Kapsamlı teknik ve temel analiz yap.

ÇIKTI FORMATI (JSON):
{
    "trend": "UPTREND" | "DOWNTREND" | "SIDEWAYS",
    "trend_strength": 0-100,
    "key_levels": {
        "resistance": [0.0, 0.0],
        "support": [0.0, 0.0]
    },
    "technical_signals": [
        {"indicator": "RSI", "signal": "OVERSOLD", "value": 30}
    ],
    "fundamental_factors": ["faktör1"],
    "outlook": "BULLISH" | "BEARISH" | "NEUTRAL",
    "summary_tr": "Türkçe özet"
}

Sadece JSON döndür.""",

        "news": """Sen finansal haber analisti yapay zekasısın. Haberlerin piyasa etkisini değerlendir.

ÇIKTI FORMATI (JSON):
{
    "headline_sentiment": "POSITIVE" | "NEGATIVE" | "NEUTRAL",
    "market_impact": "HIGH" | "MEDIUM" | "LOW",
    "affected_assets": ["EURUSD", "XAUUSD"],
    "expected_movement": "UP" | "DOWN" | "MIXED",
    "trading_implication": "Türkçe açıklama",
    "summary_tr": "Türkçe özet"
}

Sadece JSON döndür."""
    }
    
    def __init__(self, groq_api_key: str = None, openrouter_api_key: str = None,
                 together_api_key: str = None, fireworks_api_key: str = None):
        """Initialize FinAgent with API keys"""
        self.groq_api_key = groq_api_key
        self.openrouter_api_key = openrouter_api_key
        self.together_api_key = together_api_key
        self.fireworks_api_key = fireworks_api_key
        self.conversation_history: List[Dict] = []
        self.max_history = 10
        self.last_provider_used = None
        
    def classify_query(self, query: str) -> FinanceQueryType:
        """Classify user query to determine which analysis type to use"""
        query_lower = query.lower()
        
        # Sentiment keywords
        sentiment_keywords = ["sentiment", "duygu", "hissiyat", "piyasa ne düşünüyor", 
                            "genel görünüm", "mood", "havası", "beklentiler"]
        
        # Trade decision keywords
        trade_keywords = ["al", "sat", "buy", "sell", "giriş", "entry", "trade", 
                         "işlem aç", "pozisyon", "long", "short", "almalı mıyım",
                         "satmalı mıyım", "ne yapmalıyım", "karar"]
        
        # Risk keywords
        risk_keywords = ["risk", "lot", "pozisyon boyutu", "stop", "zarar", 
                        "drawdown", "margin", "kaldıraç", "leverage"]
        
        # Analysis keywords
        analysis_keywords = ["analiz", "analysis", "teknik", "destek", "direnç",
                           "trend", "seviye", "level", "indir", "pattern"]
        
        # News keywords
        news_keywords = ["haber", "news", "açıklama", "fed", "ecb", "boj", 
                        "fomc", "nfp", "cpi", "gdp", "faiz"]
        
        # Check each category
        if any(kw in query_lower for kw in sentiment_keywords):
            return FinanceQueryType.SENTIMENT
        elif any(kw in query_lower for kw in trade_keywords):
            return FinanceQueryType.TRADE_DECISION
        elif any(kw in query_lower for kw in risk_keywords):
            return FinanceQueryType.RISK_ASSESSMENT
        elif any(kw in query_lower for kw in news_keywords):
            return FinanceQueryType.NEWS_SUMMARY
        elif any(kw in query_lower for kw in analysis_keywords):
            return FinanceQueryType.MARKET_ANALYSIS
        else:
            # Check if it mentions a trading pair → probably wants analysis
            pairs = ["eurusd", "gbpusd", "usdjpy", "xauusd", "btcusd", "gold", "altın"]
            if any(pair in query_lower for pair in pairs):
                return FinanceQueryType.MARKET_ANALYSIS
            return FinanceQueryType.GENERAL
    
    async def analyze(self, query: str, context: Dict = None, 
                     query_type: FinanceQueryType = None) -> Dict[str, Any]:
        """
        Main analysis method - routes to appropriate handler
        
        Args:
            query: User's question or request
            context: Additional context (market data, account info, etc.)
            query_type: Override automatic classification
            
        Returns:
            Structured analysis result with confidence scores
        """
        # Auto-classify if not specified
        if query_type is None:
            query_type = self.classify_query(query)
        
        # Route to general AI for non-finance queries
        if query_type == FinanceQueryType.GENERAL:
            return {
                "type": "general",
                "route_to": "gpt",
                "query": query,
                "message": "Bu sorgu genel AI'a yönlendirilmeli"
            }
        
        # Get appropriate system prompt
        system_prompt = self.FINANCE_PROMPTS.get(query_type.value, self.FINANCE_PROMPTS["analysis"])
        
        # Build context string
        context_str = self._build_context(context) if context else ""
        
        # Enhanced query with context
        enhanced_query = f"{context_str}\n\nKullanıcı Sorusu: {query}" if context_str else query
        
        # Call finance model
        result = await self._call_finance_model(system_prompt, enhanced_query, query_type)
        
        # Add metadata
        result["query_type"] = query_type.value
        result["timestamp"] = datetime.now().isoformat()
        result["model_used"] = "finance-specialized"
        
        return result
    
    def _build_context(self, context: Dict) -> str:
        """Build context string from available data"""
        parts = []
        
        if context.get("symbol"):
            parts.append(f"Sembol: {context['symbol']}")
            
        if context.get("current_price"):
            parts.append(f"Güncel Fiyat: {context['current_price']}")
            
        if context.get("account_balance"):
            parts.append(f"Hesap Bakiyesi: ${context['account_balance']}")
            
        if context.get("open_positions"):
            parts.append(f"Açık Pozisyonlar: {len(context['open_positions'])}")
            
        if context.get("daily_pnl"):
            parts.append(f"Günlük P/L: {context['daily_pnl']}")
            
        if context.get("market_data"):
            md = context["market_data"]
            parts.append(f"Piyasa Verileri: RSI={md.get('rsi', 'N/A')}, "
                        f"Trend={md.get('trend', 'N/A')}")
        
        if context.get("news_headlines"):
            parts.append(f"Son Haberler: {', '.join(context['news_headlines'][:3])}")
            
        return "\n".join(parts) if parts else ""
    
    async def _call_finance_model(self, system_prompt: str, query: str, 
                                  query_type: FinanceQueryType) -> Dict:
        """Call the finance-specialized model"""
        
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        # Add conversation history for context
        if self.conversation_history:
            # Insert history between system and user
            history_messages = self.conversation_history[-4:]  # Last 4 exchanges
            messages = [messages[0]] + history_messages + [messages[1]]
        
        # Try providers in order of preference (free first)
        providers = [
            ("groq", self.groq_api_key, self._call_groq),
            ("openrouter", self.openrouter_api_key, self._call_openrouter),
            ("together", self.together_api_key, self._call_together_ai),
            ("fireworks", self.fireworks_api_key, self._call_fireworks_ai)
        ]
        
        for provider_name, api_key, call_func in providers:
            if api_key:
                try:
                    result = await call_func(messages, query_type)
                    if result:
                        self._update_history(query, result.get("summary_tr", ""))
                        self.last_provider_used = provider_name
                        result["provider_used"] = provider_name
                        return result
                except Exception as e:
                    print(f"[FinAgent] {provider_name} error: {e}")
                    continue
        
        # If no API keys available
        return {
            "error": True,
            "message": "FinAgent için API anahtarı gerekli. Groq ücretsiz ve kredi kartı gerektirmiyor!",
            "setup_guide": "1. console.groq.com adresine gidin\n2. Ücretsiz hesap oluşturun\n3. API Keys'den key alın",
            "free_providers": ["Groq (groq.com)", "OpenRouter (openrouter.ai)"]
        }
    
    async def _call_groq(self, messages: List[Dict], 
                         query_type: FinanceQueryType) -> Optional[Dict]:
        """Call Groq API - FREE, no credit card required!"""
        
        # Select model based on query complexity
        if query_type in [FinanceQueryType.TRADE_DECISION, FinanceQueryType.RISK_ASSESSMENT]:
            model = self.GROQ_MODELS["primary"]
        else:
            model = self.GROQ_MODELS["fast"]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.GROQ_API_URL, 
                                   json=payload, 
                                   headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return self._parse_json_response(content)
                else:
                    error_text = await response.text()
                    raise Exception(f"Groq API Error {response.status}: {error_text}")
    
    async def _call_openrouter(self, messages: List[Dict],
                               query_type: FinanceQueryType) -> Optional[Dict]:
        """Call OpenRouter API - 50 free requests/day"""
        
        # Select model
        if query_type in [FinanceQueryType.TRADE_DECISION, FinanceQueryType.RISK_ASSESSMENT]:
            model = self.OPENROUTER_MODELS["primary"]
        else:
            model = self.OPENROUTER_MODELS["fast"]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024
        }
        
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://uceasistan.app",
            "X-Title": "UceAsistan FinAgent"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.OPENROUTER_API_URL,
                                   json=payload,
                                   headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return self._parse_json_response(content)
                else:
                    error_text = await response.text()
                    raise Exception(f"OpenRouter API Error {response.status}: {error_text}")
    
    async def _call_together_ai(self, messages: List[Dict], 
                                query_type: FinanceQueryType) -> Optional[Dict]:
        """Call Together AI API"""
        
        # Select model based on query complexity
        if query_type in [FinanceQueryType.TRADE_DECISION, FinanceQueryType.RISK_ASSESSMENT]:
            model = self.FINANCE_MODELS["primary"]
        else:
            model = self.FINANCE_MODELS["fast"]
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,  # Lower for more consistent financial advice
            "max_tokens": 1024,
            "response_format": {"type": "json_object"}
        }
        
        headers = {
            "Authorization": f"Bearer {self.together_api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.TOGETHER_API_URL, 
                                   json=payload, 
                                   headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return self._parse_json_response(content)
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
    
    async def _call_fireworks_ai(self, messages: List[Dict],
                                 query_type: FinanceQueryType) -> Optional[Dict]:
        """Call Fireworks AI API as fallback"""
        
        payload = {
            "model": "accounts/fireworks/models/llama-v3p1-70b-instruct",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024
        }
        
        headers = {
            "Authorization": f"Bearer {self.fireworks_api_key}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.FIREWORKS_API_URL,
                                   json=payload,
                                   headers=headers,
                                   timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"]
                    return self._parse_json_response(content)
                else:
                    raise Exception(f"Fireworks API Error: {response.status}")
    
    def _parse_json_response(self, content: str) -> Dict:
        """Parse JSON from model response"""
        try:
            # Try direct parse first
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to find JSON object in text
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group(0))
            
            # Return as text if not JSON
            return {"raw_response": content, "parse_error": True}
    
    def _update_history(self, query: str, response_summary: str):
        """Update conversation history"""
        self.conversation_history.append({
            "role": "user",
            "content": query
        })
        self.conversation_history.append({
            "role": "assistant", 
            "content": response_summary
        })
        
        # Trim history
        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
    
    # ========== Convenience Methods ==========
    
    async def get_sentiment(self, symbol: str, news: List[str] = None) -> Dict:
        """Get market sentiment for a symbol"""
        query = f"{symbol} için piyasa sentiment analizi yap"
        context = {"symbol": symbol}
        if news:
            context["news_headlines"] = news
        return await self.analyze(query, context, FinanceQueryType.SENTIMENT)
    
    async def get_trade_signal(self, symbol: str, market_data: Dict) -> Dict:
        """Get trading decision for a symbol"""
        query = f"{symbol} için şu anda işlem açmalı mıyım?"
        context = {"symbol": symbol, "market_data": market_data}
        return await self.analyze(query, context, FinanceQueryType.TRADE_DECISION)
    
    async def assess_risk(self, symbol: str, account_balance: float, 
                         planned_lot: float) -> Dict:
        """Assess risk for planned trade"""
        query = f"{symbol} için {planned_lot} lot işlem riski nedir?"
        context = {
            "symbol": symbol,
            "account_balance": account_balance,
            "planned_lot": planned_lot
        }
        return await self.analyze(query, context, FinanceQueryType.RISK_ASSESSMENT)
    
    async def analyze_market(self, symbol: str, timeframe: str = "H1") -> Dict:
        """Get comprehensive market analysis"""
        query = f"{symbol} {timeframe} analizi yap"
        context = {"symbol": symbol, "timeframe": timeframe}
        return await self.analyze(query, context, FinanceQueryType.MARKET_ANALYSIS)


# Singleton instance
fin_agent = FinAgent()


# Test
if __name__ == "__main__":
    async def test():
        agent = FinAgent(together_api_key="test")
        
        # Test classification
        print("Query Classification Tests:")
        tests = [
            "EURUSD için al sinyali var mı?",
            "Piyasa sentimenti nedir?",
            "0.5 lot risk hesapla",
            "XAUUSD analiz et",
            "FED toplantısı haberi nasıl etkiledi?",
            "Merhaba nasılsın?"
        ]
        
        for q in tests:
            qtype = agent.classify_query(q)
            print(f"  '{q[:40]}...' → {qtype.value}")
    
    asyncio.run(test())
