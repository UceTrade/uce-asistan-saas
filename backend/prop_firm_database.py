"""
Prop Firm Database - Auto-detection and rules management
Detects prop firm from MT5 broker name and provides trading rules
"""

from typing import Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PropFirmRules:
    """Trading rules for a prop firm"""
    firm_name: str
    max_drawdown: float  # % of initial balance
    daily_drawdown: float  # % of initial balance
    news_trading_allowed: bool
    news_buffer_minutes: int  # Minutes before/after high-impact news
    weekend_holding_allowed: bool
    consistency_rule: bool
    consistency_max_day_profit_pct: float  # Max % single day can contribute
    min_trading_days: int
    max_daily_trades: int  # 0 = unlimited
    scaling_plan: bool
    profit_split: int  # Percentage
    special_rules: List[str]
    ai_summary: str  # Pre-generated AI summary

# Comprehensive Prop Firm Database
PROP_FIRM_DATABASE: Dict[str, PropFirmRules] = {
    "ftmo": PropFirmRules(
        firm_name="FTMO",
        max_drawdown=10.0,
        daily_drawdown=5.0,
        news_trading_allowed=True,
        news_buffer_minutes=2,
        weekend_holding_allowed=False,
        consistency_rule=False,
        consistency_max_day_profit_pct=0,
        min_trading_days=4,
        max_daily_trades=0,
        scaling_plan=True,
        profit_split=80,
        special_rules=[
            "Drawdown başlangıç bakiyesinden hesaplanır",
            "Challenge süresince max 30 gün, Verification 60 gün",
            "Swing hesapları haber kısıtlamasından muaf",
            "Her ay 14. günde ödeme"
        ],
        ai_summary="""🏦 FTMO Kuralları Özeti:

⚠️ KRİTİK RİSK LİMİTLERİ:
• Max Drawdown: %10 (başlangıç bakiyesinden)
• Günlük Kayıp: %5 (başlangıç bakiyesinden)

📰 HABER TRADİNG:
• Yüksek etkili haberlerden 2 dakika önce/sonra işlem açma
• Swing hesapları bu kuraldan muaf

📅 ÖNEMLİ NOKTALAR:
• Minimum 4 işlem günü gerekli
• Hafta sonu pozisyon tutma YASAK (Swing hesapları hariç)
• Kar payı: %80 trader'a

💡 TAVSİYELER:
• Günlük max %2 risk al (limit dolmadan durabilmek için)
• Cuma akşamı tüm pozisyonları kapat
• Ekonomik takvimi takip et"""
    ),
    
    "the5ers": PropFirmRules(
        firm_name="The5ers",
        max_drawdown=4.0,
        daily_drawdown=3.0,
        news_trading_allowed=True,
        news_buffer_minutes=0,
        weekend_holding_allowed=True,
        consistency_rule=False,
        consistency_max_day_profit_pct=0,
        min_trading_days=3,
        max_daily_trades=0,
        scaling_plan=True,
        profit_split=80,
        special_rules=[
            "Düşük max drawdown - muhafazakar yaklaşım gerekli",
            "Pozisyon başına max %0.5 risk önerisi",
            "Gerçek hesap, gerçek piyasa koşulları"
        ],
        ai_summary="""🏦 The5ers Kuralları Özeti:

⚠️ KRİTİK RİSK LİMİTLERİ:
• Max Drawdown: %4 (ÇOK DÜŞÜK!)
• Günlük Kayıp: %3

🟢 ESNEK KURALLAR:
• Haber trading SERBEST
• Hafta sonu pozisyon tutabilirsin
• Minimum 3 işlem günü

💡 TAVSİYELER:
• %4 limit ÇOK dar, pozisyon başına max %0.5 risk al
• Agresif scalping'den kaçın
• Her işlemde stop-loss ZORUNLU
• Drawdown'ı gün gün takip et"""
    ),
    
    "fundednext": PropFirmRules(
        firm_name="FundedNext",
        max_drawdown=10.0,
        daily_drawdown=5.0,
        news_trading_allowed=True,
        news_buffer_minutes=0,
        weekend_holding_allowed=True,
        consistency_rule=False,
        consistency_max_day_profit_pct=0,
        min_trading_days=5,
        max_daily_trades=0,
        scaling_plan=True,
        profit_split=90,
        special_rules=[
            "Express model: Tek aşamalı değerlendirme",
            "Stellar model: İki aşamalı, daha yüksek kar hedefi",
            "15% kar paylaşımı bonus sistemi"
        ],
        ai_summary="""🏦 FundedNext Kuralları Özeti:

⚠️ KRİTİK RİSK LİMİTLERİ:
• Max Drawdown: %10
• Günlük Kayıp: %5

🟢 SERBEST KURALLAR:
• Haber trading SERBEST
• Hafta sonu pozisyon tutabilirsin
• Kar payı: %90'a kadar (sektörün en yükseği!)

📅 ÖNEMLİ:
• Minimum 5 işlem günü
• Express: Tek aşamalı, hızlı değerlendirme
• Stellar: İki aşamalı, daha esnek

💡 TAVSİYELER:
• Yüksek kar payı için Stellar model'i düşün
• Günlük max %2-3 risk al
• 5 günü doldurmak için sabırlı ol"""
    ),
    
    "myforexfunds": PropFirmRules(
        firm_name="MyForexFunds",
        max_drawdown=12.0,
        daily_drawdown=5.0,
        news_trading_allowed=False,
        news_buffer_minutes=15,
        weekend_holding_allowed=False,
        consistency_rule=True,
        consistency_max_day_profit_pct=30,
        min_trading_days=5,
        max_daily_trades=0,
        scaling_plan=True,
        profit_split=85,
        special_rules=[
            "Tutarlılık kuralı: Tek gün toplam karın %30'undan fazla olamaz",
            "Yüksek etkili haberlerden 15dk önce/sonra işlem yasak",
            "Trailing drawdown"
        ],
        ai_summary="""🏦 MyForexFunds Kuralları Özeti:

⚠️ KRİTİK RİSK LİMİTLERİ:
• Max Drawdown: %12 (trailing!)
• Günlük Kayıp: %5

🔴 DİKKAT EDİLMESİ GEREKENLER:
• Tutarlılık kuralı: Tek günde max %30 kar!
• Haber trading YASAK (15dk buffer)
• Hafta sonu pozisyon tutma YASAK

📅 ÖNEMLİ:
• Trailing drawdown - yükseldikçe floor da yükselir
• Minimum 5 işlem günü

💡 TAVSİYELER:
• Tek büyük gün yerine tutarlı küçük karlar hedefle
• NFP, FOMC gibi günlerde işlem YAPMA
• Cuma akşamı pozisyonları kapat"""
    ),
    
    "topstep": PropFirmRules(
        firm_name="Topstep",
        max_drawdown=4.5,
        daily_drawdown=2.0,
        news_trading_allowed=True,
        news_buffer_minutes=0,
        weekend_holding_allowed=False,
        consistency_rule=True,
        consistency_max_day_profit_pct=50,
        min_trading_days=0,  # No minimum
        max_daily_trades=0,
        scaling_plan=True,
        profit_split=90,
        special_rules=[
            "Futures odaklı prop firm",
            "Çok düşük daily drawdown limiti",
            "Scaling plan mevcut"
        ],
        ai_summary="""🏦 Topstep Kuralları Özeti:

⚠️ KRİTİK RİSK LİMİTLERİ:
• Max Drawdown: %4.5
• Günlük Kayıp: %2 (ÇOK DÜŞÜK!)

⚠️ TUTARLILIK KURALI:
• Tek gün max %50 kar katkısı

🟢 ESNEK:
• Haber trading SERBEST
• Minimum işlem günü YOK

💡 TAVSİYELER:
• Günlük %2 limit ÇOK dar!
• Pozisyon başına max %0.3-0.5 risk
• Büyük hamleler yerine küçük tutarlı karlar
• Günlük hedefe ulaşınca DURDUR"""
    ),
    
    "e8funding": PropFirmRules(
        firm_name="E8 Funding",
        max_drawdown=8.0,
        daily_drawdown=4.0,
        news_trading_allowed=True,
        news_buffer_minutes=0,
        weekend_holding_allowed=True,
        consistency_rule=False,
        consistency_max_day_profit_pct=0,
        min_trading_days=0,
        max_daily_trades=0,
        scaling_plan=True,
        profit_split=80,
        special_rules=[
            "Track record olmadan funding mümkün",
            "ELEV8 programı ile %100 kar payı",
            "Esnek kurallar"
        ],
        ai_summary="""🏦 E8 Funding Kuralları Özeti:

⚠️ KRİTİK RİSK LİMİTLERİ:
• Max Drawdown: %8
• Günlük Kayıp: %4

🟢 ÇOK ESNEK KURALLAR:
• Haber trading SERBEST
• Hafta sonu pozisyon tutabilirsin
• Minimum işlem günü YOK
• Tutarlılık kuralı YOK

💡 TAVSİYELER:
• Esnek kurallardan dolayı stratejini rahatça uygula
• Standart risk yönetimi yeterli
• ELEV8'e geçiş için performansını koru"""
    ),
    
    "alphaCapital": PropFirmRules(
        firm_name="Alpha Capital Group",
        max_drawdown=10.0,
        daily_drawdown=4.0,
        news_trading_allowed=True,
        news_buffer_minutes=0,
        weekend_holding_allowed=True,
        consistency_rule=False,
        consistency_max_day_profit_pct=0,
        min_trading_days=3,
        max_daily_trades=0,
        scaling_plan=True,
        profit_split=80,
        special_rules=[
            "Hızlı ödeme süresi (48 saat)",
            "Düşük challenge ücreti"
        ],
        ai_summary="""🏦 Alpha Capital Kuralları Özeti:

⚠️ KRİTİK RİSK LİMİTLERİ:
• Max Drawdown: %10
• Günlük Kayıp: %4

🟢 ESNEK KURALLAR:
• Haber trading SERBEST
• Hafta sonu pozisyon tutabilirsin
• Minimum 3 işlem günü

💡 TAVSİYELER:
• Standart risk yönetimi uygula
• Günlük max %2 risk mantıklı
• 48 saat içinde ödeme avantajlı"""
    )
}

