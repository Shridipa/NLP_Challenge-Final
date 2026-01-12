import json
import sys
import os
from transformers import pipeline

print(f"Loading global distilled classification model (valhalla/distilbart-mnli-12-1)...")
classifier = pipeline("zero-shot-classification", model="valhalla/distilbart-mnli-12-1")

def detect_intent(query, context=""):
    """
    Detects the intent of a user query using a zero-shot classifier.
    Labels: ask_finance, ask_hr, ask_it_policy, ask_dev, action_ticket, action_access, action_schedule, other.
    """
    # Mapping descriptive labels to the required keys
    intent_map = {
        "asking for financial data, annual report stats, leadership bios, or company business summary": "ask_finance",
        "asking about HR policies, employee benefits, headcount numbers, or leave management": "ask_hr",
        "asking for internal IT guidelines, cybersecurity policies, or company rules": "ask_it_policy",
        "asking technical questions about software development, code, or engineering architecture": "ask_dev",
        "reporting a technical problem, broken hardware, slow laptop, or requesting a fix": "action_ticket",
        "requesting application access, logins, permissions, or password resets": "action_access",
        "scheduling a meeting, calendar booking, or arranging a call": "action_schedule",
        "a general greeting or conversation that does not require an action or database search": "other"
    }
    
    candidate_labels = list(intent_map.keys())
    
    # Classifying intent
    results = classifier(query, candidate_labels)
    
    best_label = results['labels'][0]
    top_intent = intent_map[best_label]
    confidence = results['scores'][0]
    
    # Confidence threshold fallback
    if confidence < 0.3:
        top_intent = "other"
        rationale = f"Low confidence ({confidence:.2f}) on '{best_label}'. Defaulting to 'other'."
    else:
        rationale = f"Classified as '{best_label}' with {confidence:.2f} confidence."
    
    return {
        "intent": top_intent,
        "confidence": confidence,
        "rationale": rationale
    }

def llm_fallback_detect(query):
    return {
        "intent": "other",
        "confidence": 0.5,
        "rationale": "LLM fallback triggered (Mocked)."
    }

if __name__ == "__main__":
    test_query = sys.argv[1] if len(sys.argv) > 1 else "What was HCLTech's revenue growth?"
    try:
        result = detect_intent(test_query)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error in ML detection: {e}")
        result = llm_fallback_detect(test_query)
        print(json.dumps(result, indent=2))
