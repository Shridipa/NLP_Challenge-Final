import json
import sys
import os
from transformers import pipeline

classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")

def detect_intent(query, context=""):
    """Detects the intent of a user query using a zero-shot classifier."""
    intent_map = {
        "asking for financial data, annual report stats, or company business summary": "ask_finance",
        "asking about HR policies, employee benefits, headcount numbers, or leave management": "ask_hr",
        "asking for internal IT guidelines, cybersecurity policies, or company rules": "ask_it_policy",
        "asking technical questions about software development, code, or engineering architecture": "ask_dev",
        "reporting a technical problem, broken hardware, slow laptop, or requesting a fix": "action_ticket",
        "requesting application access, logins, permissions, or password resets": "action_access",
        "scheduling a meeting, calendar booking, or arranging a call": "action_schedule",
        "questions about company leaders, executives, CEO, chairman, or notable people": "ask_people",
        "a general greeting or conversation that does not require an action or database search": "other"
    }
    
    candidate_labels = list(intent_map.keys())
    results = classifier(query, candidate_labels)
    
    best_label = results['labels'][0]
    top_intent = intent_map[best_label]
    confidence = results['scores'][0]
    
    if confidence < 0.7:
        keyword_maps = {
            "ask_people": ["ceo", "cfo", "chairman", "chairperson", "leader", "executive", "founder", "roshni", "nadar", "shiv", "vijaykumar", "management", "directors", "chairwoman", "who is", "who are"],
            "ask_hr": ["policy", "leave", "holiday", "benefit", "payroll", "salary", "pf", "insurance", "hr", "recruitment", "headcount", "employees", "workers"],
            "action_access": ["password", "reset", "access", "login", "permission", "account", "vpn", "mfa", "outlook", "teams"],
            "action_ticket": ["broken", "not working", "fail", "error", "laptop", "monitor", "hardware", "fix", "repair", "ticket", "issue"],
            "ask_finance": ["revenue", "profit", "ebitda", "margin", "growth", "financial", "expenditure", "cost", "dividend", "shareholder", "earnings", "cagr", "turnover"]
        }
        
        override_intent = None
        for intent_key, keywords in keyword_maps.items():
            if any(k in query.lower() for k in keywords):
                override_intent = intent_key
                break
        
        if override_intent:
            top_intent = override_intent
            confidence = 0.85
            rationale = f"Keyword match for '{override_intent}' found."
        else:
            top_intent = "other"
            rationale = f"Low confidence ({confidence:.2f}) and no keyword match."
    else:
        rationale = f"Classified as '{best_label}' with {confidence:.2f} confidence."
    
    return {
        "intent": top_intent,
        "confidence": confidence,
        "rationale": rationale
    }

if __name__ == "__main__":
    test_query = sys.argv[1] if len(sys.argv) > 1 else "What was HCLTech's revenue growth?"
    try:
        result = detect_intent(test_query)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")
