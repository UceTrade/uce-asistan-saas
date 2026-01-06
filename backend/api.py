"""
UceAsistan REST API
FastAPI-based REST endpoints for SaaS platform

Runs alongside WebSocket server for hybrid architecture
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timedelta
import asyncio
import json

try:
    from config import settings
except ImportError:
    class FallbackSettings:
        DEBUG = False
        JWT_SECRET = "dev-secret"
        JWT_ALGORITHM = "HS256"
    settings = FallbackSettings()

# ============================================
# PYDANTIC SCHEMAS
# ============================================

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class ErrorResponse(BaseModel):
    error: bool = True
    code: str
    message: str
    details: dict = {}


class StrategyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    code: str = Field(..., min_length=10)
    timeframe: str = Field(default="H1")
    category: str = Field(default="Kullanıcı")


class StrategyResponse(BaseModel):
    id: str
    name: str
    description: str
    code: str
    timeframe: str
    category: str
    created_at: str


class BacktestRequest(BaseModel):
    strategy_code: str = Field(..., min_length=10)
    symbol: str = Field(default="EURUSD")
    timeframe: str = Field(default="H1")
    initial_balance: float = Field(default=10000, ge=100)
    start_date: str
    end_date: str
    lot_size: float = Field(default=0.01, ge=0.01, le=10.0)
    spread_points: int = Field(default=2, ge=0, le=50)


class BacktestResponse(BaseModel):
    success: bool
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_profit: float
    profit_factor: float
    max_drawdown: float


class MarketAnalysisRequest(BaseModel):
    symbol: str = Field(default="EURUSD")


class AccountInfo(BaseModel):
    login: int
    server: str
    name: str
    balance: float
    equity: float
    margin: float
    profit: float


class AIProviderConfig(BaseModel):
    provider: str = Field(..., pattern="^(groq|openai|gemini)$")
    api_key: str = Field(default="")


class SettingsUpdate(BaseModel):
    ai_provider: Optional[str] = None
    telegram_enabled: Optional[bool] = None
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    max_drawdown: Optional[float] = None
    daily_limit: Optional[float] = None


# ============================================
# FASTAPI APP
# ============================================

app = FastAPI(
    title="UceAsistan API",
    description="AI Trading Coach & Risk Guardian API",
    version="2.2.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://uceasistan.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# ROUTES - Health
# ============================================

@app.get("/", response_model=HealthResponse, tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "2.2.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "version": "2.2.0",
        "timestamp": datetime.now().isoformat()
    }


# ============================================
# ROUTES - Account
# ============================================

@app.get("/api/v1/account", tags=["Account"])
async def get_account_info():
    """Get current MT5 account information."""
    try:
        from mt5_proxy import mt5
        
        if not mt5.initialize():
            raise HTTPException(status_code=503, detail="MT5 not initialized")
        
        info = mt5.account_info()
        if info is None:
            raise HTTPException(status_code=503, detail="No active MT5 account")
        
        return {
            "login": info.login,
            "server": info.server,
            "name": info.name,
            "balance": info.balance,
            "equity": info.equity,
            "margin": info.margin,
            "margin_free": info.margin_free,
            "profit": info.profit,
            "currency": info.currency
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="MT5 not available")


@app.get("/api/v1/account/positions", tags=["Account"])
async def get_positions():
    """Get current open positions."""
    try:
        from mt5_proxy import mt5
        
        if not mt5.initialize():
            raise HTTPException(status_code=503, detail="MT5 not initialized")
        
        positions = mt5.positions_get()
        result = []
        
        if positions:
            for pos in positions:
                result.append({
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "type": "BUY" if pos.type == 0 else "SELL",
                    "volume": pos.volume,
                    "price_open": pos.price_open,
                    "price_current": pos.price_current,
                    "profit": pos.profit,
                    "sl": pos.sl,
                    "tp": pos.tp
                })
        
        return {"positions": result, "count": len(result)}
    except ImportError:
        raise HTTPException(status_code=503, detail="MT5 not available")


# ============================================
# ROUTES - Market Analysis
# ============================================

@app.get("/api/v1/market/{symbol}", tags=["Market"])
async def get_market_analysis(symbol: str):
    """Get market analysis for a symbol."""
    try:
        from mt5_proxy import mt5
        import pandas as pd
        import numpy as np
        
        if not mt5.initialize():
            raise HTTPException(status_code=503, detail="MT5 not initialized")
        
        # Get tick data
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        
        # Get OHLC data
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None or len(rates) < 20:
            raise HTTPException(status_code=404, detail=f"Insufficient data for {symbol}")
        
        df = pd.DataFrame(rates)
        
        # Calculate indicators
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        sma_20 = df['close'].rolling(window=20).mean().iloc[-1]
        sma_50 = df['close'].rolling(window=50).mean().iloc[-1]
        
        # Determine trend
        current_price = tick.ask
        if current_price > sma_50:
            trend = "uptrend"
        elif current_price < sma_50:
            trend = "downtrend"
        else:
            trend = "neutral"
        
        return {
            "symbol": symbol,
            "price": current_price,
            "bid": tick.bid,
            "ask": tick.ask,
            "spread": round((tick.ask - tick.bid) * 10000, 1),
            "rsi_14": round(float(rsi.iloc[-1]), 2),
            "sma_20": round(float(sma_20), 5),
            "sma_50": round(float(sma_50), 5),
            "trend": trend,
            "timestamp": datetime.now().isoformat()
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="MT5 not available")


@app.get("/api/v1/market/symbols", tags=["Market"])
async def get_available_symbols():
    """Get list of available symbols."""
    try:
        from mt5_proxy import mt5
        
        if not mt5.initialize():
            raise HTTPException(status_code=503, detail="MT5 not initialized")
        
        symbols = mt5.symbols_get()
        visible = []
        
        if symbols:
            for s in symbols:
                if s.visible:
                    visible.append(s.name)
        
        return {"symbols": visible[:50], "count": len(visible)}
    except ImportError:
        raise HTTPException(status_code=503, detail="MT5 not available")


# ============================================
# ROUTES - Strategies
# ============================================

@app.get("/api/v1/strategies", tags=["Strategies"])
async def list_strategies():
    """List all saved strategies."""
    import os
    
    # Read from JSON file (will be migrated to DB)
    strategies_file = os.path.join(os.path.dirname(__file__), 'user_templates.json')
    
    if os.path.exists(strategies_file):
        with open(strategies_file, 'r', encoding='utf-8') as f:
            strategies = json.load(f)
    else:
        strategies = []
    
    return {"strategies": strategies, "count": len(strategies)}


@app.post("/api/v1/strategies", tags=["Strategies"])
async def create_strategy(strategy: StrategyCreate):
    """Create a new strategy."""
    import os
    import uuid
    
    strategies_file = os.path.join(os.path.dirname(__file__), 'user_templates.json')
    
    # Load existing
    strategies = []
    if os.path.exists(strategies_file):
        with open(strategies_file, 'r', encoding='utf-8') as f:
            strategies = json.load(f)
    
    # Create new strategy
    new_strategy = {
        "id": f"user_{uuid.uuid4().hex[:8]}",
        "name": strategy.name,
        "description": strategy.description,
        "code": strategy.code,
        "timeframe": strategy.timeframe,
        "category": strategy.category,
        "created_at": datetime.now().isoformat()
    }
    
    strategies.append(new_strategy)
    
    # Save
    with open(strategies_file, 'w', encoding='utf-8') as f:
        json.dump(strategies, f, ensure_ascii=False, indent=2)
    
    return {"success": True, "strategy": new_strategy}


@app.delete("/api/v1/strategies/{strategy_id}", tags=["Strategies"])
async def delete_strategy(strategy_id: str):
    """Delete a strategy."""
    import os
    
    strategies_file = os.path.join(os.path.dirname(__file__), 'user_templates.json')
    
    if not os.path.exists(strategies_file):
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    with open(strategies_file, 'r', encoding='utf-8') as f:
        strategies = json.load(f)
    
    # Filter out the strategy
    original_count = len(strategies)
    strategies = [s for s in strategies if s['id'] != strategy_id]
    
    if len(strategies) == original_count:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    with open(strategies_file, 'w', encoding='utf-8') as f:
        json.dump(strategies, f, ensure_ascii=False, indent=2)
    
    return {"success": True, "message": "Strategy deleted"}


# ============================================
# ROUTES - Templates (Built-in)
# ============================================

@app.get("/api/v1/templates", tags=["Templates"])
async def list_templates():
    """List built-in strategy templates."""
    try:
        from strategy_templates import StrategyTemplates
        templates = StrategyTemplates()
        return {"templates": templates.list_templates()}
    except ImportError:
        return {"templates": [], "error": "Templates module not available"}


# ============================================
# ROUTES - Configuration
# ============================================

@app.get("/api/v1/config/ai-providers", tags=["Configuration"])
async def get_ai_providers():
    """Get available AI providers and their status."""
    return {
        "providers": [
            {
                "id": "groq",
                "name": "Groq",
                "configured": bool(settings.GROQ_API_KEY) if hasattr(settings, 'GROQ_API_KEY') else False,
                "free_tier": True
            },
            {
                "id": "openai",
                "name": "OpenAI",
                "configured": bool(settings.OPENAI_API_KEY) if hasattr(settings, 'OPENAI_API_KEY') else False,
                "free_tier": False
            },
            {
                "id": "gemini",
                "name": "Google Gemini",
                "configured": bool(settings.GEMINI_API_KEY) if hasattr(settings, 'GEMINI_API_KEY') else False,
                "free_tier": True
            }
        ]
    }


# ============================================
# ERROR HANDLERS
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "code": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "code": "INTERNAL_ERROR",
            "message": str(exc) if settings.DEBUG else "Internal server error",
            "timestamp": datetime.now().isoformat()
        }
    )


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8080,
        reload=settings.DEBUG
    )
