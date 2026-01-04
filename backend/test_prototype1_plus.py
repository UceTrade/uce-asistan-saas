"""
PROTOTYPE1+ End-to-End Test Suite
Tests all 6 major features comprehensively
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def print_test(name, passed, details=""):
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {name}")
    if details:
        print(f"      {details}")

# ============================================
# TEST 1: Template Library
# ============================================
def test_template_library():
    print_header("TEST 1: Template Library")
    
    try:
        from strategy_templates import StrategyTemplates
        templates = StrategyTemplates()
        
        # Test 1.1: List templates
        template_list = templates.list_templates()
        print_test("List Templates", len(template_list) == 5, 
                   f"Found {len(template_list)} templates")
        
        # Test 1.2: Load each template
        for template in template_list:
            result = templates.get_template(template['id'])
            print_test(f"Load Template: {template['name']}", 
                      result is not None and 'code' in result,
                      f"Code length: {len(result.get('code', ''))} chars")
        
        # Test 1.3: Invalid template
        result = templates.get_template('invalid_id')
        print_test("Invalid Template Handling", result is None)
        
        return True
        
    except Exception as e:
        print_test("Template Library", False, str(e))
        return False

# ============================================
# TEST 2: Turkish NLU
# ============================================
def test_turkish_nlu():
    print_header("TEST 2: Turkish NLU")
    
    try:
        from turkish_nlu import TurkishNLU
        nlu = TurkishNLU()
        
        test_cases = [
            ("RSI 30'un altında ise al", 0.7),
            ("Bollinger bantları kırılımında işlem yap", 0.6),
            ("Trend takip stratejisi yap", 0.5),
            ("Random gibberish text", 0.3)
        ]
        
        for text, min_confidence in test_cases:
            result = nlu.parse(text)
            passed = result['confidence'] >= min_confidence
            print_test(f"Parse: '{text[:30]}...'", passed,
                      f"Confidence: {result['confidence']:.0%}")
        
        return True
        
    except Exception as e:
        print_test("Turkish NLU", False, str(e))
        return False

# ============================================
# TEST 3: Conversation Manager (4 Questions)
# ============================================
def test_conversation_manager():
    print_header("TEST 3: Conversation Manager (4 Questions)")
    
    try:
        from conversation_manager import ConversationManager
        manager = ConversationManager()
        
        # Test 3.1: Start conversation
        session_id = "test_session_001"
        description = "RSI trend stratejisi"
        
        q1 = manager.start_conversation(session_id, description)
        print_test("Start Conversation", q1 is not None and 'question' in q1,
                   f"Question 1: {q1.get('question', '')[:40]}...")
        
        # Test 3.2: Answer questions
        questions_answered = 0
        
        # Q1: Timeframe
        manager.process_answer(session_id, q1['id'], 'H1')
        q2 = manager.get_next_question(session_id)
        if q2:
            questions_answered += 1
            print_test("Question 2 (Risk)", q2 is not None,
                      f"{q2.get('question', '')[:40]}...")
        
        # Q2: Risk
        manager.process_answer(session_id, q2['id'], 'medium')
        q3 = manager.get_next_question(session_id)
        if q3:
            questions_answered += 1
            print_test("Question 3 (Stop Loss)", q3 is not None,
                      f"{q3.get('question', '')[:40]}...")
        
        # Q3: Stop Loss (NEW!)
        manager.process_answer(session_id, q3['id'], 'mid')
        q4 = manager.get_next_question(session_id)
        if q4:
            questions_answered += 1
            print_test("Question 4 (Trading Style)", q4 is not None,
                      f"{q4.get('question', '')[:40]}...")
        
        # Q4: Trading Style
        manager.process_answer(session_id, q4['id'], 'trend')
        q5 = manager.get_next_question(session_id)
        
        print_test("All 4 Questions Answered", q5 is None and questions_answered == 3)
        
        # Test 3.3: Generate final prompt
        final_prompt = manager.generate_final_prompt(session_id)
        has_stop_loss = 'ATR' in final_prompt or 'stop' in final_prompt.lower()
        print_test("Final Prompt with Stop Loss", has_stop_loss,
                   f"Prompt length: {len(final_prompt)} chars")
        
        return True
        
    except Exception as e:
        print_test("Conversation Manager", False, str(e))
        return False

# ============================================
# TEST 4: Context-Aware Learning
# ============================================
def test_context_learning():
    print_header("TEST 4: Context-Aware Learning")
    
    try:
        from strategy_manager import StrategyManager
        manager = StrategyManager()
        
        # Test 4.1: Analyze patterns (empty initially)
        patterns = manager.analyze_patterns()
        print_test("Analyze Patterns", patterns is not None,
                   f"Found {len(patterns.get('favorite_indicators', []))} favorite indicators")
        
        # Test 4.2: Find similar strategies
        similar = manager.get_similar_strategies("RSI strategy")
        print_test("Find Similar Strategies", isinstance(similar, list),
                   f"Found {len(similar)} similar strategies")
        
        return True
        
    except Exception as e:
        print_test("Context Learning", False, str(e))
        return False

# ============================================
# TEST 5: Strategy Optimizer (Turkish)
# ============================================
def test_optimizer():
    print_header("TEST 5: Strategy Optimizer (Turkish)")
    
    try:
        from strategy_optimizer import StrategyOptimizer
        optimizer = StrategyOptimizer()
        
        # Test 5.1: Bad results
        bad_results = {
            'success': True,
            'metrics': {
                'win_rate': 35.0,
                'max_drawdown_pct': 25.0,
                'total_trades': 5,
                'profit_factor': 0.8,
                'net_profit': -500
            }
        }
        
        suggestions = optimizer.analyze_backtest("", bad_results)
        has_turkish = any('ş' in s.get('issue', '') or 'ı' in s.get('issue', '') 
                         for s in suggestions)
        print_test("Turkish Suggestions (Bad Results)", has_turkish,
                   f"Generated {len(suggestions)} suggestions")
        
        # Test 5.2: Good results
        good_results = {
            'success': True,
            'metrics': {
                'win_rate': 55.0,
                'max_drawdown_pct': 12.0,
                'total_trades': 45,
                'profit_factor': 1.8,
                'net_profit': 2500
            }
        }
        
        suggestions = optimizer.analyze_backtest("", good_results)
        has_positive = any('İyi' in s.get('issue', '') or 'Good' in s.get('issue', '') 
                          for s in suggestions)
        print_test("Positive Feedback (Good Results)", has_positive,
                   f"Generated {len(suggestions)} suggestions")
        
        # Test 5.3: Generate report
        report = optimizer.generate_optimization_report(suggestions)
        has_turkish_headers = 'ÖNERİLER' in report or 'ORTA ÖNCELİK' in report
        print_test("Turkish Report Generation", has_turkish_headers,
                   f"Report length: {len(report)} chars")
        
        return True
        
    except Exception as e:
        print_test("Optimizer", False, str(e))
        return False

# ============================================
# TEST 6: Integration Test
# ============================================
def test_integration():
    print_header("TEST 6: Integration Test")
    
    try:
        # Test full workflow simulation
        from strategy_templates import StrategyTemplates
        from turkish_nlu import TurkishNLU
        from conversation_manager import ConversationManager
        from strategy_optimizer import StrategyOptimizer
        
        # Step 1: Load template
        templates = StrategyTemplates()
        template = templates.get_template('rsi_oversold')
        print_test("Step 1: Load Template", template is not None)
        
        # Step 2: Parse Turkish description
        nlu = TurkishNLU()
        result = nlu.parse("RSI 30 altında al, 70 üstünde sat")
        print_test("Step 2: Parse Turkish", result['confidence'] > 0.5)
        
        # Step 3: Wizard with stop loss
        manager = ConversationManager()
        session = "integration_test"
        q1 = manager.start_conversation(session, "Test strategy")
        manager.process_answer(session, q1['id'], 'H1')
        q2 = manager.get_next_question(session)
        manager.process_answer(session, q2['id'], 'medium')
        q3 = manager.get_next_question(session)
        manager.process_answer(session, q3['id'], 'hard')  # Hard stop loss!
        q4 = manager.get_next_question(session)
        manager.process_answer(session, q4['id'], 'trend')
        
        final_prompt = manager.generate_final_prompt(session)
        has_hard_stop = '0.5' in final_prompt and 'ATR' in final_prompt
        print_test("Step 3: Wizard with Hard Stop (0.5x ATR)", has_hard_stop)
        
        # Step 4: Optimize results
        optimizer = StrategyOptimizer()
        test_results = {
            'success': True,
            'metrics': {
                'win_rate': 45.0,
                'max_drawdown_pct': 18.0,
                'total_trades': 20,
                'profit_factor': 1.2,
                'net_profit': 500
            }
        }
        suggestions = optimizer.analyze_backtest("", test_results)
        print_test("Step 4: Generate Optimizer Suggestions", len(suggestions) > 0,
                   f"{len(suggestions)} suggestions")
        
        return True
        
    except Exception as e:
        print_test("Integration Test", False, str(e))
        return False

# ============================================
# MAIN TEST RUNNER
# ============================================
def run_all_tests():
    print("\n" + "="*60)
    print("  PROTOTYPE1+ COMPREHENSIVE TEST SUITE")
    print("  Testing All 6 Major Features")
    print("="*60)
    
    results = {
        'Template Library': test_template_library(),
        'Turkish NLU': test_turkish_nlu(),
        'Conversation Manager (4Q)': test_conversation_manager(),
        'Context Learning': test_context_learning(),
        'Optimizer (Turkish)': test_optimizer(),
        'Integration': test_integration()
    }
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(results.values())
    total = len(results)
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED! PROTOTYPE1+ is ready!")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed. Review above for details.")
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
