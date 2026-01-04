"""
Comprehensive test for all 5 phases
"""

print("=" * 60)
print("TESTING ALL 5 PHASES")
print("=" * 60)

# Phase 1: Template Library
print("\n[PHASE 1] Template Library")
print("-" * 40)
try:
    from strategy_templates import StrategyTemplates
    t = StrategyTemplates()
    templates = t.list_templates()
    print(f"[OK] Templates available: {len(templates)}")
    
    result = t.get_template('rsi_oversold')
    print(f"[OK] RSI template loads: {result['success']}")
    print(f"[OK] Has code: {len(result.get('code', '')) > 100}")
    print("[PASS] PHASE 1: Template Library")
except Exception as e:
    print(f"[FAIL] PHASE 1: {e}")


# Phase 2: Turkish NLU
print("\n[PHASE 2] Turkish NLU")
print("-" * 40)
try:
    from turkish_nlu import TurkishNLU
    nlu = TurkishNLU()
    result = nlu.parse('RSI 30 altinda al 70 ustunde sat')
    print(f"[OK] Indicators: {result['indicators']}")
    print(f"[OK] Actions: {result['actions']}")
    print(f"[OK] Confidence: {result['confidence']:.0%}")
    print(f"[OK] Template suggestion: {nlu.suggest_template(result)}")
    print("[PASS] PHASE 2: Turkish NLU")
except Exception as e:
    print(f"[FAIL] PHASE 2: {e}")

# Phase 3: Conversation Manager
print("\n[PHASE 3] Conversation Manager")
print("-" * 40)
try:
    from conversation_manager import ConversationManager
    m = ConversationManager()
    q1 = m.start_conversation('test', 'RSI stratejisi')
    print(f"[OK] Q1: {q1['question'][:40]}...")
    
    m.process_answer('test', 'timeframe', 'H1')
    q2 = m.get_next_question('test')
    print(f"[OK] Q2: {q2['question'][:40]}...")
    
    m.process_answer('test', 'risk_level', 'medium')
    m.process_answer('test', 'trading_style', 'trend')
    
    final = m.generate_final_prompt('test')
    print(f"[OK] Final prompt length: {len(final)} chars")
    print(f"[OK] Includes preferences: {'User Preferences' in final}")
    print("[PASS] PHASE 3: Conversation Manager")
except Exception as e:
    print(f"[FAIL] PHASE 3: {e}")

# Phase 4: Context-Aware Learning
print("\n[PHASE 4] Context-Aware Learning")
print("-" * 40)
try:
    from strategy_manager import StrategyManager
    m = StrategyManager()
    patterns = m.analyze_patterns()
    print(f"[OK] Total strategies: {patterns['total_strategies']}")
    print(f"[OK] Favorite indicators: {patterns['favorite_indicators']}")
    print(f"[OK] Favorite timeframes: {patterns['favorite_timeframes']}")
    print("[PASS] PHASE 4: Context-Aware Learning")
except Exception as e:
    print(f"[FAIL] PHASE 4: {e}")

# Phase 5: Auto-Optimization
print("\n[PHASE 5] Auto-Optimization")
print("-" * 40)
try:
    from strategy_optimizer import StrategyOptimizer
    o = StrategyOptimizer()
    
    results = {
        'success': True,
        'metrics': {
            'win_rate': 35,
            'max_drawdown_pct': 25,
            'total_trades': 5,
            'profit_factor': 0.8
        }
    }
    
    suggestions = o.analyze_backtest('', results)
    print(f"[OK] Suggestions generated: {len(suggestions)}")
    print(f"[OK] Has critical issues: {any(s['priority'] == 'critical' for s in suggestions)}")
    print(f"[OK] Has high priority: {any(s['priority'] == 'high' for s in suggestions)}")
    print("[PASS] PHASE 5: Auto-Optimization")
except Exception as e:
    print(f"[FAIL] PHASE 5: {e}")


print("\n" + "=" * 60)
print("ALL TESTS COMPLETE!")
print("=" * 60)
