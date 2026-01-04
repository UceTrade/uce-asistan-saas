"""
Telegram Bot Integration for AI Trading Coach
Sends notifications for risk alerts, confluences, and daily summaries
"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any
import json


class TelegramNotifier:
    """
    Telegram Bot API wrapper for sending trading notifications
    """
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}" if bot_token else None
        self.enabled = bool(bot_token and chat_id)
        
    def configure(self, bot_token: str, chat_id: str):
        """Configure or update bot credentials"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
        self.enabled = bool(bot_token and chat_id)
        
    async def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message via Telegram Bot API
        
        Args:
            text: Message text (supports HTML formatting)
            parse_mode: 'HTML' or 'Markdown'
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            print("[Telegram] Bot not configured, skipping notification")
            return False
            
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=10) as response:
                    if response.status == 200:
                        print(f"[Telegram] Message sent successfully")
                        return True
                    else:
                        error = await response.text()
                        print(f"[Telegram] Failed to send: {error}")
                        return False
        except Exception as e:
            print(f"[Telegram] Error sending message: {e}")
            return False
    
    # =========================================
    # TRADING NOTIFICATION TEMPLATES
    # =========================================
    
    async def notify_risk_warning(self, current_drawdown: float, max_drawdown: float, 
                                   daily_loss: float, daily_limit: float):
        """Send risk warning notification"""
        dd_pct = (current_drawdown / max_drawdown) * 100 if max_drawdown > 0 else 0
        daily_pct = (daily_loss / daily_limit) * 100 if daily_limit > 0 else 0
        
        # Determine severity
        if dd_pct >= 80 or daily_pct >= 80:
            emoji = "🚨"
            severity = "KRİTİK"
        elif dd_pct >= 60 or daily_pct >= 60:
            emoji = "⚠️"
            severity = "UYARI"
        else:
            emoji = "📊"
            severity = "BİLGİ"
        
        message = f"""
{emoji} <b>RİSK {severity}</b> {emoji}

📉 <b>Maximum Drawdown:</b>
   Mevcut: {current_drawdown:.2f}% / Limit: {max_drawdown:.2f}%
   Kullanılan: {dd_pct:.1f}%

📊 <b>Günlük Kayıp:</b>
   Mevcut: ${daily_loss:.2f} / Limit: ${daily_limit:.2f}
   Kullanılan: {daily_pct:.1f}%

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        return await self.send_message(message.strip())
    
    async def notify_confluence_detected(self, symbol: str, direction: str, 
                                          strength: float, strategies: list):
        """Send confluence detection notification"""
        dir_emoji = "🟢" if direction.upper() == "BUY" else "🔴"
        dir_text = "ALIŞ" if direction.upper() == "BUY" else "SATIŞ"
        
        # Strength indicator
        if strength >= 80:
            strength_emoji = "🔥🔥🔥"
            strength_text = "ÇOK GÜÇLÜ"
        elif strength >= 60:
            strength_emoji = "🔥🔥"
            strength_text = "GÜÇLÜ"
        else:
            strength_emoji = "🔥"
            strength_text = "ORTA"
        
        strategies_text = "\n".join([f"   • {s}" for s in strategies])
        
        message = f"""
🎯 <b>CONFLUENCE TESPİT EDİLDİ</b> 🎯

{dir_emoji} <b>{symbol}</b> - {dir_text}

{strength_emoji} <b>Güç:</b> {strength:.0f}% ({strength_text})

