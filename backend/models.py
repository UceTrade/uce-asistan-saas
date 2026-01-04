"""
UceAsistan Database Models
SQLAlchemy ORM models for SaaS platform

Supports: SQLite (development) and PostgreSQL (production)
"""

from datetime import datetime
from typing import Optional, List
import json

try:
    from sqlalchemy import (
        create_engine, Column, Integer, String, Float, Boolean, 
        DateTime, Text, ForeignKey, JSON, Enum, Index
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import relationship, sessionmaker
    from sqlalchemy.pool import StaticPool
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    print("[WARNING] SQLAlchemy not installed. Database features disabled.")

try:
    from config import settings
except ImportError:
    class FallbackSettings:
        DATABASE_URL = "sqlite:///./uceasistan.db"
    settings = FallbackSettings()


if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
    # ============================================
    # USER & AUTHENTICATION
    # ============================================
    
    class User(Base):
        """User account for SaaS platform."""
        __tablename__ = "users"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        email = Column(String(255), unique=True, nullable=False, index=True)
        password_hash = Column(String(255), nullable=False)
        name = Column(String(255))
        
        # Subscription
        subscription_tier = Column(String(50), default="free")  # free, pro, enterprise
        subscription_expires = Column(DateTime, nullable=True)
        ai_requests_used = Column(Integer, default=0)
        ai_requests_reset_date = Column(DateTime)
        
        # Settings
        default_ai_provider = Column(String(50), default="groq")
        telegram_enabled = Column(Boolean, default=False)
        telegram_chat_id = Column(String(100))
        
        # Metadata
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        last_login = Column(DateTime)
        is_active = Column(Boolean, default=True)
        
        # Relationships
        strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")
        templates = relationship("UserTemplate", back_populates="user", cascade="all, delete-orphan")
        trades = relationship("TradeJournal", back_populates="user", cascade="all, delete-orphan")
        sessions = relationship("TradingSession", back_populates="user", cascade="all, delete-orphan")
        
        def to_dict(self):
            return {
                "id": self.id,
                "email": self.email,
                "name": self.name,
                "subscription_tier": self.subscription_tier,
                "subscription_expires": self.subscription_expires.isoformat() if self.subscription_expires else None,
                "created_at": self.created_at.isoformat() if self.created_at else None
            }
    
    
    # ============================================
    # STRATEGIES
    # ============================================
    
    class Strategy(Base):
        """User-created trading strategies."""
        __tablename__ = "strategies"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        
        name = Column(String(255), nullable=False)
        description = Column(Text)
        code = Column(Text, nullable=False)
        
        # Metadata
        timeframe = Column(String(10), default="H1")
        symbols = Column(JSON, default=list)  # ["EURUSD", "GBPUSD"]
        category = Column(String(100))
        is_public = Column(Boolean, default=False)
        
        # Performance (from backtests)
        last_backtest_date = Column(DateTime)
        win_rate = Column(Float)
        profit_factor = Column(Float)
        total_trades = Column(Integer)
        net_profit = Column(Float)
        
        # Timestamps
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # Relationships
        user = relationship("User", back_populates="strategies")
        backtests = relationship("BacktestResult", back_populates="strategy", cascade="all, delete-orphan")
        
        def to_dict(self):
            return {
                "id": self.id,
                "name": self.name,
                "description": self.description,
                "code": self.code,
                "timeframe": self.timeframe,
                "category": self.category,
                "win_rate": self.win_rate,
                "profit_factor": self.profit_factor,
                "created_at": self.created_at.isoformat() if self.created_at else None
            }
    
    
    class UserTemplate(Base):
        """User-saved strategy templates."""
        __tablename__ = "user_templates"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        
        name = Column(String(255), nullable=False)
        description = Column(Text)
        code = Column(Text, nullable=False)
        timeframe = Column(String(10), default="H1")
        category = Column(String(100), default="Kullanıcı")
        
        created_at = Column(DateTime, default=datetime.utcnow)
        
        user = relationship("User", back_populates="templates")
        
        def to_dict(self):
            return {
                "id": f"user_{self.id}",
                "name": self.name,
                "description": self.description,
                "code": self.code,
                "timeframe": self.timeframe,
                "category": self.category,
                "created_at": self.created_at.isoformat() if self.created_at else None
            }
    
    
    # ============================================
    # BACKTEST RESULTS
    # ============================================
    
    class BacktestResult(Base):
        """Stored backtest results for analysis."""
        __tablename__ = "backtest_results"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        
        # Parameters
        symbol = Column(String(20), nullable=False)
        timeframe = Column(String(10), nullable=False)
        start_date = Column(DateTime, nullable=False)
        end_date = Column(DateTime, nullable=False)
        initial_balance = Column(Float, nullable=False)
        lot_size = Column(Float, default=0.01)
        
        # Results
        final_balance = Column(Float)
        net_profit = Column(Float)
        net_profit_pct = Column(Float)
        total_trades = Column(Integer)
        winning_trades = Column(Integer)
        losing_trades = Column(Integer)
        win_rate = Column(Float)
        profit_factor = Column(Float)
        max_drawdown = Column(Float)
        sharpe_ratio = Column(Float)
        
        # Raw data (JSON)
        trades_json = Column(JSON)  # List of trades
        equity_curve_json = Column(JSON)  # Equity curve points
        
        created_at = Column(DateTime, default=datetime.utcnow)
        
        strategy = relationship("Strategy", back_populates="backtests")
        
        def to_dict(self):
            return {
                "id": self.id,
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "start_date": self.start_date.isoformat() if self.start_date else None,
                "end_date": self.end_date.isoformat() if self.end_date else None,
                "initial_balance": self.initial_balance,
                "final_balance": self.final_balance,
                "net_profit": self.net_profit,
                "net_profit_pct": self.net_profit_pct,
                "total_trades": self.total_trades,
                "win_rate": self.win_rate,
                "profit_factor": self.profit_factor,
                "max_drawdown": self.max_drawdown,
                "created_at": self.created_at.isoformat() if self.created_at else None
            }
    
    
    # ============================================
    # TRADE JOURNAL
    # ============================================
    
    class TradeJournal(Base):
        """Trade journal entries with notes and emotions."""
        __tablename__ = "trade_journal"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        
        # Trade details
        ticket = Column(Integer, index=True)
        symbol = Column(String(20), nullable=False)
        direction = Column(String(10))  # BUY or SELL
        volume = Column(Float)
        
        entry_price = Column(Float)
        exit_price = Column(Float)
        stop_loss = Column(Float)
        take_profit = Column(Float)
        
        profit = Column(Float)
        pips = Column(Float)
        
        entry_time = Column(DateTime)
        exit_time = Column(DateTime)
        duration_minutes = Column(Integer)
        
        # Journal
        note = Column(Text)
        emotion = Column(String(50))  # confident, anxious, neutral, etc.
        strategy_used = Column(String(255))
        tags = Column(JSON, default=list)  # ["scalping", "news", "breakout"]
        
        # Ratings
        setup_rating = Column(Integer)  # 1-5
        execution_rating = Column(Integer)  # 1-5
        
        created_at = Column(DateTime, default=datetime.utcnow)
        
        user = relationship("User", back_populates="trades")
        
        __table_args__ = (
            Index('idx_trade_user_date', 'user_id', 'entry_time'),
        )
    
    
    # ============================================
    # TRADING SESSIONS
    # ============================================
    
    class TradingSession(Base):
        """Track MT5 trading sessions."""
        __tablename__ = "trading_sessions"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        
        mt5_login = Column(Integer)
        mt5_server = Column(String(255))
        
        start_balance = Column(Float)
        end_balance = Column(Float)
        
        trades_count = Column(Integer, default=0)
        total_profit = Column(Float, default=0)
        max_drawdown = Column(Float, default=0)
        
        started_at = Column(DateTime, default=datetime.utcnow)
        ended_at = Column(DateTime)
        
        user = relationship("User", back_populates="sessions")
    
    
    # ============================================
    # API KEYS (for user-specific AI keys)
    # ============================================
    
    class UserAPIKey(Base):
        """Store user's API keys (encrypted in production)."""
        __tablename__ = "user_api_keys"
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
        
        provider = Column(String(50), nullable=False)  # groq, openai, gemini
        api_key_encrypted = Column(String(500), nullable=False)  # Encrypted in production
        
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        __table_args__ = (
            Index('idx_user_provider', 'user_id', 'provider', unique=True),
        )
    
    
    # ============================================
    # DATABASE CONNECTION
    # ============================================
    
    def get_engine(database_url: str = None):
        """Create database engine."""
        url = database_url or settings.DATABASE_URL
        
        if url.startswith("sqlite"):
            # SQLite specific settings
            engine = create_engine(
                url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=getattr(settings, 'DEBUG', False)
            )
        else:
            # PostgreSQL / MySQL
            engine = create_engine(
                url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=getattr(settings, 'DEBUG', False)
            )
        
        return engine
    
    
    def create_session(engine=None):
        """Create a new database session."""
        if engine is None:
            engine = get_engine()
        
        Session = sessionmaker(bind=engine)
        return Session()
    
    
    def init_database(engine=None):
        """Initialize database tables."""
        if engine is None:
            engine = get_engine()
        
        Base.metadata.create_all(engine)
        print("[DB] Database tables created successfully")
        return engine


else:
    # Fallback when SQLAlchemy is not available
    class User:
        pass
    class Strategy:
        pass
    class UserTemplate:
        pass
    class BacktestResult:
        pass
    class TradeJournal:
        pass
    class TradingSession:
        pass
    class UserAPIKey:
        pass
    
    def get_engine(*args, **kwargs):
        raise ImportError("SQLAlchemy not installed")
    
    def create_session(*args, **kwargs):
        raise ImportError("SQLAlchemy not installed")
    
    def init_database(*args, **kwargs):
        raise ImportError("SQLAlchemy not installed")


# ============================================
# CLI for migrations
# ============================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "init":
        if SQLALCHEMY_AVAILABLE:
            engine = init_database()
            print("[OK] Database initialized")
        else:
            print("[ERROR] SQLAlchemy not installed")
    else:
        print("Usage: python models.py init")
