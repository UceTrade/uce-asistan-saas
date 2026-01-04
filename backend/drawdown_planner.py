"""
Drawdown Recovery Planner
Calculates recovery projections and provides risk-adjusted trading recommendations
"""

import numpy as np
from typing import Dict, Any
from datetime import datetime


class DrawdownRecoveryPlanner:
    """
    Calculates recovery projections and trading recommendations
    when account is in drawdown
    """
    
    def __init__(self):
        pass
    
    def calculate_recovery_plan(self, 
                                 current_balance: float,
                                 peak_balance: float,
                                 initial_balance: float,
                                 max_allowed_dd: float = 10.0,
                                 daily_loss_limit: float = 5.0,
                                 target_win_rate: float = 55,
                                 average_rr: float = 1.5) -> Dict[str, Any]:
        """
        Calculate recovery plan based on current drawdown state
        
        Args:
            current_balance: Current account balance
            peak_balance: Highest balance achieved
            initial_balance: Starting balance (for prop firm rules)
            max_allowed_dd: Maximum allowed drawdown percentage
            daily_loss_limit: Daily loss limit percentage
            target_win_rate: Expected win rate (%)
            average_rr: Expected risk:reward ratio
            
        Returns:
            Complete recovery plan with projections
        """
        # Current drawdown calculations
        current_dd_from_peak = ((peak_balance - current_balance) / peak_balance) * 100
        current_dd_from_initial = ((initial_balance - current_balance) / initial_balance) * 100 if current_balance < initial_balance else 0
        
        # Determine which drawdown matters (prop firm usually cares about initial)
        effective_dd = max(current_dd_from_peak, current_dd_from_initial)
        
        # Remaining buffer
        remaining_dd_buffer = max_allowed_dd - effective_dd
        remaining_dd_amount = initial_balance * (remaining_dd_buffer / 100)
        
        # Amount to recover
        amount_to_recover = peak_balance - current_balance
        
        # Calculate required performance
        performance = self._calculate_required_performance(
            amount_to_recover,
            current_balance,
            target_win_rate,
            average_rr
        )
        
        # Risk recommendations
        risk_recs = self._generate_risk_recommendations(
            effective_dd,
            remaining_dd_buffer,
            current_balance
        )
        
        # Monte Carlo projection
        projection = self._monte_carlo_projection(
            current_balance,
            peak_balance,
            target_win_rate / 100,
            average_rr,
            remaining_dd_buffer
        )
        
        # Recovery status
        if effective_dd == 0:
            status = 'AT_PEAK'
            status_tr = '🏆 Zirvedeyiz'
            urgency = 'low'
        elif effective_dd < 3:
            status = 'MINOR_DD'
            status_tr = '✅ Küçük Düşüş'
            urgency = 'low'
        elif effective_dd < 6:
            status = 'MODERATE_DD'
            status_tr = '⚠️ Orta Düşüş'
            urgency = 'medium'
        elif effective_dd < 8:
            status = 'SIGNIFICANT_DD'
            status_tr = '🔶 Önemli Düşüş'
            urgency = 'high'
        else:
            status = 'CRITICAL_DD'
            status_tr = '🚨 Kritik Düşüş'
            urgency = 'critical'
        
        return {
            'current_state': {
                'balance': round(current_balance, 2),
                'peak_balance': round(peak_balance, 2),
                'initial_balance': round(initial_balance, 2),
                'drawdown_from_peak': round(current_dd_from_peak, 2),
                'drawdown_from_initial': round(current_dd_from_initial, 2),
                'effective_drawdown': round(effective_dd, 2),
                'amount_lost': round(amount_to_recover, 2)
            },
            'risk_status': {
                'status': status,
                'status_tr': status_tr,
                'urgency': urgency,
                'remaining_buffer_pct': round(remaining_dd_buffer, 2),
                'remaining_buffer_amount': round(remaining_dd_amount, 2),
                'max_allowed_dd': max_allowed_dd,
                'daily_loss_limit': daily_loss_limit
            },
            'recovery_metrics': performance,
            'recommendations': risk_recs,
            'projection': projection,
            'timestamp': datetime.now().isoformat()
        }
    
    def _calculate_required_performance(self, 
                                         amount_to_recover: float,
                                         current_balance: float,
                                         win_rate: float,
                                         rr_ratio: float) -> Dict[str, Any]:
        """Calculate required trading performance to recover"""
        if amount_to_recover <= 0:
            return {
                'trades_needed': 0,
                'profit_per_trade_pct': 0,
                'recovery_time_estimate': '0 gün'
            }
        
        # Expected profit per trade
        # E(profit) = (WinRate * AvgWin) - ((1-WinRate) * AvgLoss)
        # If RR = 1.5, then for every 1 unit of loss, we get 1.5 units of profit
        expected_profit_per_trade = (win_rate/100 * rr_ratio) - ((1 - win_rate/100) * 1)
        
        # If negative expectancy, recovery is not possible with current stats
        if expected_profit_per_trade <= 0:
            return {
                'trades_needed': 'N/A',
                'expectancy_negative': True,
                'message': 'Mevcut kazanma oranı ve R:R ile kurtarma mümkün değil',
                'suggestion': 'Kazanma oranını veya R:R oranını artırın'
            }
        
        # Assume risk 1% per trade
        risk_per_trade_pct = 1.0
        profit_per_trade_pct = expected_profit_per_trade * risk_per_trade_pct
        profit_per_trade_amount = current_balance * (profit_per_trade_pct / 100)
        
        # Trades needed
        trades_needed = int(np.ceil(amount_to_recover / profit_per_trade_amount)) if profit_per_trade_amount > 0 else 999
        
        # Time estimate (assume 2-3 trades per day)
        days_estimate = int(np.ceil(trades_needed / 2.5))
        
        if days_estimate <= 5:
            time_estimate = f'{days_estimate} gün'
        elif days_estimate <= 20:
            time_estimate = f'{int(np.ceil(days_estimate/5))} hafta'
        else:
            time_estimate = f'{int(np.ceil(days_estimate/20))} ay+'
        
        return {
            'trades_needed': trades_needed,
            'profit_per_trade_pct': round(profit_per_trade_pct, 3),
            'profit_per_trade_amount': round(profit_per_trade_amount, 2),
            'expectancy': round(expected_profit_per_trade, 3),
            'risk_per_trade_pct': risk_per_trade_pct,
            'recovery_time_estimate': time_estimate,
            'days_estimate': days_estimate,
            'assumed_trades_per_day': 2.5
        }
    
    def _generate_risk_recommendations(self,
                                        current_dd: float,
                                        remaining_buffer: float,
                                        current_balance: float) -> list:
        """Generate risk management recommendations"""
        recommendations = []
        
        # Lot size recommendations
        if current_dd >= 8:
            lot_suggestion = 'minimum (0.01)'
            risk_suggestion = '0.5%'
            recommendations.append({
                'type': 'critical',
                'icon': '🚨',
                'title': 'Lot Büyüklüğünü Minimuma İndir',
                'description': f'Kritik düşüş! Lot: {lot_suggestion}, Risk: {risk_suggestion}/trade'
            })
            recommendations.append({
                'type': 'critical',
                'icon': '⛔',
                'title': 'Günlük İşlem Limiti',
                'description': 'Maksimum 2 işlem/gün. Kayıptan sonra işlem yapma.'
            })
        elif current_dd >= 5:
            lot_suggestion = 'düşük (0.02-0.03)'
            risk_suggestion = '0.75%'
            recommendations.append({
                'type': 'warning',
                'icon': '⚠️',
                'title': 'Riski Azalt',
                'description': f'Lot: {lot_suggestion}, Risk: {risk_suggestion}/trade'
            })
            recommendations.append({
                'type': 'info',
                'icon': '📊',
                'title': 'Sadece A+ Setuplara Gir',
                'description': 'Sadece çoklu timeframe confluence olan işlemlere gir'
            })
        elif current_dd >= 2:
            recommendations.append({
                'type': 'info',
                'icon': '💡',
                'title': 'Dikkatli Ol',
                'description': 'Normal risk (%1) ile devam edebilirsin ama seçici ol'
            })
        else:
            recommendations.append({
                'type': 'success',
                'icon': '✅',
                'title': 'Güvenli Bölge',
                'description': 'Normal trading planınla devam edebilirsin'
            })
        
        # Buffer warnings
        if remaining_buffer < 2:
            recommendations.append({
                'type': 'critical',
                'icon': '🔴',
                'title': 'Acil Durum',
                'description': f'Sadece ${remaining_buffer}% buffer kaldı! İşlem yapmayı durdur ve analiz yap.'
            })
        elif remaining_buffer < 4:
            recommendations.append({
                'type': 'warning',
                'icon': '🟠',
                'title': 'Düşük Buffer',
                'description': f'${remaining_buffer:.1f}% buffer kaldı. Ekstra dikkatli ol.'
            })
        
        # Psychology recommendations
        if current_dd >= 5:
            recommendations.append({
                'type': 'psychology',
                'icon': '🧠',
                'title': 'Psikolojik Tavsiye',
                'description': 'Kaybı geri kazanmaya çalışma. Her işlem yeni bir başlangıç.'
            })
        
        return recommendations
    
    def _monte_carlo_projection(self,
                                 current_balance: float,
                                 target_balance: float,
                                 win_rate: float,
                                 rr_ratio: float,
                                 remaining_buffer: float,
                                 simulations: int = 1000,
                                 max_trades: int = 100) -> Dict[str, Any]:
        """Run Monte Carlo simulation for recovery probability"""
        if current_balance >= target_balance:
            return {
                'recovery_probability': 100,
                'bust_probability': 0,
                'message': 'Zaten hedefte veya üstünde'
            }
        
        risk_per_trade = 0.01  # 1%
        
        successes = 0
        busts = 0
        trade_counts = []
        
        bust_level = current_balance * (1 - (remaining_buffer / 100))
        
        for _ in range(simulations):
            balance = current_balance
            trades = 0
            
            while trades < max_trades:
                trades += 1
                
                # Random trade outcome
                if np.random.random() < win_rate:
                    # Win
                    balance += balance * risk_per_trade * rr_ratio
                else:
                    # Loss
                    balance -= balance * risk_per_trade
                
                # Check outcomes
                if balance >= target_balance:
                    successes += 1
                    trade_counts.append(trades)
                    break
                
                if balance <= bust_level:
                    busts += 1
                    break
            
        recovery_prob = (successes / simulations) * 100
        bust_prob = (busts / simulations) * 100
        avg_trades = np.mean(trade_counts) if trade_counts else 0
        
        return {
            'recovery_probability': round(recovery_prob, 1),
            'bust_probability': round(bust_prob, 1),
            'neutral_probability': round(100 - recovery_prob - bust_prob, 1),
            'avg_trades_to_recovery': round(avg_trades, 0) if avg_trades > 0 else 'N/A',
            'simulations': simulations,
            'assumptions': {
                'win_rate': win_rate * 100,
                'rr_ratio': rr_ratio,
                'risk_per_trade': risk_per_trade * 100
            }
        }


# Standalone test
if __name__ == "__main__":
    planner = DrawdownRecoveryPlanner()
    
    result = planner.calculate_recovery_plan(
        current_balance=9500,
        peak_balance=10000,
        initial_balance=10000,
        max_allowed_dd=10.0,
        daily_loss_limit=5.0,
        target_win_rate=55,
        average_rr=1.5
    )
    
    print("=== RECOVERY PLAN ===")
    print(f"Status: {result['risk_status']['status_tr']}")
    print(f"Drawdown: {result['current_state']['effective_drawdown']}%")
    print(f"Remaining Buffer: {result['risk_status']['remaining_buffer_pct']}%")
    print(f"Trades Needed: {result['recovery_metrics']['trades_needed']}")
    print(f"Recovery Probability: {result['projection']['recovery_probability']}%")
    print(f"Recommendations: {len(result['recommendations'])} items")
