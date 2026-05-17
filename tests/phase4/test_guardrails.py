from src.phase4_guardrails.guardrails import InputGuard, OutputGuard

def test_input_guard():
    guard = InputGuard()
    
    # Safe query
    safe, msg = guard.check_query("What is the expense ratio?")
    assert safe is True
    assert msg == ""
    
    # Unsafe query
    safe, msg = guard.check_query("Should I invest in this fund?")
    assert safe is False
    assert "SEBI-registered" in msg

def test_output_guard():
    guard = OutputGuard()
    
    # Safe response
    safe_text = "The NAV is 100."
    assert guard.check_response(safe_text) == safe_text
    
    # Unsafe response
    unsafe_text = "I recommend you buy this fund immediately."
    assert "flagged" in guard.check_response(unsafe_text)