# Broker name patterns to match prop firms
BROKER_PATTERNS = {
    "ftmo": ["ftmo", "quantic", "ftmo.com"],
    "the5ers": ["5ers", "the5ers", "5%ers", "fivers"],
    "fundednext": ["fundednext", "funded next", "fn-"],
    "myforexfunds": ["myforexfunds", "mff", "my forex funds"],
    "topstep": ["topstep", "topsteptrader", "tsxp"],
    "e8funding": ["e8 funding", "e8funding", "e8-"],
    "alphaCapital": ["alpha capital", "alphacapital", "acg-"]
}


def detect_prop_firm(broker_name: str, server_name: str = "") -> Optional[str]:
    """
    Detect prop firm from broker name or server name
    Returns the key from PROP_FIRM_DATABASE or None if not detected
    """
    if not broker_name:
        return None
    
    combined = (broker_name + " " + server_name).lower()
    
    for firm_key, patterns in BROKER_PATTERNS.items():
        for pattern in patterns:
            if pattern in combined:
                return firm_key
    
    return None


def get_prop_firm_rules(firm_key: str) -> Optional[PropFirmRules]:
    """Get rules for a specific prop firm"""
    return PROP_FIRM_DATABASE.get(firm_key.lower())


def get_all_prop_firms() -> List[str]:
    """Get list of all supported prop firm names"""
    return [rules.firm_name for rules in PROP_FIRM_DATABASE.values()]


