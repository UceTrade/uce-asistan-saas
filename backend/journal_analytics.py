"""
Journal Analytics - Advanced trade performance analysis
Provides hour-based, day-based, and symbol-based performance insights
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from mt5_proxy import mt5


class JournalAnalytics:
    """
    Advanced analytics for trading journal data
    Provides deep insights into trading patterns and performance
    """
    
    def __init__(self, journal_manager):
        """
        Initialize with a JournalManager instance for data access
        
        Args:
            journal_manager: JournalManager instance
        """
        self.journal = journal_manager
    
    def get_full_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get comprehensive analytics report
        
        Returns:
            Complete analytics object with all metrics
        """
        trades = self.journal.get_trade_history(days)
        
        if isinstance(trades, dict) and 'error' in trades:
            return {'error': trades['error']}
        
        if not trades:
            return self._empty_analytics()
        
        df = pd.DataFrame(trades)
        df['time'] = pd.to_datetime(df['time'])
        df['hour'] = df['time'].dt.hour
        df['day_of_week'] = df['time'].dt.dayofweek  # 0=Monday, 6=Sunday
        df['day_name'] = df['time'].dt.day_name()
        df['date'] = df['time'].dt.date
        df['is_win'] = df['profit'] > 0
        
        return {
            'summary': self._get_summary(df),
            'hourly_performance': self._get_hourly_performance(df),
            'daily_performance': self._get_daily_performance(df),
            'symbol_performance': self._get_symbol_performance(df),
            'emotion_analysis': self._get_emotion_analysis(df),
            'strategy_performance': self._get_strategy_performance(df),
            'streaks': self._get_streaks(df),
            'risk_metrics': self._get_risk_metrics(df),
            'calendar_heatmap': self._get_calendar_heatmap(df),
            'recommendations': self._generate_recommendations(df)
        }
    
    def _empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            'summary': {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'net_profit': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'expectancy': 0
            },
            'hourly_performance': [],
            'daily_performance': [],
            'symbol_performance': [],
            'emotion_analysis': [],
            'strategy_performance': [],
            'streaks': {'current': 0, 'best_win': 0, 'worst_loss': 0},
            'risk_metrics': {},
            'calendar_heatmap': [],
            'recommendations': []
        }
    
    def _get_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get overall trading summary"""
        total_trades = len(df)
        winning_trades = df[df['profit'] > 0]
        losing_trades = df[df['profit'] <= 0]
        
        win_count = len(winning_trades)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        gross_profit = winning_trades['profit'].sum() if not winning_trades.empty else 0
        gross_loss = abs(losing_trades['profit'].sum()) if not losing_trades.empty else 0
        
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0
        net_profit = df['profit'].sum()
        
        avg_win = winning_trades['profit'].mean() if not winning_trades.empty else 0
        avg_loss = abs(losing_trades['profit'].mean()) if not losing_trades.empty else 0
        
        # Expectancy = (Win Rate * Avg Win) - (Loss Rate * Avg Loss)
        loss_rate = 100 - win_rate
        expectancy = ((win_rate/100) * avg_win) - ((loss_rate/100) * avg_loss)
        
        return {
            'total_trades': total_trades,
            'win_count': win_count,
            'loss_count': total_trades - win_count,
            'win_rate': round(win_rate, 2),
            'profit_factor': round(profit_factor, 2),
            'net_profit': round(net_profit, 2),
            'gross_profit': round(gross_profit, 2),
            'gross_loss': round(gross_loss, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'expectancy': round(expectancy, 2),
            'avg_trade': round(net_profit / total_trades, 2) if total_trades > 0 else 0
        }
    
    def _get_hourly_performance(self, df: pd.DataFrame) -> List[Dict]:
        """
        Analyze performance by hour of the day
        Helps identify best and worst trading hours
        """
        hourly_stats = []
        
        for hour in range(24):
            hour_df = df[df['hour'] == hour]
            if len(hour_df) == 0:
                continue
                
            wins = hour_df[hour_df['profit'] > 0]
            
            hourly_stats.append({
                'hour': hour,
                'hour_label': f"{hour:02d}:00",
                'trade_count': len(hour_df),
                'win_rate': round(len(wins) / len(hour_df) * 100, 2),
                'net_profit': round(hour_df['profit'].sum(), 2),
                'avg_profit': round(hour_df['profit'].mean(), 2)
            })
        
        # Sort by profit
        hourly_stats.sort(key=lambda x: x['net_profit'], reverse=True)
        
        return hourly_stats
    
    def _get_daily_performance(self, df: pd.DataFrame) -> List[Dict]:
        """
        Analyze performance by day of week
        Helps identify best and worst trading days
        """
        days_turkish = {
            'Monday': 'Pazartesi',
            'Tuesday': 'Salı',
            'Wednesday': 'Çarşamba',
            'Thursday': 'Perşembe',
            'Friday': 'Cuma',
            'Saturday': 'Cumartesi',
            'Sunday': 'Pazar'
        }
        
        daily_stats = []
        
        for day_num in range(7):
            day_df = df[df['day_of_week'] == day_num]
            if len(day_df) == 0:
                continue
                
            wins = day_df[day_df['profit'] > 0]
            day_name = day_df['day_name'].iloc[0] if not day_df.empty else ''
            
            daily_stats.append({
                'day_of_week': day_num,
                'day_name': day_name,
                'day_name_tr': days_turkish.get(day_name, day_name),
                'trade_count': len(day_df),
                'win_rate': round(len(wins) / len(day_df) * 100, 2),
                'net_profit': round(day_df['profit'].sum(), 2),
                'avg_profit': round(day_df['profit'].mean(), 2)
            })
        
        # Sort by profit
        daily_stats.sort(key=lambda x: x['net_profit'], reverse=True)
        
        return daily_stats
    
    def _get_symbol_performance(self, df: pd.DataFrame) -> List[Dict]:
        """
        Analyze performance by trading symbol
        Helps identify most profitable pairs
        """
        symbol_stats = []
        
        for symbol in df['symbol'].unique():
            sym_df = df[df['symbol'] == symbol]
            wins = sym_df[sym_df['profit'] > 0]
            
            symbol_stats.append({
                'symbol': symbol,
                'trade_count': len(sym_df),
                'win_rate': round(len(wins) / len(sym_df) * 100, 2),
                'net_profit': round(sym_df['profit'].sum(), 2),
                'avg_profit': round(sym_df['profit'].mean(), 2),
                'max_win': round(sym_df['profit'].max(), 2),
                'max_loss': round(sym_df['profit'].min(), 2)
            })
        
        # Sort by profit
        symbol_stats.sort(key=lambda x: x['net_profit'], reverse=True)
        
        return symbol_stats
    
    def _get_emotion_analysis(self, df: pd.DataFrame) -> List[Dict]:
        """
        Analyze performance by emotional state
        Reveals impact of psychology on trading
        """
        emotion_labels = {
            'calm': '😌 Sakin',
            'anxious': '😰 Endişeli',
            'greedy': '🤑 Açgözlü',
            'revenge': '😡 İntikam',
            'fearful': '😨 Korkulu',
            'confident': '😎 Özgüvenli',
            'neutral': '😐 Nötr',
            '': '❓ Belirtilmemiş'
        }
        
        emotion_stats = []
        
        for emotion in df['emotion'].unique():
            emo_df = df[df['emotion'] == emotion]
            wins = emo_df[emo_df['profit'] > 0]
            
            emotion_stats.append({
                'emotion': emotion,
                'emotion_label': emotion_labels.get(emotion, emotion),
                'trade_count': len(emo_df),
                'win_rate': round(len(wins) / len(emo_df) * 100, 2),
                'net_profit': round(emo_df['profit'].sum(), 2),
                'avg_profit': round(emo_df['profit'].mean(), 2)
            })
        
        # Sort by trade count
        emotion_stats.sort(key=lambda x: x['trade_count'], reverse=True)
        
        return emotion_stats
    
    def _get_strategy_performance(self, df: pd.DataFrame) -> List[Dict]:
        """
        Analyze performance by strategy tag
        """
        strategy_stats = []
        
        for strategy in df['strategy'].unique():
            if not strategy:  # Skip empty strategies
                continue
                
            strat_df = df[df['strategy'] == strategy]
            wins = strat_df[strat_df['profit'] > 0]
            
            strategy_stats.append({
                'strategy': strategy,
                'trade_count': len(strat_df),
                'win_rate': round(len(wins) / len(strat_df) * 100, 2),
                'net_profit': round(strat_df['profit'].sum(), 2),
                'avg_profit': round(strat_df['profit'].mean(), 2)
            })
        
        # Sort by profit
        strategy_stats.sort(key=lambda x: x['net_profit'], reverse=True)
        
        return strategy_stats
    
    def _get_streaks(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Calculate win/loss streaks
        """
        if df.empty:
            return {'current': 0, 'best_win': 0, 'worst_loss': 0}
        
        # Sort by time ascending
        df_sorted = df.sort_values('time')
        
        wins = df_sorted['profit'] > 0
        
        # Calculate streaks
        current_streak = 0
        best_win_streak = 0
        worst_loss_streak = 0
        streak = 0
        last_win = None
        
        for is_win in wins:
            if last_win is None:
                streak = 1
                last_win = is_win
            elif is_win == last_win:
                streak += 1
            else:
                if last_win:
                    best_win_streak = max(best_win_streak, streak)
                else:
                    worst_loss_streak = max(worst_loss_streak, streak)
                streak = 1
                last_win = is_win
        
        # Check final streak
        if last_win:
            best_win_streak = max(best_win_streak, streak)
            current_streak = streak
        else:
            worst_loss_streak = max(worst_loss_streak, streak)
            current_streak = -streak
        
        return {
            'current': current_streak,  # Positive = win streak, Negative = loss streak
            'best_win': best_win_streak,
            'worst_loss': worst_loss_streak
        }
    
    def _get_risk_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate risk-adjusted performance metrics
        """
        if df.empty:
            return {}
        
        profits = df['profit'].values
        
        # Calculate Sharpe-like ratio (simplified)
        mean_profit = np.mean(profits)
        std_profit = np.std(profits)
        sharpe = (mean_profit / std_profit) if std_profit > 0 else 0
        
        # Maximum Drawdown (simplified)
        cumsum = np.cumsum(profits)
        running_max = np.maximum.accumulate(cumsum)
        drawdowns = running_max - cumsum
        max_drawdown = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        # Recovery Factor
        total_profit = np.sum(profits)
        recovery_factor = (total_profit / max_drawdown) if max_drawdown > 0 else 0
        
        return {
            'sharpe_ratio': round(sharpe, 3),
            'max_drawdown': round(max_drawdown, 2),
            'recovery_factor': round(recovery_factor, 2),
            'profit_std_dev': round(std_profit, 2),
            'largest_win': round(df['profit'].max(), 2),
            'largest_loss': round(df['profit'].min(), 2)
        }
    
    def _get_calendar_heatmap(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate calendar heatmap data for trades
        """
        if df.empty:
            return []
        
        # Group by date
        daily = df.groupby('date').agg({
            'profit': 'sum',
            'ticket': 'count'
        }).reset_index()
        daily.columns = ['date', 'profit', 'trade_count']
        
        heatmap = []
        for _, row in daily.iterrows():
            heatmap.append({
                'date': str(row['date']),
                'profit': round(row['profit'], 2),
                'trade_count': int(row['trade_count']),
                'color': 'success' if row['profit'] > 0 else 'danger' if row['profit'] < 0 else 'neutral'
            })
        
        return heatmap
    
    def _generate_recommendations(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate AI-powered trading recommendations based on patterns
        """
        recommendations = []
        
        if df.empty:
            return [{'type': 'info', 'message': 'Henüz yeterli veri yok. İşlem yapmaya devam edin.'}]
        
        # Analyze hourly data
        hourly = self._get_hourly_performance(df)
        if hourly:
            best_hours = [h for h in hourly if h['win_rate'] >= 60][:3]
            worst_hours = [h for h in sorted(hourly, key=lambda x: x['win_rate']) if h['trade_count'] >= 3][:2]
            
            if best_hours:
                hours_str = ', '.join([h['hour_label'] for h in best_hours])
                recommendations.append({
                    'type': 'success',
                    'category': 'Saat Analizi',
                    'message': f"En iyi performans saatleriniz: {hours_str}. Bu saatlerde işlem yapmayı tercih edin.",
                    'icon': '⏰'
                })
            
            if worst_hours and worst_hours[0]['win_rate'] < 40:
                hours_str = ', '.join([h['hour_label'] for h in worst_hours])
                recommendations.append({
                    'type': 'danger',
                    'category': 'Saat Analizi',
                    'message': f"Dikkat! {hours_str} saatlerinde kazanma oranınız düşük. Bu saatlerde dikkatli olun.",
                    'icon': '⚠️'
                })
        
        # Analyze daily data
        daily = self._get_daily_performance(df)
        if daily:
            best_day = daily[0] if daily else None
            worst_day = sorted(daily, key=lambda x: x['win_rate'])[0] if daily else None
            
            if best_day and best_day['win_rate'] >= 60:
                recommendations.append({
                    'type': 'success',
                    'category': 'Gün Analizi',
                    'message': f"{best_day['day_name_tr']} günleri en iyi gününüz (%{best_day['win_rate']} kazanma).",
                    'icon': '📅'
                })
            
            if worst_day and worst_day['win_rate'] < 40 and worst_day['trade_count'] >= 5:
                recommendations.append({
                    'type': 'warning',
                    'category': 'Gün Analizi',
                    'message': f"{worst_day['day_name_tr']} günleri dikkatli olun (%{worst_day['win_rate']} kazanma).",
                    'icon': '📅'
                })
        
        # Analyze emotions
        emotions = self._get_emotion_analysis(df)
        for emo in emotions:
            if emo['emotion'] == 'revenge' and emo['trade_count'] >= 2:
                recommendations.append({
                    'type': 'danger',
                    'category': 'Psikoloji',
                    'message': f"İntikam işlemlerinde ${abs(emo['net_profit']):.2f} {'kayıp' if emo['net_profit'] < 0 else 'kazanç'}. İntikam işlemlerinden kaçının!",
                    'icon': '🧠'
                })
            elif emo['emotion'] == 'calm' and emo['win_rate'] >= 60:
                recommendations.append({
                    'type': 'success',
                    'category': 'Psikoloji',
                    'message': f"Sakin olduğunuzda %{emo['win_rate']} kazanma oranınız var. Duygusal kontrol önemli!",
                    'icon': '🧘'
                })
        
        # Symbol insights
        symbols = self._get_symbol_performance(df)
        if symbols and len(symbols) >= 2:
            best_symbol = symbols[0]
            if best_symbol['win_rate'] >= 55:
                recommendations.append({
                    'type': 'info',
                    'category': 'Sembol Analizi',
                    'message': f"{best_symbol['symbol']} sizin için en karlı sembol (${best_symbol['net_profit']:.2f}). Buraya odaklanın.",
                    'icon': '📊'
                })
        
        if not recommendations:
            recommendations.append({
                'type': 'info',
                'category': 'Genel',
                'message': 'Daha fazla veri toplandıkça kişiselleştirilmiş öneriler görünecek.',
                'icon': '📈'
            })
        
        return recommendations


# =========================================
# STANDALONE TEST
# =========================================
if __name__ == "__main__":
    from journal_manager import JournalManager
    
    jm = JournalManager()
    analytics = JournalAnalytics(jm)
    
    result = analytics.get_full_analytics(30)
    
    print("=== JOURNAL ANALYTICS TEST ===")
    print(f"Summary: {result.get('summary', {})}")
    print(f"Hourly Performance: {len(result.get('hourly_performance', []))} hours")
    print(f"Daily Performance: {len(result.get('daily_performance', []))} days")
    print(f"Symbol Performance: {len(result.get('symbol_performance', []))} symbols")
    print(f"Recommendations: {len(result.get('recommendations', []))} items")