📋 <b>Uyumlu Stratejiler:</b>
{strategies_text}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        return await self.send_message(message.strip())
    
    async def notify_trade_opened(self, symbol: str, direction: str, 
                                   lot_size: float, entry_price: float,
                                   sl: float = None, tp: float = None):
        """Send trade opened notification"""
        dir_emoji = "🟢" if direction.upper() == "BUY" else "🔴"
        dir_text = "ALIŞ" if direction.upper() == "BUY" else "SATIŞ"
        
        sl_text = f"{sl:.5f}" if sl else "Yok"
        tp_text = f"{tp:.5f}" if tp else "Yok"
        
        message = f"""
📈 <b>YENİ İŞLEM AÇILDI</b>

{dir_emoji} <b>{symbol}</b> {dir_text}

💰 <b>Lot:</b> {lot_size}
📍 <b>Giriş:</b> {entry_price:.5f}
🛑 <b>Stop Loss:</b> {sl_text}
🎯 <b>Take Profit:</b> {tp_text}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        return await self.send_message(message.strip())
    
    async def notify_trade_closed(self, symbol: str, direction: str,
                                   profit: float, pips: float = None,
                                   duration: str = None):
        """Send trade closed notification"""
        profit_emoji = "✅" if profit >= 0 else "❌"
        profit_text = f"+${profit:.2f}" if profit >= 0 else f"-${abs(profit):.2f}"
        
        pips_text = f"{pips:.1f} pips" if pips else ""
        duration_text = f"Süre: {duration}" if duration else ""
        
        message = f"""
{profit_emoji} <b>İŞLEM KAPANDI</b>

📊 <b>{symbol}</b>
💵 <b>Sonuç:</b> {profit_text} {pips_text}
{duration_text}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        return await self.send_message(message.strip())
    
    async def notify_daily_summary(self, balance: float, equity: float,
                                    daily_profit: float, total_trades: int,
                                    win_rate: float):
        """Send daily summary notification"""
        profit_emoji = "📈" if daily_profit >= 0 else "📉"
        profit_text = f"+${daily_profit:.2f}" if daily_profit >= 0 else f"-${abs(daily_profit):.2f}"
        
        message = f"""
📊 <b>GÜNLÜK ÖZET</b> 📊

💰 <b>Bakiye:</b> ${balance:,.2f}
📈 <b>Equity:</b> ${equity:,.2f}

{profit_emoji} <b>Günlük K/Z:</b> {profit_text}
📋 <b>İşlem Sayısı:</b> {total_trades}
🎯 <b>Kazanma Oranı:</b> {win_rate:.1f}%

📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}
"""
        return await self.send_message(message.strip())
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test the bot connection and get bot info"""
        if not self.bot_token:
            return {"success": False, "error": "Bot token not configured"}
            
        url = f"{self.base_url}/getMe"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "bot_name": data["result"]["first_name"],
                            "bot_username": data["result"]["username"]
                        }
                    else:
                        return {"success": False, "error": "Invalid bot token"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global instance (configured via settings)
# Try to auto-configure from environment if available
try:
    from config import settings
    telegram_notifier = TelegramNotifier(
        bot_token=settings.TELEGRAM_BOT_TOKEN if settings.TELEGRAM_BOT_TOKEN else None,
        chat_id=settings.TELEGRAM_CHAT_ID if settings.TELEGRAM_CHAT_ID else None
    )
    if settings.TELEGRAM_ENABLED and telegram_notifier.enabled:
        print("[Telegram] Auto-configured from settings")
except ImportError:
    # Fallback if config module not available
    telegram_notifier = TelegramNotifier()


# =========================================
# STANDALONE TEST
# =========================================
if __name__ == "__main__":
    import sys
    
    async def test():
        if len(sys.argv) < 3:
            print("Usage: python telegram_bot.py <BOT_TOKEN> <CHAT_ID>")
            return
            
        bot = TelegramNotifier(sys.argv[1], sys.argv[2])
        
        # Test connection
        result = await bot.test_connection()
        print(f"Connection test: {result}")
        
        if result["success"]:
            # Send test message
            await bot.send_message("🤖 <b>Test Mesajı</b>\n\nAI Trading Coach bağlantısı başarılı!")
            
            # Test risk warning
            await bot.notify_risk_warning(4.5, 10.0, 150.0, 500.0)
            
    asyncio.run(test())