def get_rules_for_broker(broker_name: str, server_name: str = "") -> Dict:
    """
    Main function to get prop firm rules from broker name
    Returns a dict with firm info, rules, and AI summary
    """
    firm_key = detect_prop_firm(broker_name, server_name)
    
    if not firm_key:
        return {
            "detected": False,
            "message": "Prop firm tespit edilemedi. Manuel olarak ayarlayabilirsiniz.",
            "supported_firms": get_all_prop_firms()
        }
    
    rules = PROP_FIRM_DATABASE[firm_key]
    
    return {
        "detected": True,
        "firm_key": firm_key,
        "firm_name": rules.firm_name,
        "rules": {
            "max_drawdown": rules.max_drawdown,
            "daily_drawdown": rules.daily_drawdown,
            "news_trading_allowed": rules.news_trading_allowed,
            "news_buffer_minutes": rules.news_buffer_minutes,
            "weekend_holding_allowed": rules.weekend_holding_allowed,
            "consistency_rule": rules.consistency_rule,
            "consistency_max_day_profit_pct": rules.consistency_max_day_profit_pct,
            "min_trading_days": rules.min_trading_days,
            "profit_split": rules.profit_split,
            "special_rules": rules.special_rules
        },
        "ai_summary": rules.ai_summary,
        "warnings": generate_current_warnings(rules)
    }


def generate_current_warnings(rules: PropFirmRules) -> List[str]:
    """Generate current warnings based on time and rules"""
    warnings = []
    now = datetime.now()
    
    # Weekend warning
    if now.weekday() >= 4:  # Friday or later
        if not rules.weekend_holding_allowed:
            if now.weekday() == 4:  # Friday
                warnings.append("⚠️ CUMA: Hafta sonu pozisyon tutma yasak! Pozisyonları kapatmayı unutma.")
            else:
                warnings.append("🔴 HAFTA SONU: Bu firma hafta sonu pozisyon tutmaya izin vermiyor!")
    
    # News trading reminder (general, would need economic calendar integration)
    if not rules.news_trading_allowed:
        warnings.append(f"📰 Yüksek etkili haberlerden {rules.news_buffer_minutes} dk önce/sonra işlem açma!")
    
    # Low drawdown warning
    if rules.max_drawdown <= 5:
        warnings.append(f"🎯 DÜŞÜK DRAWDOWN: Max {rules.max_drawdown}% - çok muhafazakar ol!")
    
    if rules.daily_drawdown <= 3:
        warnings.append(f"🎯 DÜŞÜK GÜNLÜK LİMİT: Max {rules.daily_drawdown}% - pozisyon başına max %0.5 risk!")
    
    # Consistency rule warning
    if rules.consistency_rule:
        warnings.append(f"📊 TUTARLILIK: Tek günde max %{rules.consistency_max_day_profit_pct} kar katkısı!")
    
    return warnings


def get_risk_recommendations(rules: PropFirmRules, current_drawdown: float, daily_loss: float) -> Dict:
    """Get specific risk recommendations based on current state"""
    dd_usage = (current_drawdown / rules.max_drawdown) * 100
    daily_usage = (daily_loss / rules.daily_drawdown) * 100 if rules.daily_drawdown > 0 else 0
    
    # Calculate safe position size
    remaining_dd = rules.max_drawdown - current_drawdown
    remaining_daily = rules.daily_drawdown - daily_loss
    
    # Recommended risk per trade
    if dd_usage > 80 or daily_usage > 80:
        recommended_risk = 0.25
        status = "critical"
        message = "🔴 KRİTİK: Çok düşük risk al veya bugün işlem yapma!"
    elif dd_usage > 60 or daily_usage > 60:
        recommended_risk = 0.5
        status = "warning"
        message = "🟠 DİKKAT: Riski azalt, seçici ol!"
    elif dd_usage > 40 or daily_usage > 40:
        recommended_risk = 1.0
        status = "caution"
        message = "🟡 NORMAL: Standart risk yönetimi uygula"
    else:
        recommended_risk = min(2.0, remaining_dd / 3, remaining_daily / 2)
        status = "safe"
        message = "🟢 GÜVENLİ: Normal stratejini uygulayabilirsin"
    
    return {
        "status": status,
        "message": message,
        "recommended_risk_per_trade": round(recommended_risk, 2),
        "remaining_drawdown": round(remaining_dd, 2),
        "remaining_daily_limit": round(remaining_daily, 2),
        "drawdown_usage_pct": round(dd_usage, 1),
        "daily_usage_pct": round(daily_usage, 1)
    }
